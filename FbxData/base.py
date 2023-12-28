

class DepNode(object):
    def __init__(self, node=None):
        super(DepNode, self).__init__()
        self._obj = None
        self._dep = None
        self._mfn = None
        self._data = None
        self.node = node

    def __str__(self):
        path = self.path
        if not path:
            return "INVALID OBJECT"
        return path

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.full_path == other.full_path
        elif self.full_path == other:
            return True
        elif self.path == other:
            return True
        return False

    def __getitem__(self, attr):
        if attr in self.__dict__.keys():
            return self.__dict__[attr]
        return Attribute(self.node, attr)

    def __repr__(self):
        return "< {0} | {1} >".format(self.__class__.__name__, self.path)

    @property
    def node(self):
        return self._node

    @property
    def dep(self):
        return self._dep

    @property
    def mfn(self):
        return self._mfn

    @node.setter
    def node(self, node):
        self._obj = None
        self._dep = None
        self._node = str(node) if node is not None else None
        if not self.node or not cmds.objExists(self.node):
            return False
        self._obj = api.core.to_mobject(self.node)
        self._dep = api.core.to_mfn_depnode(self.node)
        self._mfn = api.core.to_mfn(self.node)
        return True

    @property
    def full_path(self):
        if self.dep:
            return self.dep.name()

    def node_type(self, shape=False):
        """
        Get node type. If the shape key is true and a shape is found it will return the shape type.

        :return:
        """
        node = self.full_path
        return cmds.objectType(node)

    @property
    def is_referenced(self):
        """
        Check if node is referenced

        :return:
        """
        if not self.exists:
            return False

        return cmds.referenceQuery(self.full_path, isNodeReferenced=True)

    @property
    def exists(self):
        if self.full_path and cmds.objExists(self.full_path):
            return True
        return False

    @property
    def typ(self):
        return cmds.objectType(self.full_path)

    @property
    def name(self):
        """
        Get node name. Removes namespaces.

        :return: node name
        """
        if not self.exists:
            return self.node
        return path.base_name(self.full_path)

    @property
    def namespace(self):
        """
        Get namespace

        :return: namespace
        """
        return path.namespace(self.full_path)

    @property
    def obj(self):
        return self._obj

    @property
    def path(self):
        if self.dep:
            return self.dep.name()

    @property
    def data(self):
        if isinstance(self._data, struc.NodeData):
            return self._data
        self._data = struc.NodeData()
        if self.exists:
            self._data.name = self.path
            self._data.node_type = self.node_type()
            self._data.attributes = self._get_attr_data(ud=1)
        return self._data

    def list_attr(self, **kwargs):
        """
        List all attributes of node. Takes in cmds.listAttr kwargs

        :param kwargs:
        :return:
        """

        return [Attribute(self.node, a).attribute for a in cmds.listAttr(self.node, **kwargs) or []]

    def add_attr(self, attr, **kwargs):
        """
        Add attribute to node.

        :param attr: attribute name
        :param spacer: add spacer attr
        :param kwargs: kwargs for cmds.addAttr
        :return:
        """
        if self[attr].full_path:
            return

        cmds.addAttr(self.full_path, shortName=attr, longName=attr, k=True, **kwargs)

    def _get_attr_data(self, **kwargs):
        """
        Builds attribute data of node. Takes in keyword arguments for cmds.listAttr()

        :param kwargs:
        :return:
        """
        attr_dict = {}
        all_attr = self.list_attr(**kwargs)
        for attr in all_attr:
            try:
                attr_dict[attr] = Attribute(self.node, attr).get()
            except:
                pass
        return attr_dict

    # def _build_node_data(self):
    #     """
    #     Build base node data.
    #
    #     :return:
    #     """
    #     if not self.exists:
    #         raise ValueError("build_node_data : Node does not exist")
    #     self._node_data["name"] = self.full_path
    #     self._node_data["node_type"] = self.node_type()
    #     self._node_data.update(self.attr_data)
    #     return self._node_data

    # def build_data(self, **kwargs):
    #     """
    #     Builds node data based on what is needed for dependency nodes.
    #
    #     :param kwargs:
    #     :return:
    #     """
    #     self._build_attr_data(**kwargs)
    #     self._build_node_data()
    #     return self.data

    def _rebuild_attr_from_data(self, attributes):
        """
        Rebuilds attribute data onto node.

        :param data:
        :return:
        """
        for a, value in attributes.items():
            attr = Attribute(self.node, a)
            if not attr.exists:
                attr.add(value)
            # attr.set(value)

    def rebuild_data(self):
        """
        Rebuilds data onto node

        :param data:
        :return:
        """
        self._rebuild_attr_from_data()

    def create_node(self, nodeType, parent=None):
        """
        Create node if node doesn't exist. Name will be the string that has been parsed on initiation.

        :param parent:
        :param nodeType:
        :return: node
        """
        if self.full_path:
            raise ValueError("create: {} has already been created!".format(self.name))
        node = api.core.create_node(nodeType, name=self.node)
        self.node = node
        return self

    def delete(self):
        """
        Delete node

        :return:
        """
        if self.full_path and cmds.objExists(self.full_path):
            cmds.delete(self.full_path)

        self._obj = None
        self._dep = None

    def tag_by_type(self):
        """
        Tag node by type. Creates a string attribute. Naming convention for types should follow "isNodeType"

        :return:
        """
        if not "type" in dir(self):
            return
        self[self.type].add("")


