from maya.api import OpenMaya


def blend_shape(mesh):
    """
    Get blendshape connected to node.

    :param str mesh:
    :return: Blendshape found on mesh
    :rtype: str/None
    """
    dag = OpenMaya.MSelectionList().add(mesh).getDagPath(0)
    obj = dag.node()

    bs = None
    dag_iter = OpenMaya.MItDependencyGraph(obj,
                                           OpenMaya.MItDependencyGraph.kDownstream,
                                           OpenMaya.MItDependencyGraph.kPlugLevel)
    while not dag_iter.isDone():
        current_item = dag_iter.currentNode()
        if current_item.hasFn(OpenMaya.MFn.kBlendShape):
            bs = current_item
            break
        dag_iter.next()
    return bs

  
def skin_cluster(mesh):
    """
    :param str mesh:
    :return: Skin cluster attached to the mesh
    :rtype: str/None
    """
    dag = OpenMaya.MSelectionList().add(mesh).getDagPath(0)
    dag = dag.extendToShape()
    obj = dag.node()

    skin = None
    dag_iter = OpenMaya.MItDependencyGraph(obj,
                                           OpenMaya.MItDependencyGraph.kDownstream,
                                           OpenMaya.MItDependencyGraph.kPlugLevel)
    while not dag_iter.isDone():
        current_item = dag_iter.currentNode()
        if current_item.hasFn(OpenMaya.MFn.kSkinClusterFilter):
            skin = current_item
            break
        dag_iter.next()
    return skin
