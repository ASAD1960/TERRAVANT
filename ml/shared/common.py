import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import sklearn

ARTIFACT_ROOT = Path(__file__).resolve().parents[1] / "artifacts"


def save_sklearn_artifact(name: str, model, metadata: dict, out_root: Path | None = None) -> Path:
    d = (out_root or ARTIFACT_ROOT) / name
    d.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, d / "model.joblib", compress=3)
    metadata = {
        **metadata,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "sklearn_version": sklearn.__version__,
        "python_version": platform.python_version(),
    }
    (d / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return d
