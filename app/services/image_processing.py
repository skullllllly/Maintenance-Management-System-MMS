import asyncio
import io
import threading
from dataclasses import dataclass

import cv2
import numpy as np
import torch
from torch import Tensor
from torchvision import models
from torchvision.models import ResNet50_Weights

from app.core.config import settings

@dataclass(frozen=True,slots=True)
class ProcessedImage:
    image:bytes
    blur_variance:float
    is_blurry:bool
    cnn_features: list[float]

class ImageProcessingError(ValueError):
    pass

class CNNFeatureExtractor:
    def __init__(self)->None:
        self._model:torch.nn.Module |None=None
        self._lock=threading.Lock()

    def initialize(self)->None:
        with self._lock:
            if self._model is not None:
                return
            
            device=torch.device(settings.CNN_MODEL_DEVICE)
            model=models.resnet50(weights=None)

            checkpoint=torch.load(
                settings.CNN_MODEL_PATH,
                map_location=device,
                weights_only=True,
            )

            state_dict= checkpoint.get("state_dict",checkpoint)
            state_dict={
                key.removeprefix("module."): value
                for key,value in state_dict.items()
                if not key.endswith("fc.weight") and not key.endswith("fc.bias")
            }

            model.load_state_dict(state_dict, strict=False)
            model.fc=torch.nn.Identity()
            model.eval()

            self._model=model.to(device)

    def extract(self , pixels:np.ndarray)-> list[float]:
        if self._model is None:
            raise RuntimeError("CNN model is not initialized")
        
        image=cv2.resize(pixels,(224,224), interpolation=cv2.INTER_AREA)
        image=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        image=image.astype(np.float32)/255.0

        mean=np.array([0.485,0.456,0.406], dtype=np.float32)
        std=np.array([0.229,0.224,0.225], dtype=np.float32)

        image=(image-mean) / std

        tensor:Tensor= torch.from_numpy(
            np.ascontiguousarray(image.transpose(2,0,1))

        ).unsqueeze(0)
        tensor=tensor.to(
            torch.device(settings.CNN_MODEL_DEVICE),
            non_blocking=False,
        )

        with self._lock:
            with torch.inference_mode():
                result=self._model(tensor)
                result=torch.nn.functional.normalize(result, dim=1)
                result=result.cpu().squeeze(0)

            return result.tolist()


cnn_feature_extractor=CNNFeatureExtractor()

def _decode_and_measure(image_bytes:bytes) ->tuple[np.ndarray,float]:
    if not image_bytes:
        raise ImageProcessingError("Uploaded image is empty.")

    encoded=np.frombuffer(image_bytes, dtype=np.uint8)
    if encoded.size == 0:
        raise ImageProcessingError("The uploaded file is not a valid image.")

    try:
        pixels=cv2.imdecode(encoded,cv2.IMREAD_COLOR)
    except cv2.error as exc:
        raise ImageProcessingError("The uploaded file is not a valid image.") from exc

    if pixels is None:
        raise ImageProcessingError("The uploaded file is not a vaild image.")

    height,width=pixels.shape[:2]
    if height < 32 or width < 32 :
        raise ImageProcessingError("Image dimensions must be at least 32x32.")
    
    grayscale=cv2.cvtColor(pixels,cv2.COLOR_BGR2GRAY)
    variance=float(cv2.Laplacian(grayscale,cv2.CV_64F).var())

    if not np.isfinite(variance):
        raise ImageProcessingError("Unable to calculate image sharpness")

    return pixels,variance

def _analyze(image_bytes:bytes) ->ProcessedImage:
    pixels,blur_variance=_decode_and_measure(image_bytes)
    features=cnn_feature_extractor.extract(pixels)

    return ProcessedImage(
        image=image_bytes,
        blur_variance=blur_variance,
        is_blurry=blur_variance < settings.IMAGE_BLUR_THRESHOLD,
        cnn_features=features,
    )

async def read_limited_upload(upload)-> bytes:
    chunks:list[bytes]=[]
    total_bytes=0

    while chunk:= await upload.read(1024 * 1024):
        total_bytes +=len(chunk)
        if total_bytes > settings.IMAGE_MAX_BYTES:
            raise ImageProcessingError(
                f"Image exceeds the {settings.IMAGE_MAX_BYTES} byte limit."
            )
        chunks.append(chunk)

    await upload.seek(0)

    if not chunks:
        raise ImageProcessingError("Uploaded image is empty")

    return b"".join(chunks)

async def analyze_image(image_bytes:bytes)-> ProcessedImage:
    return await asyncio.to_thread(_analyze,image_bytes)

async def initialize_image_processor() ->None:
    await asyncio.to_thread(cnn_feature_extractor.initialize)