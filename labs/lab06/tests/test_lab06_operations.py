import csv
from pathlib import Path

from PIL import Image

from operations import (
    add_brightness_dependent_noise,
    add_coordinate_dependent_noise,
    add_gaussian_noise,
    add_salt_pepper_noise,
    alpha_trimmed_mean_filter,
    calculate_mse,
    FILTERS,
    generate_test_images,
    maximum_filter,
    mean_filter,
    median_filter,
    midpoint_filter,
    minimum_filter,
    prepare_base_image,
    run_filter_analysis,
)


def _checkerboard(size: int = 24) -> Image.Image:
    image = Image.new("RGB", (size, size))
    for y in range(size):
        for x in range(size):
            image.putpixel((x, y), ((x * 10) % 256, (y * 10) % 256, 120))
    return image


# ----- Підготовка базового зображення -----


def test_prepare_base_image_resizes_to_requested_square_rgb() -> None:
    source = Image.new("RGBA", (40, 20), (10, 20, 30, 255))
    result = prepare_base_image(source, size=128)

    assert result.size == (128, 128)
    assert result.mode == "RGB"


# ----- Генерація шуму -----


def test_generate_test_images_produces_nine_images_of_same_size() -> None:
    base = prepare_base_image(_checkerboard(), size=32)
    test_images = generate_test_images(base)

    assert list(test_images.keys()) == ["f0", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8"]
    for image, _noise_type in test_images.values():
        assert image.size == (32, 32)
        assert image.mode == "RGB"


def test_noisy_channels_always_stay_within_0_255() -> None:
    base = prepare_base_image(_checkerboard(), size=32)
    noisy = add_gaussian_noise(base, sigma=60)

    for y in range(noisy.height):
        for x in range(noisy.width):
            for channel in noisy.getpixel((x, y)):
                assert 0 <= channel <= 255


def test_fixed_seed_gives_reproducible_noise() -> None:
    base = prepare_base_image(_checkerboard(), size=32)

    first = add_gaussian_noise(base, sigma=20, seed=42)
    second = add_gaussian_noise(base, sigma=20, seed=42)

    assert first.tobytes() == second.tobytes()


def test_gaussian_noise_changes_the_image() -> None:
    base = prepare_base_image(_checkerboard(), size=32)
    noisy = add_gaussian_noise(base, sigma=10)

    assert noisy.tobytes() != base.tobytes()


def test_stronger_gaussian_noise_differs_more_from_clean_image() -> None:
    base = prepare_base_image(_checkerboard(), size=32)
    weak = add_gaussian_noise(base, sigma=10)
    strong = add_gaussian_noise(base, sigma=25)

    assert calculate_mse(strong, base) > calculate_mse(weak, base)


def test_salt_pepper_noise_introduces_pure_black_and_white_pixels() -> None:
    base = Image.new("RGB", (32, 32), (100, 120, 140))
    noisy = add_salt_pepper_noise(base, probability=0.2)

    pixels = [noisy.getpixel((x, y)) for y in range(32) for x in range(32)]
    assert (0, 0, 0) in pixels
    assert (255, 255, 255) in pixels


def test_brightness_dependent_noise_is_stronger_on_bright_regions() -> None:
    half_dark_half_bright = Image.new("RGB", (20, 20))
    for y in range(20):
        for x in range(20):
            half_dark_half_bright.putpixel((x, y), (10, 10, 10) if x < 10 else (240, 240, 240))

    noisy = add_brightness_dependent_noise(half_dark_half_bright, alpha=5.0, seed=1)

    dark_region = Image.new("RGB", (10, 20), (10, 10, 10))
    bright_region = Image.new("RGB", (10, 20), (240, 240, 240))
    noisy_dark = noisy.crop((0, 0, 10, 20))
    noisy_bright = noisy.crop((10, 0, 20, 20))

    assert calculate_mse(noisy_bright, bright_region) > calculate_mse(noisy_dark, dark_region)


def test_coordinate_dependent_noise_is_stronger_in_bottom_right_corner() -> None:
    flat = Image.new("RGB", (40, 40), (128, 128, 128))
    noisy = add_coordinate_dependent_noise(flat, max_sigma=40, seed=1)

    top_left = flat.crop((0, 0, 8, 8))
    bottom_right = flat.crop((32, 32, 40, 40))
    noisy_top_left = noisy.crop((0, 0, 8, 8))
    noisy_bottom_right = noisy.crop((32, 32, 40, 40))

    assert calculate_mse(noisy_bottom_right, bottom_right) > calculate_mse(noisy_top_left, top_left)


# ----- Лінійні та нелінійні фільтри -----


def _uniform_with_center(values: list[tuple[int, int, int]], size: int = 3) -> Image.Image:
    image = Image.new("RGB", (size, size))
    for index, value in enumerate(values):
        image.putpixel((index % size, index // size), value)
    return image


def test_mean_filter_3x3_averages_all_channels() -> None:
    values = [
        (0, 10, 20), (30, 40, 50), (60, 70, 80),
        (90, 100, 110), (120, 130, 140), (150, 160, 170),
        (180, 190, 200), (210, 220, 230), (240, 250, 255),
    ]
    image = _uniform_with_center(values)

    result = mean_filter(image, window_size=3)

    assert result.getpixel((1, 1)) == (120, 130, 139)


def test_mean_filter_leaves_border_pixels_untouched() -> None:
    image = Image.new("RGB", (5, 5), (10, 20, 30))
    image.putpixel((2, 2), (200, 200, 200))

    result = mean_filter(image, window_size=3)

    assert result.getpixel((0, 0)) == (10, 20, 30)


def test_median_filter_removes_a_single_outlier() -> None:
    gray_values = [1, 2, 3, 4, 255, 6, 7, 8, 9]
    image = _uniform_with_center([(value, value, value) for value in gray_values])

    result = median_filter(image, window_size=3)

    # Відсортовані значення: 1,2,3,4,6,7,8,9,255 — медіана (5-те значення) прибирає викид 255.
    assert result.getpixel((1, 1)) == (6, 6, 6)


def test_minimum_filter_picks_the_smallest_value_per_channel() -> None:
    gray_values = [5, 9, 7, 3, 255, 6, 8, 2, 4]
    image = _uniform_with_center([(value, value, value) for value in gray_values])

    result = minimum_filter(image)

    assert result.getpixel((1, 1)) == (2, 2, 2)


def test_maximum_filter_picks_the_largest_value_per_channel() -> None:
    gray_values = [5, 9, 7, 3, 1, 6, 8, 2, 4]
    image = _uniform_with_center([(value, value, value) for value in gray_values])

    result = maximum_filter(image)

    assert result.getpixel((1, 1)) == (9, 9, 9)


def test_midpoint_filter_averages_min_and_max() -> None:
    gray_values = [5, 9, 7, 3, 1, 6, 8, 2, 100]
    image = _uniform_with_center([(value, value, value) for value in gray_values])

    result = midpoint_filter(image)

    # min=1, max=100 -> (1+100)/2 = 50.5, Python's round() rounds .5 to the nearest even number.
    assert result.getpixel((1, 1)) == (50, 50, 50)


def test_alpha_trimmed_mean_filter_discards_min_and_max() -> None:
    gray_values = [0, 50, 51, 52, 53, 54, 55, 56, 255]
    image = _uniform_with_center([(value, value, value) for value in gray_values])

    naive_average = round(sum(gray_values) / len(gray_values))
    trimmed_average = round(sum(gray_values[1:-1]) / len(gray_values[1:-1]))

    result = alpha_trimmed_mean_filter(image)

    assert result.getpixel((1, 1)) == (trimmed_average, trimmed_average, trimmed_average)
    assert trimmed_average != naive_average


def test_filters_registry_has_three_linear_and_seven_nonlinear() -> None:
    linear = [entry for entry in FILTERS if entry[1] == "linear"]
    nonlinear = [entry for entry in FILTERS if entry[1] == "nonlinear"]

    assert len(linear) == 3
    assert len(nonlinear) == 7
    assert len(FILTERS) == 10


# ----- Метрика якості -----


def test_calculate_mse_is_zero_for_identical_images() -> None:
    image = _checkerboard()

    assert calculate_mse(image, image) == 0


def test_calculate_mse_is_positive_for_different_images() -> None:
    image_a = Image.new("RGB", (4, 4), (0, 0, 0))
    image_b = Image.new("RGB", (4, 4), (10, 10, 10))

    assert calculate_mse(image_a, image_b) > 0


# ----- Інтеграційний smoke test повного аналізу -----


def test_run_filter_analysis_creates_all_expected_outputs(tmp_path: Path) -> None:
    source_image = _checkerboard(size=20)
    output_dir = tmp_path / "lab06_results"

    summary = run_filter_analysis(source_image, output_dir)

    assert summary.test_image_count == 9
    assert summary.filter_count == 10
    assert summary.filtered_result_count == 90

    test_images_dir = output_dir / "test_images"
    for name in ("f0", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8"):
        bmp_path = test_images_dir / f"{name}.bmp"
        assert bmp_path.exists()
        with Image.open(bmp_path) as image:
            assert image.size == (128, 128)

    assert (output_dir / "all_results" / "f0_mean_3x3.png").exists()
    assert (output_dir / "all_results" / "f3_median_3x3.png").exists()

    metrics_path = output_dir / "metrics.csv"
    assert metrics_path.exists()
    with metrics_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert len(rows) == 90
    assert {row["image"] for row in rows} == {f"f{i}" for i in range(9)}

    demonstration_path = output_dir / "demonstration.html"
    assert demonstration_path.exists()
    demonstration_html = demonstration_path.read_text(encoding="utf-8")
    assert "ЛР №6 — оцінка якості фільтрації" in demonstration_html
    assert "all_results/f2_" in demonstration_html
