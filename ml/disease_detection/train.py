"""Fine-tune a MobileNetV3 for plant disease classification (transfer learning).

Requires: pip install -r backend/requirements-dl.txt

Dataset layout (ImageFolder), ALREADY split to avoid leakage:
  data/train/<class>/*.jpg   data/val/<class>/*.jpg   data/test/<class>/*.jpg

Split by plant / field / source BEFORE this step (PlantVillage has near-duplicate
images of the same leaf — a random image-level split inflates accuracy).
Include real field-condition photos in val/test (e.g. PlantDoc), not only lab images.

  python -m disease_detection.train --data ./data --epochs 12
Exports a TorchScript model + classes.json + metadata.json to ml/artifacts/disease_detection.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from shared.common import ARTIFACT_ROOT


def main():
    import torch
    import torch.nn as nn
    from sklearn.metrics import classification_report
    from torch.utils.data import DataLoader
    from torchvision import datasets, models, transforms as T

    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--size", type=int, default=224)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--version", default="0.1.0")
    a = ap.parse_args()

    norm = T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    train_tf = T.Compose([T.RandomResizedCrop(a.size, scale=(0.7, 1.0)), T.RandomHorizontalFlip(), T.RandomRotation(20),
                          T.ColorJitter(0.2, 0.2), T.ToTensor(), norm])  # mild: must preserve disease appearance
    eval_tf = T.Compose([T.Resize((a.size, a.size)), T.ToTensor(), norm])
    root = Path(a.data)
    tr, va, te = (datasets.ImageFolder(root / s, t) for s, t in (("train", train_tf), ("val", eval_tf), ("test", eval_tf)))
    assert tr.classes == va.classes == te.classes, "class folders differ between splits"
    dl = lambda ds, sh: DataLoader(ds, batch_size=a.batch, shuffle=sh, num_workers=2)
    dtr, dva, dte = dl(tr, True), dl(va, False), dl(te, False)

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    net = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
    net.classifier[-1] = nn.Linear(net.classifier[-1].in_features, len(tr.classes))
    net.to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, a.epochs)
    loss_fn = nn.CrossEntropyLoss(label_smoothing=0.05)

    def evaluate(loader):
        net.eval()
        ys, ps = [], []
        with torch.no_grad():
            for x, y in loader:
                ps += net(x.to(dev)).argmax(1).cpu().tolist()
                ys += y.tolist()
        return ys, ps

    best, best_state = 0.0, None
    for ep in range(a.epochs):
        net.train()
        for x, y in dtr:
            opt.zero_grad()
            loss_fn(net(x.to(dev)), y.to(dev)).backward()
            opt.step()
        sched.step()
        ys, ps = evaluate(dva)
        acc = sum(int(i == j) for i, j in zip(ys, ps)) / max(len(ys), 1)
        print(f"epoch {ep + 1}/{a.epochs} val_acc={acc:.4f}")
        if acc > best:
            best, best_state = acc, {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}

    net.load_state_dict(best_state)
    ys, ps = evaluate(dte)  # test set used once
    report = classification_report(ys, ps, target_names=tr.classes, output_dict=True, zero_division=0)
    print(classification_report(ys, ps, target_names=tr.classes, zero_division=0))

    out = ARTIFACT_ROOT / "disease_detection"
    out.mkdir(parents=True, exist_ok=True)
    net.eval().cpu()
    torch.jit.trace(net, torch.randn(1, 3, a.size, a.size)).save(str(out / "model.pt"))
    (out / "classes.json").write_text(json.dumps(tr.classes))
    (out / "metadata.json").write_text(json.dumps({
        "version": a.version, "model_type": "MobileNetV3-Small (TorchScript)", "image_size": a.size,
        "data_source": f"imagefolder:{root}", "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {"val_accuracy": best, "test_accuracy": report["accuracy"], "macro_f1": report["macro avg"]["f1-score"],
                    "n_classes": len(tr.classes)},
        "field_condition_validated": False,
    }, indent=2))


if __name__ == "__main__":
    main()
