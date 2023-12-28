from maya.api import OpenMaya
import numpy


def _get_selected_vtx_data():
    selection = OpenMaya.MGlobal.getActiveSelectionList()
    node, component = selection.getComponent(0)
    vertices = dict()

    vertex_iter = OpenMaya.MItMeshVertex(node, component)
    while not vertex_iter.isDone():
        vertices[tuple(vertex_iter.position(OpenMaya.MSpace.kWorld))] = {'vertex_id': vertex_iter.index(),
                                                                         'normals': vertex_iter.getNormals(
                                                                             OpenMaya.MSpace.kWorld),
                                                                         'masks': vertex_iter.getConnectedFaces()}
        vertex_iter.next()
    return vertices


def _get_border_vtx_data(mesh_name):
    mesh = OpenMaya.MSelectionList().add(mesh_name).getDagPath(0)
    border = dict()

    vertex_iter = OpenMaya.MItMeshVertex(mesh)
    while not vertex_iter.isDone():
        if vertex_iter.onBoundary():
            border[tuple(vertex_iter.getUV())] = {'vertex_id': vertex_iter.index(), 'normals': vertex_iter.getNormals(),
                                                  'masks': vertex_iter.getConnectedFaces()}
        vertex_iter.next()
    return border


class CopyNormals(object):
    def __init__(self):
        self._source = None
        self._target = None

    def from_selection(self):
        self._source = _get_selected_vtx_data()

    def to_selection(self, mesh_name):
        source_pos = numpy.array(self._source.keys())

        mesh = OpenMaya.MSelectionList().add(mesh_name).getDagPath(0)
        mesh_mfn = OpenMaya.MFnMesh(mesh)

        for pos, value in _get_selected_vtx_data().items():
            np_pos = numpy.array(pos)
            distance = numpy.linalg.norm(source_pos - np_pos, axis=1)
            closest_pos = numpy.argmin(distance)
            pos_key = tuple(source_pos[closest_pos])
            for normal, face_id in zip(self._source[pos_key]['normals'], value['masks']):
                mesh_mfn.setFaceVertexNormal(normal, face_id, value['vertex_id'], OpenMaya.MSpace.kWorld)

    def from_uv_border(self, mesh_a, mesh_b):
        mesh_a = OpenMaya.MSelectionList().add(mesh_a).getDagPath(0)
        self._source = _get_border_vtx_data(mesh_a)
        mesh_a_uvs = numpy.array(self._source.keys())

        mesh_b = OpenMaya.MSelectionList().add(mesh_b).getDagPath(0)
        self._target = _get_border_vtx_data(mesh_b)
        mesh_b_mfn = OpenMaya.MFnMesh(mesh_b)

        for uv, value in self._target.items():
            np_uv = numpy.array(uv)
            distance = numpy.linalg.norm(mesh_a_uvs - np_uv, axis=1)
            closest_uv = numpy.argmin(distance)
            uv_key = tuple(mesh_a_uvs[closest_uv])

            for normal, face_id in zip(self._source[uv_key]['normals'], value['masks']):
                mesh_b_mfn.setFaceVertexNormal(normal, face_id, value['vertex_id'])
