
"""Plant disease inference using an optional PyTorch model.

Low-confidence predictions return an explicit uncertain result.
Missing or invalid model artifacts produce ModelUnavailable.
"""

import io
import json
import logging
import threading

from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings
from app.ml.registry import ModelUnavailable, registry

log = logging.getLogger(__name__)

_lock = threading.Lock()
_state: dict = {}


def _load():
    with _lock:
        settings = get_settings()
        directory = settings.ML_ARTIFACT_DIR / "disease_detection"

        weights = directory / "model.pt"
        classes_path = directory / "classes.json"
        metadata_path = directory / "metadata.json"

        paths = (weights, classes_path, metadata_path)

        if not all(path.is_file() for path in paths):
            raise ModelUnavailable(
                "Disease model artifacts are incomplete. "
                "Train and deploy the disease detection model."
            )

        try:
            signature = tuple(
                (path.stat().st_mtime_ns, path.stat().st_size)
                for path in paths
            )
        except OSError as exc:
            raise ModelUnavailable(
                "Cannot inspect disease model artifacts."
            ) from exc

        if _state.get("signature") == signature:
            return _state

        try:
            import torch
            import torchvision.transforms as T

            meta = registry.metadata("disease_detection")

            classes = json.loads(
                classes_path.read_text(encoding="utf-8")
            )

            if (
                not isinstance(classes, list)
                or not classes
                or not all(
                    isinstance(label, str) and label.strip()
                    for label in classes
                )
                or len(classes) != len(set(classes))
            ):
                raise ValueError("Invalid disease class definitions.")

            version = meta.get("version")
            if not isinstance(version, str) or not version:
                raise ValueError("Invalid disease model version.")

            size = meta.get("image_size", 224)

            if (
                not isinstance(size, int)
                or isinstance(size, bool)
                or not 64 <= size <= 1024
            ):
                raise ValueError("Invalid model image size.")

            model = torch.jit.load(
                str(weights),
                map_location="cpu",
            ).eval()

            transform = T.Compose([
                T.Resize((size, size)),
                T.ToTensor(),
                T.Normalize(
                    [0.485, 0.456, 0.406],
                    [0.229, 0.224, 0.225],
                ),
            ])

            # Validate output shape before accepting the artifact.
            with torch.inference_mode():
                sample = torch.zeros(1, 3, size, size)
                output = model(sample)

            if (
                not isinstance(output, torch.Tensor)
                or output.ndim != 2
                or output.shape[0] != 1
                or output.shape[1] != len(classes)
            ):
                raise ValueError(
                    "Model output dimensions do not match disease classes."
                )

            if not torch.isfinite(output).all():
                raise ValueError("Model produced invalid test output.")

            _state.clear()
            _state.update(
                torch=torch,
                model=model,
                tfm=transform,
                classes=classes,
                meta=meta,
                signature=signature,
            )

            return _state

        except ModelUnavailable:
            raise
        except ImportError as exc:
            raise ModelUnavailable(
                "PyTorch dependencies are unavailable. "
                "See requirements-dl.txt."
            ) from exc
        except Exception as exc:
            log.exception("Failed loading disease detection model")
            raise ModelUnavailable(
                "Disease detection model could not be loaded."
            ) from exc


def reset():
    """Clear cached disease model."""
    with _lock:
        _state.clear()


def validate_image(raw: bytes) -> Image.Image:
    """Validate actual image bytes instead of trusting file metadata."""
    try:
        if not raw:
            raise ValueError("empty image")

        with Image.open(io.BytesIO(raw)) as img:
            img.verify()

        with Image.open(io.BytesIO(raw)) as img:
            if img.format not in ("JPEG", "PNG", "WEBP"):
                raise ValueError("unsupported image format")

            if img.width * img.height > get_settings().MAX_IMAGE_PIXELS:
                raise ValueError("image exceeds maximum pixel limit")

            if min(img.size) < 64:
                raise ValueError("image too small")

            return img.convert("RGB")

    except (
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        ValueError,
        OSError,
    ) as exc:
        raise ValueError(f"Invalid image: {exc}") from exc


def predict_disease(img: Image.Image) -> dict:
    state = _load()
    torch = state["torch"]

    try:
        tensor = state["tfm"](img).unsqueeze(0)

        with torch.inference_mode():
            logits = state["model"](tensor)

            if (
                not isinstance(logits, torch.Tensor)
                or logits.ndim != 2
                or logits.shape[0] != 1
                or logits.shape[1] != len(state["classes"])
            ):
                raise ValueError("Invalid disease model output.")

            if not torch.isfinite(logits).all():
                raise ValueError("Disease model returned invalid values.")

            probabilities = torch.softmax(logits, dim=1)[0]

            if not torch.isfinite(probabilities).all():
                raise ValueError("Invalid prediction probabilities.")

            top = torch.topk(
                probabilities,
                k=min(3, len(state["classes"])),
            )

        alternatives = [
            {
                "label": state["classes"][int(index)],
                "probability": round(float(probability), 4),
            }
            for probability, index in zip(
                top.values,
                top.indices,
                strict=True,
            )
        ]

    except Exception as exc:
        log.exception("Disease inference failed")
        raise ModelUnavailable(
            "Disease detection model could not process this image."
        ) from exc

    confidence = alternatives[0]["probability"]
    uncertain = (
        confidence < get_settings().DISEASE_CONFIDENCE_THRESHOLD
    )

    return {
        "predicted_class": (
            "uncertain" if uncertain else alternatives[0]["label"]
        ),
        "top_label": alternatives[0]["label"],
        "confidence": confidence,
        "is_uncertain": uncertain,
        "alternatives": alternatives,
        "model_version": state["meta"]["version"],
        "data_source": state["meta"].get("data_source", "unknown"),
        "message": (
            "The model is not confident. Retake the photo "
            "(single leaf, good light, in focus) or consult an advisor."
            if uncertain
            else "Possible match only. This is a model prediction, "
            "not a confirmed diagnosis."
        ),
        "limitations": [
            "Trained on a limited set of crops and diseases; "
            "unsupported plants/diseases may be misclassified.",
            "Field photos can differ strongly from training images; "
            "confirm with an agricultural advisor.",
        ],
    }
