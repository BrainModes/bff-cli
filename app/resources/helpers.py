import json
import httpx
from ..config import ConfigClass
from ..resources. error_handler import customized_error_template, ECustomizedError
from ..models.base_models import EAPIResponseCode
from logger import LoggerFactory

_logger = LoggerFactory("Helpers").get_logger()

def get_zone(namespace):
    return {ConfigClass.GREEN_ZONE_LABEL.lower(): ConfigClass.GREEN_ZONE_LABEL,
            ConfigClass.CORE_ZONE_LABEL.lower(): ConfigClass.CORE_ZONE_LABEL
            }.get(namespace.lower(), ConfigClass.GREEN_ZONE_LABEL.lower())


def get_user_role(user_id, project_id):
    url = ConfigClass.NEO4J_SERVICE + "/v1/neo4j/relations"
    try:
        with httpx.Client() as client:
            res = client.get(
            url=url,
            params={"start_id": user_id,
                    "end_id": project_id})
        _res = json.loads(res.text)[0]
        return _res
    except Exception:
        return None


def query__node_has_relation_with_admin(label='Container'):
    _logger.info("query__node_has_relation_with_admin".center(80, '-'))
    url = ConfigClass.NEO4J_SERVICE + f"/v1/neo4j/nodes/{label}/query"
    _logger.info(f"Requesting API: {url}")
    data = {'is_all': 'true'}
    try:
        with httpx.Client() as client:
            res = client.post(url=url, json=data)
        project = res.json()
        return project
    except Exception:
        return []

def query_node_has_relation_for_user(username, label='Container'):
    _logger.info("query_node_has_relation_for_user".center(80, '-'))
    url = ConfigClass.NEO4J_SERVICE + "/v1/neo4j/relations/query"
    data = {
        'start_label': 'User',
        'start_params': {'name': username},
        'end_label': label
    }
    _logger.info(f"Requesting API: {url}")
    _logger.info(f'Query payload: {data}')
    try:
        with httpx.Client() as client:
            res = client.post(url=url, json=data)
        _logger.info(f'Query response: {res.text}')
        res = res.json()
        return res
    except Exception:
        return []
    
def get_node_by_geid(geid):
    _logger.info("get_node_by_geid".center(80, '-'))
    url = ConfigClass.NEO4J_SERVICE + f"/v1/neo4j/nodes/geid/{geid}"
    _logger.info(f'Getting node: {url}')
    try:
        with httpx.Client() as client:
            res = client.get(url)
        _logger.info(f'Getting node info: {res.text}')
        result = res.json()
    except Exception as e:
        _logger.error(f'Error getting node by geid: {e}')
        result = None
    return result


def batch_query_node_by_geid(geid_list):
    url = ConfigClass.NEO4J_SERVICE + "/v1/neo4j/nodes/query/geids"
    payload = {
        "geids": geid_list
    }
    with httpx.Client() as client:
        res = client.post(url, json=payload)
    res_json = res.json()
    result = res_json.get('result')
    located_geid = []
    query_result = {}
    for node in result:
        geid = node.get('global_entity_id', '')
        if geid in geid_list:
            located_geid.append(geid)
            query_result[geid] = node
    return located_geid, query_result


def query_file_in_project(project_code, filename, zone=ConfigClass.GREEN_ZONE_LABEL):
    _logger.info("query_file_in_project".center(80, '-'))
    url = ConfigClass.NEO4J_SERVICE + "/v2/neo4j/nodes/query"
    data = {"query": {
        "name": filename.split('/')[-1],
        "display_path": filename,
        "archived": False,
        "project_code": project_code,
        "labels": [zone]}}
    _logger.info(f"Query url: {url}")
    try:
        _logger.info(f"Get file info payload: {data}")
        with httpx.Client() as client:
            res = client.post(url=url, json=data)
        _logger.info(f"Query file response: {res.text}")
        file_res = res.json()
        _logger.info(f"file response: {file_res}")
        if file_res.get('code') == 200 and file_res.get('result'):
            result =  file_res
        else:
            result = []
    except Exception as e:
        _logger.error(str(e))
        result = []
    finally:
        return result


def get_file_entity_id(project_code, file_name, zone=ConfigClass.GREEN_ZONE_LABEL):
    res = query_file_in_project(project_code, file_name, zone)
    res = res.get('result')
    if not res:
        return None
    else:
        global_entity_id = res[0].get('global_entity_id')
        return global_entity_id


def get_file_by_id(file_id):
    post_data = {"global_entity_id": file_id}
    try:
        with httpx.Client() as client:
            response = client.post(ConfigClass.NEO4J_SERVICE + f"/v1/neo4j/nodes/File/query", json=post_data)
        if not response.json():
            return None
        return response.json()[0]
    except Exception:
        return None


