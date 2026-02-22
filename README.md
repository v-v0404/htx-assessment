# API Documentation

## Contents

- [Overview](#overview)
- [Setup and Installation](#setup-and-installation)
- [End Points](#end-points)
  - [Base URL](#base-url)
  - [Upload Images](#upload-images)
  - [List All Images](#list-all-images)
  - [Get Image by ID](#get-image-by-id)
  - [Get Thumbnail](#get-thumbnail)
  - [Get Statistics](#get-statistics)
- [Data Models](#data-models)
- [Example Requests and Responses](#example-requests-and-responses)
- [Error Handling](#error-handling)

---

## Overview

This API provides an endpoint for image uploading and processing. Images uploaded are being processed in the background. This includes extracting metadata, generating thumbnails and adding captions with AI.

**Supported image format**

- JPEG (image/jpeg)
- PNG (image/png)

**Processing Pipeline**

When an image is uploaded, the API performs the following steps asynchronously:

1. Validates file type and image integrity
2. Saves the original file to the uploads directory
3. Extracts image metadata (dimensions, format, file size)
4. Generates small (128×128) and medium (512×512) thumbnails
5. Extracts EXIF data if present
6. Generates an AI caption using the BLIP large model

**Image Processing Status**

| **Status** | **Description** |
|------------|-----------------|
| processing | Image has been uploaded and is being processed in the background |
| success | Processing completed successfully; metadata and caption are available |
| failed | Processing failed; see error_message for details |

---

## Setup and Installation

### Prerequisites

| **Requirement** | **Version** | **Notes** |
|-----------------|-------------|-----------|
| Python | 3.9+ | Required for FastAPI and ML libraries |
| pip | Latest | For installing Python dependencies |
| Git | Any | To clone the repository |

### 1. Clone the repository

```bash
git clone https://github.com/v-v0404/htx-assessment.git
cd htx-assessment
```

### 2. Install the required dependencies

```bash
pip install -r main/requirements.txt
```

> **Note:** The PyTorch CPU build is several hundred MB. The BLIP captioning model (Salesforce/blip-image-captioning-large) is an additional ~1.9 GB downloaded from Hugging Face on first startup. Ensure you have at least 4 GB of free disk space and a stable internet connection before proceeding.

### 3. Start the application

```bash
uvicorn main.main:app
```

The application will be available at `http://127.0.0.1:8000`

On first run, you will see Hugging Face downloading the BLIP model weights. This only happens once — the model is cached locally in your user profile (typically `C:\Users\<you>\.cache\huggingface\`).

The SQLite database file (`images.db`) and storage directories (`uploads\` and `thumbnails\`) are created automatically in the project folder on first run.

### Interactive API Docs

FastAPI automatically generates interactive documentation. Once the server is running, visit either of these URLs in your browser:

| **URL** | **Description** |
|---------|-----------------|
| http://localhost:8000/docs | Swagger UI — try out each endpoint directly in the browser |
| http://localhost:8000/redoc | ReDoc — clean, readable reference documentation |

---

## End Points

### Base URL

```
http://localhost:8000
```

### Upload Images

**POST /api/images**

Upload one or more images for asynchronous processing. The endpoint accepts multipart form data and immediately returns image IDs while processing continues in the background.

**Request**

| **Parameter** | **Type** | **Required** | **Description** |
|---------------|----------|--------------|-----------------|
| file | File[] (multipart) | Yes | One or more image files to upload (JPEG or PNG) |

**Response (200 OK)**

Returns a results array where each entry corresponds to one uploaded file.

```json
{
  "status": "success",
  "data": {
    "image_id": image_id,
    "message": "Image {file.filename} uploaded and processing started"
  },
  "error": None
}
```

**Results Field**

| **Field** | **Type** | **Description** |
|-----------|----------|-----------------|
| status | string | "success" if accepted, "failed" if rejected immediately |
| data.image_id | string (UUID) | Unique identifier for the image |
| data.message | string | Human-readable status message (on success) |
| error | string \| null | Error description (on failure), otherwise null |

---

### List All Images

**GET /api/images**

Returns a list of all images, including their processing status, metadata (if available), EXIF data (if available), and thumbnail URLs (if available).

**Response (200 OK)**

```json
{
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
    "exif_data": img.exif_data,
    "thumbnails": {
      "small": "http://localhost:8000/api/images/{img.id}/thumbnails/small",
      "medium": "http://localhost:8000/api/images/{img.id}/thumbnails/medium"
    }
  },
  "error": img.error_message
}
```

**Response Fields**

| **Field** | **Type** | **Description** |
|-----------|----------|-----------------|
| status | string | Processing status: processing, success, or failed |
| caption | string \| null | AI-generated image caption (only on success) |
| data.image_id | string | UUID of the image |
| data.original_name | string | Original filename as uploaded |
| data.processed_at | string (ISO 8601) | Timestamp when processing completed |
| data.processing_time | float | Time taken to process the image in seconds |
| data.metadata.width | integer | Image width in pixels |
| data.metadata.height | integer | Image height in pixels |
| data.metadata.format | string | Image format (e.g. JPEG, PNG) |
| data.metadata.size_bytes | integer | File size in bytes |
| data.exif_data | object \| null | EXIF metadata extracted from the image |
| data.thumbnails.small | string (URL) | URL to the 128×128 thumbnail |
| data.thumbnails.medium | string (URL) | URL to the 512×512 thumbnail |
| error | string \| null | Error message if processing failed |

---

### Get Image by ID

**GET /api/images/{image_id}**

Retrieves full details for a specific image. Only available for images with status success.

**Path Parameters**

| **Parameter** | **Type** | **Description** |
|---------------|----------|-----------------|
| image_id | string (UUID) | The unique identifier of the image |

**Response (200 OK)**

```json
{
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
    "exif_data": img.exif_data,
    "thumbnails": {
      "small": "http://localhost:8000/api/images/{img.id}/thumbnails/small",
      "medium": "http://localhost:8000/api/images/{img.id}/thumbnails/medium"
    }
  },
  "error": img.error_message
}
```

**Response Fields**

| **Field** | **Type** | **Description** |
|-----------|----------|-----------------|
| status | string | Processing status: processing, success, or failed |
| caption | string \| null | AI-generated image caption (only on success) |
| data.image_id | string | UUID of the image |
| data.original_name | string | Original filename as uploaded |
| data.processed_at | string (ISO 8601) | Timestamp when processing completed |
| data.processing_time | float | Time taken to process the image in seconds |
| data.metadata.width | integer | Image width in pixels |
| data.metadata.height | integer | Image height in pixels |
| data.metadata.format | string | Image format (e.g. JPEG, PNG) |
| data.metadata.size_bytes | integer | File size in bytes |
| data.exif_data | object \| null | EXIF metadata extracted from the image |
| data.thumbnails.small | string (URL) | URL to the 128×128 thumbnail |
| data.thumbnails.medium | string (URL) | URL to the 512×512 thumbnail |
| error | string \| null | Error message if processing failed |

**Error Responses**

| **Status Code** | **Condition** |
|-----------------|---------------|
| 404 Not Found | No image exists with the given image_id |
| 400 Bad Request | Image exists but status is not success (still processing or failed) |

---

### Get Thumbnail

**GET /api/images/{image_id}/thumbnails/{size}**

Returns the JPEG thumbnail image file for a successfully processed image.

**Path Parameters**

| **Parameter** | **Type** | **Values** | **Description** |
|---------------|----------|------------|-----------------|
| image_id | string (UUID) | — | The unique identifier of the image |
| size | string | small, medium | Thumbnail size: small (128×128) or medium (512×512) |

**Response**

Returns the JPEG image file directly with `Content-Type: image/jpeg`.

**Error Responses**

| **Status Code** | **Condition** |
|-----------------|---------------|
| 404 Not Found | No image with the given image_id |
| 400 Bad Request | Image is not yet successfully processed |
| 400 Bad Request | size is not small or medium |

---

### Get Statistics

**GET /api/stats**

Returns statistics about all images in the system.

**Response (200 OK)**

```json
{
  "total": total_images,
  "successful": successful_images,
  "failed": failed_images,
  "average_processing_time_seconds": avg_processing_time
}
```

**Response Fields**

| **Field** | **Type** | **Description** |
|-----------|----------|-----------------|
| total | integer | Total number of images (all statuses) |
| successful | integer | Number of images with status success |
| failed | integer | Number of images with status failed |
| average_processing_time_seconds | float | Mean processing time across all images (seconds, rounded to 2 decimal places) |

---

## Data Models

### Image Object

| **Field** | **Type** | **Nullable** | **Description** |
|-----------|----------|--------------|-----------------|
| id | string (UUID) | No | Primary key, auto-generated on upload |
| original_name | string | No | Filename as provided during upload |
| status | string | No | Current state: processing, success, or failed |
| width | integer | Yes | Image width in pixels (set after processing) |
| height | integer | Yes | Image height in pixels (set after processing) |
| format | string | Yes | Image format string from Pillow (e.g. JPEG) |
| size_bytes | integer | Yes | File size in bytes |
| caption | string | Yes | AI-generated caption from BLIP large model |
| exif_data | JSON object | Yes | Key-value pairs of EXIF tag names and values |
| processed_at | datetime | Yes | UTC timestamp of processing completion |
| processing_time | float | Yes | Duration of processing in seconds |
| error_message | string | Yes | Error description when status is failed |

---

## Example Requests and Responses

### Example 1: Uploading a single image (success)

**Response (200 OK)**

```json
{
  "results": [
    {
      "status": "success",
      "data": {
        "image_id": "2a894558-fc56-427e-a825-f43752f0d270",
        "message": "Image Canon_40D.jpg uploaded and processing started"
      },
      "error": null
    }
  ]
}
```

### Example 2: Uploading a single image (invalid file format)

**Response (200 OK)**

```json
{
  "results": [
    {
      "status": "failed",
      "data": {
        "image_id": "96ec7bf0-2c02-4285-99f2-90ce7f5ed0d1"
      },
      "error": "Invalid file type for Software Engineering THA (mandatory).pdf"
    }
  ]
}
```

### Example 3: Uploading multiple images (mix of success and invalid images)

**Response 200 (OK)**

```json
{
  "results": [
    {
      "status": "success",
      "data": {
        "image_id": "d6b62d64-c1d1-4f69-815c-3ad2495d9a65",
        "message": "Image Olympus_C8080WZ.jpg uploaded and processing started"
      },
      "error": null
    },
    {
      "status": "success",
      "data": {
        "image_id": "f301697f-c1ef-4ac4-bc6b-6c10e8a9ab39",
        "message": "Image Canon_DIGITAL_IXUS_400.jpg uploaded and processing started"
      },
      "error": null
    },
    {
      "status": "failed",
      "data": {
        "image_id": "187f1892-c38b-4c84-b820-7601419ea18c"
      },
      "error": "Corrupted or invalid image content for test.jpg"
    }
  ]
}
```

### Example 4: List all images

**Response 200 (OK)**

```json
[
  {
    "status": "success",
    "caption": "a close up of a fish with a lot of water on it",
    "data": {
      "image_id": "a15731a0-f4f8-4b4a-b9bb-f377ebf81f7d",
      "original_name": "Olympus_C8080WZ.jpg",
      "processed_at": "2026-02-22T14:25:51.389434",
      "processing_time": 1.42746901512146,
      "metadata": {
        "width": 100,
        "height": 72,
        "format": "JPEG",
        "size_bytes": 3224
      },
      "exif_data": {
        "ResolutionUnit": 2,
        "ExifOffset": 222,
        "Make": "OLYMPUS CORPORATION",
        "Model": "C8080WZ",
        "Software": "GIMP 2.4.5",
        "Orientation": 1,
        "DateTime": "2008:07:31 13:03:47",
        "YCbCrPositioning": 1,
        "YResolution": "72.0",
        "XResolution": "72.0",
        "Artist": ""
      },
      "thumbnails": {
        "small": "http://localhost:8000/api/images/a15731a0-f4f8-4b4a-b9bb-f377ebf81f7d/thumbnails/small",
        "medium": "http://localhost:8000/api/images/a15731a0-f4f8-4b4a-b9bb-f377ebf81f7d/thumbnails/medium"
      }
    },
    "error": null
  },
  {
    "status": "success",
    "caption": "yellow motorcycle parked on the side of the road near bushes",
    "data": {
      "image_id": "32887bd8-c673-4d47-9cc9-9603725e75d8",
      "original_name": "Canon_DIGITAL_IXUS_400.jpg",
      "processed_at": "2026-02-22T14:25:52.524390",
      "processing_time": 1.124220848083496,
      "metadata": {
        "width": 100,
        "height": 75,
        "format": "JPEG",
        "size_bytes": 9198
      },
      "exif_data": {
        "ResolutionUnit": 2,
        "ExifOffset": 200,
        "Make": "Canon",
        "Model": "Canon DIGITAL IXUS 400",
        "Software": "GIMP 2.4.5",
        "Orientation": 1,
        "DateTime": "2008:07:31 17:15:01",
        "YCbCrPositioning": 1,
        "XResolution": "72.0",
        "YResolution": "72.0"
      },
      "thumbnails": {
        "small": "http://localhost:8000/api/images/32887bd8-c673-4d47-9cc9-9603725e75d8/thumbnails/small",
        "medium": "http://localhost:8000/api/images/32887bd8-c673-4d47-9cc9-9603725e75d8/thumbnails/medium"
      }
    },
    "error": null
  },
  {
    "status": "failed",
    "caption": null,
    "data": {
      "image_id": "f56b19b9-51f3-47cf-a892-42e6a62f0605",
      "original_name": "test.jpg",
      "processed_at": "2026-02-22T14:25:49.952045",
      "metadata": null,
      "thumbnails": null
    },
    "error": "Corrupted or invalid image content"
  }
]
```

### Example 5: List a single image

**Response 200 (OK)**

```json
{
  "status": "success",
  "caption": "a close up of a fish with a lot of water on it",
  "data": {
    "image_id": "a15731a0-f4f8-4b4a-b9bb-f377ebf81f7d",
    "original_name": "Olympus_C8080WZ.jpg",
    "processed_at": "2026-02-22T14:25:51.389434",
    "processing_time": 1.42746901512146,
    "metadata": {
      "width": 100,
      "height": 72,
      "format": "JPEG",
      "size_bytes": 3224
    },
    "exif_data": {
      "ResolutionUnit": 2,
      "ExifOffset": 222,
      "Make": "OLYMPUS CORPORATION",
      "Model": "C8080WZ",
      "Software": "GIMP 2.4.5",
      "Orientation": 1,
      "DateTime": "2008:07:31 13:03:47",
      "YCbCrPositioning": 1,
      "YResolution": "72.0",
      "XResolution": "72.0",
      "Artist": ""
    },
    "thumbnails": {
      "small": "http://localhost:8000/api/images/a15731a0-f4f8-4b4a-b9bb-f377ebf81f7d/thumbnails/small",
      "medium": "http://localhost:8000/api/images/a15731a0-f4f8-4b4a-b9bb-f377ebf81f7d/thumbnails/medium"
    }
  },
  "error": null
}
```

### Example 6: Get statistics

**Response 200 (OK)**

```json
{
  "total": 3,
  "successful": 2,
  "failed": 1,
  "average_processing_time_seconds": 0.85
}
```

### Example 7: Get small thumbnail

**Response 200 (OK)**

Returns the JPEG thumbnail image file directly.

---

## Error Handling

All error responses return a JSON body with a field describing the error.

**Validation**

File type validation is performed in two stages: first by checking the Content-Type header, then by attempting to open and verify the file as an image using Pillow. Files that fail either check are rejected immediately and recorded with status failed do not get processed.

**Processing Errors**

If an error occurs during background processing (thumbnail generation, EXIF extraction, or captioning), the image status is set to failed and the error message is stored in error_message.