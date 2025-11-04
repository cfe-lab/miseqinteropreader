
from pathlib import Path

import pytest

from miseqinteropreader.models import (
    CollapsedQRecord,
    CorrectedIntensityRecord,
    ErrorRecord,
    ExtractionRecord,
    ImageRecord,
    IndexRecord,
    PhasingRecord,
    TileMetricRecord,
)
from miseqinteropreader.read_records import (
    read_collapsed_q_metric,
    read_corrected_intensities,
    read_extractions,
    read_images,
    read_index,
    read_phasing,
    read_tiles,
)


# mypy: disable-error-code="arg-type"
def test_read_tile_file(
    run_dir: Path, tile_metric_row: list[list[int | float]], tile_metric_file: Path
):
    decoded_data = TileMetricRecord(
        lane=tile_metric_row[0][0],
        tile=tile_metric_row[0][1],
        metric_code=tile_metric_row[0][2],
        metric_value=tile_metric_row[0][3],
    )

    with open(tile_metric_file, "rb") as f:
        rows = list(read_tiles(f))

        assert len(rows) == len(tile_metric_row)
        assert rows[0] == decoded_data


def test_read_tile_file_assert_failed_00(
    run_dir: Path, tile_metric_row: list[list[int | float]], tile_metric_file: Path
):
    decoded_data = TileMetricRecord(
        lane=1,
        tile=2,
        metric_code=3,
        metric_value=4,
    )

    with open(tile_metric_file, "rb") as f:
        rows = list(read_tiles(f))

        assert len(rows) == len(tile_metric_row)
        assert rows[0] != decoded_data


def test_read_tile_file_assert_failed_01(
    run_dir: Path, error_metric_row: list[list[int | float]], tile_metric_row: list[list[int | float]], tile_metric_file: Path
):
    # decoded_data is a different type to expected TileRecord
    decoded_data = ErrorRecord(
        lane=error_metric_row[0][0],
        tile=error_metric_row[0][1],
        cycle=error_metric_row[0][2],
        error_rate=error_metric_row[0][3],
        num_0_errors=error_metric_row[0][4],
        num_1_errors=error_metric_row[0][5],
        num_2_errors=error_metric_row[0][6],
        num_3_errors=error_metric_row[0][7],
        num_4_errors=error_metric_row[0][8],
    )

    with open(tile_metric_file, "rb") as f:
        rows = list(read_tiles(f))

        assert len(rows) == len(tile_metric_row)
        assert rows[0] != decoded_data


def test_read_index(
    run_dir: Path, index_metric_row: list[list[int | bytes]], index_metric_file: Path
):
    decoded_data = IndexRecord(
        lane_number=index_metric_row[0][0],
        tile_number=index_metric_row[0][1],
        read_number=index_metric_row[0][2],
        index_name_length=index_metric_row[0][3],
        index_name_b=index_metric_row[0][4],
        index_cluster_count=index_metric_row[0][5],
        sample_name_length=index_metric_row[0][6],
        sample_name_b=index_metric_row[0][7],
        project_name_length=index_metric_row[0][8],
        project_name_b=index_metric_row[0][9],
    )

    assert decoded_data.index_name == index_metric_row[0][4].decode()  # type: ignore
    assert decoded_data.sample_name == index_metric_row[0][7].decode()  # type: ignore
    assert decoded_data.project_name == index_metric_row[0][9].decode()  # type: ignore

    with open(index_metric_file, mode="rb") as f:
        rows = list(read_index(f))

        assert len(rows) == len(index_metric_row)
        assert rows[0] == decoded_data

def test_read_collapsed_q(
    run_dir: Path, collapsed_q_metric_row: list[list[int | bytes]], collapsed_q_metric_file: Path
):
    decoded_data = CollapsedQRecord(
        lane=collapsed_q_metric_row[0][0],
        tile=collapsed_q_metric_row[0][1],
        cycle=collapsed_q_metric_row[0][2],
        q20=collapsed_q_metric_row[0][3],
        q30=collapsed_q_metric_row[0][4],
        total_count=collapsed_q_metric_row[0][5],
        median_score=collapsed_q_metric_row[0][6],
    )

    with open(collapsed_q_metric_file, mode="rb") as f:
        rows = list(read_collapsed_q_metric(f))

        assert len(rows) == len(collapsed_q_metric_row)
        assert rows[0] == decoded_data

