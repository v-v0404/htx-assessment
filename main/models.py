from sqlalchemy import Column, String, Integer, DateTime, Float, func
from datetime import datetime
from database import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(String, primary_key=True, index=True)
    original_name = Column(String)
    status = Column(String, default="processing")

    width = Column(Integer)
    height = Column(Integer)
    format = Column(String)
    size_bytes = Column(Integer)

    caption = Column(String)

    processed_at = Column(DateTime, default=func.now())
    processing_time = Column(Float)

    error_message = Column(String)