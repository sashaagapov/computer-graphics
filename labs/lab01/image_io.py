from __future__ import annotations

from pathlib import Path

from PIL import Image


def open_image(path: Path) -> Image.Image:
    # Відкриваємо файл через context manager, щоб дескриптор файлу закрився автоматично.
    # Це особливо корисно при batch-обробці, коли файлів може бути багато.
    with Image.open(path) as image:
        # Копія дозволяє працювати із зображенням після закриття початкового файлу.
        loaded_image = image.copy()

        # Зберігаємо початковий формат, щоб потім можна було записати результат так само.
        loaded_image.format = image.format
        return loaded_image


def save_image(image: Image.Image, path: Path, output_format: str) -> None:
    # Створюємо папку збереження, якщо користувач вибрав ще неіснуючий шлях.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Додаткові параметри збереження збираємо окремо, бо вони залежать від формату.
    save_kwargs = {}

    # Для JPEG задаємо нормальну якість, щоб результат не був надто стисненим.
    if output_format.upper() in {"JPEG", "JPG"}:
        save_kwargs["quality"] = 95

    # Pillow сам вибирає потрібний encoder за значенням format.
    image.save(path, format=output_format, **save_kwargs)


def build_output_path(
    input_path: Path,
    output_dir: Path,
    suffix: str,
    extension: str | None = None,
) -> Path:
    # Ця функція формує шлях результату, але сама нічого не записує на диск.
    # Якщо розширення не передали явно, залишаємо розширення вхідного файлу.
    final_extension = extension if extension is not None else input_path.suffix

    # Суфікс у назві показує, яку операцію виконали над файлом.
    candidate = output_dir / f"{input_path.stem}{suffix}{final_extension}"
    return unique_path(candidate)


def unique_path(path: Path) -> Path:
    # Якщо такого файлу ще немає, можна безпечно використовувати початкову назву.
    if not path.exists():
        return path

    # Додаємо номер до назви, щоб не перезаписувати вже наявний результат.
    counter = 1
    while True:
        # Наприклад: image.png -> image_1.png -> image_2.png.
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate

        # Переходимо до наступного номера, якщо така назва теж уже зайнята.
        counter += 1