def test_read_corrected_intensity(
    run_dir: Path, corrected_intensity_metric_row: list[list[int | bytes]], corrected_intensity_metric_file: Path
):
    decoded_data = CorrectedIntensityRecord(
        lane=corrected_intensity_metric_row[0][0],
        tile=corrected_intensity_metric_row[0][1],
        cycle=corrected_intensity_metric_row[0][2],
        avg_cycle_intensity=corrected_intensity_metric_row[0][3],
        avg_corrected_intensity_a=corrected_intensity_metric_row[0][4],
        avg_corrected_intensity_c=corrected_intensity_metric_row[0][5],
        avg_corrected_intensity_g=corrected_intensity_metric_row[0][6],
        avg_corrected_intensity_t=corrected_intensity_metric_row[0][7],
        avg_corrected_cluster_intensity_a=corrected_intensity_metric_row[0][8],
        avg_corrected_cluster_intensity_c=corrected_intensity_metric_row[0][9],
        avg_corrected_cluster_intensity_g=corrected_intensity_metric_row[0][10],
        avg_corrected_cluster_intensity_t=corrected_intensity_metric_row[0][11],
        num_base_calls_none=corrected_intensity_metric_row[0][12],
        num_base_calls_a=corrected_intensity_metric_row[0][13],
        num_base_calls_c=corrected_intensity_metric_row[0][14],
        num_base_calls_g=corrected_intensity_metric_row[0][15],
        num_base_calls_t=corrected_intensity_metric_row[0][16],
        snr=corrected_intensity_metric_row[0][17],
    )

    with open(corrected_intensity_metric_file, mode="rb") as f:
        rows = list(read_corrected_intensities(f))

        assert len(rows) == len(corrected_intensity_metric_row)
        assert rows[0] == decoded_data

def test_read_extraction(
    run_dir: Path, extraction_metric_row: list[list[int | bytes]], extraction_metric_file: Path
):
    decoded_data = ExtractionRecord(
        lane=extraction_metric_row[0][0],
        tile=extraction_metric_row[0][1],
        cycle=extraction_metric_row[0][2],
        focus_a=extraction_metric_row[0][3],
        focus_c=extraction_metric_row[0][4],
        focus_g=extraction_metric_row[0][5],
        focus_t=extraction_metric_row[0][6],
        max_intensity_a=extraction_metric_row[0][7],
        max_intensity_c=extraction_metric_row[0][8],
        max_intensity_g=extraction_metric_row[0][9],
        max_intensity_t=extraction_metric_row[0][10],
        datestamp=extraction_metric_row[0][11],
    )

    with open(extraction_metric_file, mode="rb") as f:
        rows = list(read_extractions(f))

        assert len(rows) == len(extraction_metric_row)
        assert rows[0] == decoded_data

def test_read_image(
    run_dir: Path, image_metric_row: list[list[int | bytes]], image_metric_file: Path
):
    decoded_data = ImageRecord(
        lane=image_metric_row[0][0],
        tile=image_metric_row[0][1],
        cycle=image_metric_row[0][2],
        channel_number=image_metric_row[0][3],
        min_contrast=image_metric_row[0][4],
        max_contrast=image_metric_row[0][5],
    )

    with open(image_metric_file, mode="rb") as f:
        rows = list(read_images(f))

        assert len(rows) == len(image_metric_row)
        assert rows[0] == decoded_data

def test_read_phasing(
    run_dir: Path, phasing_metric_row: list[list[int | bytes]], phasing_metric_file: Path
):
    decoded_data = PhasingRecord(
        lane=phasing_metric_row[0][0],
        tile=phasing_metric_row[0][1],
        cycle=phasing_metric_row[0][2],
        phasing_weight=phasing_metric_row[0][3],
        prephasing_weight=phasing_metric_row[0][4],
    )

    with open(phasing_metric_file, mode="rb") as f:
        rows = list(read_phasing(f))

        assert len(rows) == len(phasing_metric_row)
        assert rows[0] == decoded_data
