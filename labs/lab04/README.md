# Computer Graphics — Laboratory 4

Image-processing laboratory covering brightness analysis, histograms, grayscale, binarization, and negative images.

From the repository root, install the shared dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the lab from its directory:

```bash
cd labs/lab04
python main.py
python -m pytest
```

On Windows PowerShell, activate the virtual environment with `.venv\Scripts\Activate.ps1` before running these commands.

## Реалізовано

- Transparency with alpha values saved as PNG.
- Rectangular cropping and area removal.
- Splitting an image into a requested number of parts.
- Contrast adjustment using the laboratory formula.
- Reuse of the laboratory 1 conversion, resize, color replacement, and color-balance operations.
- Merging two images horizontally or vertically on a white canvas.
- Adding a text watermark with position, RGB color, font size, and alpha value.
- A Tkinter slideshow with Start/Stop controls and a non-blocking `after()` timer.
- Brightness matrix and brightness histogram based on `Y = 0.299R + 0.587G + 0.114B`.
- Grayscale conversion, binarization with threshold, and negative image.

## Основні функції

- `set_transparency(image, alpha)`
- `crop_selected_area(image, left, top, right, bottom)`
- `remove_selected_area(image, left, top, right, bottom)`
- `split_image(image, parts)`
- `adjust_contrast(image, factor)`
- `merge_images(image1, image2, direction)`
- `add_text_watermark(image, text, position, alpha, font_size, color)`
- `brightness_value(red, green, blue)`
- `brightness_matrix(image)`
- `brightness_histogram(image)`
- `to_grayscale(image)`
- `binarize(image, threshold)`
- `negative(image)`
