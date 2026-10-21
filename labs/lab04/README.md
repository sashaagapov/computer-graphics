# Lab 04 — Brightness and Tone

This [Tkinter app](main.py) adds brightness analysis and tonal transformations to the operations from Labs 01–03. The [processing functions](operations.py), [tests](tests/test_operations.py), and [report](report_lab04.docx) are included.

![Original tiger photo beside grayscale, binary, and negative results](../../assets/lab04-preview.png)

The tracked preview uses the [tiger input](../../assets/input/tigr-1024x754.jpg) at 320 × 236 pixels. Grayscale, threshold-128 binarization, and negative were produced by the functions in `operations.py`; the image does not show the GUI.

| Feature | Result |
| --- | --- |
| Brightness matrix | One integer brightness value per pixel, using `Y = 0.299R + 0.587G + 0.114B`. |
| Brightness histograms | Counts pixels at each brightness value; the GUI can also show a grayscale histogram. |
| Grayscale | Saves a monochrome PNG. |
| Binarization | Saves a black-and-white PNG using the selected threshold. |
| Negative | Saves an inverted-color PNG. |

The GUI also retains the earlier labs' operations. Its matrix and histograms appear in windows; saved images go to the selected output folder. For steps to capture GUI screenshots for the report, see [SCREENSHOTS.md](SCREENSHOTS.md).

From the repository root, [install the dependencies](../../README.md#run-and-test), then:

```bash
cd labs/lab04
python main.py
python -m pytest
```
