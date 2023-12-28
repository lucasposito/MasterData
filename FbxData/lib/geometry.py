
import fbx


def get(node):
    attr = node.GetNodeAttribute()
    if not isinstance(attr, fbx.FbxMesh):
        return
    
    data = GeometryData()
    data['name'] = node.GetName()

    vtx_count = attr.GetControlPointsCount()
    data['vertices'] += [list(attr.GetControlPointAt(i))[:3] for i in range(vtx_count)]
    
    return data






# def get(name):
#     dag_obj = OpenMaya.MSelectionList().add(name).getDagPath(0)
#     mfn_mesh = OpenMaya.MFnMesh(dag_obj)
#     data = GeometryData()
#     data['name'] = name
#     data['matrix'] = list(dag_obj.inclusiveMatrix())

#     vertex_data = list()
#     points = mfn_mesh.getPoints()
#     for point in points:
#         vertex_data.append([point.x, point.y, point.z])

#     face_vertex_indices = list()
#     face_counts = list()

#     for face_id in range(0, mfn_mesh.numPolygons):
#         poly_connect = mfn_mesh.getPolygonVertices(face_id)
#         face_vertex_indices.extend([i for i in poly_connect])
#         face_counts.append(len(poly_connect))

#     data['vertices'] = vertex_data
#     data['indices'] = face_vertex_indices
#     data['faces'] = face_counts
#     return data


class GeometryData(dict):
    def __init__(self):
        super(GeometryData, self).__init__()
        self['name'] = str()
        self['vertices'] = list()
        self['indices'] = list()
        self['faces'] = list()
        self['matrix'] = list()
