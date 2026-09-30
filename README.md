# Computer Graphics and Visualization

Python image-processing applications for laboratories 1 and 2 of the Computer Graphics and Visualization course.

The applications use Tkinter for the GUI, Pillow for image processing, and pytest for tests.

## Structure

```text
labs/lab01/       # format conversion, resizing, and color operations
labs/lab02/       # transparency, cropping, splitting, and contrast
assets/input/     # small source images used by the labs
reports/          # submitted laboratory reports
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run a lab

```bash
cd labs/lab01
python main.py

cd ../lab02
python main.py
```

The GUI lets you choose input images and an output directory. The shared input images are in `assets/input/`.

## Tests

```bash
cd labs/lab01
python -m pytest

cd ../lab02
python -m pytest
```
