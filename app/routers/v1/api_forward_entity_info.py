from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi_utils.cbv import cbv
from ...resources.error_handler import catch_internal
from ...resources.dependencies import jwt_required
from ...resources.helpers import *
from ...models.entity_info_models import CheckFileResponse
from logger import LoggerFactory
import httpx

router = APIRouter()


@cbv(router)
class APIEntityInfo:
    _API_TAG = 'Entity INFO'
    _API_NAMESPACE = "api_forward_entity_info"

    def __init__(self):
        self._logger = LoggerFactory(self._API_NAMESPACE).get_logger()

    @router.get("/project/{project_code}/file/exist", tags=[_API_TAG],
                response_model=CheckFileResponse,
                summary="Check source file")
    @catch_internal(_API_NAMESPACE)
    async def check_source_file(self, project_code, zone, file_relative_path,
                                current_identity: dict = Depends(jwt_required)):
        try:
            role = current_identity["role"]
        except (AttributeError, TypeError):
            return current_identity
        query = {
            "project_code": project_code,
            "zone": zone,
            "file_relative_path": file_relative_path
        }
        with httpx.Client() as client:
            fw_response = client.get(ConfigClass.FILEINFO_HOST + "/v1/project/{}/file/exist".format(project_code), params=query)
        return JSONResponse(content=fw_response.json(), status_code=fw_response.status_code)
