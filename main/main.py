import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse, FileResponse
from PIL import Image as PILImage
from typing import Annotated
import uuid
import shutil
import os
import io
import time
from datetime import datetime

from sqlalchemy import func
from database import engine, SessionLocal, Base
from models import Image
from image_processing import THUMBNAIL_DIR, process_image, UPLOAD_DIR
from logger import logger

app = FastAPI()

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/images")
async def upload_image(
    background_tasks: BackgroundTasks,
    file: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    response = []

    for file in file:
        image_id = str(uuid.uuid4())

        # Validate file type
        if not file.content_type or file.content_type not in {"image/jpeg", "image/png"}:
            db_image = Image(id=image_id, original_name=file.filename, status="failed", processed_at=datetime.utcnow(), error_message=f"Invalid file type: {file.content_type}")
            db.add(db_image)
            db.commit()
            response.append({
                "status": "failed",
                "data": {"image_id": image_id},
                "error": f"Invalid file type for {file.filename}"
            })
            continue
        
        # Validate actual image content (eg extension is changed)
        try:
            contents = await file.read()
            image = PILImage.open(io.BytesIO(contents))
            image.verify()
        except Exception:
            db_image = Image(id=image_id, original_name=file.filename, status="failed", processed_at=datetime.utcnow(), error_message="Corrupted or invalid image content")
            db.add(db_image)
            db.commit()
            response.append({
                "status": "failed",
                "data": {"image_id": image_id},
                "error": f"Corrupted or invalid image content for {file.filename}"
            })
            continue
        finally:
            await file.seek(0)

        file_path = os.path.join(UPLOAD_DIR, f"{image_id}_{file.filename}")

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create DB record
        db_image = Image(
            id=image_id,
            original_name=file.filename,
            status="processing"
        )

        db.add(db_image)
        db.commit()

        # Background processing (non-blocking)
        background_tasks.add_task(process_image, db, image_id, file_path)

        logger.info(f"Uploaded image {image_id}")

        response.append({
            "status": "success",
            "data": {
                "image_id": image_id,
                "message": f"Image {file.filename} uploaded and processing started"
            },
            "error": None
        })

    return {"results": response} 

@app.get("/api/images")
def list_images(db: Session = Depends(get_db)):
    images = db.query(Image).all()

    result = []

    for img in images:
        if img.status == "success":
            result.append({
                "status": img.status,
                "caption": img.caption,
                "data": {
                    "image_id": img.id,
                    "original_name": img.original_name,
                    "processed_at": img.processed_at.isoformat() if img.processed_at else None,
                    "processing_time": img.processing_time,
                    "metadata": {
                        "width": img.width,
                        "height": img.height,
                        "format": img.format,
                        "size_bytes": img.size_bytes
                    },
                    "thumbnails": {
                        "small": f"http://localhost:8000/api/images/{img.id}/thumbnails/small",
                        "medium": f"http://localhost:8000/api/images/{img.id}/thumbnails/medium"
                    }
                },
                "error": img.error_message
            })
        else:
            result.append({
                "status": img.status,
                "caption": None,
                "data": {
                    "image_id": img.id,
                    "original_name": img.original_name,
                    "processed_at": img.processed_at.isoformat() if img.processed_at else None,
                    "metadata": None,
                    "thumbnails": None
                },
                "error": img.error_message
            })

    return JSONResponse(content=result)

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_images = db.query(Image).count()
    successful_images = db.query(Image).filter(Image.status == "success").count()
    failed_images = db.query(Image).filter(Image.status == "failed").count()
    total_processing_time = db.query(Image).with_entities(func.sum(Image.processing_time)).scalar() or 0
    avg_processing_time = round(total_processing_time / total_images, 2)

    return {
        "total": total_images,
        "successful": successful_images,
        "failed": failed_images,
        "average_processing_time_seconds": avg_processing_time
    }

@app.get("/api/images/{image_id}")
def get_image(image_id: str, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if image.status != "success":
        raise HTTPException(status_code=400, detail=f"Image processing {image.status}")

    return {
        "status": image.status,
        "caption": image.caption,
        "data": {
            "image_id": image.id,
            "original_name": image.original_name,
            "processed_at": image.processed_at.isoformat() if image.processed_at else None,
            "processing_time": image.processing_time,
            "metadata": {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "size_bytes": image.size_bytes
            },
            "thumbnails": {
                "small": f"http://localhost:8000/api/images/{image.id}/thumbnails/small",
                "medium": f"http://localhost:8000/api/images/{image.id}/thumbnails/medium"
            }
        },
        "error": image.error_message
    }

@app.get("/api/images/{image_id}/thumbnails/{size}")
def get_thumbnail(image_id: str, size: str, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if image.status != "success":
        raise HTTPException(status_code=400, detail=f"Image processing {image.status}")
    
    if size.lower() == "small":
        return FileResponse(f"{THUMBNAIL_DIR}/{image_id}_small.jpg", media_type="image/jpeg")
    elif size.lower() == "medium":
        return FileResponse(f"{THUMBNAIL_DIR}/{image_id}_medium.jpg", media_type="image/jpeg")
    else:
        raise HTTPException(status_code=400, detail="Invalid thumbnail size requested, please choose 'small' or 'medium'")
