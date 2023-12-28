from MayaData.lib import get_node, pivot, decorator
from MayaData.data import geometry, uv
from MayaData.data.base import BaseData

from maya.api import OpenMaya
from maya import cmds


@decorator.timer()
def get(name):
    blend_node = get_node.blend_shape(name)
    if not blend_node:
        return
    mesh = OpenMaya.MSelectionList().add(name).getDagPath(0)
    mesh = OpenMaya.MFnMesh(mesh)

    blend_node = OpenMaya.MFnDependencyNode(blend_node)
    plug = blend_node.findPlug('weight', False)

    for i in range(plug.numElements()):
        plug.elementByPhysicalIndex(i).setFloat(0)

    data = BlendShapeData()
    data['name'] = blend_node.name()
    data['numShapes'] = plug.numElements()
    data['geometry'] = geometry.get(name)
    data['uv'] = uv.get(name)

    for j in range(plug.numElements()):
        data['shapes'].append(plug.elementByPhysicalIndex(j).name().split('.')[-1])
        plug.elementByPhysicalIndex(j).setFloat(1)
        data['weights'].append(map(list, mesh.getPoints()))
        plug.elementByPhysicalIndex(j).setFloat(0)
    return data


@decorator.timer()
def load(data=None, name=None, same_topology=True, meshes_overlapped=True, clamp=0):
    if not data:
        data = BlendShapeData()
        data.load()

    if name:
        data['geometry']['name'] = name

    blend_node = get_node.blend_shape(data['geometry']['name'])

    if same_topology:
        if not blend_node:
            blend_node = cmds.blendShape(data['geometry']['name'], n=data['name'])[0]
        for i in range(data['numShapes']):
            temp_dag = OpenMaya.MSelectionList().add(cmds.duplicate(data['geometry']['name'], n=data['shapes'][i])[0])
            temp_dag = temp_dag.getDagPath(0)
            temp = OpenMaya.MFnMesh(temp_dag)

            temp.setPoints(map(OpenMaya.MPoint, data['weights'][i]))

            cmds.blendShape(blend_node, edit=True, t=[data['geometry']['name'], i, temp_dag.fullPathName(), 1.0])
            cmds.delete(temp_dag.fullPathName())
        return

    if meshes_overlapped:
        pivot.match_transformations(OpenMaya.MMatrix(data['mesh_matrix']), data['geometry']['name'])
    if not blend_node:
        blend_node = cmds.blendShape(data['geometry']['name'], n=data['name'])[0]

    base_shape = geometry.load(data['geometry'])
    base_mfn = OpenMaya.MFnTransform(base_shape.parent(0))
    base_uv = base_shape.getUVSetNames()[0]

    if clamp <= 0:
        clamp = data['numShapes']

    for i in range(clamp):
        temp_dag = OpenMaya.MSelectionList().add(cmds.duplicate(base_mfn.fullPathName())[0])
        temp_dag = temp_dag.getDagPath(0)
        temp = OpenMaya.MFnMesh(temp_dag)

        copy_dag = OpenMaya.MSelectionList().add(cmds.duplicate(data['geometry']['name'], n=data['shapes'][i])[0])
        copy_dag = copy_dag.getDagPath(0)
        copy_uv = OpenMaya.MFnMesh(copy_dag).getUVSetNames()[0]

        temp.setPoints(map(OpenMaya.MPoint, data['weights'][i]))

        cmds.transferAttributes(temp_dag.fullPathName(), copy_dag.fullPathName(),
                                pos=True, nml=True, spa=3, sus=base_uv, tus=copy_uv, sm=3, clb=1)
        cmds.blendShape(blend_node, edit=True, t=[data['geometry']['name'], i, copy_dag.fullPathName(), 1.0])

        cmds.delete(temp_dag.fullPathName(), copy_dag.fullPathName())

    cmds.delete(base_mfn.fullPathName())


class BlendShapeData(BaseData):
    def __init__(self):
        super(BlendShapeData, self).__init__()
        self['name'] = str()
        self['shapes'] = list()
        self['weights'] = list()
        self['numShapes'] = int()

        self['geometry'] = dict()
        self['uv'] = dict()
