# ML validation checklist (before any real-world use)
- [ ] Replace synthetic data with real datasets (licence, provenance, units verified).
- [ ] Crop: validate on Punjab-region records; report per-class metrics; check class balance.
- [ ] Yield: use real district/farm yield records; calibrate prediction intervals (current range is uncalibrated ensemble spread).
- [ ] Disease: split by plant/field/source; include real field photos in validation/test; set the uncertainty threshold from calibration data; add an out-of-distribution/“not a leaf” check.
- [ ] Fertilizer: have an agronomist approve thresholds in `ml/fertilizer.py` and the ruleset version.
- [ ] User study with farmers (SRS RQ5) before claiming usability.
