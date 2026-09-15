from __future__ import annotations

from pathlib import Path

from PIL import Image


def open_image(path: Path) -> Image.Image:
    with Image.open(path) as image:
        loaded_image = image.copy()
        loaded_image.format = image.format
        return loaded_image


def save_image(image: Image.Image, path: Path, output_format: str) -> None:
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


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
