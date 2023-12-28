from MayaData.data.base import BaseData
from MayaData.lib import get_node, decorator

from maya.api import OpenMaya, OpenMayaAnim
from maya import cmds


@decorator.timer()
def get(name):
    data = SkinData()
    data['geometry'] = name

    mfn_skin = get_node.skin_cluster(name)
    mfn_skin = OpenMayaAnim.MFnSkinCluster(mfn_skin)

    mesh_path = mfn_skin.getPathAtIndex(0)
    mesh_node = mesh_path.node()

    vertex_mfn = OpenMaya.MItMeshVertex(mesh_node)
    indices = range(vertex_mfn.count())

    id_component = OpenMaya.MFnSingleIndexedComponent()
    vtx_component = id_component.create(OpenMaya.MFn.kMeshVertComponent)
    id_component.addElements(indices)

    influence_objects = mfn_skin.influenceObjects()
    influences = [x.partialPathName() for x in influence_objects]

    wts, num_inf = mfn_skin.getWeights(mesh_path, vtx_component)
    data['weights'] = list(wts)
    data['influences'] = influences
    data['max_influence'] = mfn_skin.findPlug('maxInfluences', False).asInt()

    return data


def set_weights(skin_cluster, weights):
    skin_mfn = OpenMayaAnim.MFnSkinCluster(skin_cluster)

    mesh_path = skin_mfn.getPathAtIndex(0)
    mesh_node = mesh_path.node()

    vertex_mfn = OpenMaya.MItMeshVertex(mesh_node)
    indices = range(vertex_mfn.count())

    id_component = OpenMaya.MFnSingleIndexedComponent()
    vtx_component = id_component.create(OpenMaya.MFn.kMeshVertComponent)
    id_component.addElements(indices)

    influence_objects = skin_mfn.influenceObjects()
    influence_index = OpenMaya.MIntArray(len(influence_objects), 0)
    for x in range(len(influence_objects)):
        influence_index[x] = int(skin_mfn.indexForInfluenceObject(influence_objects[x]))

    skin_mfn.setWeights(mesh_path, vtx_component, influence_index, OpenMaya.MDoubleArray(weights))


@decorator.timer()
def load(data=None, name=None):
    if not data:
        data = SkinData()
        data.load()

    if name:
        data['geometry'] = name
    skin_mfn = get_node.skin_cluster(data['geometry'])
    if skin_mfn:
        cmds.skinCluster(data['geometry'], edit=1, unbind=1, unbindKeepHistory=0)

    set_weights(OpenMaya.MGlobal.getSelectionListByName(cmds.skinCluster(*(data['influences'] + [data['geometry']]),
                                                                         toSelectedBones=True,
                                                                         mi=data['max_influence'],
                                                                         bindMethod=3)[0]).getDependNode(0),
                data['weights'])
    return data


class SkinData(BaseData):
    def __init__(self):
        super(SkinData, self).__init__()
        self['geometry'] = str()
        self['weights'] = list()
        self['influences'] = dict()
        self['max_influence'] = int()
