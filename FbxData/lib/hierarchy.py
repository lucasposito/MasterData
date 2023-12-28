import fbx
import math
import copy

try:
    from .tree import Tree
except ImportError:
    from tree import Tree

JOINT_DATA = {'name': str(), 'matrix': None, 'orient': list(), 'rotation': list(), 'radius': float(),
              'rotateOrder': float(), 'side': float(), 'type': float()}


def string_to_int(full_name):
    int_name = list()
    for i in full_name:
        hex_name = i.encode('utf-8').hex()  # python 3
        int_name.append(int(hex_name, 16))
    return int_name


def _get_attributes(node):
    data = copy.deepcopy(JOINT_DATA)
    data['name'] = node.GetName()

    local_transform = node.EvaluateLocalTransform()
    data['matrix'] = list(local_transform.GetRow(0)) + list(local_transform.GetRow(1)) + list(
        local_transform.GetRow(2)) + list(local_transform.GetRow(3))
    data['orient'] = [math.radians(i) for i in list(local_transform.GetR())][:3]
    data['radius'] = 1.0

    # for k in ['radius', 'rotateOrder', 'side', 'type']:
    #     data[k] = mfn_node.findPlug(k, False).asDouble()

    return data


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


def get(root_nodes):
    if not isinstance(root_nodes, list):
        root_nodes = [root_nodes]

    tree = Tree()
    [iterate_hierarchy(node, tree) for node in root_nodes]
    return tree

    # attr = root_node.GetNodeAttribute()
    # if not isinstance(attr, fbx.FbxSkeleton):
    #     return
    #
    # return iterate_hierarchy(root_node, Tree())
