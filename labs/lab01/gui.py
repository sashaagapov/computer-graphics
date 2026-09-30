from pathlib import Path
from tkinter import END, Listbox, StringVar, Tk, filedialog, messagebox, scrolledtext, ttk

from image_io import build_output_path, open_image, save_image
from operations import (
    adjust_color_balance,
    convert_image,
    extension_for_format,
    file_size_kb,
    normalize_format,
    replace_color,
    resize_keep_aspect,
)


def run_app() -> None:

    root = Tk()
    root.title("ЛР №1 — Обробка зображень")
    root.geometry("720x650")

    selected_files: list[Path] = []
    output_folder = StringVar()
    operation = StringVar(value="Convert format")
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

    def choose_files() -> None:
        # askopenfilenames дозволяє вибрати як один, так і декілька файлів.
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
        file_list.delete(0, END)
        for path in selected_files:
            file_list.insert(END, path.name)

    def choose_output_folder() -> None:
        # Результати зберігаються в окремій папці, а оригінали не змінюються.
        folder = filedialog.askdirectory()
        if folder:
            output_folder.set(folder)

    def run_processing() -> None:
        # Спочатку перевіряємо, що користувач обрав файли та папку результатів.
        if not selected_files:
            messagebox.showwarning("Немає зображень", "Оберіть хоча б одне зображення.")
            return
        if not output_folder.get():
            messagebox.showwarning("Немає папки", "Оберіть папку для результатів.")
            return

        try:
            current_operation = operation.get()

            # Зчитуємо тільки ті параметри, які потрібні вибраній операції.
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
            else:
                raise ValueError("Оберіть операцію.")
        except ValueError as error:
            messagebox.showerror("Неправильні параметри", str(error))
            return

        output_dir = Path(output_folder.get())
        result_lines: list[str] = []

        # Кожен файл обробляється окремо: помилка одного не зупиняє інші.
        for input_path in selected_files:
            try:
                image = open_image(input_path)
                original_file_size = file_size_kb(input_path)

                # Прямий вибір потрібного алгоритму за операцією з Combobox.
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
                    save_image(result, output_path, image.format or "PNG")

                elif current_operation == "Replace color":
                    result = replace_color(image, source_color, target_color)
                    output_path = build_output_path(input_path, output_dir, "_color_replaced")
                    save_image(result, output_path, image.format or "PNG")

                elif current_operation == "Adjust color balance":
                    result = adjust_color_balance(image, red_change, green_change, blue_change)
                    output_path = build_output_path(input_path, output_dir, "_balanced")
                    save_image(result, output_path, image.format or "PNG")

                # Після збереження показуємо розмір зображення та файлу до і після операції.
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

        # Тут відображається, де саме збережено результат кожної операції.
        results.delete("1.0", END)
        results.insert(END, "\n".join(result_lines))
        messagebox.showinfo("Готово", "Обробку завершено.")

    def show_parameters(_event=None) -> None:
        # Спочатку прибираємо поля попередньої операції.
        for widget in parameter_content.winfo_children():
            widget.destroy()

        # Для вибраної операції показуємо тільки потрібні їй параметри.
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
            ttk.Entry(parameter_content, textvariable=source_r, width=5).grid(
                row=0, column=2, padx=2, pady=4
            )
            ttk.Label(parameter_content, text="G").grid(row=0, column=3, padx=2, pady=4)
            ttk.Entry(parameter_content, textvariable=source_g, width=5).grid(
                row=0, column=4, padx=2, pady=4
            )
            ttk.Label(parameter_content, text="B").grid(row=0, column=5, padx=2, pady=4)
            ttk.Entry(parameter_content, textvariable=source_b, width=5).grid(
                row=0, column=6, padx=2, pady=4
            )

            ttk.Label(parameter_content, text="Target:").grid(
                row=1, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Label(parameter_content, text="R").grid(row=1, column=1, padx=2, pady=4)
            ttk.Entry(parameter_content, textvariable=target_r, width=5).grid(
                row=1, column=2, padx=2, pady=4
            )
            ttk.Label(parameter_content, text="G").grid(row=1, column=3, padx=2, pady=4)
            ttk.Entry(parameter_content, textvariable=target_g, width=5).grid(
                row=1, column=4, padx=2, pady=4
            )
            ttk.Label(parameter_content, text="B").grid(row=1, column=5, padx=2, pady=4)
            ttk.Entry(parameter_content, textvariable=target_b, width=5).grid(
                row=1, column=6, padx=2, pady=4
            )

        elif current_operation == "Adjust color balance":
            ttk.Label(parameter_content, text="Red delta:").grid(
                row=0, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=red_delta, width=8).grid(
                row=0, column=1, sticky="w", pady=4
            )
            ttk.Label(parameter_content, text="Green delta:").grid(
                row=1, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=green_delta, width=8).grid(
                row=1, column=1, sticky="w", pady=4
            )
            ttk.Label(parameter_content, text="Blue delta:").grid(
                row=2, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parameter_content, textvariable=blue_delta, width=8).grid(
                row=2, column=1, sticky="w", pady=4
            )

    # Images section
    images_frame = ttk.LabelFrame(root, text="Images")
    images_frame.pack(fill="x", padx=12, pady=(12, 6))
    ttk.Button(images_frame, text="Choose images", command=choose_files).pack(
        anchor="w", padx=8, pady=(8, 4)
    )
    file_list = Listbox(images_frame, height=5)
    file_list.pack(fill="x", padx=8, pady=(0, 8))

    # Output folder section
    output_frame = ttk.LabelFrame(root, text="Output folder")
    output_frame.pack(fill="x", padx=12, pady=6)
    ttk.Entry(output_frame, textvariable=output_folder).pack(
        side="left", fill="x", expand=True, padx=8, pady=8
    )
    ttk.Button(output_frame, text="Choose output folder", command=choose_output_folder).pack(
        side="left", padx=(0, 8), pady=8
    )

    # Operation section
    operation_frame = ttk.LabelFrame(root, text="Operation")
    operation_frame.pack(fill="x", padx=12, pady=6)
    operation_box = ttk.Combobox(
        operation_frame,
        textvariable=operation,
        values=("Convert format", "Resize", "Replace color", "Adjust color balance"),
        state="readonly",
    )
    operation_box.pack(fill="x", padx=8, pady=8)

    # Parameters section
    parameters = ttk.LabelFrame(root, text="Parameters")
    parameters.pack(fill="x", padx=12, pady=6)
    parameter_content = ttk.Frame(parameters)
    parameter_content.pack(fill="x", padx=8, pady=8)
    operation_box.bind("<<ComboboxSelected>>", show_parameters)
    show_parameters()

    # Run button
    ttk.Button(root, text="Run processing", command=run_processing).pack(pady=8)

    # Results section
    results_frame = ttk.LabelFrame(root, text="Results")
    results_frame.pack(fill="both", expand=True, padx=12, pady=(6, 12))
    results = scrolledtext.ScrolledText(results_frame, height=9, wrap="word", font=("Menlo", 12))
    results.pack(fill="both", expand=True, padx=8, pady=8)

    root.mainloop()
