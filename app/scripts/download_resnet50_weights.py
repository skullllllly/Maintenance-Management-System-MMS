from pathlib import Path

import torch
from torchvision.models import ResNet50_Weights, resnet50


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIRECTORY = PROJECT_ROOT / "models"
WEIGHTS_PATH = MODELS_DIRECTORY / "resnet50_ticket_image.pt"


def download_and_save_weights() -> Path:
    MODELS_DIRECTORY.mkdir(parents=True, exist_ok=True)

    if WEIGHTS_PATH.is_file() and WEIGHTS_PATH.stat().st_size > 0:
        print(f"Model weights already exist: {WEIGHTS_PATH}")
        return WEIGHTS_PATH

    print("Downloading pre-trained ResNet50 weights...")
    weights = ResNet50_Weights.DEFAULT
    model = resnet50(weights=weights)

    # Store the application-compatible state dictionary.
    temporary_path = WEIGHTS_PATH.with_suffix(".pt.tmp")

    torch.save(
        {
            "state_dict": model.state_dict(),
            "architecture": "resnet50",
            "weights": weights.meta,
        },
        temporary_path,
    )

    temporary_path.replace(WEIGHTS_PATH)
    print(f"Model weights saved to: {WEIGHTS_PATH}")
    return WEIGHTS_PATH


if __name__ == "__main__":
    download_and_save_weights()