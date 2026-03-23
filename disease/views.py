# disease/views.py

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Tuple, Optional
import random

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DiseaseImage
from .serializers import DiseaseImageSerializer
from .treatment_kb import get_treatment


# -----------------------------
# Config
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "plant_disease_model.h5"
CLASSES_PATH = BASE_DIR / "model" / "classes.txt"

IMAGE_SIZE = (224, 224)          # must match your model input
TOP_K = 3
CONFIDENCE_THRESHOLD = 0.60      # below this -> Unknown (safe)


# -----------------------------
# Lazy caches (avoid reloading)
# -----------------------------
_MODEL = None
_CLASSES: Optional[List[str]] = None


def load_classes() -> List[str]:
    """
    Loads class labels from disease/model/classes.txt
    Each line should be a label exactly matching your training classes.
    """
    global _CLASSES
    if _CLASSES is not None:
        return _CLASSES

    if CLASSES_PATH.exists():
        labels = []
        for line in CLASSES_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                labels.append(line)
        _CLASSES = labels
        return _CLASSES

    # Fallback demo labels (you can edit)
    _CLASSES = [
        "Tomato___Early_blight",
        "Tomato___Bacterial_spot",
        "Tomato___healthy",
        "Potato___Late_blight",
        "Corn___Common_rust",
    ]
    return _CLASSES


def load_model():
    """
    Loads TensorFlow model if available.
    If anything fails (TF not installed, incompatible, etc.), returns None.
    """
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    if not MODEL_PATH.exists():
        _MODEL = None
        return None

    try:
        import tensorflow as tf
        _MODEL = tf.keras.models.load_model(MODEL_PATH)
        return _MODEL
    except Exception:
        _MODEL = None
        return None


def _mock_topk() -> List[Dict]:
    """
    Offline-safe fallback predictions (for demo).
    """
    options = [
        ("Tomato___Early_blight", 0.87),
        ("Tomato___Bacterial_spot", 0.81),
        ("Tomato___healthy", 0.95),
        ("Potato___Late_blight", 0.78),
        ("Corn___Common_rust", 0.76),
    ]
    # choose top-3 random unique
    picks = random.sample(options, k=min(TOP_K, len(options)))
    # sort desc by confidence
    picks.sort(key=lambda x: x[1], reverse=True)
    return [{"label": a, "confidence": round(float(b), 4)} for a, b in picks]


def preprocess_image(file_path: str):
    """
    Returns numpy array (1, H, W, 3) normalized [0,1] if PIL+numpy available.
    """
    from PIL import Image  # requires Pillow working
    import numpy as np

    img = Image.open(file_path).convert("RGB")
    img = img.resize(IMAGE_SIZE)
    arr = (np.array(img) / 255.0).astype("float32")
    arr = np.expand_dims(arr, axis=0)
    return arr


def predict_topk(file_path: str) -> Tuple[List[Dict], bool]:
    """
    Returns (topk_list, used_real_model)
    topk_list = [{"label": str, "confidence": float}, ...]
    """
    model = load_model()
    classes = load_classes()

    # If no real model -> mock
    if model is None:
        return _mock_topk(), False

    # Try real inference; if any error -> mock
    try:
        import numpy as np

        x = preprocess_image(file_path)
        preds = model.predict(x)

        # preds can be (1, n)
        probs = preds[0]
        # get top-k indices
        top_idx = np.argsort(probs)[::-1][:TOP_K]

        topk = []
        for i in top_idx:
            label = classes[int(i)] if int(i) < len(classes) else f"Class_{int(i)}"
            conf = float(probs[int(i)])
            topk.append({"label": label, "confidence": round(conf, 4)})

        return topk, True

    except Exception:
        return _mock_topk(), False


def choose_final_label(topk: List[Dict]) -> Tuple[str, float]:
    """
    Applies confidence threshold.
    Returns (label, confidence)
    """
    if not topk:
        return "Unknown", 0.0

    best = topk[0]
    label = best.get("label", "Unknown")
    conf = float(best.get("confidence", 0.0))

    if conf < CONFIDENCE_THRESHOLD:
        return "Unknown", conf

    return label, conf


class DiseaseImageViewSet(viewsets.ModelViewSet):
    queryset = DiseaseImage.objects.all().order_by("-created_at")
    serializer_class = DiseaseImageSerializer

    @action(detail=False, methods=["post"], url_path="predict")
    def predict(self, request):
        """
        POST /api/disease-images/predict/
        multipart/form-data:
          - farm_id (or farm)
          - image (file)

        Response includes:
          - saved record (id, image url/path, predicted_label, confidence)
          - top_k predictions
          - treatment for predicted_label
          - used_real_model flag
        """
        farm_id = request.data.get("farm_id") or request.data.get("farm")
        image_file = request.FILES.get("image")

        if not farm_id or not image_file:
            return Response(
                {"error": "farm_id (or farm) and image are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save image first
        record = DiseaseImage.objects.create(farm_id=farm_id, image=image_file)

        # Predict
        topk, used_real_model = predict_topk(record.image.path)
        label, conf = choose_final_label(topk)

        record.predicted_label = label
        record.confidence = round(float(conf), 4)
        record.save()

        # Treatment for final label
        treatment = get_treatment(label)

        data = DiseaseImageSerializer(record).data
        data.update(
            {
                "used_real_model": used_real_model,
                "top_k": topk,
                "treatment": treatment,
                "note": (
                    "Low confidence → label set to Unknown (no risky chemical advice)."
                    if label == "Unknown"
                    else ""
                ),
            }
        )

        return Response(data, status=status.HTTP_201_CREATED)