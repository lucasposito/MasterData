from MayaData.data.base import BaseData
from MayaData.lib import decorator

import copy
from maya.api import OpenMaya
from maya import cmds


DEFAULT_ATTR = {'name': None, 'type': None, 'node': None, 'custom': False}


class MayaNodes(dict):
    def __init__(self):
        super(MayaNodes, self).__init__()
        self['DEFAULT'] = {'name': None, 'type': None, 'DAG': False}
        self['multiplyDivide'] = {'operation': float(), 'input1X': float(), 'input1Y': float(), 'input1Z': float(),
                                  'input2X': float(), 'input2Y': float(), 'input2Z': float()}
        self['condition'] = {'operation': float(), 'firstTerm': float(), 'secondTerm': float(),
                             'colorIfTrueR': float(), 'colorIfTrueG': float(), 'colorIfTrueB': float(),
                             'colorIfFalseR': float(), 'colorIfFalseG': float(), 'colorIfFalseB': float()}


@decorator.timer()
def get(name, attribute=None):
    network = Network()
    obj = OpenMaya.MSelectionList().add(name).getDependNode(0)
    network.start(obj, attribute)
    return network.data


def _replace_prefix(name, prefix_list):
    root, mid, end = prefix_list
    name = name.split('_')
    if name[0] == 'root':
        return '{}_{}'.format(root, '_'.join(name[1:]))
    if name[0] == 'mid':
        return '{}_{}'.format(mid, '_'.join(name[1:]))
    if name[0] == 'end':
        return '{}_{}'.format(end, '_'.join(name[1:]))
    return '_'.join(name)


@decorator.timer()
def load(data=None, prefix_list=None):
    if not data:
        data = NetworkData()
        data.load()

    for key, node in data['nodes'].items():
        if prefix_list:
            data['nodes'][key]['name'] = _replace_prefix(node['name'], prefix_list)

        if cmds.objExists(node['name']):
            base_node = OpenMaya.MSelectionList().add(node['name']).getDependNode(0)
        else:
            if node['DAG']:
                node_mod = OpenMaya.MDagModifier()
                base_node = node_mod.createNode(node['type'], OpenMaya.MObject.kNullObj)
                node_mod.renameNode(base_node, node['name'])
                node_mod.doIt()
                continue

            node_mod = OpenMaya.MDGModifier()
            base_node = node_mod.createNode(node['type'])
            node_mod.renameNode(base_node, node['name'])
            node_mod.doIt()

        if 'attributes' in node.keys():
            base_node = OpenMaya.MFnDependencyNode(base_node)
            for attr, value in node['attributes'].items():
                plug = OpenMaya.MSelectionList().add('{}.{}'.format(base_node.name(), attr)).getPlug(0)
                plug.setDouble(value)

    if prefix_list:
        for key, plug in data['plugs'].items():
            data['plugs'][key]['name'] = _replace_prefix(plug['name'], prefix_list)
    for source, destination in data['connections'].items():
        source_node = data['plugs'][source]['node']
        source_node = data['nodes'][str(source_node)]['name']

        source_attr = data['plugs'][source]['name']
        source_plug = OpenMaya.MSelectionList().add('{}.{}'.format(source_node, source_attr)).getPlug(0)

        connect_mod = OpenMaya.MDGModifier()
        for dest in destination:
            dest_node = data['plugs'][str(dest)]['node']
            dest_node = data['nodes'][str(dest_node)]['name']

            dest_attr = data['plugs'][str(dest)]['name']
            dest_plug = OpenMaya.MSelectionList().add('{}.{}'.format(dest_node, dest_attr)).getPlug(0)

            if not dest_plug.source().isNull:
                continue
            connect_mod.connect(source_plug, dest_plug)
        connect_mod.doIt()
    return data


