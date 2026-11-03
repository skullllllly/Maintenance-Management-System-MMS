import io
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from starlette.datastructures import UploadFile

import app.main as main_module
import app.api.ticket_images as ticket_images_api

from app.db.session import get_db
from app.main import app
from app.services.image_processing import (
    CNNFeatureExtractor,
    ImageProcessingError,
    analyze_image,
    cnn_feature_extractor,
)


def encode_image(pixels: np.ndarray, extension: str = ".png") -> bytes:
    success, encoded = cv2.imencode(extension, pixels)
    if not success:
        raise RuntimeError("OpenCV failed to encode the test image.")
    return encoded.tobytes()


@pytest.fixture
def clear_image_bytes() -> bytes:
    image = np.full((256, 256, 3), 235, dtype=np.uint8)

    cv2.rectangle(
        image,
        (30, 30),
        (225, 225),
        (25, 25, 25),
        thickness=-1,
    )
    cv2.circle(
        image,
        (128, 128),
        38,
        (20, 70, 220),
        thickness=-1,
    )
    cv2.line(
        image,
        (20, 128),
        (236, 128),
        (30, 220, 40),
        thickness=5,
    )

    return encode_image(image)


@pytest.fixture
def blurry_image_bytes() -> bytes:
    image = np.full((256, 256, 3), 180, dtype=np.uint8)

    cv2.rectangle(
        image,
        (55, 55),
        (200, 200),
        (45, 45, 45),
        thickness=-1,
    )

    image = cv2.GaussianBlur(image, (31, 31), 18)
    return encode_image(image)


@pytest.fixture
def mock_cnn(monkeypatch):
    feature_vector = np.linspace(
        -1.0,
        1.0,
        2048,
        dtype=np.float32,
    )

    monkeypatch.setattr(
        cnn_feature_extractor,
        "extract",
        lambda pixels: feature_vector.tolist(),
    )


@pytest.mark.asyncio
async def test_clear_image_analysis(
    clear_image_bytes: bytes,
    mock_cnn,
):
    processed = await analyze_image(clear_image_bytes)

    assert isinstance(processed.blur_variance, float)
    assert np.isfinite(processed.blur_variance)
    assert processed.blur_variance >= 0.0
    assert processed.is_blurry is False
    assert len(processed.cnn_features) == 2048
    assert all(isinstance(value, float) for value in processed.cnn_features)


@pytest.mark.asyncio
async def test_blurry_image_is_rejected(
    blurry_image_bytes: bytes,
    mock_cnn,
):
    processed = await analyze_image(blurry_image_bytes)

    assert processed.is_blurry is True
    assert processed.blur_variance < 100.0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"not-an-image",
        b"\x89PNG\r\nnot-a-valid-png",
    ],
)
async def test_invalid_image_payload_raises_custom_exception(payload: bytes):
    with pytest.raises(ImageProcessingError):
        await analyze_image(payload)


@pytest.mark.asyncio
async def test_small_image_is_rejected():
    image = np.full((16, 16, 3), 128, dtype=np.uint8)

    with pytest.raises(
        ImageProcessingError,
        match="32x32",
    ):
        await analyze_image(encode_image(image))


@pytest.mark.asyncio
async def test_empty_upload_is_rejected():
    upload = UploadFile(
        filename="empty.png",
        file=io.BytesIO(b""),
        headers={"content-type": "image/png"},
    )

    from app.services.image_processing import read_limited_upload

    with pytest.raises(ImageProcessingError, match="empty"):
        await read_limited_upload(upload)


@pytest.mark.asyncio
async def test_upload_is_read_asynchronously():
    payload = b"test-image-content"
    upload = UploadFile(
        filename="test.png",
        file=io.BytesIO(payload),
        headers={"content-type": "image/png"},
    )

    from app.services.image_processing import read_limited_upload

    result = await read_limited_upload(upload)

    assert result == payload


def test_placeholder_model_does_not_break_initialization(monkeypatch):
    extractor = CNNFeatureExtractor()

    monkeypatch.setattr(
        extractor,
        "initialize",
        lambda: setattr(extractor, "_model", object()),
    )

    extractor.initialize()

    assert extractor._model is not None


@pytest.fixture
def client(monkeypatch, mock_cnn):
    monkeypatch.setattr(
        main_module.minio_client,
        "verify_bucket_existence",
        AsyncMock(),
    )
    monkeypatch.setattr(
        main_module,
        "initialize_image_processor",
        AsyncMock(),
    )

    mock_database = SimpleNamespace(
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )

    async def override_database_dependency():
        yield mock_database

    async def mock_create(db, payload):
        return SimpleNamespace(
            image_id=1,
            ticket_id=payload.ticket_id,
            file_url=payload.file_url,
            minio_object_name=payload.minio_object_name,
            blur_variance=payload.blur_variance,
            is_blurry=payload.is_blurry,
            cnn_features=payload.cnn_features,
            processing_status=payload.processing_status,
            uploaded_at=datetime.now(timezone.utc),
        )

    monkeypatch.setattr(
        ticket_images_api.minio_client,
        "upload_ticket_image",
        AsyncMock(
            return_value=(
                "tickets/1/test.png",
                "https://example.test/test.png",
            )
        ),
    )
    monkeypatch.setattr(ticket_images_api, "create", mock_create)

    app.dependency_overrides[get_db] = override_database_dependency

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_image_upload_endpoint(client, clear_image_bytes):
    response = client.post(
        "/ticket-image",
        data={"ticket_id": "1"},
        files={
            "file": (
                "clear.png",
                clear_image_bytes,
                "image/png",
            )
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["ticket_id"] == 1
    assert body["processing_status"] == "COMPLETED"
    assert isinstance(body["blur_variance"], float)
    assert body["is_blurry"] is False
    assert len(body["cnn_features"]) == 2048