def get_node(post_data, label):
    try:
        with httpx.Client() as client:
            response = client.post(ConfigClass.NEO4J_SERVICE + f"/v1/neo4j/nodes/{label}/query", json=post_data)
        if not response.json():
            return None
        return response.json()[0]
    except Exception:
        return None

def get_user_projects(user_role, username):
    _logger.info("get_user_projects".center(80, '-'))
    _logger.info(f'Current username: {username}')
    projects_list = []
    if user_role == "admin":
        project_candidate = query__node_has_relation_with_admin()
    else:
        projects = query_node_has_relation_for_user(username)
        project_candidate = []
        for p in projects:
            _logger.info(f"Found project status: {p['r']}")
            if p['r'].get('status', 'hibernated') == 'active':
                project_candidate.append(p['end_node'])
            else:
                _logger.info(f"Disabled project: {p['end_node']}")
        _logger.info(f'Found projects: {project_candidate}')
    _logger.info(f"Number of candidates: {len(project_candidate)}")
    for p in project_candidate:
        res_projects = {'name': p.get('name'),
                        'code': p.get('code'),
                        'id': p.get('id'),
                        'geid': p.get('global_entity_id')}
        projects_list.append(res_projects)
    _logger.info(f"Number of projects found: {len(projects_list)}")
    return projects_list


def attach_manifest_to_file(event):
    project_code = event.get('project_code')
    global_entity_id = event.get('global_entity_id')
    manifest_id = event.get('manifest_id')
    attributes = event.get('attributes')
    username = event.get('username')
    project_role = event.get('project_role')
    _logger.info("attach_manifest_to_file".center(80, '-'))
    url = ConfigClass.FILEINFO_HOST + "/v1/files/attributes/attach"
    payload = {"project_code": project_code,
               "manifest_id": manifest_id,
               "global_entity_id": [global_entity_id],
               "attributes": attributes,
               "inherit": True,
               "project_role": project_role,
               "username": username}
    _logger.info(f"POSTING: {url}")
    _logger.info(f"PAYLOAD: {payload}")
    with httpx.Client() as client:
        response = client.post(url=url, json=payload)
    _logger.info(f"RESPONSE: {response.text}")
    if not response.json():
        return None
    return response.json()


def http_query_node_zone(folder_event):
    namespace = folder_event.get('namespace')
    project_code = folder_event.get('project_code')
    folder_name = folder_event.get('folder_name')
    display_path = folder_event.get('display_path')
    folder_relative_path = folder_event.get('folder_relative_path')
    zone_label = get_zone(namespace)
    payload = {
        "query": {
            "folder_relative_path": folder_relative_path,
            "display_path": display_path,
            "name": folder_name,
            "project_code": project_code,
            "archived": False,
            "labels": ['Folder', zone_label]}
    }
    node_query_url = ConfigClass.NEO4J_SERVICE + "/v2/neo4j/nodes/query"
    with httpx.Client() as client:
        response = client.post(node_query_url, json=payload)
    return response


def get_parent_label(source):
    return {
        'folder': 'Folder',
        'container': 'Container'
    }.get(source.lower(), None)


def separate_rel_path(folder_path):
    folder_layers = folder_path.strip('/').split('/')
    if len(folder_layers) > 1:
        rel_path = '/'.join(folder_layers[:-1])
        folder_name = folder_layers[-1]
    else:
        rel_path = ''
        folder_name = folder_path
    return rel_path, folder_name


def verify_list_event(source_type, folder):
    if source_type == 'Folder' and not folder:
        code = EAPIResponseCode.bad_request
        error_msg = 'missing folder name'
    elif source_type == 'Container' and folder:
        code = EAPIResponseCode.bad_request
        error_msg = 'Query project does not require folder name'
    else:
        code = EAPIResponseCode.success
        error_msg = ''
    return code, error_msg


def check_folder_exist(zone, project_code, folder):
    folder_check_event = {
        'namespace': zone,
        'project_code': project_code,
        'display_path': folder,
        'folder_name': folder.split('/')[-1],
        'folder_relative_path': '/'.join(folder.split('/')[0:-1])
    }
    folder_response = http_query_node_zone(folder_check_event)
    res = folder_response.json().get('result')
    if folder_response.status_code != 200:
        error_msg = folder_response.json()["error_msg"]
        code = EAPIResponseCode.internal_error
    elif res:
        error_msg = ''
        code = EAPIResponseCode.success
    else:
        error_msg = 'Folder not exist'
        code = EAPIResponseCode.not_found
    return code, error_msg
