import os
import uuid
import time
from PIL import Image as PILImage
from sqlalchemy.orm import Session
from datetime import datetime

from models import Image
from logger import logger

UPLOAD_DIR = "uploads"
THUMBNAIL_DIR = "thumbnails"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

ALLOWED_FORMATS = ["JPEG", "PNG"]


def process_image(db: Session, image_id: str, file_path: str):
    start_time = time.time()

    try:
        logger.info(f"Processing image {image_id}")

        img = PILImage.open(file_path)

        if img.format not in ALLOWED_FORMATS:
            raise ValueError("invalid file format")

        # Extract metadata
        width, height = img.size
        file_size = os.path.getsize(file_path)

        # Generate thumbnails
        small_thumb_path = f"{THUMBNAIL_DIR}/{image_id}_small.jpg"
        medium_thumb_path = f"{THUMBNAIL_DIR}/{image_id}_medium.jpg"

        img.thumbnail((128, 128))
        img.save(small_thumb_path)

        img = PILImage.open(file_path)
        img.thumbnail((512, 512))
        img.save(medium_thumb_path)

        # # AI Caption
        # caption = generate_caption(file_path)

        # Update DB
        db_image = db.query(Image).filter(Image.id == image_id).first()
        db_image.width = width
        db_image.height = height
        db_image.format = img.format
        db_image.size_bytes = file_size
        # db_image.caption = caption
        db_image.status = "success"
        db_image.processed_at = datetime.utcnow()
        db_image.processing_time = time.time() - start_time

        db.commit()

        logger.info(f"Successfully processed {image_id}")

    except Exception as e:
        logger.error(f"Processing failed for {image_id}: {str(e)}")

        db_image = db.query(Image).filter(Image.id == image_id).first()
        db_image.status = "failed"
        db_image.error_message = str(e)
        db.commit()