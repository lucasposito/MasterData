from MayaData.data.base import BaseData

from maya.api import OpenMaya, OpenMayaAnim
from maya import cmds


def get_channels(node):
    """
    Simple function to get all keyable and user defined attributes.

    :param node: str node
    :return: list of attributes
    """
    ke = cmds.listAttr(node, r=True, w=True, v=True, k=True) or []
    ud = cmds.listAttr(node, r=True, w=True, v=True, ud=True, unlocked=True) or []
    return list(set(ke + ud))


def _validate(node):
    """
    Checks if it's an expression node connected to the attribute.
    Since it's a function useful only for internal operation,
    it's faster to take an MObject instead of a string as input.

    :param node: MObject of node connected to the attribute
    :return: boolean
    """
    if node.hasFn(OpenMaya.MFn.kExpression):
        return True
    elif node.hasFn(OpenMaya.MFn.kAnimCurve):
        plug = OpenMaya.MFnDependencyNode(node).findPlug("output", False)
        for each in plug.destinations():
            return _validate(each.node())
    return False


def _process_string(code, node_name):
    """
    The whole expression string is processed here and returns only the last line where the attributes name and value are

    :param code: str of the whole expression returned by cmds.expression('expression_name')
    :param node_name: str of the Node that the expressions are connected to ('FaceOutput')
    :return: tuple with the str of the attribute name, float of the value and boolean
    """
    combo = True
    line = code.split("combo(")
    if len(line) == 1:
        combo = False
        line = code.split("inbetween(")
        if len(line) == 1:
            return None

    line = line[-1].split("},")
    line = [x.replace("{", "").replace(" ", "").replace(";", "").replace(node_name, "").replace(")", "") for x in line]

    if combo:
        attributes = line[0].split(",")
        max_value = map(float, line[1].split(","))
        return zip(attributes, max_value), combo

    line = line[0].split(",")
    return line[0:1] + map(float, line[1:]), combo


def _get_min_max(attr):
    """
    Gives min and max of specified attribute.
    Since it's a function useful only for internal operation,
    it's faster to take an MFnNumericAttribute instead of a string as input.

    :param attr: MFnNumericAttribute wrapper of attribute
    :return: float of min and max
    """
    min_value, max_value = False, False
    if attr.hasMin():
        min_value = attr.getMin()
    if attr.hasSoftMin():
        min_value = attr.getSoftMin()
    if attr.hasMax():
        max_value = attr.getMax()
    if attr.hasSoftMax():
        max_value = attr.getSoftMax()

    if not all([isinstance(min_value, float), isinstance(max_value, float)]):
        min_value, max_value = -1.0, 1.0

    return min_value, max_value


def build_logic(source, destination):
    """
    Main function that gives the mayaData, the expression nodes have FaceOutput attributes as input
    and FaceAnim is the source node controlling these attributes through driven keys.

    :param source: str of origin node, FaceAnim for facial rig files
    :param destination: str of destination node, FaceOutput for facial rig files
    :return: dict ExpressionData
    """
    expression_data = ExpressionData()

    temp_list = OpenMaya.MSelectionList().add(destination)
    nod = temp_list.getDependNode(0)
    nod_mfn = OpenMaya.MFnTransform(nod)

    attributes = get_channels(nod_mfn.fullPathName())
    attributes.remove("json_path")
    processed = list()

    for attr in attributes:
        main_plug = nod_mfn.findPlug(attr, False)
        attr_node = main_plug.source().node()
        if not attr_node.hasFn(OpenMaya.MFn.kAnimCurveUnitlessToUnitless):
            continue

        source_plug = OpenMaya.MFnDependencyNode(attr_node).findPlug("input", False).source()
        source_node = OpenMaya.MFnDependencyNode(source_plug.node())
        if source_node.name() != source:
            continue

        anim = OpenMayaAnim.MFnAnimCurve().setObject(attr_node)
        numeric_attr = OpenMaya.MFnNumericAttribute(source_plug.attribute())
        keys = list()

        for i in range(anim.numKeys):
            keys.append([anim.input(i), anim.value(i)])

        undershoot = False
        overshoot = False
        ctr_min, ctr_max = _get_min_max(numeric_attr)

        if keys[-1][0] > 0.0:
            key = keys[-1]
            undershoot = (keys[0][-1] < 0.0 or anim.preInfinityType == 1) and ctr_min < 0.0
        else:
            key = keys[0]
            overshoot = (keys[-1][-1] < 0.0 or anim.postInfinityType == 1) and ctr_max > 0.0

        _max = (1.0 / key[1]) * key[0]
        expression_data["FaceOut"].append([attr, [source_plug.name(), _max, undershoot or overshoot]])

        connection_check = {_validate(x.node()) for x in main_plug.destinations()}
        connection_check.discard(False)

        if not connection_check:
            continue

        for expr in [
            x.node() for x in main_plug.connectedTo(False, True) or [] if x.node().hasFn(OpenMaya.MFn.kExpression)
        ]:
            if expr in processed:
                continue

            attr_plug = OpenMaya.MFnDependencyNode(expr).findPlug("output", False).elementByPhysicalIndex(0)
            attr_plug = [u for u in attr_plug.destinations() or None if u.node() == nod]
            attr_name = attr_plug[0].partialName() if attr_plug else None

            expr_name = OpenMaya.MFnDependencyNode(expr).name()
            line = _process_string(cmds.expression(expr_name, s=True, q=True).split("\n")[-1], destination)

            if line and line[-1]:
                expression_data["combos"].append((attr_name, line[0]))
            elif line and not line[-1]:
                expression_data["in_between"].append((attr_name, line[0]))

            processed.append(expr)

    expression_data["all_channels"] = (
        expression_data["FaceOut"] + expression_data["in_between"] + expression_data["combos"]
    )
    return expression_data


def rebuild_logic():
    """
    TODO: the rebuild function is not a priority when running the heads through the solver
    :return:
    """
    pass


class ExpressionData(BaseData):
    def __init__(self, *args, **kwargs):
        super(ExpressionData, self).__init__(*args, **kwargs)
        self["FaceOut"] = list()
        self["combos"] = list()
        self["in_between"] = list()
        self["all_channels"] = list()

    def get_driver_values(self):
        if not self['all_channels']:
            return

        data = list()
        face_out = dict(self['FaceOut'])
        combos = dict(self['combos'])
        in_between = dict(self['in_between'])

        for channel in [x[0] for x in self['all_channels']]:
            if channel in face_out:
                data.append({channel: 1.0})
                continue
            if channel in in_between:
                driver = in_between[channel][0]
                value = in_between[channel][2]
                data.append({driver: value})
                continue
            if channel in combos:
                temp = dict()
                for driver, value in combos[channel]:
                    if driver in in_between:
                        _driver = driver
                        driver = in_between[_driver][0]
                        value = in_between[_driver][2]
                    temp[driver] = value
                data.append(temp)
                continue
            data.append(dict())

        return data
