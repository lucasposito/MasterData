class Leaf(dict):
    def __init__(self, node_id, *args, **kwargs):
        super(Leaf, self).__init__(*args, **kwargs)
        self['parent'] = None
        self['id'] = node_id


class Tree(dict):
    def __init__(self):
        super(Tree, self).__init__()
        self['id'] = 0
        self._custom = None

    @property
    def custom_node(self):
        return self._custom

    @custom_node.setter
    def custom_node(self, attributes):
        self._custom = attributes

    def find_node(self, *args):
        node = self
        for _id in args:
            if _id in node.keys():
                node = node[_id]
                continue
        return node

    def delete_node(self, name):
        pass

    def add_node(self, *args):
        node = self
        for _id in args:
            if _id in node.keys():
                node = node[_id]
                continue
            new = Leaf(_id)
            if self._custom:
                new.update(self._custom)
            new['parent'] = node['id']
            node[_id] = new
            node = new
