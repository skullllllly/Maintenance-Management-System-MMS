import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import app.api.ticket_images as ticket_images_api
import app.main as main_module
from app.db.session import get_db
from app.main import app
from app.services.image_processing import (
    cnn_feature_extractor,
    initialize_image_processor,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLE_IMAGE = PROJECT_ROOT / "app" / "tests" / "assets" / "sample-image.jpg"


def resolve_sample_image() -> Path:
    configured_path = os.getenv("TEST_SAMPLE_IMAGE")
    path = Path(configured_path).expanduser() if configured_path else DEFAULT_SAMPLE_IMAGE
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


@pytest.fixture(scope="module")
def sample_image_path() -> Path:
    path = resolve_sample_image()
    if not path.is_file():
        pytest.skip(
            f"Real integration image not found: {path}. "
            "Place an image there or set TEST_SAMPLE_IMAGE."
        )
    return path


@pytest.fixture(scope="module")
def real_cnn_model():
    from app.core.config import settings

    model_path = Path(settings.CNN_MODEL_PATH).expanduser().resolve()
    if not model_path.is_file():
        pytest.skip(f"Real ResNet50 checkpoint not found: {model_path}")

    try:
        initialize_image_processor_sync()
    except Exception as exc:
        pytest.skip(f"ResNet50 checkpoint is not usable for integration testing: {exc}")

    assert cnn_feature_extractor._model is not None


def initialize_image_processor_sync() -> None:
    import asyncio

    asyncio.run(initialize_image_processor())


@pytest.fixture(scope="module")
def integration_client(monkeypatch_module, real_cnn_model):
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

    monkeypatch_module.setattr(
        main_module.minio_client,
        "verify_bucket_existence",
        AsyncMock(),
    )
    monkeypatch_module.setattr(
        main_module,
        "initialize_image_processor",
        AsyncMock(),
    )
    monkeypatch_module.setattr(
        ticket_images_api.minio_client,
        "upload_ticket_image",
        AsyncMock(
            return_value=(
                "tickets/1/sample-image.jpg",
                "https://example.test/sample-image.jpg",
            )
        ),
    )
    monkeypatch_module.setattr(ticket_images_api, "create", mock_create)

    app.dependency_overrides[get_db] = override_database_dependency

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def monkeypatch_module():
    from _pytest.monkeypatch import MonkeyPatch

    monkeypatch = MonkeyPatch()
    yield monkeypatch
    monkeypatch.undo()


def test_real_image_upload_runs_opencv_and_resnet50(
    integration_client: TestClient,
    sample_image_path: Path,
):
    content_type = "image/png" if sample_image_path.suffix.lower() == ".png" else "image/jpeg"

    with sample_image_path.open("rb") as image_file:
        response = integration_client.post(
            "/ticket-image",
            data={"ticket_id": "1"},
            files={
                "file": (
                    sample_image_path.name,
                    image_file,
                    content_type,
                )
            },
        )

    assert response.status_code == 200

    body = response.json()
    assert set(body) == {
        "image_id",
        "ticket_id",
        "file_url",
        "minio_object_name",
        "blur_variance",
        "is_blurry",
        "cnn_features",
        "processing_status",
        "uploaded_at",
    }
    assert body["ticket_id"] == 1
    assert isinstance(body["blur_variance"], float)
    assert body["blur_variance"] >= 0.0
    assert isinstance(body["is_blurry"], bool)
    assert body["processing_status"] == "COMPLETED"
    assert isinstance(body["cnn_features"], list)
    assert len(body["cnn_features"]) == 2048
    assert all(isinstance(value, float) for value in body["cnn_features"])
