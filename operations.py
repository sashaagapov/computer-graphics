from __future__ import annotations

from pathlib import Path

from PIL import Image


SUPPORTED_FORMATS: dict[str, str] = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "JPG": ".jpg",
    "BMP": ".bmp",
    "TIFF": ".tiff",
    "WEBP": ".webp",
}


def normalize_format(output_format: str) -> str:
    normalized = output_format.strip().upper()
    if normalized not in SUPPORTED_FORMATS:
        supported = ", ".join(SUPPORTED_FORMATS)
        raise ValueError(f"Unsupported format: {output_format}. Supported: {supported}")
    return "JPEG" if normalized == "JPG" else normalized


def extension_for_format(output_format: str) -> str:
    return SUPPORTED_FORMATS[normalize_format(output_format)]


def convert_image(image: Image.Image, output_format: str) -> Image.Image:
    normalized = normalize_format(output_format)
    converted = image.copy()

    if normalized in {"JPEG", "BMP"}:
        converted = _image_without_alpha(converted)

    return converted


def _image_without_alpha(image: Image.Image) -> Image.Image:
    if image.mode in {"RGBA", "LA"} or (
        image.mode == "P" and "transparency" in image.info
    ):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background

    return image.convert("RGB")


def file_size_kb(path: Path) -> float:
    return path.stat().st_size / 1024


def resize_keep_aspect(
    image: Image.Image,
    width: int | None = None,
    height: int | None = None,
) -> Image.Image:
    """
    STUDENT TODO.

    Student must implement calculation of the resulting image size.

    Requirements:
    - width and height may both be provided;
    - only width may be provided;
    - only height may be provided;
    - if only one dimension is provided,
      original aspect ratio must be preserved.
    """
    raise NotImplementedError("This operation has not been implemented yet.")


def replace_color(
    image: Image.Image,
    source_rgb: tuple[int, int, int],
    target_rgb: tuple[int, int, int],
) -> Image.Image:
    """
    STUDENT TODO.

    Student must implement RGB pixel replacement.
    """
    raise NotImplementedError("This operation has not been implemented yet.")


def adjust_color_balance(
    image: Image.Image,
    red_delta: int = 0,
    green_delta: int = 0,
    blue_delta: int = 0,
) -> Image.Image:
    """
    STUDENT TODO.

    Student must implement RGB channel correction.

    Resulting channel values must always stay
    inside the valid 0..255 range.
    """
    raise NotImplementedError("This operation has not been implemented yet.")
