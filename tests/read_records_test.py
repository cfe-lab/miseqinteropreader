from pathlib import Path

from miseqinteropreader.models import ErrorRecord, TileMetricRecord
from miseqinteropreader.read_records import read_tiles

# import pytest


# mypy: disable-error-code="arg-type"
def test_read_tile_file(
    run_dir: Path, tile_metric_data: list[int | float], tile_metric_file: Path
):
    decoded_data = TileMetricRecord(
        lane=tile_metric_data[0],
        tile=tile_metric_data[1],
        metric_code=tile_metric_data[2],
        metric_value=tile_metric_data[3],
    )

    with open(tile_metric_file, "rb") as f:
        rows = list(read_tiles(f))

        assert len(rows) == 1
        assert rows[0] == decoded_data


def test_read_tile_file_assert_failed_00(
    run_dir: Path, error_metric_data: list[int | float], tile_metric_file: Path
):
    decoded_data = TileMetricRecord(
        lane=0,
        tile=1,
        metric_code=2,
        metric_value=3,
    )

    with open(tile_metric_file, "rb") as f:
        rows = list(read_tiles(f))

        assert len(rows) == 1
        assert rows[0] != decoded_data


def test_read_tile_file_assert_failed_01(
    run_dir: Path, error_metric_data: list[int | float], tile_metric_file: Path
):
    decoded_data = ErrorRecord(
        lane=error_metric_data[0],
        tile=error_metric_data[1],
        cycle=error_metric_data[2],
        error_rate=error_metric_data[3],
        num_0_errors=error_metric_data[4],
        num_1_errors=error_metric_data[5],
        num_2_errors=error_metric_data[6],
        num_3_errors=error_metric_data[7],
        num_4_errors=error_metric_data[8],
    )

    with open(tile_metric_file, "rb") as f:
        rows = list(read_tiles(f))

        assert len(rows) == 1
        assert rows[0] != decoded_data
