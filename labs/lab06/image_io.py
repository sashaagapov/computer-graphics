from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image

METRICS_FIELDNAMES = [
    "image",
    "noise_type",
    "filter",
    "filter_type",
    "window_size",
    "distortion_vs_input",
    "mse_vs_clean",
]


def open_image(path: Path) -> Image.Image:
    # Копія дозволяє закрити файл одразу після його читання.
    with Image.open(path) as image:
        loaded_image = image.copy()
        loaded_image.format = image.format
        return loaded_image


def save_image(image: Image.Image, path: Path, output_format: str) -> None:
    # Папка результатів створюється автоматично за потреби.
    path.parent.mkdir(parents=True, exist_ok=True)
    save_kwargs = {}
    if output_format.upper() in {"JPEG", "JPG"}:
        save_kwargs["quality"] = 95
    image.save(path, format=output_format, **save_kwargs)


def build_output_path(
    input_path: Path,
    output_dir: Path,
    suffix: str,
    extension: str | None = None,
) -> Path:
    final_extension = extension if extension is not None else input_path.suffix
    candidate = output_dir / f"{input_path.stem}{suffix}{final_extension}"
    return unique_path(candidate)


def write_metrics_csv(rows: list[dict], path: Path) -> None:
    # Кожен рядок описує один результат: яке зображення, який фільтр і яка похибка.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=METRICS_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def unique_path(path: Path) -> Path:
    # Нове ім'я не дає результату перезаписати наявний файл.
    if not path.exists():
        return path

    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
