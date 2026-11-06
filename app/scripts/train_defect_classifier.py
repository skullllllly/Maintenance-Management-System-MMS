import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd 
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss
)

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder ,StandardScaler
from xgboost import XGBClassifier

DEFAULT_FEATURE_DIMENSION =2048
MODEL_ARTIFACT_PATH= Path("models/xgboost_defect_classifier.joblib")


def parse_arguments() ->argparse.Namespace:
    parser= argparse.ArgumentParser(
        description= "Train an XGBoost defect classifier"
    )
    parser.add_argument(
        "--training-data",
        default="training_data.csv"  
    )
        parser.add_argument(
        "--output",
        default=str(MODEL_ARTIFACT_PATH),
    )
    parser.add_argument("--random-state",type=int,default=42)
    parser.add_argument("--test-size",type=float,default=0.2)
    return parser.parse_args()

def load_training_data(path:str ,feature_dimension:int)->tuple[np.ndarray,np.ndarray,np.ndarray]:

    data=pd.read_csv(path)

    required_columns={"image_id","label","cnn_features"}
    missing_columns=required_columns - set(data.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)} "
        )

    if data.empty:
        raise ValueError ("Training dataset is empty ")

    feature_vectors: list[list[float]] = []
    labels:list[str]= []
    image_ids:list[int]= []

    for row in data.itertuples(index=False):
        try:
            vector= json.loads(row.cnn_features)
            label= str(row.label).strip()
        except(json.JSONDecodeError,AttributeError) as exc :
            raise ValueError (
                f"Invalid training row for image {row.image_id}"
            )from exc
        
        if not isinstance(vector,list):
            raise ValueError(f"feature must be an array: image {row.image_id}")

        if len(vector) != feature_dimension:
            raise ValueError(
                f"Expected {feature_dimension} feature ,received "
                f"{len(vector)} for image {row.image_id}"
            )

        numeric_vector=np.asarray(vector,dtype=np.float64)

        if numeric_vector.shape != (feature_dimension,):
            raise ValueError(
                f"Invalid feature shape: image {row.image_id}"
            )

        if not np.isfinite(numeric_vector).all():
            raise ValueError(
                f"Non-finite feature found for image {row.image_id} "
            )
        
        if not label:
            raise ValueError (
                f"Empty label for image {row.image_id}"
            )

        feature_vectors.append(numeric_vector.tolist())
        labels.append(label)
        image_ids.append(int(row.image_id))

    return(
        np.asarray(feature_vectors,dtype=np.float64),
        np.asarray(labels,dtype=object)
        np.asarray(image_ids,dtype=np.int64)
    )

def calculate_training_hash(
    features:np.ndarray,
    labels:np.ndarray,
    image_ids:np.ndarray
)->str:

    digest=hashlib.sha256()
    digest.update(str(features.shape).encode("ascii"))
    digest.update(str(labels.shape).encode("ascii"))
    digest.update(image_ids.tobytes())
    digest.update(labels.astype(str).tobytes())
    digest.update(features.astype("<f8").tobytes())
    return digest.hexdigest()

def main() ->None:
    args=parse_arguments()

    features,labels,image_ids =load_training_data(
        args.training_data,
        DEFAULT_FEATURE_DIMENSION,
    )

    if len(np.unique(labels)) < 2:
        raise ValueError("At least two classes are required")
    
    minimum_class_count=int(pd.Series(labels).value_counts().min())
    if minimum_class_count < 2:
        raise ValueError(
            "Every class must contain at least two samples."
        )
    
    label_encoder=LabelEncoder()
    encoded_labels= label_encoder.fit_transform(labels)

    train_indices, test_indices= train_test_split(
        np.arange(len(features)),
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=encoded_labels
    )

    x_train=features[train_indices]
    x_test=features[test_indices]

    y_train=encoded_labels[train_indices]
    y_test=encoded_labels[test_indices]

    scaler=StandardScaler()
    x_train_scaled=scaler.fit_transform(x_train)
    x_test_scaled=scaler.fit_transform(x_test)

    class_counts=np.bincount(y_train,min_length=len(label_encoder.classes_))
    maximum_class_count=int(class_counts.max())
    class_weights= maximum_class_count / np.maximum(class_counts, 1)
    sample_weights=np.asarray(
        [class_weights[label] for label in y_train], dtype=np.float64
    )

    classifier=XGBClassifier(
        objective="multi:softprob",
        num_class=len(label_encoder.classes_),
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        min_child_weight=1.0,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.0,
        reg_lambda=1.0,
        gamma=0.0,
        eval_metric="mlogloss",
        random_state=args.random_state,
        n_jobs=max(1 , __import__("os").cpu_count() or 1 ),
    )

    classifier.fit(
        x_train_scaled,
        y_train,
        sample_weight=sample_weights
    )

    predicted_classes=classifier.predict(x_test_scaled)
    probabilities = classifier.predict_proba(x_test_scaled)

    print(" \n Accuracy:", accuracy_score(y_test,predicted_classes))
    print(
        "Balanced accuracy:",
        balanced_accuracy_score(y_test,predicted_classes)
    )

    print(
        "Marco F1:",
        f1_score(y_test,predicted_classes, average="marco"),
    )

    print("Weighted F1:"
        f1_score(y_test,predicted_classes,average="weighted"),    
    )

    print("Log_loss:",log_loss(y_test,probabilities))

    print(" \n Classifiacation report:")
    print(
        classification_report(
            y_test,
            predicted_classes,
            target_names=label_encoder.classes_,
            zero_division=0
        )
    )

    print("Confusion matrix:")
    print(confusion_matrix(y_test,predicted_classes))

    output_path=Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    artifact={
        "format_version":1,
        "model":classifier,
        "scaler":scaler,
        "label_encoder":label_encoder,
        "feature_dimension":DEFAULT_FEATURE_DIMENSION,
        "classes": label_encoder.classes_.tolist(),
        "training_hash":calculate_training_hash(
            features,
            labels,
            image_ids
        ),
        "training_rows":len(features,)
        "train_rows":len(train_indices),
        "test_rows":len(test_indices),
        "random_state":args.random_state,
        "model_family":"xgboost",
        "model_version":"xgboost-defect-v1"
    }

    joblib.dump(artifact,output_path,compress=3)
    print(f"\n saved modle artifact: { output_path}")

if __name__== "__main__":
    main()
