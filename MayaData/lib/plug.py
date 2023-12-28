from maya.api import OpenMaya


def get_children(plug=None, counter=0):
    """
    If the plug is an array or compound plug, it will return a list of all its children.

    :param plug: OpenMaya.MPlug for recursive purposes
    :param counter: int counts the times the function is recursively called
    :return: list of children plugs
    """
    if not plug:
        return

    if plug.isArray:
        if plug.numElements() > 1:
            return [get_children(plug.elementByPhysicalIndex(x), counter + 1) for x in
                    range(plug.numElements())]
        plugs = [get_children(plug.elementByPhysicalIndex(x), counter + 1) for x in range(plug.numElements())]
        if isinstance(plugs[0], list):
            return plugs[0]
        return plugs

    if plug.isCompound:
        return [get_children(plug.child(x), counter + 1) for x in range(plug.numChildren())]
    if counter > 0:
        return plug
    return [plug]
