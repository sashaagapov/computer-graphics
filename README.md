# KGV Lab 1 - Image Processing

Локальний проєкт для лабораторної роботи №1 з предмету "Комп'ютерна графіка та візуалізація".

Програма має простий desktop GUI на Tkinter і використовує Pillow для роботи із зображеннями.

## Вимоги

- Python 3
- Pillow
- pytest для тестів
- Tkinter зі стандартної бібліотеки Python

## Підготовка середовища на macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Запуск програми

```bash
source .venv/bin/activate
python main.py
```

## Запуск тестів

```bash
source .venv/bin/activate
python -m pytest
```

Поки `STUDENT TODO` не реалізовані, відповідні тести пропускаються. Після реалізації функцій вони почнуть перевіряти очікуваний результат.

## Структура

```text
kgv-lab1/
    main.py
    gui.py
    operations.py
    image_io.py
    requirements.txt
    README.md
    .gitignore
    tests/
        test_operations.py
```

## Реалізовано

- Вибір одного або кількох зображень.
- Перегляд списку вибраних файлів.
- Вибір папки для збереження результатів.
- Вибір операції та її параметрів.
- Конвертація форматів PNG, JPEG/JPG, BMP, TIFF, WebP.
- Batch-конвертація кількох файлів.
- Показ розміру оригінального та конвертованого файлу.
- Захист від автоматичного перезапису вихідних файлів.
- Обробка помилок і повідомлення для ще не реалізованих операцій.

## STUDENT TODO

У файлі `operations.py` потрібно реалізувати:

1. `resize_keep_aspect(image, width=None, height=None)`
2. `replace_color(image, source_rgb, target_rgb)`
3. `adjust_color_balance(image, red_delta=0, green_delta=0, blue_delta=0)`

Рекомендований порядок реалізації:

1. Спочатку `resize_keep_aspect`, бо її легше перевіряти через розмір зображення.
2. Потім `replace_color`, бо вона працює з конкретними RGB-пікселями.
3. Наприкінці `adjust_color_balance`, бо там треба уважно контролювати межі 0..255.
