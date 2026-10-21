# Lab 03 — Merging, Watermarks, and Slideshows

This [Tkinter app](main.py) extends [Lab 02](../lab02/README.md) with three features. Its [processing functions](operations.py), [tests](tests/test_operations.py), and [report](../../reports/Звіт_ЛР3_КГВ_Агапов.docx) are included.

| Feature | Result |
| --- | --- |
| Merge images | Places two images side by side or one above the other on a white canvas. |
| Text watermark | Places text using the selected position, color, font size, and opacity. |
| Slideshow | Shows selected images in a Tkinter window with Start/Stop controls. |

The earlier conversion, resizing, color, transparency, region, splitting, and contrast operations remain available. No processed Lab 03 images are tracked; the GUI creates them from [sample inputs](../../assets/input/) in a folder you select.

From the repository root, [install the dependencies](../../README.md#run-and-test), then:

```bash
cd labs/lab03
python main.py
python -m pytest
```
