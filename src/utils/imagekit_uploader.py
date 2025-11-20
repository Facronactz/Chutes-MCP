from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from src.config import config
import uuid
import json
import tempfile
import os
from loguru import logger # Import loguru logger

def get_imagekit_instance():
    public_key = config.get('imagekit.public_key')
    private_key = config.get('imagekit.private_key')
    url_endpoint = config.get('imagekit.url_endpoint')

    if not all([public_key, private_key, url_endpoint]) or \
       public_key == "your_public_key" or \
       private_key == "your_private_key" or \
       url_endpoint == "your_url_endpoint":
        logger.warning("ImageKit is not fully configured (public_key, private_key, or url_endpoint missing/default). Skipping ImageKit instance creation.")
        return None

    return ImageKit(
        public_key=public_key,
        private_key=private_key,
        url_endpoint=url_endpoint
    )

def upload_to_imagekit(file_data, file_name_prefix, metadata, file_extension):
    imagekit = get_imagekit_instance()
    if not imagekit:
        logger.warning("ImageKit instance not available. Skipping upload.")
        return None

    # Serialize the entire metadata dictionary to a JSON string
    # Filter out None values before serialization
    filtered_metadata = {k: v for k, v in metadata.items() if v is not None}
    metadata_json = json.dumps(filtered_metadata, indent=2)
    request_metadata = json.loads(json.dumps({"generation_parameters": metadata_json}))

    extensions = [
        {"name": "google-auto-tagging", "maxTags": 10, "minConfidence": 90}, 
        {"name": "ai-auto-description"}
    ]

    temp_file_path = None
    try:
        # Create a temporary file and write the file data to it
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name
            logger.debug(f"Temporary file created for upload: {temp_file_path}")
        
        with open(temp_file_path, "rb") as f:
            upload_result = imagekit.upload(
                file=f,
                file_name=f"{file_name_prefix}_{uuid.uuid4()}.{file_extension}",
                options=UploadFileRequestOptions(
                    tags=["ai_generated", "chutes"],
                    custom_metadata=request_metadata,
                    use_unique_file_name=False, # We are generating a unique name ourselves
                    folder="/Chutes/", # Optional: specify a folder
                    extensions=extensions,
                ),
            )
        logger.info(f"File uploaded successfully to ImageKit: {upload_result.url}")
        return upload_result.url
    except Exception as e:
        logger.error(f"Error uploading to ImageKit: {e}", exc_info=True)
        return None
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.debug(f"Temporary file removed: {temp_file_path}")