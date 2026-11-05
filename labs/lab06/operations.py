from __future__ import annotations

import random
from dataclasses import dataclass
from math import isqrt
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from image_io import save_image, write_metrics_csv


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


def merge_images(image1: Image.Image, image2: Image.Image, direction: str) -> Image.Image:
    direction = direction.strip().lower()
    if direction not in {"horizontal", "vertical"}:
        raise ValueError("Напрямок має бути Horizontal або Vertical.")

    # Нове полотно має суму сторін у напрямку об'єднання.
    if direction == "horizontal":
        canvas_size = (image1.width + image2.width, max(image1.height, image2.height))
        second_position = (image1.width, 0)
    else:
        canvas_size = (max(image1.width, image2.width), image1.height + image2.height)
        second_position = (0, image1.height)

    result = Image.new("RGB", canvas_size, "white")
    first = image1.convert("RGBA")
    second = image2.convert("RGBA")
    result.paste(first, (0, 0), first)
    result.paste(second, second_position, second)
    return result


def add_text_watermark(
    image: Image.Image,
    text: str,
    position: str,
    alpha: int,
    font_size: int,
    color: tuple[int, int, int],
) -> Image.Image:
    if not text.strip():
        raise ValueError("Введіть текст водяного знаку.")
    if position not in {"Top Left", "Top Right", "Center", "Bottom Left", "Bottom Right"}:
        raise ValueError("Оберіть позицію водяного знаку.")
    if alpha < 0 or alpha > 255:
        raise ValueError("Alpha має бути в межах 0..255.")
    if font_size <= 0:
        raise ValueError("Розмір шрифту має бути більшим за нуль.")
    if any(channel < 0 or channel > 255 for channel in color):
        raise ValueError("Усі RGB-канали мають бути в межах 0..255.")

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        # The default scalable Pillow font keeps the requested size on systems
        # where Arial is unavailable (including a standard macOS install).
        font = ImageFont.load_default(size=font_size)

    base = image.convert("RGBA")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    margin = 10

    # Координати обчислюються за вибраною позицією та розмірами тексту.
    positions = {
        "Top Left": (margin, margin),
        "Top Right": (base.width - text_width - margin, margin),
        "Center": ((base.width - text_width) // 2, (base.height - text_height) // 2),
        "Bottom Left": (margin, base.height - text_height - margin),
        "Bottom Right": (base.width - text_width - margin, base.height - text_height - margin),
    }
    x, y = positions[position]
    draw.text((x, y), text, font=font, fill=(*color, alpha))

    # Прозорий шар з текстом накладається на оригінальне зображення.
    return Image.alpha_composite(base, layer)


def brightness_value(red: int, green: int, blue: int) -> int:
    # Зважена формула враховує, що око найкраще розрізняє зелений канал.
    return max(0, min(255, round(0.299 * red + 0.587 * green + 0.114 * blue)))


def brightness_matrix(image: Image.Image) -> list[list[int]]:
    source = image.convert("RGB")
    matrix: list[list[int]] = []

    for y in range(source.height):
        row: list[int] = []
        for x in range(source.width):
            red, green, blue = source.getpixel((x, y))
            row.append(brightness_value(red, green, blue))
        matrix.append(row)

    return matrix


def brightness_histogram(image: Image.Image) -> list[int]:
    source = image.convert("RGB")
    histogram = [0] * 256

    for y in range(source.height):
        for x in range(source.width):
            red, green, blue = source.getpixel((x, y))
            brightness = brightness_value(red, green, blue)
            # Індекс масиву — рівень яскравості, значення — кількість таких пікселів.
            histogram[brightness] += 1

    return histogram


def to_grayscale(image: Image.Image) -> Image.Image:
    source = image.convert("RGB")
    result = Image.new("RGB", source.size)

    for y in range(source.height):
        for x in range(source.width):
            red, green, blue = source.getpixel((x, y))
            brightness = brightness_value(red, green, blue)
            result.putpixel((x, y), (brightness, brightness, brightness))

    return result


def binarize(image: Image.Image, threshold: int) -> Image.Image:
    if threshold < 0 or threshold > 255:
        raise ValueError("Threshold має бути в межах 0..255.")

    source = image.convert("RGB")
    result = Image.new("RGB", source.size)

    for y in range(source.height):
        for x in range(source.width):
            red, green, blue = source.getpixel((x, y))
            brightness = brightness_value(red, green, blue)
            # За порогом залишаємо лише два кольори: чорний або білий.
            color = (0, 0, 0) if brightness <= threshold else (255, 255, 255)
            result.putpixel((x, y), color)

    return result


def negative(image: Image.Image) -> Image.Image:
    source = image.convert("RGB")
    result = Image.new("RGB", source.size)

    for y in range(source.height):
        for x in range(source.width):
            red, green, blue = source.getpixel((x, y))
            result.putpixel((x, y), (255 - red, 255 - green, 255 - blue))

    return result


def smoothing_filter(image: Image.Image) -> Image.Image:
    """Згладжує зображення середнім значенням RGB у вікні 3×3."""
    source = image.convert("RGB")
    result = source.copy()

    for y in range(1, source.height - 1):
        for x in range(1, source.width - 1):
            sum_r = 0
            sum_g = 0
            sum_b = 0

            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    red, green, blue = source.getpixel((x + dx, y + dy))
                    sum_r += red
                    sum_g += green
                    sum_b += blue

            new_r = round(sum_r / 9)
            new_g = round(sum_g / 9)
            new_b = round(sum_b / 9)
            result.putpixel((x, y), (new_r, new_g, new_b))

    return result


# ======================================================================
# ЛР №6 — Оцінка якості фільтрації: генерація шуму, лінійні/нелінійні
# фільтри, метрика якості та оркестрація повного аналізу.
# ======================================================================

# Фіксований seed робить усі шуми відтворюваними між запусками програми.
RANDOM_SEED = 42
TEST_IMAGE_SIZE = 128


def clamp_channel(value: float) -> int:
    # Після додавання шуму канал може вийти за межі 0..255.
    return max(0, min(255, round(value)))


def prepare_base_image(image: Image.Image, size: int = TEST_IMAGE_SIZE) -> Image.Image:
    """Приводить довільне зображення до RGB та розміру size×size (f0)."""
    return image.convert("RGB").resize((size, size), Image.Resampling.LANCZOS)


def add_gaussian_noise(image: Image.Image, sigma: float, seed: int = RANDOM_SEED) -> Image.Image:
    """Адитивний гауссівський шум: I_noisy(x,y) = I(x,y) + N(0, sigma^2)."""
    source = image.convert("RGB")
    result = Image.new("RGB", source.size)
    rng = random.Random(seed)

    for y in range(source.height):
        for x in range(source.width):
            red, green, blue = source.getpixel((x, y))
            new_red = clamp_channel(red + rng.gauss(0, sigma))
            new_green = clamp_channel(green + rng.gauss(0, sigma))
            new_blue = clamp_channel(blue + rng.gauss(0, sigma))
            result.putpixel((x, y), (new_red, new_green, new_blue))

    return result


def add_salt_pepper_noise(image: Image.Image, probability: float, seed: int = RANDOM_SEED) -> Image.Image:
    """Імпульсний шум: частина пікселів стає чорною (pepper) або білою (salt)."""
    source = image.convert("RGB")
    result = source.copy()
    rng = random.Random(seed)

    for y in range(source.height):
        for x in range(source.width):
            roll = rng.random()
            if roll < probability / 2:
                result.putpixel((x, y), (0, 0, 0))
            elif roll < probability:
                result.putpixel((x, y), (255, 255, 255))

    return result


def add_brightness_dependent_noise(image: Image.Image, alpha: float, seed: int = RANDOM_SEED) -> Image.Image:
    """Нестаціонарний шум: variance = alpha * brightness, тобто сильніший у світлих ділянках."""
    source = image.convert("RGB")
    result = Image.new("RGB", source.size)
    rng = random.Random(seed)

    for y in range(source.height):
        for x in range(source.width):
            red, green, blue = source.getpixel((x, y))
            brightness = (red + green + blue) / 3
            sigma = (alpha * brightness) ** 0.5
            new_red = clamp_channel(red + rng.gauss(0, sigma))
            new_green = clamp_channel(green + rng.gauss(0, sigma))
            new_blue = clamp_channel(blue + rng.gauss(0, sigma))
            result.putpixel((x, y), (new_red, new_green, new_blue))

    return result


def add_coordinate_dependent_noise(image: Image.Image, max_sigma: float, seed: int = RANDOM_SEED) -> Image.Image:
    """Нестаціонарний шум: sigma росте від лівого верхнього до правого нижнього кута."""
    source = image.convert("RGB")
    result = Image.new("RGB", source.size)
    rng = random.Random(seed)
    width, height = source.size
    max_distance = width + height - 2

    for y in range(height):
        for x in range(width):
            distance_ratio = (x + y) / max_distance
            sigma = max_sigma * distance_ratio
            red, green, blue = source.getpixel((x, y))
            new_red = clamp_channel(red + rng.gauss(0, sigma))
            new_green = clamp_channel(green + rng.gauss(0, sigma))
            new_blue = clamp_channel(blue + rng.gauss(0, sigma))
            result.putpixel((x, y), (new_red, new_green, new_blue))

    return result


# Параметри шуму обрано як прості навчальні значення (не вимога методички) і
# задокументовані тут же, щоб генерація f1..f8 була повністю відтворюваною.
NOISE_DEFINITIONS: list[tuple[str, str, callable]] = [
    ("f1", "gaussian", lambda image: add_gaussian_noise(image, sigma=10)),
    ("f2", "gaussian", lambda image: add_gaussian_noise(image, sigma=25)),
    ("f3", "salt_pepper", lambda image: add_salt_pepper_noise(image, probability=0.03)),
    ("f4", "salt_pepper", lambda image: add_salt_pepper_noise(image, probability=0.08)),
    ("f5", "brightness_dependent", lambda image: add_brightness_dependent_noise(image, alpha=0.5)),
    ("f6", "brightness_dependent", lambda image: add_brightness_dependent_noise(image, alpha=2.0)),
    ("f7", "coordinate_dependent", lambda image: add_coordinate_dependent_noise(image, max_sigma=15)),
    ("f8", "coordinate_dependent", lambda image: add_coordinate_dependent_noise(image, max_sigma=35)),
]


def generate_test_images(clean_image: Image.Image) -> dict[str, tuple[Image.Image, str]]:
    """Будує усі 9 тестових зображень (f0 — чисте, f1..f8 — зашумлені)."""
    test_images: dict[str, tuple[Image.Image, str]] = {"f0": (clean_image, "none")}
    for name, noise_type, noise_function in NOISE_DEFINITIONS:
        test_images[name] = (noise_function(clean_image), noise_type)
    return test_images


def _collect_window_channels(
    source: Image.Image, x: int, y: int, margin: int
) -> tuple[list[int], list[int], list[int]]:
    reds: list[int] = []
    greens: list[int] = []
    blues: list[int] = []
    for dy in range(-margin, margin + 1):
        for dx in range(-margin, margin + 1):
            red, green, blue = source.getpixel((x + dx, y + dy))
            reds.append(red)
            greens.append(green)
            blues.append(blue)
    return reds, greens, blues


def mean_filter(image: Image.Image, window_size: int) -> Image.Image:
    """Лінійний фільтр: кожен піксель замінюється середнім по вікну window_size×window_size."""
    source = image.convert("RGB")
    result = source.copy()
    margin = window_size // 2
    pixel_count = window_size * window_size

    for y in range(margin, source.height - margin):
        for x in range(margin, source.width - margin):
            reds, greens, blues = _collect_window_channels(source, x, y, margin)
            new_pixel = (
                round(sum(reds) / pixel_count),
                round(sum(greens) / pixel_count),
                round(sum(blues) / pixel_count),
            )
            result.putpixel((x, y), new_pixel)

    return result


def median_filter(image: Image.Image, window_size: int) -> Image.Image:
    """Нелінійний фільтр: кожен піксель замінюється медіаною значень у вікні."""
    source = image.convert("RGB")
    result = source.copy()
    margin = window_size // 2
    middle_index = (window_size * window_size) // 2

    for y in range(margin, source.height - margin):
        for x in range(margin, source.width - margin):
            reds, greens, blues = _collect_window_channels(source, x, y, margin)
            reds.sort()
            greens.sort()
            blues.sort()
            result.putpixel((x, y), (reds[middle_index], greens[middle_index], blues[middle_index]))

    return result


def minimum_filter(image: Image.Image, window_size: int = 3) -> Image.Image:
    """Нелінійний фільтр: кожен канал замінюється мінімумом у вікні."""
    source = image.convert("RGB")
    result = source.copy()
    margin = window_size // 2

    for y in range(margin, source.height - margin):
        for x in range(margin, source.width - margin):
            reds, greens, blues = _collect_window_channels(source, x, y, margin)
            result.putpixel((x, y), (min(reds), min(greens), min(blues)))

    return result


def maximum_filter(image: Image.Image, window_size: int = 3) -> Image.Image:
    """Нелінійний фільтр: кожен канал замінюється максимумом у вікні."""
    source = image.convert("RGB")
    result = source.copy()
    margin = window_size // 2

    for y in range(margin, source.height - margin):
        for x in range(margin, source.width - margin):
            reds, greens, blues = _collect_window_channels(source, x, y, margin)
            result.putpixel((x, y), (max(reds), max(greens), max(blues)))

    return result


def midpoint_filter(image: Image.Image, window_size: int = 3) -> Image.Image:
    """Нелінійний фільтр: кожен канал замінюється (min + max) / 2 у вікні."""
    source = image.convert("RGB")
    result = source.copy()
    margin = window_size // 2

    for y in range(margin, source.height - margin):
        for x in range(margin, source.width - margin):
            reds, greens, blues = _collect_window_channels(source, x, y, margin)
            new_pixel = (
                round((min(reds) + max(reds)) / 2),
                round((min(greens) + max(greens)) / 2),
                round((min(blues) + max(blues)) / 2),
            )
            result.putpixel((x, y), new_pixel)

    return result


def alpha_trimmed_mean_filter(image: Image.Image, window_size: int = 3, trim: int = 1) -> Image.Image:
    """Нелінійний фільтр: сортуємо вікно, відкидаємо trim найменших і trim найбільших, рахуємо середнє решти."""
    source = image.convert("RGB")
    result = source.copy()
    margin = window_size // 2

    for y in range(margin, source.height - margin):
        for x in range(margin, source.width - margin):
            reds, greens, blues = _collect_window_channels(source, x, y, margin)
            reds.sort()
            greens.sort()
            blues.sort()
            trimmed_reds = reds[trim:-trim]
            trimmed_greens = greens[trim:-trim]
            trimmed_blues = blues[trim:-trim]
            new_pixel = (
                round(sum(trimmed_reds) / len(trimmed_reds)),
                round(sum(trimmed_greens) / len(trimmed_greens)),
                round(sum(trimmed_blues) / len(trimmed_blues)),
            )
            result.putpixel((x, y), new_pixel)

    return result


# Реєстр усіх 10 фільтрів лабораторної: (назва, тип, розмір вікна, папка результатів, функція).
FILTERS: list[tuple[str, str, int, str, callable]] = [
    ("Mean 3x3", "linear", 3, "mean_3x3", lambda image: mean_filter(image, 3)),
    ("Mean 5x5", "linear", 5, "mean_5x5", lambda image: mean_filter(image, 5)),
    ("Mean 7x7", "linear", 7, "mean_7x7", lambda image: mean_filter(image, 7)),
    ("Median 3x3", "nonlinear", 3, "median_3x3", lambda image: median_filter(image, 3)),
    ("Median 5x5", "nonlinear", 5, "median_5x5", lambda image: median_filter(image, 5)),
    ("Median 7x7", "nonlinear", 7, "median_7x7", lambda image: median_filter(image, 7)),
    ("Minimum 3x3", "nonlinear", 3, "minimum_3x3", lambda image: minimum_filter(image)),
    ("Maximum 3x3", "nonlinear", 3, "maximum_3x3", lambda image: maximum_filter(image)),
    ("Midpoint 3x3", "nonlinear", 3, "midpoint_3x3", lambda image: midpoint_filter(image)),
    ("Alpha-trimmed mean 3x3", "nonlinear", 3, "alpha_trimmed_3x3", lambda image: alpha_trimmed_mean_filter(image)),
]


def calculate_mse(image_a: Image.Image, image_b: Image.Image) -> float:
    """Середня квадратична різниця (ε²) між двома RGB-зображеннями однакового розміру."""
    a = image_a.convert("RGB")
    b = image_b.convert("RGB")
    if a.size != b.size:
        raise ValueError("Зображення мають бути однакового розміру.")

    total_squared_difference = 0
    for y in range(a.height):
        for x in range(a.width):
            a_red, a_green, a_blue = a.getpixel((x, y))
            b_red, b_green, b_blue = b.getpixel((x, y))
            total_squared_difference += (a_red - b_red) ** 2
            total_squared_difference += (a_green - b_green) ** 2
            total_squared_difference += (a_blue - b_blue) ** 2

    value_count = a.width * a.height * 3
    return total_squared_difference / value_count


@dataclass
class AnalysisSummary:
    test_image_count: int
    filter_count: int
    filtered_result_count: int
    metrics_path: Path


def run_filter_analysis(source_image: Image.Image, output_dir: Path) -> AnalysisSummary:
    """Повний аналіз ЛР6: будує f0..f8, застосовує всі 10 фільтрів і рахує метрики."""
    clean_image = prepare_base_image(source_image)
    test_images = generate_test_images(clean_image)

    test_images_dir = output_dir / "test_images"
    for name, (image, _noise_type) in test_images.items():
        save_image(image, test_images_dir / f"{name}.bmp", "BMP")

    metrics_rows: list[dict] = []
    for name, (noisy_image, noise_type) in test_images.items():
        for filter_name, filter_type, window_size, slug, filter_function in FILTERS:
            filtered_image = filter_function(noisy_image)
            save_image(filtered_image, output_dir / slug / f"{name}_{slug}.png", "PNG")

            # Основна метрика методички: спотворення поточного (можливо зашумленого) зображення.
            distortion_vs_input = calculate_mse(filtered_image, noisy_image)
            # Додаткова метрика: наскільки результат наблизився до чистого f0.
            mse_vs_clean = calculate_mse(filtered_image, clean_image)

            metrics_rows.append(
                {
                    "image": name,
                    "noise_type": noise_type,
                    "filter": filter_name,
                    "filter_type": filter_type,
                    "window_size": window_size,
                    "distortion_vs_input": round(distortion_vs_input, 4),
                    "mse_vs_clean": round(mse_vs_clean, 4),
                }
            )

    metrics_path = output_dir / "metrics.csv"
    write_metrics_csv(metrics_rows, metrics_path)

    return AnalysisSummary(
        test_image_count=len(test_images),
        filter_count=len(FILTERS),
        filtered_result_count=len(metrics_rows),
        metrics_path=metrics_path,
    )
