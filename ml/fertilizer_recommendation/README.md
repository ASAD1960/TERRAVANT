# Fertilizer recommendation

Rule-based by design. Rules and thresholds live in `backend/app/ml/fertilizer.py` (`RULESET_VERSION`).
Thresholds are generic placeholders and **must be validated with Punjab agronomy guidance / soil lab
experts** before production use. The module never emits dosage figures. A learned component can be added
later only once validated, paired measurements (soil test → agronomist-approved plan) are available.
