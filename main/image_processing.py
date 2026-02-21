import os
import uuid
import time
from PIL import Image as PILImage
from PIL.ExifTags import TAGS
from sqlalchemy.orm import Session
from datetime import datetime

from models import Image
from logger import logger
from generate_caption import generate_caption

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
THUMBNAIL_DIR = os.path.join(BASE_DIR, "thumbnails")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)


def extract_exif_data(image_path: str) -> dict:
    img = PILImage.open(image_path)
    exif_data_raw = img.getexif()

    if exif_data_raw:
        exif_table = {}
        for tag_id, value in exif_data_raw.items():
            tag_name = TAGS.get(tag_id, tag_id)
            # Convert non-serializable values to strings for JSON storage
            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="replace")
            elif not isinstance(value, (str, int, float, bool, list, dict)):
                value = str(value)
            exif_table[str(tag_name)] = value
        return exif_table

    return {}


def process_image(db: Session, image_id: str, file_path: str):
    start_time = time.time()

    try:
        logger.info(f"Processing image {image_id}")

        img = PILImage.open(file_path)

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

        # Extract EXIF data
        exif = extract_exif_data(file_path)

        # Generate caption
        caption = generate_caption(file_path)

        # Update DB
        db_image = db.query(Image).filter(Image.id == image_id).first()
        db_image.width = width
        db_image.height = height
        db_image.format = img.format
        db_image.size_bytes = file_size
        db_image.caption = caption
        db_image.exif_data = exif
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