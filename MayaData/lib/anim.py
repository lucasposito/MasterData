from maya.api import OpenMaya, OpenMayaAnim
import copy


DEFAULT_DATA = {"node": None, "attribute": None, "frames": dict()}
FRAME_DATA = {"value": None}


def cut_key(node, attribute, first_frame, last_frame):
    frames = range(first_frame, last_frame + 1)

    obj = OpenMaya.MSelectionList().add(node).getDependNode(0)
    plug = OpenMaya.MFnTransform(obj).findPlug(attribute, False)

    anim_obj = plug.source().node()
    anim_mfn = OpenMayaAnim.MFnAnimCurve()

    if not anim_mfn.hasObj(anim_obj):
        return
    anim_mfn.setObject(anim_obj)

    data = copy.deepcopy(DEFAULT_DATA)
    data["node"] = node
    data["attribute"] = attribute
    first = False
    for key in frames:
        time = OpenMaya.MTime(key, OpenMaya.MTime.uiUnit())
        index = anim_mfn.find(time)

        if index is None:
            continue
        if not first:
            first = key

        key -= first
        data["frames"][key] = copy.deepcopy(FRAME_DATA)
        data["frames"][key]["value"] = anim_mfn.value(index)

        anim_mfn.remove(index)

    return data


def paste_key(animation_data, frame_destination):
    if not animation_data:
        return

    obj = OpenMaya.MSelectionList().add(animation_data["node"]).getDependNode(0)
    plug = OpenMaya.MFnTransform(obj).findPlug(animation_data["attribute"], False)

    anim_obj = plug.source().node()
    anim_mfn = OpenMayaAnim.MFnAnimCurve()

    if not anim_mfn.hasObj(anim_obj):
        return
    anim_mfn.setObject(anim_obj)

    for frame in animation_data["frames"]:
        time = OpenMaya.MTime(frame + frame_destination, OpenMaya.MTime.uiUnit())
        index = anim_mfn.find(time)

        if index is not None:
            anim_mfn.remove(index)

        index = anim_mfn.insertKey(time)
        anim_mfn.setValue(index, animation_data["frames"][frame]["value"])


def set_key(node, attribute, value=None, frame=None):
    current_time = OpenMayaAnim.MAnimControl.currentTime()
    if frame:
        current_time = OpenMaya.MTime(frame, OpenMaya.MTime.kNTSCFrame)

    obj = OpenMaya.MSelectionList().add(node).getDependNode(0)
    plug = OpenMaya.MFnTransform(obj).findPlug(attribute, False)

    if value:
        plug.setDouble(value)
    value = plug.asDouble()

    anim_obj = plug.source().node()
    anim_mfn = OpenMayaAnim.MFnAnimCurve()

    if anim_mfn.hasObj(anim_obj):
        anim_mfn.setObject(anim_obj)
    else:
        anim_mfn.create(plug, OpenMayaAnim.MFnAnimCurve.kAnimCurveUnknown)

    index = anim_mfn.find(current_time)
    if index is None:
        index = anim_mfn.insertKey(current_time)
        anim_mfn.setValue(index, value)
        return anim_mfn

    anim_mfn.remove(index)
    if anim_mfn.numKeys:
        return anim_mfn

    OpenMaya.MDagModifier().deleteNode(anim_obj).doIt()
    plug.setDouble(value)