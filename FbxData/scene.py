import fbx
import FbxCommon
import json
from PySide2 import QtWidgets


try:
    from .lib import Tree, geometry  # how it works in maya
except ImportError:
    from lib import Tree, geometry  # how it works in the IDE


class FbxUI(QtWidgets.QMainWindow):
    def __init__(self):
        super(FbxUI, self).__init__()


def string_to_int(full_name):
    int_name = list()
    for i in full_name:
        hex_name = i.encode('utf-8').hex()  # python 3
        int_name.append(int(hex_name, 16))
    return int_name


def iterate_hierarchy(node, tree, long_name=list()):
    long_name.append(node.GetName())
    int_name = string_to_int(long_name)

    if 'nodes' not in tree:
        tree['nodes'] = list()

    tree['nodes'].append(node.GetName())
    # tree.custom_node = _get_attributes(node)
    tree.add_node(*int_name)

    for i in range(node.GetChildCount()):
        child = node.GetChild(i)
        iterate_hierarchy(child, tree, long_name)
    long_name.pop()
    return tree


class FbxScene:

    # TODO: serialize elements

    FBX_DATATYPE = {fbx.eFbxString: fbx.FbxPropertyString,
                    fbx.eFbxBool: fbx.FbxPropertyBool1}

    def __init__(self, path):
        self.path = path
        self.Skeletons = list()
        self.Meshes = list()
        self.Metadata = None

        self.QTreeWidget = QtWidgets.QTreeWidget()

        self._scene_nodes = dict()

    def read_hierarchy(self):
        self.fbx_manager = fbx.FbxManager.Create()
        importer = fbx.FbxImporter.Create(self.fbx_manager, 'myImporter')

        status = importer.Initialize(self.path)

        self.fbx_scene = fbx.FbxScene.Create(self.fbx_manager, 'myScene')
        importer.Import(self.fbx_scene)

        root = self.fbx_scene.GetRootNode()
        tree_data = Tree()
        [iterate_hierarchy(node, tree_data) for node in [root.GetChild(i) for i in range(root.GetChildCount())]]
        # hierarchy_data = hierarchy.get([root.GetChild(i) for i in range(root.GetChildCount())])
        print(tree_data)
        # for i in range(root.GetChildCount()):
        #     node = root.GetChild(i)
        #     # attr = node.GetNodeAttribute()

    def read_scene(self):
        # TODO: create scene hierarchy and display nodes based on their type
        # TODO: create a UI to visualize it
        self.fbx_manager = fbx.FbxManager.Create()
        importer = fbx.FbxImporter.Create(self.fbx_manager, 'myImporter')

        status = importer.Initialize(self.path)

        self.fbx_scene = fbx.FbxScene.Create(self.fbx_manager, 'myScene')
        importer.Import(self.fbx_scene)

        root = self.fbx_scene.GetRootNode()
        for i in range(root.GetChildCount()):
            node = root.GetChild(i)
            attr = node.GetNodeAttribute()

            if node.GetName() == 'metadata':
                self._scene_nodes['metadata'] = node

            if isinstance(attr, fbx.FbxSkeleton):
                self.Skeletons.append(hierarchy.get(node))

            if isinstance(attr, fbx.FbxMesh):
                self.Meshes.append(geometry.get(node))

        if not self._scene_nodes['metadata']:
            # scene does not contain a metadata node
            # creating based on Mesh name
            self.create_metadata(AssetData())
            return

        self.Metadata = self.listAttr('metadata', True)
        # if self.Skeletons:
        #     with open('C:\\Users\\lucas.esposito\\Desktop\\supertest.json', 'w') as f:
        #         f.write(json.dumps(self.Skeletons[0], indent=4))
        return self

    # TODO: list attributes based on flags (userDefined, keyable)
    def listAttr(self, node, userDefined=False):
        if userDefined is False:
            return
        if isinstance(node, str):
            if node not in self._scene_nodes:
                print(f'{node} was not found in the scene')
                return
            node = self._scene_nodes[node]

        data = dict()
        prop = node.GetFirstProperty()
        while prop.IsValid():
            if prop.GetFlag(fbx.FbxPropertyFlags.eUserDefined):
                enum_type = prop.GetPropertyDataType().GetType()
                try:
                    data[str(prop.GetName())] = self.FBX_DATATYPE[enum_type](prop).Get()
                except Exception as e:
                    data[str(prop.GetName())] = f'{type(e).__name__}_{prop.GetPropertyDataType().GetName()}'
            prop = node.GetNextProperty(prop)

        return data if data else None

    # TODO: get, set, add and del attribute
    def getAttr(self, node, attr):
        pass

    def setAttr(self, node, attr):
        pass

    def addAttr(self, node, attr, typ):
        pass

    def delAttr(self, node, attr):
        pass

    # TODO: create node based on type
    def addNode(self, name, typ):
        pass

    def delNode(self, name, typ):
        pass

    def create_metadata(self, metadata):
        root = self.fbx_scene.GetRootNode()
        metadata_node = fbx.FbxNode.Create(self.fbx_manager, 'TestNode')

        root.AddChild(metadata_node)
        metadata_node.LclTranslation.Set(fbx.FbxDouble3(10.0, 20.0, 30.0))

        # attribute = fbx.FbxNodeAttribute.Create(self.fbx_manager, 'TestAttr')#
        attribute = fbx.FbxNull.Create(self.fbx_manager, 'TestAttr')

        metadata_node.AddNodeAttribute(attribute)
        prop = metadata_node.FindProperty('TestAttr', False)
        print(prop.GetName())

        for i in range(root.GetChildCount()):
            node = root.GetChild(i)
            print(node.GetName())

        # self.suffix_metadata


# file_path = 'l:\\Projects\\unreal\\SpeedBall_RN\\Source_Art\\Character_Art\\Body\\LargeMale\\Mesh\\SKM_LM_Body.fbx'
file_path = 'c:\\Users\\lucas.esposito\\Desktop\\haha.fbx'
# file_path = 'c:\\Users\\lucas.esposito\\Desktop\\haha_no_meta.fbx'


class AssetData(dict):
    def __init__(self, *args, **kwargs):
        super(AssetData, self).__init__(*args, **kwargs)
        self['character'] = 'AF'
        self['category'] = 'Helmet'
        self['subcategory'] = '10'
        self['addable'] = False
        self['name'] = 'SKM_AF_Helmet_10'
        self['path'] = 'c:\\Users\\lucas.esposito\\Desktop\\haha_no_meta.fbx'

print('hey')
a = QtWidgets.QLabel()
print(a)
print('ha')
# FbxScene(file_path).read_hierarchy()
# print(new_scene.Metadata)
