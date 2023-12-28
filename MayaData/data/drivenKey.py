from MayaData.data.base import BaseData
from MayaData.lib import decorator, pivot, unplug_attr

from maya.api import OpenMaya
from maya import cmds


def _find_joint(node):
    """
    Checks if the output connection is a joint,
    if it's 'set driven keys' dependency node it will recursively check if the next one is a joint
    to finally return it.
    Since it's a function useful only for internal operation,
    it's faster to take an MObject instead of a string as the input.

    :param node: MObject of node connected to the attribute
    :return: str Joint Name
    """
    # TODO: Discuss and try a more generic solution accounting all conditions (BlendShapes, Driven Keys and Expressions)
    if node.hasFn(OpenMaya.MFn.kJoint):
        return OpenMaya.MFnTransform(node).partialPathName()
    elif node.apiType() in [
        OpenMaya.MFn.kAnimCurveUnitlessToUnitless,
        OpenMaya.MFn.kAnimCurveUnitlessToDistance,
        OpenMaya.MFn.kAnimCurveUnitlessToAngular,
        OpenMaya.MFn.kAnimCurveUnitlessToTime,
        OpenMaya.MFn.kBlendWeighted,
    ]:
        plug = OpenMaya.MFnDependencyNode(node).findPlug("output", False)
        for each in plug.destinations():
            return _find_joint(each.node())


def get_driven_joints_by_attr(node, attr="neutral"):
    """
    Traverses from the source node attribute (driver node) all the way to the destination joints (driven node)
    if the nodes in between are 'set driven key' dependency nodes
    (animCurveUL, animCurveUU, animCurveUA, animCurveUT, blendWeighted)
    and returns all the joints being influenced by this attribute.

    :param node: str node
    :param attr: specific attribute to traverse from
    :return: a list of the destination joints being driven by the specified attribute through 'set driven keys'
    """
    temp_list = OpenMaya.MSelectionList().add(node)
    node = temp_list.getDependNode(0)

    main_plug = OpenMaya.MFnTransform(node).findPlug(attr, False)
    driven = {_find_joint(connected.node()) for connected in main_plug.destinations()}
    driven.discard(None)
    return list(driven)


def get_attr_by_driven_joints(destination, source):
    """
    Traverses from the destination joints (driven node), all the way back to the source node attributes (driver node)
    if the nodes in between are 'set driven key' dependency nodes
    (animCurveUL, animCurveUU, animCurveUA, animCurveUT, blendWeighted)
    and returns all the attributes that are driving these joints.

    :param destination: str or a list of str objects
    :param source: str of the driver's node
    :return: a list of the attributes driving the destination joints through 'set driven keys'
    """
    temp_list = OpenMaya.MSelectionList().add(source)
    source = temp_list.getDependNode(0)

    if not isinstance(destination, list):
        destination = [destination]
    attributes = list()

    def get_attribute(plug):
        obj = plug.source().node()
        if obj == source:
            attributes.append(plug.source().partialName())
        elif (
            obj.apiType()
            in [
                OpenMaya.MFn.kAnimCurveUnitlessToUnitless,
                OpenMaya.MFn.kAnimCurveUnitlessToDistance,
                OpenMaya.MFn.kAnimCurveUnitlessToAngular,
                OpenMaya.MFn.kAnimCurveUnitlessToTime,
                OpenMaya.MFn.kBlendWeighted,
            ]
            and plug.isDestination
        ):
            for each in OpenMaya.MFnDependencyNode(obj).getConnections():
                get_attribute(each)

    for jnt in destination:
        temp_list = OpenMaya.MSelectionList().add(jnt)
        jnt = temp_list.getDependNode(0)
        for attr in OpenMaya.MFnDependencyNode(jnt).getConnections():
            get_attribute(attr)

    return list(set(attributes))


