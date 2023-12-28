from maya.api import OpenMaya
from maya import cmds
import math


def aim_matrix(aim_vector, up_vector):
    """
    Builds the orientation from two vectors.
    It behaves with the same logic as an aim constraint,
    with main vector as the aiming axis and the secondary as the up axis.

    :param aim_vector: OpenMaya.MVector
    :param up_vector: OpenMaya.MVector
    :return: OpenMaya.MMatrix
    """
    aim_axis = OpenMaya.MVector().kYaxisVector
    up_axis = OpenMaya.MVector().kXaxisVector

    obj_u = aim_vector.normal()
    obj_w = (obj_u ^ up_vector).normal()
    obj_v = obj_w ^ obj_u

    quat_u = OpenMaya.MQuaternion(aim_axis, obj_u)
    up_axis_rotated = up_axis.rotateBy(quat_u)

    angle = math.acos(up_axis_rotated * obj_v)
    quat_v = OpenMaya.MQuaternion(angle, obj_u)

    if not obj_v.isEquivalent(up_axis_rotated.rotateBy(quat_v), 1.0e-1):
        angle = (2 * math.pi) - angle
        quat_v = OpenMaya.MQuaternion(angle, obj_u)

    mod = OpenMaya.MDagModifier()
    target_obj = mod.createNode("transform", OpenMaya.MObject.kNullObj)
    mod.doIt()

    quat = quat_u * quat_v
    target_mfn = OpenMaya.MFnTransform(target_obj)
    target_mfn.setRotation(quat, OpenMaya.MSpace.kObject)
    result_matrix = target_mfn.getPath().inclusiveMatrix()

    OpenMaya.MDagModifier().deleteNode(target_obj).doIt()
    return result_matrix


def get_offset_matrix(parent, child):
    parent = OpenMaya.MSelectionList().add(parent).getDagPath(0).inclusiveMatrix()
    child = OpenMaya.MSelectionList().add(child).getDagPath(0).inclusiveMatrix()

    return child * parent.inverse()


def matrix_between_vertices(mesh_name, vertices=None):
    """
    It will return a pivot merely based on two vertices of a given mesh.
    Useful when you can't rely on the transform node pivot, bounding box or world position.

    :param mesh_name: string of the mesh
    :param vertices: list with the two vertices to build the vectors
    :return: OpenMaya.MMatrix
    """
    if isinstance(vertices, list) and len(vertices) == 2:
        a, b = vertices
        print("The vertices {} and {} were used in the mesh {}.".format(a, b, mesh_name))
    else:
        a, b = [0, 1]

    mesh = OpenMaya.MSelectionList().add(mesh_name).getDagPath(0)
    mesh = OpenMaya.MFnMesh(mesh)

    vertex_position = OpenMaya.MVector(mesh.getPoint(a, OpenMaya.MSpace.kWorld))
    vertex_a_normal = mesh.getVertexNormal(a, False, OpenMaya.MSpace.kWorld)
    vertex_b_normal = mesh.getVertexNormal(b, False, OpenMaya.MSpace.kWorld)

    result_mat = aim_matrix(vertex_a_normal, vertex_b_normal)

    result_mat.setElement(3, 0, vertex_position.x)
    result_mat.setElement(3, 1, vertex_position.y)
    result_mat.setElement(3, 2, vertex_position.z)

    return result_mat


def match_transformations(source_matrix, target):
    """
    :param source_matrix: OpenMaya.MMatrix of the source mesh
    :param target: str of the target mesh
    :return: None
    """
    target_mat = OpenMaya.MMatrix(cmds.xform(target, q=True, m=True, ws=True))

    if source_matrix == target_mat:
        return

    cmds.makeIdentity(target, a=True, n=False, pn=True, t=True, r=True)
    offset_mat = target_mat * source_matrix.inverse()
    cmds.xform(target, m=offset_mat * target_mat, ws=True)
    cmds.makeIdentity(target, a=True, n=False, pn=True, t=True, r=True)
    cmds.xform(target, ztp=True)
    cmds.xform(target, m=source_matrix, ws=True)
