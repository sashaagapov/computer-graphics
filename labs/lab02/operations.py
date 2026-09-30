from __future__ import annotations

from math import isqrt
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


def _image_without_alpha(image: Image.Image) -> Image.Image:
    if image.mode in {"RGBA", "LA"} or (
        image.mode == "P" and "transparency" in image.info
    ):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def convert_image(image: Image.Image, output_format: str) -> Image.Image:
    normalized = normalize_format(output_format)
    converted = image.copy()
    if normalized in {"JPEG", "BMP"}:
        converted = _image_without_alpha(converted)
    return converted


def file_size_kb(path: Path) -> float:
    return path.stat().st_size / 1024


def resize_keep_aspect(
    image: Image.Image,
    width: int | None = None,
    height: int | None = None,
) -> Image.Image:
    # Якщо задано одну сторону, друга обчислюється зі збереженням пропорцій.
    if width is None and height is None:
        raise ValueError("Width or height must be provided.")
    if width is not None and width <= 0:
        raise ValueError("Width must be greater than zero.")
    if height is not None and height <= 0:
        raise ValueError("Height must be greater than zero.")

    if width is not None and height is not None:
        new_width = width
        new_height = height
    elif width is not None:
        new_width = width
        new_height = round(image.height * width / image.width)
    else:
        assert height is not None
        new_width = round(image.width * height / image.height)
        new_height = height

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def replace_color(
    image: Image.Image,
    source_rgb: tuple[int, int, int],
    target_rgb: tuple[int, int, int],
) -> Image.Image:
    # Змінюється лише точний RGB-збіг; alpha-канал не втрачається.
    has_alpha = "A" in image.getbands()
    result = image.convert("RGBA" if has_alpha else "RGB")
    pixels = result.load()

    for y in range(result.height):
        for x in range(result.width):
            pixel = pixels[x, y]
            if has_alpha:
                r, g, b, alpha = pixel
                if (r, g, b) == source_rgb:
                    pixels[x, y] = (*target_rgb, alpha)
            elif pixel == source_rgb:
                pixels[x, y] = target_rgb

    return result


def adjust_color_balance(
    image: Image.Image,
    red_delta: int = 0,
    green_delta: int = 0,
    blue_delta: int = 0,
) -> Image.Image:
    # Значення каналів обмежуються діапазоном 0..255.
    has_alpha = "A" in image.getbands()
    result = image.convert("RGBA" if has_alpha else "RGB")
    pixels = result.load()

    for y in range(result.height):
        for x in range(result.width):
            if has_alpha:
                r, g, b, alpha = pixels[x, y]
            else:
                r, g, b = pixels[x, y]

            new_r = max(0, min(255, r + red_delta))
            new_g = max(0, min(255, g + green_delta))
            new_b = max(0, min(255, b + blue_delta))

            if has_alpha:
                pixels[x, y] = (new_r, new_g, new_b, alpha)
            else:
                pixels[x, y] = (new_r, new_g, new_b)

    return result


def set_transparency(image: Image.Image, alpha: int) -> Image.Image:
    if alpha < 0 or alpha > 255:
        raise ValueError("Alpha має бути в межах 0..255.")

    # PNG зберігає alpha-канал, тому результат завжди RGBA.
    result = image.convert("RGBA")
    pixels = result.load()
    for y in range(result.height):
        for x in range(result.width):
            r, g, b, _ = pixels[x, y]
            pixels[x, y] = (r, g, b, alpha)
    return result


def _selection_box(
    image: Image.Image, left: int, top: int, right: int, bottom: int
) -> tuple[int, int, int, int]:
    left = max(0, min(image.width, left))
    top = max(0, min(image.height, top))
    right = max(0, min(image.width, right))
    bottom = max(0, min(image.height, bottom))
    left, right = sorted((left, right))
    top, bottom = sorted((top, bottom))
    if left >= right or top >= bottom:
        raise ValueError("Вибрана область має бути ненульовою.")
    return left, top, right, bottom


def crop_selected_area(
    image: Image.Image, left: int, top: int, right: int, bottom: int
) -> Image.Image:
    # Повертається лише прямокутник, який вибрав користувач.
    return image.crop(_selection_box(image, left, top, right, bottom))


def remove_selected_area(
    image: Image.Image, left: int, top: int, right: int, bottom: int
) -> Image.Image:
    # Колір області лишається, але її alpha стає нульовим.
    left, top, right, bottom = _selection_box(image, left, top, right, bottom)
    result = image.convert("RGBA")
    pixels = result.load()

    for y in range(top, bottom):
        for x in range(left, right):
            red, green, blue, _ = pixels[x, y]
            pixels[x, y] = (red, green, blue, 0)
    return result


def split_image(image: Image.Image, parts: int) -> list[Image.Image]:
    if parts <= 0:
        raise ValueError("Кількість частин має бути більшою за нуль.")
    if parts > image.width * image.height:
        raise ValueError("Частин більше, ніж пікселів у зображенні.")

    # Частини розташовуються у близькій до квадратної сітці без втрати пікселів.
    rows = max(isqrt(parts), (parts + image.width - 1) // image.width)
    rows = min(rows, image.height)
    parts_per_row = parts // rows
    extra_parts = parts % rows
    result: list[Image.Image] = []

    for row in range(rows):
        columns = parts_per_row + (1 if row < extra_parts else 0)
        top = image.height * row // rows
        bottom = image.height * (row + 1) // rows
        for column in range(columns):
            left = image.width * column // columns
            right = image.width * (column + 1) // columns
            result.append(image.crop((left, top, right, bottom)))

    return result


def adjust_contrast(image: Image.Image, factor: float) -> Image.Image:
    if factor <= 1:
        raise ValueError("Коефіцієнт контрастності має бути більшим за 1.")

    has_alpha = "A" in image.getbands()
    result = image.convert("RGBA" if has_alpha else "RGB")
    pixels = result.load()
    red_sum = green_sum = blue_sum = 0
    pixel_count = result.width * result.height

    # Перший прохід знаходить середнє значення кожного RGB-каналу.
    for y in range(result.height):
        for x in range(result.width):
            red, green, blue = pixels[x, y][:3]
            red_sum += red
            green_sum += green
            blue_sum += blue

    average_red = red_sum / pixel_count
    average_green = green_sum / pixel_count
    average_blue = blue_sum / pixel_count

    # Другий прохід застосовує коефіцієнт контрастності до кожного пікселя.
    for y in range(result.height):
        for x in range(result.width):
            if has_alpha:
                red, green, blue, alpha = pixels[x, y]
            else:
                red, green, blue = pixels[x, y]

            # Формула зберігає середню яскравість зображення.
            new_red = max(0, min(255, round(factor * (red - average_red) + average_red)))
            new_green = max(0, min(255, round(factor * (green - average_green) + average_green)))
            new_blue = max(0, min(255, round(factor * (blue - average_blue) + average_blue)))

            if has_alpha:
                pixels[x, y] = (new_red, new_green, new_blue, alpha)
            else:
                pixels[x, y] = (new_red, new_green, new_blue)

    return result