class Network(object):
    def __init__(self):
        self.data = NetworkData()
        self.nodes = MayaNodes()
        self.plug_cache = dict()
        self.node_cache = dict()
        self.stop_at_node = None
        self.connection_cache = dict()
        self._id = 1

    def get_node_data(self, node):
        node_data = copy.deepcopy(self.nodes['DEFAULT'])
        custom_data = None
        if node.typeName in self.nodes:
            custom_data = copy.deepcopy(self.nodes[node.typeName])

        node_data['name'] = node.name()
        node_data['type'] = node.typeName

        if 'dagNode' in cmds.nodeType(node.name(), inherited=True):
            node_data['DAG'] = True

        if not custom_data:
            return node_data

        for attr in custom_data.keys():
            plug = node.findPlug(attr, False)
            custom_data[attr] = plug.asDouble()

        node_data.update({'attributes': custom_data})
        return node_data

    def get_plug_data(self, plug):
        plug_data = copy.deepcopy(DEFAULT_ATTR)
        plug_data['name'] = plug.partialName(useLongNames=True)

        plug_data['type'] = plug.attribute().apiTypeStr
        if OpenMaya.MFnAttribute(plug.attribute()).dynamic:
            plug_data['custom'] = True

        temp_node = OpenMaya.MFnDependencyNode(plug.node()).name()
        plug_data['node'] = self.node_cache[temp_node]

        return plug_data

    def start(self, node, attribute=None):
        # TODO: Connections need to stop at FaceOutput
        self.node_cache[OpenMaya.MFnDependencyNode(node).name()] = 0
        self.data['nodes'].update({0: self.get_node_data(OpenMaya.MFnDependencyNode(node))})
        # initial_node_name = self.data['nodes'][0]['name']
        if attribute:
            node = OpenMaya.MFnDependencyNode(node).findPlug(attribute, False)
        left_iter = OpenMaya.MItDependencyGraph(node,
                                                OpenMaya.MItDependencyGraph.kUpstream,
                                                OpenMaya.MItDependencyGraph.kBreadthFirst,
                                                OpenMaya.MItDependencyGraph.kPlugLevel)

        while not left_iter.isDone():
            node_on_left = OpenMaya.MFnDependencyNode(left_iter.currentNode())
            map(self.traverse_connections, node_on_left.getConnections())
            right_iter = OpenMaya.MItDependencyGraph(left_iter.currentNode(),
                                                     OpenMaya.MItDependencyGraph.kUpstream,
                                                     OpenMaya.MItDependencyGraph.kDepthFirst,
                                                     OpenMaya.MItDependencyGraph.kPlugLevel)
            while not right_iter.isDone():
                node_on_right = OpenMaya.MFnDependencyNode(right_iter.currentNode())
                map(self.traverse_connections, node_on_right.getConnections())
                right_iter.next()
            left_iter.next()
        self.data['connections'].update(self.connection_cache)

    def traverse_connections(self, source_plug):
        source_node = OpenMaya.MFnDependencyNode(source_plug.node())
        for destination_plug in source_plug.destinations():
            destination_node = OpenMaya.MFnDependencyNode(destination_plug.node())

            if destination_node.isDefaultNode or destination_plug.attribute().hasFn(OpenMaya.MFn.kMessageAttribute):
                continue

            # print(source_plug)
            # print(destination_plug)
            if source_node.name() not in self.node_cache.keys():
                self.node_cache[source_node.name()] = self._id
                self.data['nodes'].update({self._id: self.get_node_data(source_node)})
                self._id += 1
            if destination_node.name() not in self.node_cache.keys():
                self.node_cache[destination_node.name()] = self._id
                self.data['nodes'].update({self._id: self.get_node_data(destination_node)})
                self._id += 1

            if source_plug.name() not in self.plug_cache.keys():
                self.plug_cache[source_plug.name()] = self._id
                self.data['plugs'].update({self._id: self.get_plug_data(source_plug)})
                self._id += 1
            if destination_plug.name() not in self.plug_cache.keys():
                self.plug_cache[destination_plug.name()] = self._id
                self.data['plugs'].update({self._id: self.get_plug_data(destination_plug)})
                self._id += 1

            plug_id = self.plug_cache[source_plug.name()]
            each_id = self.plug_cache[destination_plug.name()]

            if plug_id not in self.connection_cache.keys():
                self.connection_cache[plug_id] = list()

            if each_id not in self.connection_cache[plug_id]:
                self.connection_cache[plug_id].append(each_id)


class NetworkData(BaseData):
    def __init__(self):
        super(NetworkData, self).__init__()
        self['nodes'] = dict()  # {9261: {'name': 'example', 'type': 'multiplyDivide', 'custom_attrs': CUSTOM_ATTR}}
        self['plugs'] = dict()
        # {1792: {'parent': 'plugA', 'source': 'plugA[0].another.output', 'destination': 'plugA[0].another.input'}}
        self['connections'] = dict()  # {1792: [8359, 3147]}
