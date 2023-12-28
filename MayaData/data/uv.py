from MayaData.data.base import BaseData
from MayaData.lib import decorator

from maya.api import OpenMaya
from maya import cmds


@decorator.timer()
def get(name):
    dag_obj = OpenMaya.MSelectionList().add(name).getDagPath(0)
    mfn_mesh = OpenMaya.MFnMesh(dag_obj)
    
    data = UvData()
    uv_count = mfn_mesh.getAssignedUVs()
    uv_array = mfn_mesh.getUVs()
    index = 0
    for i in uv_count[0]:
        data['indices'].append(list(uv_count[1][index:index + i]))
        index += i
    data['vertices'] = [[u, v] for u, v in zip(uv_array[0], uv_array[1])]
    data['geometry'] = name
    return data


@decorator.timer()
def load(data=None, name=None):
    if not data:
        data = UvData()
        data.load()

    if name:
        data['geometry'] = name

    dag_obj = OpenMaya.MSelectionList().add(data['geometry']).getDagPath(0)
    mfn_mesh = OpenMaya.MFnMesh(dag_obj)
        
    u_array = [j[0] for j in data["vertices"]]
    v_array = [j[1] for j in data["vertices"]]

    uv_counts = []
    uv_ids = []

    for uv_faces in data["indices"]:
        uv_counts.append(len(uv_faces))
        for uv_face_id in uv_faces:
            uv_ids.append(uv_face_id)

    mfn_mesh.clearUVs()
    uv_set_names = mfn_mesh.getUVSetNames()[0]
    if len(uv_set_names) == 0:
        uv_set_names = cmds.polyUVSet(create=True, uvSet="map1")

    mfn_mesh.setUVs(u_array, v_array, uv_set_names)
    mfn_mesh.assignUVs(uv_counts, uv_ids, uv_set_names)
    return data

      
class UvData(BaseData):
    def __init__(self):
        super(UvData, self).__init__()
        self['geometry'] = str()
        self['indices'] = list()
        self['vertices'] = list()
