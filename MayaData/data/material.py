from MayaData.data.base import BaseData
from MayaData.lib import decorator

from pathlib import Path
from maya.api import OpenMaya
from maya import cmds


def get_texture_path(material):
    color_plug = material.findPlug('color', False)
    file_plug = color_plug.connectedTo(True, False)
    if file_plug:
        file = OpenMaya.MFnDependencyNode(file_plug[0].node())
        path = Path(file.findPlug('fileTextureName', False).asString())
        return path.name


@decorator.timer()
def get(name):
    data = MaterialData()
    data['geometry'] = name

    mfn_mesh = OpenMaya.MSelectionList().add(name).getDagPath(0)
    mfn_mesh = OpenMaya.MFnMesh(mfn_mesh.extendToShape())
    m_objects, face_ids = mfn_mesh.getConnectedShaders(0)

    data['shading_groups'] = [OpenMaya.MFnDependencyNode(obj).name() for obj in m_objects]

    for index, obj in enumerate(m_objects):
        data['face_id_map'][str(index)] = list()
        mfn_shader = OpenMaya.MFnDependencyNode(obj)
        plug = mfn_shader.findPlug("surfaceShader", False)
        plug_array = plug.connectedTo(True, False)
        for p in plug_array:
            mfn_material = OpenMaya.MFnDependencyNode(p.node())
            data['materials'][mfn_material.name()] = None
            texture_path = get_texture_path(mfn_material)
            if texture_path:
                data['materials'][mfn_material.name()] = texture_path

    for face_index, material_index in enumerate(face_ids):
        data['face_id_map'][str(material_index)].append(face_index)

    return data


def consecutive_blocks(index_list):
    """return start indices and subsequences of each run of
    consecutive or equal values
    """
    index_list = sorted(index_list)
    starts = [0]
    for i in range(len(index_list) - 1):
        if abs(index_list[i + 1] - index_list[i]) > 1:
            starts.append(i + 1)
    blocks = []
    starts.append(len(index_list))
    for i in range(len(starts) - 1):
        blocks.append(index_list[starts[i] : starts[i + 1]])
    if not blocks:
        print(starts, blocks)
    return starts, blocks


def set_face_materials(mesh_name, n_faces, sg):

    starts, blocks = consecutive_blocks(sorted(n_faces))
    for block in blocks:
        # combine to get face strings
        f_string = "f[{}:{}]".format(block[0], block[-1])
        ns = cmds.namespaceInfo(currentNamespace=1)
        mesh_ns_name = ns + ":" + mesh_name
        if not cmds.objExists(mesh_ns_name):
            print("mesh", mesh_ns_name, "not found, skipping material load")
            continue
        mesh_face_string = mesh_ns_name + "." + f_string
        cmds.sets(mesh_face_string, e=True, forceElement=sg)


def delete_texture(plug):
    texture_obj = plug.source().node()

    mod = OpenMaya.MDGModifier()
    mod.deleteNode(texture_obj)
    mod.doIt()


def create_texture():
    mod = OpenMaya.MDGModifier()
    node_2d = mod.createNode("place2dTexture")
    file_node = mod.createNode("file")
    mod.doIt()

    file_mfn = OpenMaya.MFnDependencyNode(file_node)
    mfn_2d = OpenMaya.MFnDependencyNode(node_2d)

    output_attributes = [
        "coverage",
        "mirrorU",
        "mirrorV",
        "noiseUV",
        "offset",
        "outUV",
        "outUvFilterSize",
        "repeatUV",
        "rotateFrame",
        "rotateUV",
        "stagger",
        "translateFrame",
        "vertexCameraOne",
        "vertexUvOne",
        "vertexUvThree",
        "vertexUvTwo",
        "wrapU",
        "wrapV",
    ]

    connect_mod = OpenMaya.MDGModifier()
    for attr in output_attributes:
        input_attr = attr
        if attr == "outUV":
            input_attr = "uvCoord"
        if attr == "outUvFilterSize":
            input_attr = "uvFilterSize"
        output_plug = mfn_2d.findPlug(attr, False)
        input_plug = file_mfn.findPlug(input_attr, False)

        connect_mod.connect(output_plug, input_plug)
    connect_mod.doIt()
    return file_mfn


def create_materials(materials, shading_groups, path):

    scene_mats = cmds.ls(materials=True)
    index = 0
    for mat_name, file_name in materials.items():
        # checks if material is already created if not, creates it.
        if mat_name not in scene_mats:
            mat_name = cmds.shadingNode("lambert", name=mat_name, asShader=True)
            cmds.sets(
                name=mat_name + "SG",
                empty=True,
                renderable=True,
                noSurfaceShader=True)

        mat_obj = OpenMaya.MSelectionList().add(mat_name).getDependNode(0)
        mat_mfn = OpenMaya.MFnDependencyNode(mat_obj)

        if file_name:
            input_color = mat_mfn.findPlug("color", False)
            if not input_color.source().isNull:
                # The shading group is not deleted with the texture deletion
                delete_texture(input_color)

            file_mfn = create_texture()
            output_color = file_mfn.findPlug("outColor", False)

            OpenMaya.MDGModifier().connect(output_color, input_color).doIt()
            file_mfn.findPlug("fileTextureName", False).setString(str(Path(path) / file_name))

        shader_obj = OpenMaya.MSelectionList().add(shading_groups[index]).getDependNode(0)

        out_color_plug = mat_mfn.findPlug('outColor', False)
        shader_plug = OpenMaya.MFnDependencyNode(shader_obj).findPlug('surfaceShader', False)

        OpenMaya.MDGModifier().connect(out_color_plug, shader_plug).doIt()
        index += 1


@decorator.timer()
def load(data=None, name=None, path=None):
    if not data:
        data = MaterialData()
        data.load()

    if name:
        data['geometry'] = name

    if not path:
        path = Path(__file__).parent / 'Textures'
    create_materials(data['materials'], data['shading_groups'], path)

    for index, material_name in enumerate(data['materials'].keys()):
        set_face_materials(data['geometry'], data['face_id_map'][str(index)], data['shading_groups'][index])


class MaterialData(BaseData):
    def __init__(self):
        super(MaterialData, self).__init__()
        self['geometry'] = str()
        self['materials'] = dict()
        self['shading_groups'] = list()
        self['face_id_map'] = dict()
