from pathlib import Path
from tkinter import END, Canvas, Listbox, StringVar, Tk, Toplevel, filedialog, messagebox, scrolledtext, ttk

from PIL import Image, ImageTk

from image_io import build_output_path, open_image, save_image
from operations import (
    adjust_color_balance,
    adjust_contrast,
    add_text_watermark,
    convert_image,
    crop_selected_area,
    extension_for_format,
    file_size_kb,
    normalize_format,
    merge_images,
    remove_selected_area,
    replace_color,
    resize_keep_aspect,
    set_transparency,
    split_image,
)


def run_app() -> None:
    # Головне вікно програми.
    root = Tk()
    root.title("ЛР №3 — Об'єднання, водяний знак та слайд-шоу")
    root.geometry("760x740")
    root.configure(bg="#121212")
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(".", background="#121212", foreground="#f2f2f2")
    style.configure("TFrame", background="#121212")
    style.configure("TLabel", background="#121212", foreground="#f2f2f2")
    style.configure(
        "TLabelframe",
        background="#121212",
        foreground="#b8b8b8",
        bordercolor="#303030",
        lightcolor="#303030",
        darkcolor="#303030",
        borderwidth=1,
    )
    style.configure("TLabelframe.Label", background="#121212", foreground="#f2f2f2")
    style.configure(
        "TButton",
        background="#303030",
        foreground="#f2f2f2",
        bordercolor="#454545",
        lightcolor="#454545",
        darkcolor="#1b1b1b",
        padding=6,
    )
    style.map("TButton", background=[("active", "#454545")])
    style.configure(
        "TEntry",
        fieldbackground="#252525",
        foreground="#f2f2f2",
        bordercolor="#3a3a3a",
        lightcolor="#3a3a3a",
        darkcolor="#1b1b1b",
    )
    style.configure(
        "TCombobox",
        fieldbackground="#252525",
        foreground="#f2f2f2",
        bordercolor="#3a3a3a",
        lightcolor="#3a3a3a",
        darkcolor="#1b1b1b",
        arrowcolor="#b8b8b8",
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", "#252525")],
        foreground=[("readonly", "#f2f2f2")],
        selectbackground=[("readonly", "#454545")],
        selectforeground=[("readonly", "#f2f2f2")],
    )

    selected_files: list[Path] = []
    selected_area: tuple[int, int, int, int] | None = None
    output_folder = StringVar()
    operation = StringVar(value="Set transparency")
    output_format = StringVar(value="PNG")
    width = StringVar()
    height = StringVar()
    source_r = StringVar(value="255")
    source_g = StringVar(value="0")
    source_b = StringVar(value="0")
    target_r = StringVar(value="0")
    target_g = StringVar(value="0")
    target_b = StringVar(value="255")
    red_delta = StringVar(value="0")
    green_delta = StringVar(value="0")
    blue_delta = StringVar(value="0")
    alpha = StringVar(value="128")
    split_parts = StringVar(value="4")
    contrast_factor = StringVar(value="1.5")
    merge_direction = StringVar(value="Horizontal")
    watermark_text = StringVar(value="Watermark")
    watermark_position = StringVar(value="Bottom Right")
    watermark_alpha = StringVar(value="128")
    watermark_font_size = StringVar(value="32")
    watermark_r = StringVar(value="255")
    watermark_g = StringVar(value="255")
    watermark_b = StringVar(value="255")
    slideshow_delay = StringVar(value="2")
    area_text = StringVar(value="Область не вибрана")

    def choose_files() -> None:
        nonlocal selected_area
        paths = filedialog.askopenfilenames(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp"),
                ("All files", "*.*"),
            ]
        )
        if not paths:
            return

        selected_files.clear()
        selected_files.extend(Path(path) for path in paths)
        selected_area = None
        area_text.set("Область не вибрана")
        file_list.delete(0, END)
        for path in selected_files:
            file_list.insert(END, path.name)

    def choose_output_folder() -> None:
        folder = filedialog.askdirectory()
        if folder:
            output_folder.set(folder)

    def open_slideshow() -> None:
        if not selected_files:
            messagebox.showwarning("Немає зображень", "Оберіть зображення для слайд-шоу.")
            return
        try:
            delay_ms = round(float(slideshow_delay.get()) * 1000)
            if delay_ms <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Неправильна затримка", "Вкажіть затримку в секундах, більшу за нуль.")
            return

        window = Toplevel(root)
        window.title("Слайд-шоу")
        window.configure(bg="#121212")
        current_index = 0
        after_id = None
        playing = False
        image_label = ttk.Label(window)
        image_label.pack(padx=12, pady=12)
        info_label = ttk.Label(window)
        info_label.pack(pady=(0, 8))

        def show_current() -> None:
            nonlocal current_index, after_id
            image = open_image(selected_files[current_index])
            image.thumbnail((800, 550), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            image_label.configure(image=photo)
            image_label.image = photo
            info_label.configure(text=f"{current_index + 1} / {len(selected_files)}: {selected_files[current_index].name}")
            current_index = (current_index + 1) % len(selected_files)
            if playing:
                # after() планує наступний кадр і не блокує інтерфейс.
                after_id = window.after(delay_ms, show_current)

        def start() -> None:
            nonlocal playing
            if not playing:
                playing = True
                show_current()

        def stop() -> None:
            nonlocal playing, after_id
            playing = False
            if after_id is not None:
                # Скасовуємо запланований callback, щоб кадри більше не змінювалися.
                window.after_cancel(after_id)
                after_id = None

        def close() -> None:
            stop()
            window.destroy()

        buttons = ttk.Frame(window)
        buttons.pack(pady=(0, 12))
        ttk.Button(buttons, text="Start", command=start).pack(side="left", padx=4)
        ttk.Button(buttons, text="Stop", command=stop).pack(side="left", padx=4)
        window.protocol("WM_DELETE_WINDOW", close)

    def choose_area() -> None:
        # Область вибирається на першому зображенні зі списку.
        nonlocal selected_area
        if not selected_files:
            messagebox.showwarning("Немає зображення", "Спочатку оберіть зображення.")
            return

        image = open_image(selected_files[0])
        max_width = 700
        max_height = 430
        scale = min(max_width / image.width, max_height / image.height, 1)
        preview_width = max(1, round(image.width * scale))
        preview_height = max(1, round(image.height * scale))
        preview = image.resize((preview_width, preview_height), Image.Resampling.LANCZOS)

        preview_window = Toplevel(root)
        preview_window.title("Виберіть область")
        preview_window.configure(bg="#121212")
        preview_photo = ImageTk.PhotoImage(preview)
        canvas = Canvas(
            preview_window,
            width=preview_width,
            height=preview_height,
            bg="#121212",
            highlightthickness=0,
        )
        canvas.pack(padx=10, pady=10)
        canvas.create_image(0, 0, anchor="nw", image=preview_photo)
        preview_window.preview_photo = preview_photo

        start_x = start_y = end_x = end_y = None
        rectangle = None

        def start_selection(event) -> None:
            nonlocal start_x, start_y, end_x, end_y, rectangle
            start_x = max(0, min(preview_width, event.x))
            start_y = max(0, min(preview_height, event.y))
            end_x = start_x
            end_y = start_y
            if rectangle is not None:
                canvas.delete(rectangle)
            rectangle = canvas.create_rectangle(start_x, start_y, end_x, end_y, outline="red", width=2)

        def update_selection(event) -> None:
            nonlocal end_x, end_y
            if start_x is None or start_y is None:
                return
            end_x = max(0, min(preview_width, event.x))
            end_y = max(0, min(preview_height, event.y))
            canvas.coords(rectangle, start_x, start_y, end_x, end_y)

        def save_selection() -> None:
            nonlocal selected_area
            if start_x is None or start_y is None or end_x is None or end_y is None:
                messagebox.showwarning("Немає області", "Виділіть прямокутну область мишею.")
                return

            # Координати зменшеного preview переводимо в координати оригіналу.
            left = round(min(start_x, end_x) * image.width / preview_width)
            top = round(min(start_y, end_y) * image.height / preview_height)
            right = round(max(start_x, end_x) * image.width / preview_width)
            bottom = round(max(start_y, end_y) * image.height / preview_height)
            left = max(0, min(image.width, left))
            top = max(0, min(image.height, top))
            right = max(0, min(image.width, right))
            bottom = max(0, min(image.height, bottom))

            if left >= right or top >= bottom:
                messagebox.showwarning("Мала область", "Виділіть область ненульового розміру.")
                return

            selected_area = (left, top, right, bottom)
            area_text.set(f"Область: ({left}, {top}) — ({right}, {bottom}) px")
            preview_window.destroy()

        canvas.bind("<ButtonPress-1>", start_selection)
        canvas.bind("<B1-Motion>", update_selection)
        ttk.Button(preview_window, text="Підтвердити область", command=save_selection).pack(pady=(0, 10))

    def run_processing() -> None:
        # Спочатку зчитуються параметри лише вибраної операції.
        if not selected_files:
            messagebox.showwarning("Немає зображень", "Оберіть хоча б одне зображення.")
            return
        current_operation = operation.get()
        if current_operation == "Slideshow":
            open_slideshow()
            return
        if not output_folder.get():
            messagebox.showwarning("Немає папки", "Оберіть папку для результатів.")
            return

        try:
            if current_operation == "Convert format":
                format_name = normalize_format(output_format.get())
            elif current_operation == "Resize":
                width_text = width.get().strip()
                height_text = height.get().strip()
                new_width = int(width_text) if width_text else None
                new_height = int(height_text) if height_text else None
                if new_width is None and new_height is None:
                    raise ValueError("Вкажіть width, height або обидва значення.")
                if (new_width is not None and new_width <= 0) or (
                    new_height is not None and new_height <= 0
                ):
                    raise ValueError("Width і height мають бути більшими за нуль.")
            elif current_operation == "Replace color":
                source_color = (int(source_r.get()), int(source_g.get()), int(source_b.get()))
                target_color = (int(target_r.get()), int(target_g.get()), int(target_b.get()))
                if any(channel < 0 or channel > 255 for channel in source_color + target_color):
                    raise ValueError("Усі RGB-канали мають бути в межах 0..255.")
            elif current_operation == "Adjust color balance":
                red_change = int(red_delta.get())
                green_change = int(green_delta.get())
                blue_change = int(blue_delta.get())
            elif current_operation == "Set transparency":
                alpha_value = int(alpha.get())
                if alpha_value < 0 or alpha_value > 255:
                    raise ValueError("Alpha має бути в межах 0..255.")
            elif current_operation in {"Crop selected area", "Remove selected area"}:
                if selected_area is None:
                    raise ValueError("Спочатку виберіть область на preview.")
                left, top, right, bottom = selected_area
            elif current_operation == "Split image":
                number_of_parts = int(split_parts.get())
                if number_of_parts <= 0:
                    raise ValueError("Кількість частин має бути більшою за нуль.")
            elif current_operation == "Adjust contrast":
                factor = float(contrast_factor.get())
                if factor <= 1:
                    raise ValueError("Коефіцієнт контрастності має бути більшим за 1.")
            elif current_operation == "Merge images":
                if len(selected_files) != 2:
                    raise ValueError("Для об'єднання оберіть рівно два зображення.")
                direction = merge_direction.get()
            elif current_operation == "Add watermark":
                text = watermark_text.get()
                position = watermark_position.get()
                watermark_alpha_value = int(watermark_alpha.get())
                font_size = int(watermark_font_size.get())
                watermark_color = (
                    int(watermark_r.get()),
                    int(watermark_g.get()),
                    int(watermark_b.get()),
                )
                if not text.strip():
                    raise ValueError("Введіть текст водяного знаку.")
                if watermark_alpha_value < 0 or watermark_alpha_value > 255:
                    raise ValueError("Alpha має бути в межах 0..255.")
                if font_size <= 0:
                    raise ValueError("Розмір шрифту має бути більшим за нуль.")
                if any(channel < 0 or channel > 255 for channel in watermark_color):
                    raise ValueError("Усі RGB-канали мають бути в межах 0..255.")
            else:
                raise ValueError("Оберіть операцію.")
        except ValueError as error:
            messagebox.showerror("Неправильні параметри", str(error))
            return

        output_dir = Path(output_folder.get())
        result_lines: list[str] = []

        if current_operation == "Merge images":
            try:
                first_image = open_image(selected_files[0])
                second_image = open_image(selected_files[1])
                result = merge_images(first_image, second_image, direction)
                output_path = build_output_path(selected_files[0], output_dir, "_merged", ".png")
                save_image(result, output_path, "PNG")
                result_lines.append(
                    f"{selected_files[0].name} + {selected_files[1].name} → {output_path.name}\n"
                    f"  Розмір результату: {result.width}×{result.height} px"
                )
            except Exception as error:
                result_lines.append(f"ПОМИЛКА — {error}")
            results.delete("1.0", END)
            results.insert(END, "\n".join(result_lines))
            messagebox.showinfo("Готово", "Обробку завершено.")
            return

        for input_path in selected_files:
            try:
                image = open_image(input_path)
                original_file_size = file_size_kb(input_path)
                source_format = image.format or "PNG"

                # Кожна операція викликає відповідну функцію з operations.py.
                if current_operation == "Convert format":
                    result = convert_image(image, format_name)
                    output_path = build_output_path(
                        input_path,
                        output_dir,
                        f"_converted_{format_name.lower()}",
                        extension_for_format(format_name),
                    )
                    save_image(result, output_path, format_name)

                elif current_operation == "Resize":
                    result = resize_keep_aspect(image, new_width, new_height)
                    output_path = build_output_path(input_path, output_dir, "_resized")
                    save_image(result, output_path, source_format)

                elif current_operation == "Replace color":
                    result = replace_color(image, source_color, target_color)
                    output_path = build_output_path(input_path, output_dir, "_color_replaced")
                    save_image(result, output_path, source_format)

                elif current_operation == "Adjust color balance":
                    result = adjust_color_balance(image, red_change, green_change, blue_change)
                    output_path = build_output_path(input_path, output_dir, "_balanced")
                    save_image(result, output_path, source_format)

                elif current_operation == "Set transparency":
                    result = set_transparency(image, alpha_value)
                    output_path = build_output_path(input_path, output_dir, "_transparent", ".png")
                    save_image(result, output_path, "PNG")

                elif current_operation == "Crop selected area":
                    result = crop_selected_area(image, left, top, right, bottom)
                    output_path = build_output_path(input_path, output_dir, "_cropped")
                    save_image(result, output_path, source_format)

                elif current_operation == "Remove selected area":
                    result = remove_selected_area(image, left, top, right, bottom)
                    output_path = build_output_path(input_path, output_dir, "_area_removed", ".png")
                    save_image(result, output_path, "PNG")

                elif current_operation == "Split image":
                    # Для поділу один файл створює кілька результатів.
                    pieces = split_image(image, number_of_parts)
                    part_lines: list[str] = []
                    total_size = 0.0
                    for index, piece in enumerate(pieces, start=1):
                        output_path = build_output_path(
                            input_path, output_dir, f"_part_{index}", ".png"
                        )
                        save_image(piece, output_path, "PNG")
                        part_size = file_size_kb(output_path)
                        total_size += part_size
                        part_lines.append(
                            f"  Частина {index}: {output_path.name}, "
                            f"{piece.width}×{piece.height} px, {part_size:.2f} KB"
                        )
                    difference = total_size - original_file_size
                    percent = difference / original_file_size * 100
                    result_lines.append(
                        f"{input_path.name}: створено {len(pieces)} частин\n"
                        f"  Сумарний розмір: {original_file_size:.2f} KB → {total_size:.2f} KB | "
                        f"різниця: {difference:+.2f} KB ({percent:+.1f}%)\n"
                        + "\n".join(part_lines)
                    )
                    continue

                elif current_operation == "Adjust contrast":
                    result = adjust_contrast(image, factor)
                    output_path = build_output_path(input_path, output_dir, "_contrast")
                    save_image(result, output_path, source_format)

                elif current_operation == "Add watermark":
                    result = add_text_watermark(
                        image, text, position, watermark_alpha_value, font_size, watermark_color
                    )
                    output_path = build_output_path(input_path, output_dir, "_watermark", ".png")
                    save_image(result, output_path, "PNG")

                new_file_size = file_size_kb(output_path)
                size_difference = new_file_size - original_file_size
                percentage_difference = size_difference / original_file_size * 100
                result_lines.append(
                    f"{input_path.name} → {output_path.name}\n"
                    f"  Зображення: {image.width}×{image.height} px → "
                    f"{result.width}×{result.height} px\n"
                    f"  Файл: {original_file_size:.2f} KB → {new_file_size:.2f} KB | "
                    f"різниця: {size_difference:+.2f} KB ({percentage_difference:+.1f}%)"
                )
            except Exception as error:
                result_lines.append(f"{input_path.name}: ПОМИЛКА — {error}")

        results.delete("1.0", END)
        results.insert(END, "\n\n".join(result_lines))
        messagebox.showinfo("Готово", "Обробку завершено.")

    def show_parameters(_event=None) -> None:
        # Показуємо тільки поля, потрібні для вибраної операції.
        for widget in parameter_content.winfo_children():
            widget.destroy()

        current_operation = operation.get()
        if current_operation == "Convert format":
            ttk.Label(parameter_content, text="Output format:").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Combobox(
                parameter_content,
                textvariable=output_format,
                values=("PNG", "JPEG", "JPG", "BMP", "TIFF", "WEBP"),
                state="readonly",
                width=10,
            ).grid(row=0, column=1, sticky="w", pady=4)

        elif current_operation == "Resize":
            ttk.Label(parameter_content, text="Width:").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=width, width=12).grid(
                row=0, column=1, sticky="w", pady=4
            )
            ttk.Label(parameter_content, text="Height:").grid(
                row=0, column=2, sticky="w", padx=(20, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=height, width=12).grid(
                row=0, column=3, sticky="w", pady=4
            )

        elif current_operation == "Replace color":
            ttk.Label(parameter_content, text="Source:").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Label(parameter_content, text="R").grid(row=0, column=1, padx=2, pady=4)
            ttk.Entry(parameter_content, textvariable=source_r, width=5).grid(row=0, column=2, padx=2, pady=4)
            ttk.Label(parameter_content, text="G").grid(row=0, column=3, padx=2, pady=4)
            ttk.Entry(parameter_content, textvariable=source_g, width=5).grid(row=0, column=4, padx=2, pady=4)
            ttk.Label(parameter_content, text="B").grid(row=0, column=5, padx=2, pady=4)
            ttk.Entry(parameter_content, textvariable=source_b, width=5).grid(row=0, column=6, padx=2, pady=4)
            ttk.Label(parameter_content, text="Target:").grid(
                row=1, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Label(parameter_content, text="R").grid(row=1, column=1, padx=2, pady=4)
            ttk.Entry(parameter_content, textvariable=target_r, width=5).grid(row=1, column=2, padx=2, pady=4)
            ttk.Label(parameter_content, text="G").grid(row=1, column=3, padx=2, pady=4)
            ttk.Entry(parameter_content, textvariable=target_g, width=5).grid(row=1, column=4, padx=2, pady=4)
            ttk.Label(parameter_content, text="B").grid(row=1, column=5, padx=2, pady=4)
            ttk.Entry(parameter_content, textvariable=target_b, width=5).grid(row=1, column=6, padx=2, pady=4)

        elif current_operation == "Adjust color balance":
            ttk.Label(parameter_content, text="Red delta:").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=red_delta, width=8).grid(row=0, column=1, sticky="w", pady=4)
            ttk.Label(parameter_content, text="Green delta:").grid(
                row=1, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=green_delta, width=8).grid(row=1, column=1, sticky="w", pady=4)
            ttk.Label(parameter_content, text="Blue delta:").grid(
                row=2, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=blue_delta, width=8).grid(row=2, column=1, sticky="w", pady=4)

        elif current_operation == "Set transparency":
            ttk.Label(parameter_content, text="Alpha (0..255):").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=alpha, width=8).grid(row=0, column=1, sticky="w", pady=4)

        elif current_operation in {"Crop selected area", "Remove selected area"}:
            ttk.Button(parameter_content, text="Вибрати область на preview", command=choose_area).grid(
                row=0, column=0, sticky="w", padx=(0, 12), pady=4
            )
            ttk.Label(parameter_content, textvariable=area_text).grid(row=0, column=1, sticky="w", pady=4)

        elif current_operation == "Split image":
            ttk.Label(parameter_content, text="Кількість частин:").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=split_parts, width=8).grid(row=0, column=1, sticky="w", pady=4)

        elif current_operation == "Adjust contrast":
            ttk.Label(parameter_content, text="Коефіцієнт K (> 1):").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=contrast_factor, width=8).grid(row=0, column=1, sticky="w", pady=4)

        elif current_operation == "Merge images":
            ttk.Label(parameter_content, text="Напрямок:").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Combobox(
                parameter_content,
                textvariable=merge_direction,
                values=("Horizontal", "Vertical"),
                state="readonly",
                width=14,
            ).grid(row=0, column=1, sticky="w", pady=4)
            ttk.Label(parameter_content, text="Оберіть рівно два зображення.").grid(
                row=1, column=0, columnspan=2, sticky="w", pady=4
            )

        elif current_operation == "Add watermark":
            ttk.Label(parameter_content, text="Text:").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=watermark_text, width=30).grid(
                row=0, column=1, columnspan=5, sticky="w", pady=4
            )
            ttk.Label(parameter_content, text="Position:").grid(
                row=1, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Combobox(
                parameter_content,
                textvariable=watermark_position,
                values=("Top Left", "Top Right", "Center", "Bottom Left", "Bottom Right"),
                state="readonly",
                width=16,
            ).grid(row=1, column=1, sticky="w", pady=4)
            ttk.Label(parameter_content, text="Alpha:").grid(row=1, column=2, padx=(16, 4), pady=4)
            ttk.Entry(parameter_content, textvariable=watermark_alpha, width=6).grid(row=1, column=3, pady=4)
            ttk.Label(parameter_content, text="Size:").grid(row=1, column=4, padx=(16, 4), pady=4)
            ttk.Entry(parameter_content, textvariable=watermark_font_size, width=6).grid(row=1, column=5, pady=4)
            ttk.Label(parameter_content, text="RGB:").grid(
                row=2, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=watermark_r, width=6).grid(row=2, column=1, sticky="w", pady=4)
            ttk.Entry(parameter_content, textvariable=watermark_g, width=6).grid(row=2, column=2, sticky="w", pady=4)
            ttk.Entry(parameter_content, textvariable=watermark_b, width=6).grid(row=2, column=3, sticky="w", pady=4)

        elif current_operation == "Slideshow":
            ttk.Label(parameter_content, text="Затримка (секунди):").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=slideshow_delay, width=8).grid(
                row=0, column=1, sticky="w", pady=4
            )
            ttk.Button(parameter_content, text="Start slideshow", command=open_slideshow).grid(
                row=0, column=2, padx=(16, 0), pady=4
            )

    # Вибір вхідних зображень.
    images_frame = ttk.LabelFrame(root, text="Images")
    images_frame.pack(fill="x", padx=12, pady=(12, 6))
    ttk.Button(images_frame, text="Choose images", command=choose_files).pack(
        anchor="w", padx=8, pady=(8, 4)
    )
    file_list = Listbox(
        images_frame,
        height=5,
        bg="#252525",
        fg="#f2f2f2",
        selectbackground="#454545",
        selectforeground="#f2f2f2",
        highlightthickness=0,
    )
    file_list.pack(fill="x", padx=8, pady=(0, 8))

    # Папка, у якій зберігаються нові файли.
    output_frame = ttk.LabelFrame(root, text="Output folder")
    output_frame.pack(fill="x", padx=12, pady=6)
    ttk.Entry(output_frame, textvariable=output_folder).pack(
        side="left", fill="x", expand=True, padx=8, pady=8
    )
    ttk.Button(output_frame, text="Choose output folder", command=choose_output_folder).pack(
        side="left", padx=(0, 8), pady=8
    )

    # Вибір режиму обробки.
    operation_frame = ttk.LabelFrame(root, text="Operation")
    operation_frame.pack(fill="x", padx=12, pady=6)
    operation_box = ttk.Combobox(
        operation_frame,
        textvariable=operation,
        values=(
            "Set transparency",
            "Crop selected area",
            "Remove selected area",
            "Split image",
            "Adjust contrast",
            "Convert format",
            "Resize",
            "Replace color",
            "Adjust color balance",
            "Merge images",
            "Add watermark",
            "Slideshow",
        ),
        state="readonly",
        height=12,
    )
    operation_box.pack(fill="x", padx=8, pady=8)

    # Параметри змінюються після вибору операції.
    parameters = ttk.LabelFrame(root, text="Parameters")
    parameters.pack(fill="x", padx=12, pady=6)
    parameter_content = ttk.Frame(parameters)
    parameter_content.pack(fill="x", padx=8, pady=8)
    operation_box.bind("<<ComboboxSelected>>", show_parameters)
    show_parameters()

    ttk.Button(root, text="Run processing", command=run_processing).pack(pady=8)

    # Тут показуються створені файли, розміри та можливі помилки.
    results_frame = ttk.LabelFrame(root, text="Results")
    results_frame.pack(fill="both", expand=True, padx=12, pady=(6, 12))
    results = scrolledtext.ScrolledText(
        results_frame,
        height=9,
        wrap="word",
        font=("Menlo", 12),
        bg="#252525",
        fg="#f2f2f2",
        insertbackground="#f2f2f2",
        highlightthickness=0,
    )
    results.vbar.configure(
        background="#303030",
        activebackground="#454545",
        troughcolor="#1b1b1b",
        highlightthickness=0,
    )
    results.pack(fill="both", expand=True, padx=8, pady=8)

    root.mainloop()
