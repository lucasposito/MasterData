from MayaData.data.base import BaseData
from MayaData.lib import decorator
from maya.api import OpenMaya


def get(name):
    pass


@decorator.timer()
def load(data=None):
    if not data:
        data = AttrData()
        data.load()

    obj = OpenMaya.MSelectionList().add(data['node']).getDependNode(0)
    num_attr = OpenMaya.MFnNumericAttribute()

    attr_obj = num_attr.create(data['name'], data['name'], OpenMaya.MFnNumericData.kFloat, 0)

    if data['keyable']:
        num_attr.keyable = True
    if isinstance(data['hasMin'], float):
        num_attr.setMin(data['hasMin'])
    if isinstance(data['hasMax'], float):
        num_attr.setMax(data['hasMax'])

    mod = OpenMaya.MDGModifier()
    mod.addAttribute(obj, attr_obj)
    mod.doIt()


class AttrData(BaseData):
    def __init__(self):
        super(AttrData, self).__init__()
        self['node'] = None
        self['name'] = None
        self['type'] = None
        self['hasMin'] = False
        self['hasMax'] = False
        self['keyable'] = True
