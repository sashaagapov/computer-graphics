from __future__ import annotations

from pathlib import Path

from PIL import Image

# Формати, які підтримує програма під час конвертації.
# Ключ словника - назва формату для Pillow, значення - розширення майбутнього файлу.
SUPPORTED_FORMATS: dict[str, str] = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "JPG": ".jpg",
    "BMP": ".bmp",
    "TIFF": ".tiff",
    "WEBP": ".webp",
}


def normalize_format(output_format: str) -> str:
    # Приводимо введений формат до одного стандартного вигляду.
    # Це дозволяє приймати, наприклад, "jpg", "JPG" або " jpeg " без зайвих помилок.
    normalized = output_format.strip().upper()
    if normalized not in SUPPORTED_FORMATS:
        # Якщо формат не підтримується, одразу показуємо користувачу зрозумілу помилку.
        supported = ", ".join(SUPPORTED_FORMATS)
        raise ValueError(f"Unsupported format: {output_format}. Supported: {supported}")

    # Pillow використовує назву JPEG, тому JPG нормалізуємо до JPEG.
    return "JPEG" if normalized == "JPG" else normalized


def extension_for_format(output_format: str) -> str:
    # Повертаємо правильне розширення файлу для вибраного формату.
    # Спочатку нормалізуємо формат, щоб JPG і JPEG працювали однаково.
    return SUPPORTED_FORMATS[normalize_format(output_format)]


def convert_image(image: Image.Image, output_format: str) -> Image.Image:
    # Конвертація формату реалізована повністю, бо це дозволено умовою.
    normalized = normalize_format(output_format)

    # Працюємо з копією, щоб оригінальне зображення в пам'яті не змінювалося.
    converted = image.copy()

    # JPEG і BMP не підтримують прозорість, тому перед збереженням прибираємо alpha.
    if normalized in {"JPEG", "BMP"}:
        converted = _image_without_alpha(converted)

    return converted


def _image_without_alpha(image: Image.Image) -> Image.Image:
    # Якщо у зображенні є прозорість, замінюємо її білим фоном.
    # Це потрібно, бо формати без alpha-каналу не знають, як зберегти прозорі пікселі.
    if image.mode in {"RGBA", "LA"} or (
        image.mode == "P" and "transparency" in image.info
    ):
        # Спершу приводимо зображення до RGBA, щоб гарантовано мати alpha-канал.
        rgba = image.convert("RGBA")

        # Білий фон використовується як нейтральна підкладка для прозорих областей.
        background = Image.new("RGB", rgba.size, (255, 255, 255))

        # Маска alpha-каналу визначає, де саме треба накласти початкове зображення.
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background

    # Якщо прозорості немає, достатньо привести зображення до RGB.
    return image.convert("RGB")


def file_size_kb(path: Path) -> float:
    # Розмір файлу потрібен для порівняння до і після конвертації.
    return path.stat().st_size / 1024


def resize_keep_aspect(
    image: Image.Image,
    width: int | None = None,
    height: int | None = None,
) -> Image.Image:
    # Хоча GUI перевіряє введення, функція також має власний захист.
    # Так її безпечніше викликати з тестів або з іншого Python-коду.
    if width is None and height is None:
        raise ValueError("Width or height must be provided.")

    # Ширина не може бути нульовою або від'ємною.
    if width is not None and width <= 0:
        raise ValueError("Width must be greater than zero.")

    # Висота так само має бути додатним числом.
    if height is not None and height <= 0:
        raise ValueError("Height must be greater than zero.")

    # Якщо користувач задав обидва розміри, використовуємо їх напряму.
    # У цьому режимі співвідношення сторін може змінитися, бо так явно попросили.
    if width is not None and height is not None:
        new_width = width
        new_height = height

    # Якщо задана тільки ширина, висоту рахуємо через коефіцієнт масштабування.
    elif width is not None:
        scale = width / image.width
        new_width = width
        new_height = round(image.height * scale)

    # Якщо задана тільки висота, ширину рахуємо через той самий принцип.
    else:
        # Після попередніх перевірок Python не завжди може сам вивести, що height вже не None.
        assert height is not None

        scale = height / image.height
        new_height = height
        new_width = round(image.width * scale)

    # LANCZOS дає якісніше масштабування, особливо при зменшенні зображення.
    return image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS,
    )


def replace_color(
    image: Image.Image,
    source_rgb: tuple[int, int, int],
    target_rgb: tuple[int, int, int],
) -> Image.Image:
    # Перевіряємо, чи має зображення alpha-канал, щоб не втратити прозорість.
    has_alpha = "A" in image.getbands()

    # Для зручної роботи з пікселями приводимо зображення до RGB або RGBA.
    result = image.convert("RGBA" if has_alpha else "RGB")

    # load() повертає доступ до пікселів, які можна читати й змінювати.
    pixels = result.load()

    # Проходимо всі рядки зображення.
    for y in range(result.height):
        # У кожному рядку проходимо всі стовпці.
        for x in range(result.width):
            pixel = pixels[x, y]

            if has_alpha:
                # Для RGBA окремо зберігаємо прозорість, щоб змінювати тільки RGB.
                r, g, b, alpha = pixel

                # Замінюємо лише точний збіг кольору, без схожих відтінків.
                if (r, g, b) == source_rgb:
                    pixels[x, y] = (*target_rgb, alpha)

            else:
                # Для RGB-пікселя можна порівнювати весь tuple одразу.
                if pixel == source_rgb:
                    pixels[x, y] = target_rgb

    # Повертаємо нове зображення, а не змінений оригінал.
    return result


def adjust_color_balance(
    image: Image.Image,
    red_delta: int = 0,
    green_delta: int = 0,
    blue_delta: int = 0,
) -> Image.Image:
    # Alpha-канал перевіряємо окремо, бо корекція має торкатися тільки RGB.
    has_alpha = "A" in image.getbands()

    # Приведення до RGB/RGBA робить формат пікселя передбачуваним.
    result = image.convert("RGBA" if has_alpha else "RGB")

    # Через pixels можна швидко читати та записувати значення кожного пікселя.
    pixels = result.load()

    # Зовнішній цикл іде по вертикалі зображення.
    for y in range(result.height):
        # Внутрішній цикл іде по горизонталі зображення.
        for x in range(result.width):
            pixel = pixels[x, y]

            if has_alpha:
                # Для RGBA alpha зберігаємо без змін.
                r, g, b, alpha = pixel
            else:
                r, g, b = pixel

            # Кожен канал змінюється на власну delta.
            # max/min не дають значенню вийти за допустимі межі 0..255.
            new_r = max(0, min(255, r + red_delta))
            new_g = max(0, min(255, g + green_delta))
            new_b = max(0, min(255, b + blue_delta))

            if has_alpha:
                # Для прозорих PNG повертаємо alpha таким самим, яким він був.
                pixels[x, y] = (new_r, new_g, new_b, alpha)
            else:
                pixels[x, y] = (new_r, new_g, new_b)

    # Результат повертається як окремий об'єкт Image.
    return result
