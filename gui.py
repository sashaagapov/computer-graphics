from __future__ import annotations

from pathlib import Path
from tkinter import (
    BOTH,
    END,
    LEFT,
    RIGHT,
    Button,
    Frame,
    IntVar,
    Label,
    Listbox,
    StringVar,
    Text,
    Tk,
    filedialog,
    messagebox,
    colorchooser,
)
from tkinter import ttk

from image_io import build_output_path, open_image, save_image
from operations import (
    SUPPORTED_FORMATS,
    adjust_color_balance,
    convert_image,
    extension_for_format,
    file_size_kb,
    normalize_format,
    replace_color,
    resize_keep_aspect,
)


class ImageLabApp:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("KGV Lab 1 - Image Processing")
        self.root.geometry("820x620")

        self.selected_files: list[Path] = []
        self.output_dir = StringVar()
        self.operation = StringVar(value="Convert format")
        self.output_format = StringVar(value="PNG")
        self.width = StringVar()
        self.height = StringVar()
        self.source_rgb: tuple[int, int, int] = (255, 0, 0)
        self.target_rgb: tuple[int, int, int] = (0, 0, 255)
        self.red_delta = IntVar(value=0)
        self.green_delta = IntVar(value=0)
        self.blue_delta = IntVar(value=0)

        self._build_layout()
        self._refresh_parameters()

    def run(self) -> None:
        self.root.mainloop()

    def _build_layout(self) -> None:
        root_padding = {"padx": 12, "pady": 8}

        file_frame = ttk.LabelFrame(self.root, text="Selected images")
        file_frame.pack(fill=BOTH, expand=False, **root_padding)

        button_row = Frame(file_frame)
        button_row.pack(fill="x", padx=8, pady=8)

        Button(button_row, text="Choose one image", command=self._choose_one_file).pack(
            side=LEFT, padx=(0, 8)
        )
        Button(
            button_row,
            text="Choose multiple images",
            command=self._choose_multiple_files,
        ).pack(side=LEFT, padx=(0, 8))
        Button(button_row, text="Clear list", command=self._clear_files).pack(side=LEFT)

        self.file_list = Listbox(file_frame, height=7)
        self.file_list.pack(fill=BOTH, expand=True, padx=8, pady=(0, 8))

        output_frame = ttk.LabelFrame(self.root, text="Output directory")
        output_frame.pack(fill="x", **root_padding)

        ttk.Entry(output_frame, textvariable=self.output_dir).pack(
            side=LEFT, fill="x", expand=True, padx=8, pady=8
        )
        Button(output_frame, text="Choose folder", command=self._choose_output_dir).pack(
            side=RIGHT, padx=8, pady=8
        )

        operation_frame = ttk.LabelFrame(self.root, text="Operation")
        operation_frame.pack(fill="x", **root_padding)

        operations = (
            "Convert format",
            "Resize",
            "Replace color",
            "Adjust color balance",
        )
        operation_box = ttk.Combobox(
            operation_frame,
            textvariable=self.operation,
            values=operations,
            state="readonly",
        )
        operation_box.pack(fill="x", padx=8, pady=8)
        operation_box.bind("<<ComboboxSelected>>", lambda _event: self._refresh_parameters())

        self.params_frame = ttk.LabelFrame(self.root, text="Parameters")
        self.params_frame.pack(fill="x", **root_padding)

        action_frame = Frame(self.root)
        action_frame.pack(fill="x", padx=12, pady=8)
        Button(action_frame, text="Run processing", command=self._run_processing).pack(
            side=RIGHT
        )

        result_frame = ttk.LabelFrame(self.root, text="Results")
        result_frame.pack(fill=BOTH, expand=True, **root_padding)

        self.result_text = Text(result_frame, height=8, wrap="word")
        self.result_text.pack(fill=BOTH, expand=True, padx=8, pady=8)

    def _refresh_parameters(self) -> None:
        for child in self.params_frame.winfo_children():
            child.destroy()

        operation = self.operation.get()
        if operation == "Convert format":
            self._build_convert_parameters()
        elif operation == "Resize":
            self._build_resize_parameters()
        elif operation == "Replace color":
            self._build_replace_color_parameters()
        elif operation == "Adjust color balance":
            self._build_color_balance_parameters()

    def _build_convert_parameters(self) -> None:
        Label(self.params_frame, text="Output format:").pack(side=LEFT, padx=8, pady=8)
        ttk.Combobox(
            self.params_frame,
            textvariable=self.output_format,
            values=("PNG", "JPEG", "BMP", "TIFF", "WEBP"),
            state="readonly",
            width=12,
        ).pack(side=LEFT, padx=8, pady=8)

    def _build_resize_parameters(self) -> None:
        Label(self.params_frame, text="Width:").pack(side=LEFT, padx=8, pady=8)
        ttk.Entry(self.params_frame, textvariable=self.width, width=10).pack(
            side=LEFT, padx=8, pady=8
        )
        Label(self.params_frame, text="Height:").pack(side=LEFT, padx=8, pady=8)
        ttk.Entry(self.params_frame, textvariable=self.height, width=10).pack(
            side=LEFT, padx=8, pady=8
        )

    def _build_replace_color_parameters(self) -> None:
        Button(
            self.params_frame,
            text="Source color",
            command=lambda: self._choose_color("source"),
        ).pack(side=LEFT, padx=8, pady=8)
        self.source_label = Label(self.params_frame, width=12, text=self._rgb_text(self.source_rgb))
        self.source_label.pack(side=LEFT, padx=8, pady=8)

        Button(
            self.params_frame,
            text="Target color",
            command=lambda: self._choose_color("target"),
        ).pack(side=LEFT, padx=8, pady=8)
        self.target_label = Label(self.params_frame, width=12, text=self._rgb_text(self.target_rgb))
        self.target_label.pack(side=LEFT, padx=8, pady=8)
        self._update_color_labels()

    def _build_color_balance_parameters(self) -> None:
        for label, variable in (
            ("Red", self.red_delta),
            ("Green", self.green_delta),
            ("Blue", self.blue_delta),
        ):
            row = Frame(self.params_frame)
            row.pack(fill="x", padx=8, pady=4)
            Label(row, text=f"{label}:", width=8, anchor="w").pack(side=LEFT)
            ttk.Scale(
                row,
                from_=-255,
                to=255,
                variable=variable,
                orient="horizontal",
            ).pack(side=LEFT, fill="x", expand=True, padx=8)
            Label(row, textvariable=variable, width=5).pack(side=RIGHT)

    def _choose_one_file(self) -> None:
        file_name = filedialog.askopenfilename(filetypes=self._image_filetypes())
        if file_name:
            self.selected_files = [Path(file_name)]
            self._refresh_file_list()

    def _choose_multiple_files(self) -> None:
        file_names = filedialog.askopenfilenames(filetypes=self._image_filetypes())
        if file_names:
            self.selected_files = [Path(file_name) for file_name in file_names]
            self._refresh_file_list()

    def _choose_output_dir(self) -> None:
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)

    def _clear_files(self) -> None:
        self.selected_files.clear()
        self._refresh_file_list()

    def _refresh_file_list(self) -> None:
        self.file_list.delete(0, END)
        for path in self.selected_files:
            self.file_list.insert(END, str(path))

    def _choose_color(self, color_kind: str) -> None:
        _rgb_float, hex_value = colorchooser.askcolor()
        if not hex_value:
            return

        rgb = self._hex_to_rgb(hex_value)
        if color_kind == "source":
            self.source_rgb = rgb
        else:
            self.target_rgb = rgb
        self._update_color_labels()

    def _update_color_labels(self) -> None:
        if hasattr(self, "source_label"):
            self.source_label.config(
                text=self._rgb_text(self.source_rgb),
                background=self._rgb_to_hex(self.source_rgb),
            )
        if hasattr(self, "target_label"):
            self.target_label.config(
                text=self._rgb_text(self.target_rgb),
                background=self._rgb_to_hex(self.target_rgb),
            )

    def _run_processing(self) -> None:
        if not self.selected_files:
            messagebox.showwarning("No images", "Please choose at least one image.")
            return

        if not self.output_dir.get():
            messagebox.showwarning("No output directory", "Please choose an output directory.")
            return

        output_dir = Path(self.output_dir.get())
        try:
            results = self._process_files(output_dir)
        except ValueError as error:
            messagebox.showerror("Invalid parameters", str(error))
            return
        except NotImplementedError as error:
            messagebox.showinfo("Not implemented", str(error))
            self._write_results([str(error)])
            return

        self._write_results(results)
        messagebox.showinfo("Done", "Processing finished.")

    def _process_files(self, output_dir: Path) -> list[str]:
        results: list[str] = []
        operation = self.operation.get()

        for input_path in self.selected_files:
            try:
                image = open_image(input_path)

                if operation == "Convert format":
                    line = self._process_convert(image, input_path, output_dir)
                elif operation == "Resize":
                    line = self._process_resize(image, input_path, output_dir)
                elif operation == "Replace color":
                    line = self._process_replace_color(image, input_path, output_dir)
                elif operation == "Adjust color balance":
                    line = self._process_color_balance(image, input_path, output_dir)
                else:
                    raise ValueError(f"Unknown operation: {operation}")

                results.append(line)
            except NotImplementedError:
                raise
            except Exception as error:
                results.append(f"{input_path.name}: ERROR - {error}")

        return results

    def _process_convert(
        self,
        image,
        input_path: Path,
        output_dir: Path,
    ) -> str:
        output_format = normalize_format(self.output_format.get())
        output_path = build_output_path(
            input_path,
            output_dir,
            suffix=f"_converted_{output_format.lower()}",
            extension=extension_for_format(output_format),
        )
        converted = convert_image(image, output_format)
        save_image(converted, output_path, output_format)
        return (
            f"{input_path.name} -> {output_path.name} | "
            f"original: {file_size_kb(input_path):.2f} KB, "
            f"converted: {file_size_kb(output_path):.2f} KB"
        )

    def _process_resize(self, image, input_path: Path, output_dir: Path) -> str:
        width = self._optional_positive_int(self.width.get(), "width")
        height = self._optional_positive_int(self.height.get(), "height")
        if width is None and height is None:
            raise ValueError("Enter width, height, or both.")

        resized = resize_keep_aspect(image, width=width, height=height)
        output_path = build_output_path(input_path, output_dir, suffix="_resized")
        save_image(resized, output_path, image.format or "PNG")
        return f"{input_path.name} -> {output_path.name}"

    def _process_replace_color(self, image, input_path: Path, output_dir: Path) -> str:
        changed = replace_color(image, self.source_rgb, self.target_rgb)
        output_path = build_output_path(input_path, output_dir, suffix="_color_replaced")
        save_image(changed, output_path, image.format or "PNG")
        return f"{input_path.name} -> {output_path.name}"

    def _process_color_balance(self, image, input_path: Path, output_dir: Path) -> str:
        adjusted = adjust_color_balance(
            image,
            red_delta=self.red_delta.get(),
            green_delta=self.green_delta.get(),
            blue_delta=self.blue_delta.get(),
        )
        output_path = build_output_path(input_path, output_dir, suffix="_balanced")
        save_image(adjusted, output_path, image.format or "PNG")
        return f"{input_path.name} -> {output_path.name}"

    def _write_results(self, lines: list[str]) -> None:
        self.result_text.delete("1.0", END)
        self.result_text.insert(END, "\n".join(lines))

    @staticmethod
    def _optional_positive_int(value: str, field_name: str) -> int | None:
        stripped = value.strip()
        if not stripped:
            return None

        try:
            number = int(stripped)
        except ValueError as error:
            raise ValueError(f"{field_name} must be a whole number.") from error

        if number <= 0:
            raise ValueError(f"{field_name} must be greater than zero.")

        return number

    @staticmethod
    def _image_filetypes() -> list[tuple[str, str]]:
        return [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp"),
            ("All files", "*.*"),
        ]

    @staticmethod
    def _hex_to_rgb(hex_value: str) -> tuple[int, int, int]:
        clean = hex_value.lstrip("#")
        return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)

    @staticmethod
    def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    @staticmethod
    def _rgb_text(rgb: tuple[int, int, int]) -> str:
        return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"
