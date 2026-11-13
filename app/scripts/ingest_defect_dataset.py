import argparse
import asyncio 
import json
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from sklearn.model_selection import train_test_split
from sqlalchemy import delete

from app.db.session import Base
from app,ml_contract import DEFECT_LABELS,FEATURE_DIMENSION,FEATURE_PIPELINE_VERSION
from app.models.defect_training_sample import DefectTrainingSample
from app.services.image_processing import cnn_feature_extractor
from app.core.config import settings

logger= logging.getLogger(__name__)
IMAGE_EXTENSIONS={".jpg",".png",".jpeg",".webp"}
BATCH_SIZE=250

def parse_arguments() ->argparse.Namespace:

    parser=argparse.ArgumentParser(
        description= "Extract Resnet50 feature and persist a labeled dataset"
    )
    parser.add_argument("--root",type=Path,default=Path("processed_dataset"))
    parser.add_argument(
        "--dataset-version",
        default="processed -dataset-v1"
    )
    parser.add_argument("--test-size",type=float,default=0.2)   
    parser.add_argument("--random-state", type=int,default=42)

    return parser.parse_args()

def find_samples(root:Path) ->list[tuple[Path,str]]:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"Dataset root is not directory:{root}")

    class_directories ={
        path.name
        for path in root.iterdir()
        if path.is_dir()
    }

    expected_labels =set(DEFECT_LABELS)

    if class_directories != expected_labels:
        raise ValueError(
            "Dataset must contain exactly class directories"
            f"Expected={sorted(expected_labels)}",
            f"found ={sorted(class_directories)}"
        )

    samples: list[tuple[Path,str]] =[]
    for label in DEFECT_LABELS:
        class_directory =root / label
        for path in sorted(class_directory.rglob("*")):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                samples.append((path,label))
    
    if not samples:
        raise ValueError(f"No supported images found under {root}")

    return samples


def assign_splits(
    samples:list[tuple[Path,str]],
    *,
    test_size:float,
    random_state:int,
)->list[tuple[Path,str,str]]:
    if not 0.0 < test_size < 1.0 :
        raise ValueError("--test-size must be between 0 and 1")

    labels=np.asarray([label for _,label in samples], dtype=object)
    counts ={
        label:int(np.count_nonzero(labels == label))
        for label in DEFECT_LABELS
    }
    too_small =[label for label,count in counts.items() if count < 2]
    if too_small:
        raise ValueError(
            "Each class neess at least two images for a stratified split."
            f"Insufficient classes : {too_small}"
        )

    indices= np.arange(len(samples))
    train_indices, test_indices= train_test_split(
        indices,
        test_size= test_size,
        random_state=random_state,
        stratify=labels
    )

    splits ={int(index): "train" for index in train_indices}
    splits.update({int(index): " test" for index in test_indices})

    return[
        (path,label,splits[index])
        for index,(path,label) in enumerate(samples)
    ]

def decode_image(path:Path) ->np.ndarray:
    if path.stat().st_size > settings.IMAGE_MAX_BYTES:
        raise ValueError(
            f"Image exceeds IMAGE_MAX_BYTES ({settings.IMAGE_MAX_BYTES}) : {path}"
        )

    encoded=np.frombuffer(path.read_bytes(),dtype=np.uint8)
    try:
        pixels=cv2.imdecode(encoded,cv2.IMREAD_COLOR)
    except cv2.error as exc:
        raise ValueError(f"Could not decode image:{path}") from exc

    if pixels is None:
        raise ValueError(f"Could not decode image:{path}")

    height,width=pixels.shape[:2]
    if height < 32 or width < 32 :
        raise ValueError(f"Image must be at least 32x32 pixels: {path}")
    
    return pixels

def make_image_id(dataset_version:str,relative_path:str) ->uuid.UUID:
    return uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"defect-training:{dataset_version}:{relative_path}",
    )

async def extract_to_jsonl(
    samples:list[tuple[Path,str,str]],
    *,
    root:Path,
    dataset_version:str,
    output_path:Path
) -> int:
    await asyncio.to_thread(cnn_feature_extractor.initialize)

    count = 0
    with output_path.open("w",encoding="utf-8") as output:
        for index, (path,label,split) in enumerate(samples,start=1):
            pixels=decode_image(path)
            features=await asyncio.to_thread(
                cnn_feature_extractor.extract,
                pixels
            )

            vector=np.asarray(feature,dtype=np.float64)
            if vector.shape != (FEATURE_DIMENSION,):
                raise ValueError(
                    f"Expected {FEATURE_DIMENSION} feature for {path};"
                    f"got shape {vector.shape}"
                )

            if not np.isfinite(vector).all():
                raise ValueError(f"Non-finite features extractes for {path}")

            norm=float(np.linalg.norm(vector))
            if not np.isclose(norm, 1.0,atol=1e-4):
                raise ValueError (
                    f"Expected L2-normalized feature for {path}; norm={norm}"
                )

            relative_path=path.relative_to(root).as_posix()
            record: dict[str, Any] ={
                "image_id":str(make_image_id(dataset_version,relative_path)),
                "dataset_version":dataset_version,
                "relative_path":relative_path,
                "label":label,
                "split":split,
                "feature_pipeline_version":FEATURE_PIPELINE_VERSION,
                "cnn_features":vector.tolist(),
            }
            output.write(json.dumps(record, separators=(",",":")) + "\n")
            count+= 1

            if index % 100 == 0:
                logger.info("Extracted  features for %d/%d images", index, len(samples))

    return count 

async def persist_jsonl(
    #here
    )

        

