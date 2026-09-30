# Computer Graphics — Laboratory 2

Image-processing laboratory covering transparency, cropping, splitting, contrast, and the operations from laboratory 1.

From the repository root, install the shared dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the lab from its directory:

```bash
cd labs/lab02
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

## Основні функції

- `set_transparency(image, alpha)`
- `crop_selected_area(image, left, top, right, bottom)`
- `remove_selected_area(image, left, top, right, bottom)`
- `split_image(image, parts)`
- `adjust_contrast(image, factor)`
