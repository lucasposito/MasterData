from MayaData.data.base import BaseData
from MayaData.data.tree import Tree
from MayaData.lib import hash, decorator

from maya.api import OpenMaya

import copy

DEFAULT_DATA = {'name': str(), 'matrix': None, 'orient': list(), 'rotation': list(), 'radius': float(),
                'rotateOrder': float(), 'side': float(), 'type': float()}


def _get_attributes(joint):
    mfn_node = OpenMaya.MFnTransform(joint)
    data = copy.deepcopy(DEFAULT_DATA)
    data['name'] = mfn_node.partialPathName()
    data['matrix'] = list(mfn_node.transformationMatrix())

    orient_plug = mfn_node.findPlug('jointOrient', False)
    for i in range(orient_plug.numChildren()):
        data['orient'].append(orient_plug.child(i).asDouble())
    for j in ['rx', 'ry', 'rz']:
        data['rotation'].append(mfn_node.findPlug(j, False).asDouble())
    for k in ['radius', 'rotateOrder', 'side', 'type']:
        data[k] = mfn_node.findPlug(k, False).asDouble()

    return data


def _set_attributes(joint, attributes):
    mfn_node = OpenMaya.MFnTransform(joint)

    matrix = OpenMaya.MMatrix(attributes['matrix'])
    matrix = OpenMaya.MTransformationMatrix(matrix)

    translation = matrix.translation(OpenMaya.MSpace.kWorld)
    for i, translate in zip(['tx', 'ty', 'tz'], [translation.x, translation.y, translation.z]):
        mfn_node.findPlug(i, False).setDouble(translate)

    for j, rotate in zip(attributes['rotation'], ['rx', 'ry', 'rz']):
        mfn_node.findPlug(rotate, False).setDouble(j)

    orient_plug = mfn_node.findPlug('jointOrient', False)
    for k, orient in zip(attributes['orient'], range(orient_plug.numChildren())):
        orient_plug.child(orient).setDouble(k)

    mfn_node.findPlug('radius', False).setDouble(attributes['radius'])

    for l in ['rotateOrder', 'side', 'type']:
        mfn_node.findPlug(l, False).setInt(int(attributes[l]))


@decorator.timer()
def get(name):
    obj = OpenMaya.MSelectionList().add(name).getDependNode(0)
    dag_iter = OpenMaya.MItDag(OpenMaya.MItDag.kBreadthFirst, OpenMaya.MFn.kJoint)
    dag_iter.reset(obj)
    data = SkeletonData()

    while not dag_iter.isDone():
        attrs = _get_attributes(dag_iter.currentItem())
        data.get_bone(dag_iter.fullPathName(), attrs)
        dag_iter.next()

    return data


def _build_hierarchy(joint_data, parent=None):
    if not isinstance(joint_data, dict):
        return
    mod = OpenMaya.MDagModifier()
    jnt_obj = mod.createNode('joint', OpenMaya.MObject.kNullObj)
    
    if parent:
        mod.reparentNode(jnt_obj, parent)
        
    mod.renameNode(jnt_obj, joint_data['name'])
    mod.doIt()

    _set_attributes(jnt_obj, joint_data)

    for val in joint_data.values():
        _build_hierarchy(val, jnt_obj)


@decorator.timer()
def load(data=None):
    if not data:
        data = SkeletonData()
        data.load()

    for val in data.values():
        _build_hierarchy(val)
    return data


class SkeletonData(BaseData, Tree):
    def __init__(self, *args, **kwargs):
        super(SkeletonData, self).__init__(*args, **kwargs)

    def get_bone(self, full_path_name, attributes):
        int_name = hash.string_to_int(full_path_name)

        self.custom_node = attributes
        self.add_node(*int_name)
