# Generated outputs (v4)

Run `python run_study.py` then `python verify_manifest.py`. Tables and figures use the literal dB/km convention unless explicitly marked legacy or comparison. Radius and diameter are distinguished in CSV headers. Empty cells indicate no solution in the declared interval, not zero diameter. The weather and optical inputs are hypothetical.

| Figure | Description |
|---|---|
| 01 | Gaussian aperture integral vs independent Bessel integration |
| 02 | Atmospheric coefficient conventions |
| 03 | Nominal and robust availability curves |
| 04 | Jitter/aperture frontier |
| 05 | TV sensitivity vs independent LP |
| 06 | Feasibility map (aligned pcolormesh grid) |
| 07 | Weather and pointing ablation, including no-extinction/no-jitter reference |
| 08 | MC vs analytic nominal availability |
| 09 | Legacy exponential branch ceiling (not the default) |
| 10 | Both coefficient conventions and their aperture solutions |
| 11 | Atmospheric-profile and target sensitivity |
| 12 | Published fog coefficient model comparison, not field validation |

Tables 01–08 retain the original names, with updated conventions and columns where necessary. Table 09 compares four atmospheric profiles, five targets and three TV radii (60 rows). Table 10 compares fog specific attenuation. Table 11 contains independent-sampling checks in four geometry/profile cases and three seeds. The metadata contains configuration, runtime, environment and checksums. See [technical note](../docs/TECHNICAL_NOTE.md) for meaning and limitations.
