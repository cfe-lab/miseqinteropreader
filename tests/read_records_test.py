
from pathlib import Path

import pytest
from miseqinteropreader.models import ErrorRecord, IndexRecord, TileMetricRecord
from miseqinteropreader.read_records import read_index, read_tiles


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
