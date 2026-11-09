from __future__ import annotations

import csv
from html import escape
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


def write_demonstration_html(
    rows: list[dict],
    examples: list[dict],
    path: Path,
) -> None:
    """Зберігає зручну HTML-сторінку з прикладами та повною таблицею метрик."""
    path.parent.mkdir(parents=True, exist_ok=True)

    example_sections = []
    for example in examples:
        example_sections.append(
            "<section class=\"example\">"
            f"<h2>{escape(example['title'])}</h2>"
            "<div class=\"images\">"
            "<figure>"
            f"<img src=\"{escape(example['input_path'])}\" alt=\"Зашумлене зображення\">"
            f"<figcaption>Вхідне зображення {escape(example['image'])}</figcaption>"
            "</figure>"
            "<figure>"
            f"<img src=\"{escape(example['result_path'])}\" alt=\"Результат фільтрації\">"
            f"<figcaption>Найкращий результат: {escape(example['filter'])} "
            f"(MSE до f0: {example['mse_vs_clean']:.2f})</figcaption>"
            "</figure>"
            "</div>"
            "</section>"
        )

    table_rows = []
    for row in rows:
        table_rows.append(
            "<tr>"
            f"<td>{escape(row['image'])}</td>"
            f"<td>{escape(row['noise_type'])}</td>"
            f"<td>{escape(row['filter'])}</td>"
            f"<td>{escape(row['filter_type'])}</td>"
            f"<td>{row['window_size']}×{row['window_size']}</td>"
            f"<td>{row['distortion_vs_input']:.2f}</td>"
            f"<td>{row['mse_vs_clean']:.2f}</td>"
            "</tr>"
        )

    html = f"""<!doctype html>
<html lang=\"uk\">
<head>
  <meta charset=\"utf-8\">
  <title>ЛР №6 — результати фільтрації</title>
  <style>
    body {{ max-width: 1100px; margin: 32px auto; padding: 0 20px; font-family: Arial, sans-serif; color: #202124; }}
    h1 {{ margin-bottom: 8px; }}
    .note {{ color: #5f6368; }}
    .example {{ margin: 28px 0; padding: 18px; border: 1px solid #dadce0; border-radius: 8px; }}
    .images {{ display: flex; gap: 24px; flex-wrap: wrap; }}
    figure {{ margin: 0; }}
    img {{ width: 280px; image-rendering: auto; border: 1px solid #dadce0; }}
    figcaption {{ margin-top: 8px; max-width: 280px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ padding: 8px; border: 1px solid #dadce0; text-align: left; }}
    th {{ background: #f1f3f4; }}
  </style>
</head>
<body>
  <h1>ЛР №6 — оцінка якості фільтрації</h1>
  <p class=\"note\">Для кожного типу шуму показано зашумлене зображення та фільтр з найменшим MSE відносно чистого f0. Менше значення MSE означає кращу близькість до оригіналу.</p>
  {''.join(example_sections)}
  <details>
    <summary>Повна таблиця метрик: {len(rows)} результатів</summary>
    <p class=\"note\">distortion_vs_input — наскільки фільтр змінив вхідне зображення; mse_vs_clean — наскільки результат близький до чистого f0.</p>
    <table>
      <thead><tr><th>Зображення</th><th>Шум</th><th>Фільтр</th><th>Тип</th><th>Вікно</th><th>Спотворення</th><th>MSE до f0</th></tr></thead>
      <tbody>{''.join(table_rows)}</tbody>
    </table>
  </details>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


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
