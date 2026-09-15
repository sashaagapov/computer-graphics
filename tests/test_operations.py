from pathlib import Path

import pytest
from PIL import Image

from image_io import build_output_path, save_image
from operations import (
    adjust_color_balance,
    convert_image,
    file_size_kb,
    replace_color,
    resize_keep_aspect,
)


def skip_if_todo(error: NotImplementedError) -> None:
    pytest.skip(str(error))


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
    image = Image.new("RGB", (1000, 500))

    try:
        result = resize_keep_aspect(image, width=500)
    except NotImplementedError as error:
        skip_if_todo(error)

    assert result.size == (500, 250)


def test_resize_by_height_keeps_aspect_ratio() -> None:
    image = Image.new("RGB", (1000, 500))

    try:
        result = resize_keep_aspect(image, height=250)
    except NotImplementedError as error:
        skip_if_todo(error)

    assert result.size == (500, 250)


def test_resize_with_width_and_height_uses_given_dimensions() -> None:
    image = Image.new("RGB", (1000, 500))

    try:
        result = resize_keep_aspect(image, width=300, height=300)
    except NotImplementedError as error:
        skip_if_todo(error)

    assert result.size == (300, 300)


def test_replace_color_changes_only_matching_pixels() -> None:
    image = Image.new("RGB", (2, 1))
    image.putpixel((0, 0), (255, 0, 0))
    image.putpixel((1, 0), (0, 255, 0))

    try:
        result = replace_color(image, (255, 0, 0), (0, 0, 255))
    except NotImplementedError as error:
        skip_if_todo(error)

    assert result.getpixel((0, 0)) == (0, 0, 255)
    assert result.getpixel((1, 0)) == (0, 255, 0)


def test_adjust_color_balance_adds_channel_values() -> None:
    image = Image.new("RGB", (1, 1), (10, 20, 30))

    try:
        result = adjust_color_balance(image, red_delta=5, green_delta=-10, blue_delta=20)
    except NotImplementedError as error:
        skip_if_todo(error)

    assert result.getpixel((0, 0)) == (15, 10, 50)


def test_adjust_color_balance_clamps_lower_bound() -> None:
    image = Image.new("RGB", (1, 1), (10, 20, 30))

    try:
        result = adjust_color_balance(image, red_delta=-50, green_delta=-50, blue_delta=-50)
    except NotImplementedError as error:
        skip_if_todo(error)

    assert result.getpixel((0, 0)) == (0, 0, 0)


def test_adjust_color_balance_clamps_upper_bound() -> None:
    image = Image.new("RGB", (1, 1), (250, 240, 230))

    try:
        result = adjust_color_balance(image, red_delta=20, green_delta=20, blue_delta=40)
    except NotImplementedError as error:
        skip_if_todo(error)

    assert result.getpixel((0, 0)) == (255, 255, 255)
