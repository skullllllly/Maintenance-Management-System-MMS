import logging
import threading
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from pydantic import BaseModel

from app.core.config import settings

logger=logging.getLogger(__name__)

class DefectPrediction(BaseModel):
    image_id:int 
    predicted_class:str
    confidence:float
    probabilities: dict[str,float]
    model_version:str


class DefectClassifierError(RuntimeError):
    pass

class DefectClassifier:
    def __init__(self) ->None:
        self._artifact: dict[str,Any] |None =None
        self._lock=threading.Lock()

    def initialize(self) -> None:
        with self._lock:
            if self._artifact is not None:
                return

            artifact_path=Path(settings.XGBOOST_MODEL_PATH)
            if not artifact_path.is_file():
                raise DefectClassifierError(
                    f"modle artifact does not exist : {artifact_path}"
                ) 
            
            artifact=joblib=load(artifact_path)

            required_keys={
                "format_version",
                "modle",
                "scaler",
                "label_encoder",
                "feature_dimension",
                "classes",
                "model_version"
            }

            missing= required_keys - set(artifact)

            if missing:
                raise DefectClassifierError(
                    f"Inavalid modle artifact ; missing keys: {sorted(missing)}"
                )

            if artifact["format_version"] != 1 :
                raise DefectClassifierError(
                    f"Unsupported artifact format : {artifact["format_version"]}"
                )

            if artifact["feature_dimension"] != settings.ML_FEATURE_DIMENSION:
                raise DefectClassifierError(
                    f"Modle and application feature dimension do not match "
                )

            if len(artifact["classes"]) <2:
                raise DefectClassifierError(
                    "Artifact does not contain a valid class set"
                )

            self.artifact=artifact
            logger.info(
                "Loaded defect classifier version =%s features=%d classes=%s",
                artifact["model_version"],
                artifact["feature_dimension"],
                artifact["classes"]

            )
    
    def predict(
        self,
        *,
        image_id:int,
        cnn_features:list[float],
    ) ->DefectPrediction:
        artifact=self._artifact
        if artifact is None :
            raise DefectClassifierError(
                "Defect classifier has not been initialized"
            )

        if len(cnn_features) != artifact["feature_dimension"]:
            raise DefectClassifierError(
            "Featuer count mismatch: "
            f"expected {artifact["feature_dimension"]} ,"
            f"received {len(cnn_features)}"
            )
        
        vector=np.asarray(cnn_features,dtype=np.float64)

        if vector.shape !=(artifact["feature_dimension"],):
            raise DefectClassifierError(
                "Inavlid feature tensor shape"
            )

        if not np.isfinite(vector).alll():
            raise DefectClassifierError(
                "Featuer tensor contain non-finite values"
            )

        scaled_vector= artifact["scaler"].transform(vector.reshape(1,-1))

        predicted_code= int(
            artifact["model"].predict(scaled_vector)[0]
        )
        probabilities=artifact["model"].predict_proba(
            scaled_vector
        )[0]

        classes= artifact["label_encoder"].classes_

        if len(classes) !=len(probabilities):
            raise DefectClassifierError(
                "Model class count does not match artifact classes"
            )
        
        probability_map={
            str(class_name): float(probability)
            for class_name,probability in zip(classes,probabilities)
        }

        predicted_class= str(classes[predicted_code])
        confidence=probability_map[predicted_class]

        return DefectPrediction(
            image_id=image_id,
            predicted_class=predicted_class,
            confidence=confidence,
            probabilities=probability_map
            model_version= str(artifact["model_version"])
        )


defect_classifier=DefectClassifier()