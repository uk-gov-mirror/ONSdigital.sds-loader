from typing import Literal, Annotated

from fastapi import APIRouter, Request
from fastapi.params import Query
from lagom.integrations.fast_api import FastApiIntegration
from sdx_base.models.pubsub import get_message, Message, get_data
from starlette.responses import JSONResponse

from app import get_logger
from app.dependencies import build_container
from app.exceptions import NonCriticalException, DatasetException, SchemaException
from app.services.dataset_service import DatasetService
from app.services.schema_service import SchemaService
from app.settings import get_instance
from app.util.file_getters import get_file_path_from_bucket_notification, get_file_paths_from_github_notification

logger = get_logger()
router = APIRouter()
DEPS = FastApiIntegration(build_container())


# ------------------------
# core routes
# ------------------------


@router.get("/")
async def root():
    return {"message": "Welcome to sds-loader!"}


@router.get("/health")
async def health():
    return {"message": "OK"}


@router.get("/version")
async def version():
    return {"version": get_instance().app_version}


# ------------------------
# event driven endpoints
# ------------------------


@router.post("/events/schema/publish")
async def publish_schemas(
    request: Request,
    source: Annotated[
        Literal["github", "bucket"], Query(description="The source of the file specified in this request.")
    ] = "github",
    schema_service: SchemaService = DEPS.depends(SchemaService),
):
    """
    This endpoint handles a publishing schemas from a given location

    - If the source is "bucket", this will always be a single file (the one added to the bucket)
        - The body of the message Must contain a "name" field in the json payload, this specifies the name of the file in the bucket
    - If the source is "github", this could be multiple files (the new additions to the repo)
        - The body of the message must contain a comma separated list of file names
    """

    try:
        # Fetch the message from pubsub
        message: Message = await get_message(request)
    except Exception as e:
        logger.exception("Exception fetching message from request")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Invalid message body received: " + str(e)},
        )

    try:
        # Publish the new schemas
        schema_service.publish_new_schemas(
            source=source,
            file_list=[get_file_path_from_bucket_notification(get_data(message))]
            if source.lower() == "bucket"
            else get_file_paths_from_github_notification(get_data(message)),
        )
    except NonCriticalException as e:
        # Return a status 200 (non-critical exception)
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": str(e)},
        )

    except (SchemaException, Exception) as e:
        logger.exception("Exception publishing schemas")

        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Exception publishing schema: " + str(e)},
        )

    return JSONResponse(
        status_code=200,
        content={"success": True, "message": "Schemas published successfully"},
    )


@router.post("/events/dataset/create")
async def create_dataset(dataset_service: DatasetService = DEPS.depends(DatasetService)):
    """
    This endpoint handles creating a dataset

    A status 200 is returned in the following conditions:
        - Dataset created successfully
        - A non-critical exception is raised (e.g. no files to process)

    A status 500 is returned if the process to create the dataset failed.
    """

    try:
        dataset_service.create_dataset()
    except NonCriticalException as e:
        # Return a status 200 (non-critical exception)
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": str(e)},
        )

    except (DatasetException, Exception) as e:
        logger.exception("Exception creating dataset")

        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Exception creating dataset: " + str(e)},
        )

    return JSONResponse(
        status_code=200,
        content={"success": True, "message": "Dataset created successfully"},
    )


@router.post("/events/dataset/delete")
async def delete_dataset(dataset_service: DatasetService = DEPS.depends(DatasetService)):
    """
    This endpoint deletes a dataset

    A status 200 is returned in the following conditions:
        - Dataset deleted successfully
        - A non-critical exception is raised (e.g. no datasets to delete)

    A status 500 is returned if the process to delete the dataset failed.
    """

    try:
        dataset_service.delete_dataset()
    except NonCriticalException as e:
        # Return a status 200 (non-critical exception)
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": str(e)},
        )

    except (DatasetException, Exception) as e:
        logger.exception("Exception deleting dataset")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Exception deleting dataset: " + str(e)},
        )

    return JSONResponse(
        status_code=200,
        content={"success": True, "message": "Dataset deleted successfully"},
    )