@decorator.timer()
def get(driver, root, pose_attrs=None, driven=None):
    """
    Sets Neutral attribute to 1 and the rest to 0 then saves as 'neutral' its driven joints matrices
    Then iterates through every attribute, sets it to 1, saves the joints matrices in the pose with same name,
    and sets back to 0 before going to next item

    :param driver: str of the FaceOutput node containing all sdk poses
    :param root: str of the parent joint
    :param pose_attrs: it's the list of channelBox attributes used to pose
    :param driven: it's the list of joints being controlled by the attributes
    :return: DrivenKeysDict dictionary
    """

    if not driven:
        driven = get_driven_joints_by_attr(driver)

    all_pose_attrs = get_attr_by_driven_joints(driven, driver)

    if not pose_attrs:
        pose_attrs = all_pose_attrs

    pose_attrs.remove("neutral") if "neutral" in pose_attrs else False
    data = DrivenKeyData()
    data["driver"] = driver

    data["matrix"] = list(OpenMaya.MSelectionList().add(root).getDagPath(0).inclusiveMatrix())

    with unplug_attr.Unplugged(driver, all_pose_attrs):
        driver_obj = OpenMaya.MSelectionList().add(driver).getDependNode(0)
        neutral_plug = OpenMaya.MFnTransform(driver_obj).findPlug("neutral", False)
        neutral_plug.setDouble(1)

        all_pose_attrs.remove("neutral") if "neutral" in all_pose_attrs else False

        for attr in all_pose_attrs:
            attr_plug = OpenMaya.MFnTransform(driver_obj).findPlug(attr, False)
            attr_plug.setDouble(0)

        cmds.dgdirty(neutral_plug.name())

        joint_mat = [list(pivot.get_offset_matrix(root, x)) for x in driven]
        data["poses"]["neutral"] = dict(zip([x for x in driven], joint_mat))

        for z in pose_attrs:
            z_plug = OpenMaya.MFnTransform(driver_obj).findPlug(z, False)
            joints = get_driven_joints_by_attr(driver, z)
            joints = filter(lambda x: str(x) in joints, driven)

            z_plug.setDouble(1)
            joint_mat = [list(pivot.get_offset_matrix(root, x)) for x in joints]
            data["poses"][z] = dict(zip([x for x in joints], joint_mat))

            z_plug.setDouble(0)
    return data


@decorator.timer()
def load(data=None, root_matrix=None, offset_matrix=False, poses=None, driven=None):
    """
    The joints need to be cleared out of sdk or animation keys in order to work

    :param data: DrivenKeysDict dictionary
    :param root_matrix: list or MMatrix of where to create it
    :param offset_matrix: boolean
    :param poses: list of attributes to apply the sdk
    :param driven: list of the joints to apply the sdk
    :return: None
    """
    if not data:
        data = DrivenKeyData()
        data.load()
    if not root_matrix:
        root_matrix = data["matrix"]
    if not isinstance(root_matrix, OpenMaya.MMatrix):
        root_matrix = OpenMaya.MMatrix(root_matrix)
    attribute_poses = data["poses"].keys()

    if poses:
        attribute_poses = data["poses"].keys()

    with unplug_attr.Unplugged(data["driver"], data["poses"].keys()):
        driver_obj = OpenMaya.MSelectionList().add(data["driver"]).getDependNode(0)
        neutral_plug = OpenMaya.MFnDependencyNode(driver_obj).findPlug("neutral", False)

        # data['poses'].pop('neutral') if 'neutral' in data['poses'].keys() else False
        cmds.dgdirty(neutral_plug.name())

        for attr in attribute_poses:
            attr_plug = OpenMaya.MFnDependencyNode(driver_obj).findPlug(attr, False)
            for jnt in data["poses"][attr]:
                if driven and jnt not in driven:
                    continue

                root = root_matrix
                if offset_matrix:
                    offset = OpenMaya.MMatrix(data["poses"]["neutral"][jnt]).inverse()
                    jnt_mat = OpenMaya.MSelectionList().add(jnt).getDagPath(0).inclusiveMatrix()
                    root = offset * jnt_mat

                neutral_mat = OpenMaya.MMatrix(data["poses"]["neutral"][jnt]) * root
                cmds.xform(jnt, m=neutral_mat, ws=True)

                cmds.setDrivenKeyframe(
                    jnt, attribute=["translate", "rotate"], cd=attr_plug.name(), dv=0, itt="spline", ott="spline"
                )

                pose_mat = OpenMaya.MMatrix(data["poses"][attr][jnt]) * root
                cmds.xform(jnt, m=pose_mat, ws=True)

                cmds.setDrivenKeyframe(
                    jnt, attribute=["translate", "rotate"], cd=attr_plug.name(), dv=1, itt="spline", ott="spline"
                )
                cmds.xform(jnt, m=neutral_mat, ws=True)


class DrivenKeyData(BaseData):
    """
    Store offset matrices for a set of joints for a set of poses
    """

    def __init__(self, *args, **kwargs):
        super(DrivenKeyData, self).__init__(*args, **kwargs)
        # Each key is name of pose, values are dicts with joint name as key and joint transformation as value
        self["driver"] = None
        self["poses"] = dict()
        self["matrix"] = list()
