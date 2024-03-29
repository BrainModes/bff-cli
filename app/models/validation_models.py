from pydantic import BaseModel, Field
from .base_models import APIResponse


class ManifestValidatePost(BaseModel):
    """
    Validate Manifest post model
    """
    manifest_json: dict = Field({}, example={
                "manifest_name": "Manifest1",
                "project_code": "sampleproject",
                "attributes": {"attr1": "a1", "attr2": "test cli upload"},
                "file_path": "/data/core-storage/sampleproject/raw/testf1"
            }
    )


class ManifestValidateResponse(APIResponse):
    """
    Validate Manifest Response class
    """
    result: dict = Field({}, example={
                    "code": 200,
                    "error_msg": "",
                    "result": "Valid"
                }
            )


class ValidateDICOMIDPOST(BaseModel):
    """Validate DICOM ID Post model"""
    dcm_id: str


class ValidateDICOMIDResponse(APIResponse):
    """
    Validate DICOM ID response class
    """
    result: dict = Field({}, example={
            "code": 200,
            "error_msg": "",
            "result": "VALID"
        }
    )

class EnvValidatePost(BaseModel):
    """
    Validate Environment post model
    """
    action: str
    environ: str
    zone: str


class EnvValidateResponse(APIResponse):
    """
    Validate Manifest Response class
    """
    result: dict = Field({}, example={
        "code":200,
        "error_msg":"",
        "result":"valid"
        }
    )
