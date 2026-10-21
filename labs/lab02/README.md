# Lab 02 — Regions and Contrast

This [Tkinter app](main.py) adds region-based image operations to [Lab 01](../lab01/main.py). Its [processing functions](operations.py) and [tests](tests/test_operations.py) are included; see the [report](../../reports/Звіт_ЛР2_КГВ_Агапов.docx).

| Operation | Result |
| --- | --- |
| Transparency | Applies an alpha value and saves a PNG. |
| Crop or remove an area | Keeps or removes a selected rectangle. |
| Split image | Saves the requested number of image parts. |
| Contrast | Adjusts contrast using the lab formula. |

The app also offers Lab 01's format conversion, proportional resize, color replacement, and RGB balance. No processed Lab 02 images are tracked; choose a [sample input](../../assets/input/) and an output folder to create them.

From the repository root, [install the dependencies](../../README.md#run-and-test), then:

```bash
cd labs/lab02
python main.py
python -m pytest
```
