from pathlib import Path

from PIL import Image

from image_io import build_output_path, save_image
from operations import (
    add_text_watermark,
    adjust_color_balance,
    adjust_contrast,
    convert_image,
    crop_selected_area,
    file_size_kb,
    merge_images,
    remove_selected_area,
    replace_color,
    resize_keep_aspect,
    set_transparency,
    split_image,
)


def test_convert_image_to_jpeg_removes_alpha(tmp_path: Path) -> None:
    image = Image.new("RGBA", (2, 2), (100, 20, 10, 128))
    converted = convert_image(image, "JPEG")
    output_path = tmp_path / "converted.jpg"
    save_image(converted, output_path, "JPEG")

    assert converted.mode == "RGB"
    assert output_path.exists()
    assert file_size_kb(output_path) > 0


def test_build_output_path_does_not_overwrite_existing_file(tmp_path: Path) -> None:
    source = tmp_path / "photo.png"
    existing = tmp_path / "photo_converted.png"
    source.write_bytes(b"source")
    existing.write_bytes(b"existing")

    output_path = build_output_path(source, tmp_path, "_converted", ".png")

    assert output_path.name == "photo_converted_1.png"


def test_resize_by_width_keeps_aspect_ratio() -> None:
    result = resize_keep_aspect(Image.new("RGB", (1000, 500)), width=500)

    assert result.size == (500, 250)


def test_resize_by_height_keeps_aspect_ratio() -> None:
    result = resize_keep_aspect(Image.new("RGB", (1000, 500)), height=250)

    assert result.size == (500, 250)


def test_resize_with_width_and_height_uses_given_dimensions() -> None:
    result = resize_keep_aspect(Image.new("RGB", (1000, 500)), width=300, height=300)

    assert result.size == (300, 300)


def test_replace_color_changes_only_matching_pixels() -> None:
    image = Image.new("RGB", (2, 1))
    image.putpixel((0, 0), (255, 0, 0))
    image.putpixel((1, 0), (0, 255, 0))

    result = replace_color(image, (255, 0, 0), (0, 0, 255))

    assert result.getpixel((0, 0)) == (0, 0, 255)
    assert result.getpixel((1, 0)) == (0, 255, 0)


def test_adjust_color_balance_adds_channel_values() -> None:
    result = adjust_color_balance(
        Image.new("RGB", (1, 1), (10, 20, 30)),
        red_delta=5,
        green_delta=-10,
        blue_delta=20,
    )

    assert result.getpixel((0, 0)) == (15, 10, 50)


def test_adjust_color_balance_clamps_lower_bound() -> None:
    result = adjust_color_balance(
        Image.new("RGB", (1, 1), (10, 20, 30)),
        red_delta=-50,
        green_delta=-50,
        blue_delta=-50,
    )

    assert result.getpixel((0, 0)) == (0, 0, 0)


def test_adjust_color_balance_clamps_upper_bound() -> None:
    result = adjust_color_balance(
        Image.new("RGB", (1, 1), (250, 240, 230)),
        red_delta=20,
        green_delta=20,
        blue_delta=40,
    )

    assert result.getpixel((0, 0)) == (255, 255, 255)


def test_set_transparency_keeps_rgb_and_sets_alpha() -> None:
    image = Image.new("RGB", (1, 1), (10, 20, 30))
    result = set_transparency(image, 128)

    assert result.mode == "RGBA"
    assert result.getpixel((0, 0)) == (10, 20, 30, 128)


def test_crop_selected_area_clamps_coordinates() -> None:
    image = Image.new("RGB", (4, 3))
    result = crop_selected_area(image, -2, -1, 10, 2)

    assert result.size == (4, 2)


def test_remove_selected_area_makes_only_area_transparent() -> None:
    image = Image.new("RGB", (3, 2), (20, 30, 40))
    result = remove_selected_area(image, 1, 0, 3, 1)

    assert result.mode == "RGBA"
    assert result.getpixel((1, 0)) == (20, 30, 40, 0)
    assert result.getpixel((0, 1)) == (20, 30, 40, 255)


def test_split_image_returns_exact_number_of_parts_without_losing_pixels() -> None:
    image = Image.new("RGB", (7, 5))
    pieces = split_image(image, 5)

    assert len(pieces) == 5
    assert sum(piece.width * piece.height for piece in pieces) == 35
    assert all(piece.width > 0 and piece.height > 0 for piece in pieces)


def test_adjust_contrast_uses_average_and_keeps_alpha() -> None:
    image = Image.new("RGBA", (2, 1))
    image.putpixel((0, 0), (0, 0, 0, 100))
    image.putpixel((1, 0), (100, 100, 100, 200))

    result = adjust_contrast(image, 2)

    assert result.getpixel((0, 0)) == (0, 0, 0, 100)
    assert result.getpixel((1, 0)) == (150, 150, 150, 200)


def test_merge_images_horizontal_uses_sum_of_widths() -> None:
    first = Image.new("RGB", (2, 3), "red")
    second = Image.new("RGB", (4, 1), "blue")

    result = merge_images(first, second, "Horizontal")

    assert result.size == (6, 3)
    assert result.getpixel((0, 0)) == (255, 0, 0)
    assert result.getpixel((2, 0)) == (0, 0, 255)
    assert result.getpixel((5, 2)) == (255, 255, 255)


def test_merge_images_vertical_uses_sum_of_heights() -> None:
    first = Image.new("RGB", (2, 3), "red")
    second = Image.new("RGB", (4, 1), "blue")

    result = merge_images(first, second, "Vertical")

    assert result.size == (4, 4)
    assert result.getpixel((0, 0)) == (255, 0, 0)
    assert result.getpixel((0, 3)) == (0, 0, 255)
    assert result.getpixel((3, 0)) == (255, 255, 255)


def test_add_text_watermark_returns_rgba_image() -> None:
    result = add_text_watermark(
        Image.new("RGB", (200, 100), "black"),
        "Test",
        "Center",
        255,
        24,
        (255, 255, 255),
    )

    assert result.mode == "RGBA"
    assert result.size == (200, 100)
    assert any(
        result.getpixel((x, y))[:3] == (255, 255, 255)
        for y in range(result.height)
        for x in range(result.width)
    )


def test_add_text_watermark_rejects_invalid_alpha() -> None:
    try:
        add_text_watermark(
            Image.new("RGB", (20, 20)), "Test", "Center", 300, 12, (255, 255, 255)
        )
    except ValueError:
        return
    assert False, "Expected invalid alpha to raise ValueError"