class DagNode(DepNode):
    """
    Dag Path class that inherits from DepNode. This is used as a base for handling dag paths within maya.
    It can be used to create and handle any DagPath object.

    TODO:
        - Get Drivers/Drivens
    """

    def __init__(self, node=None):
        super(DagNode, self).__init__(node)
        self._hierarchy_data = None
        self._colour = None

    @property
    def node(self):
        return self._node

    @node.setter
    def node(self, node):
        self._dag = None
        self._transform = None
        if not DepNode.node.fset(self, node):
            return False
        self._dag = api.core.to_mdag_path(self.node)
        self._transform = api.core.to_mfn_transform(self.node)

    @property
    def dag(self):
        return self._dag

    @property
    def transform(self):
        return self._transform

    @property
    def path(self):
        """
        Get path to node

        :return: path
        """
        if self.dag:
            return self.dag.partialPathName()
        else:
            return DepNode.path.fget(self)

    @property
    def full_path(self):
        """
        Get full path to node

        :return: full path
        """
        if self.dag:
            return self.dag.fullPathName()
        else:
            return DepNode.full_path.fget(self)

    @property
    def shape(self):
        """
        Get connected shape nodes.

        :return: shapes
        """
        return get_node_class(path.get_shape(self.full_path))

    @property
    def parent(self):
        """
        Get parent node

        :return: parent
        """
        return get_node_class(path.get_parent(self.full_path))

    @property
    def children(self):
        children = self.get_children()
        children_array = DagNodeArray()
        for child in children:
            setattr(children_array, child, get_node_class(child))
        return children_array

    def position(self, world=True):
        """
        Returns both the world space translate and rotate of an object

        :return:
        """
        pos = self.transform.translation(OpenMaya.MSpace.kWorld)
        if not world:
            pos = self.transform.translation(OpenMaya.MSpace.kObject)
        return pos

    @property
    def data(self):
        if isinstance(self._data, struc.NodeData):
            return self._data

        self._data = struc.NodeData()
        if self.exists:
            self._data.name = self.path
            self._data.node_type = self.node_type()
            self._data.attributes = self._get_attr_data(ud=True)
            self._data.world_matrix = list(self.get_world_matrix())
            self._data.parent = self.parent.path if self.parent else None

        return self._data

    @property
    def hierarchy_data(self):
        if isinstance(self._hierarchy_data, struc.HierarchyData):
            return self._hierarchy_data

        self._hierarchy_data = struc.HierarchyData()
        if self.exists:
            all_nodes = self.children.to_list()
            all_nodes.insert(0, self)
            for i, node in enumerate(all_nodes):
                self._hierarchy_data.__dict__[node.data.name] = node.data
        return self._hierarchy_data

    @property
    def inherit_transform(self):
        """
        Set inherit transform value

        :param value: value
        """
        return cmds.getAttr("{0}.inheritsTransform".format(self))

    @property
    def pivot(self):
        """
        :returns list: The translate pivot and rotate value.
        """
        val = cmds.xform(self.full_path, q=1, ws=1, t=1)[:3] + cmds.xform(self.full_path, q=1, ws=1, ro=1)
        return val

    def node_type(self, shape=False):
        """
        Get node type. If the shape key is true and a shape is found it will return the shape type.

        :return:
        """
        node = self.full_path
        if shape:
            if self.shape:
                node = self.shape.full_path
        return cmds.objectType(node)

    def rename(self, new_name):
        with api.core.MDagModifier() as modifier:
            modifier.renameNode(self.obj, new_name)
        self.node = new_name

    def add_to_namespace(self, namespace_name):
        """
        Checks if namespace exists, if it doesn't

        :param namespace_name:
        :return:
        """
        namespace = OpenMaya.MNamespace
        if not namespace.namespaceExists(namespace_name):
            namespace.addNamespace(namespace_name)
        with api.core.MDagModifier() as modifier:
            modifier.renameNode(self.obj, "{}:{}".format(namespace_name, self.full_path))

    def rebuild_data(self):
        if not self.exists:
            return
        if not self.path == self.data.name:
            self.rename(self.data.name)
        self._rebuild_attr_from_data(self.data.attributes)
        self.set_parent(self.data.parent)
        self.set_matrix(self.data.world_matrix)

    @decorator.timer()
    def rebuild_hierarchy_data(self, node_type="transform"):
        """
        :param node_type:
        :param data:
        :return:
        """
        if not self.hierarchy_data:
            return
        for key, data in self._hierarchy_data.to_dict().items():
            node_typ = data["node_type"] if "node_type" in data.keys() else node_type
            node = cmds.createNode(node_typ, name=data["name"], parent=data["parent"])
            node = get_node_class(node)
            node.data.load_from_dict(data)
            node.rebuild_data()

        self.node = next(iter(self._hierarchy_data.to_dict()))
        # node.set_matrix(data["world_matrix"])
        # for attr, value in data["attributes"].items():
        #     if not node[attr].exists:
        #         node[attr].add(value)

    def create_child(self, name=None, nodeType="transform"):
        """
        Create child

        :return: RDag child
        """
        child = api.ops.create_node(name=name, node_type=nodeType, parent=self.node)
        return get_node_class(child)

    def delete(self):
        DepNode.delete(self)
        self._dag = None
        self._data = None
        self._hierarchy_data = None

    def project_to_mesh(self, meshes, offset=0.25):
        """
        Projects a ray to the nearest point on the mesh and returns a scale value

        :param
        :return: scale value
        """
        meshes = path.as_list(meshes)
        scale = projection.project_to_mesh_circular(self.full_path, meshes, offset=offset)
        return scale

    def center_pivot(self):
        """
        Center pivot.

        :return:
        """
        cmds.xform(self.full_path, cp=1)

    def matrix_constraint(self, target, mo=True, translate=True, rotate=True, scale=False):
        """
        Create matrix constraint to target. Takes inherited transforms into account.

        :param target:
        :param mo:
        :param translate:
        :param rotate:
        :param scale:
        :return:
        """
        constraints.matrix_constraint(self.full_path, target, mo=mo, translate=translate, rotate=rotate, scale=scale)

    def get_highest_level(self):
        """

        :return:
        """
        return path.get_highest_level(self.full_path)

    def get_root_hierarchy(self):
        """

        :return:
        """
        root = self.get_highest_level()
        root_hierarchy = get_node_class(root).get_children()
        root_hierarchy.insert(0, root)
        return root_hierarchy

    def get_children(self, cutoff=None, exclude_shapes=True, sort=True):
        """

        :param sort:
        :param cutoff:
        :param exclude_shapes:
        :return: list
        """
        children = path.get_children(self.full_path, cutoff=cutoff, exclude_shapes=exclude_shapes, sort=sort)
        return children

    def get_parents(self, cutoff=None, pool=None, **kwargs):
        """
        Get all parents

        :param cutoff:
        :param pool:
        :return: list
        """
        return path.get_parents(self.full_path, cutoff, pool, **kwargs)

    def get_world_matrix(self):
        """
        Get object matrix

        :return:
        """
        return api.core.to_inclusive_matrix(self.full_path)

    def get_local_matrix(self):
        """
        Get local matrix

        :return:
        """
        return api.core.to_exclusive_matrix(self.full_path)

    def get_object_matrix(self):
        """

        :return:
        """
        return api.core.to_object_matrix(self.full_path)

    def get_local_offset(self, child):
        """
        Get offset between object and parsed object

        :param child:
        :return:
        """
        if not child:
            raise ValueError("No child selected.")
        return api.ops.get_local_offset(self.node, child)

    def get_colour(self, rgb=False):
        """
        Get colour as string or rgb.

        :param rgb:
        :return:
        """
        return colour.get_colour(self.full_path, rgb=rgb)

    def get_constraint(self):
        """
        Remove constraints attached to the node

        :param str node:
        """
        con = []
        constraint_types = ["constraint", "decomposeMatrix"]
        for con in constraint_types:
            con = cmds.listConnections(self.full_path, type=con, source=True, destination=False)
        return con

    def get_vertices_in_radius(self, geo, radius):
        """
        Get all vertices within radius of center point.

        :return:
        """
        return mesh.get_vertices_in_radius(self.position(), geo, radius=radius)

    def set_colour(self, col):
        """
        Set colour as string or rgb.

        :param col:
        :return:
        """
        colour.set_colour(self.full_path, col)

    def set_matrix(self, matrix, world_space=True):
        """
        Set from MMatrix or matrix list
        :param world_space:
        :param matrix:
        :return:
        """
        cmds.xform(self.full_path, matrix=matrix, ws=world_space)

    def set_inherit_transform(self, value):
        """
        Set inherit transform value

        :param value: value
        """
        cmds.setAttr("{0}.inheritsTransform".format(self), value)

    def set_rotate(self, x=None, y=None, z=None):
        """
        Set rotate

        :param x: value
        :param y: value
        :param z: value
        """
        for axis, val in zip([".rx", ".ry", ".rz"], [x, y, z]):

            if not val:
                continue

            cmds.setAttr("{0}{1}".format(self, axis), val)

    def set_translate(self, x=None, y=None, z=None):
        """
        Set translate

        :param x: value
        :param y: value
        :param z: value
        """
        for axis, val in zip([".tx", ".ty", ".tz"], [x, y, z]):

            if not val:
                continue

            cmds.setAttr("{0}{1}".format(self, axis), val)

    def set_position(self, position):
        """
        Set position

        :param position: position object or coordinate list.
        :return:
        """
        if type(position) is str:
            matrix = api.core.to_inclusive_matrix(position)
            self.set_matrix(matrix)

        elif type(position) == list:
            self.set_translate(position[0], position[1], position[2])
            self.set_rotate(position[3], position[4], position[5])

    def set_parent(self, parent):
        """
        Tries to parent itself to the parsed node. Fails if node doesn't exist.
        :param parent:
        :return:
        """
        path.try_parent(self.full_path, parent)

    def set_to_zero_pos(self):
        """
        Sets to zero position.

        :return:
        """
        matrix = [1.0, 0.0, 0.0, 0.0,
                  0.0, 1.0, 0.0, 0.0,
                  0.0, 0.0, 1.0, 0.0,
                  0.0, 0.0, 0.0, 1.0]
        self.set_matrix(matrix)