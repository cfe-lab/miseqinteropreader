from pathlib import Path
from random import Random

import pytest

from miseqinteropreader import InterOpReader, MetricFile
from miseqinteropreader.models import TileMetricRecord


def test_run_dir_missing(tmp_path: Path):
    run_dir = tmp_path / "foobar"

    with pytest.raises(FileNotFoundError):
        InterOpReader(run_dir)


def test_run_dir_missing_02(tmp_path: Path):
    run_dir = tmp_path / "foobar"

    with pytest.raises(FileNotFoundError):
        InterOpReader(str(run_dir))


def test_run_dir_not_a_dir(tmp_path: Path):
    run_dir = tmp_path / "foobar"
    run_dir.touch()

    with pytest.raises(NotADirectoryError):
        InterOpReader(run_dir)


def test_interop_dir_no_samplesheet(tmp_path: Path):
    run_dir = tmp_path / "foobar"
    run_dir.mkdir()

    with pytest.raises(FileNotFoundError):
        InterOpReader(run_dir)


def test_interop_dir_no_interop_dir(tmp_path: Path):
    run_dir = tmp_path / "foobar"
    run_dir.mkdir()
    samplesheet = run_dir / "SampleSheet.csv"
    samplesheet.touch()

    with pytest.raises(FileNotFoundError):
        InterOpReader(run_dir)


def test_interop_dir_missing_file(tmp_path: Path):
    run_dir = tmp_path / "foobar"
    run_dir.mkdir()
    samplesheet = run_dir / "SampleSheet.csv"
    samplesheet.touch()
    interop_dir = run_dir / "InterOp"
    interop_dir.mkdir()

    ior = InterOpReader(run_dir)
    files_present = ior.check_files_present({MetricFile.QUALITY_METRICS})

    assert not files_present


def test_interopreader(run_dir: Path, tile_metric_row: list[list[int | float]], tile_metric_file: Path):
    (run_dir / "SampleSheet.csv").touch()

    ior = InterOpReader(run_dir)
    files_present = ior.check_files_present({MetricFile.TILE_METRICS})

    assert files_present

    records = ior.read_tile_records()

    assert len(records) == len(tile_metric_row)

    for record in records:
        assert isinstance(record, TileMetricRecord)

def test_interopreader_02(
    run_dir: Path,
    tile_metric_row: list[list[int | float]],
    tile_metric_file: Path,
    extended_tile_metric_file: Path,
    extraction_metric_row: list[list[int | float]],
    extraction_metric_file: Path,
    corrected_intensity_metric_row: list[list[int | float]],
    corrected_intensity_metric_file: Path,
    image_metric_row: list[list[int | float]],
    image_metric_file: Path,
    index_metric_row: list[list[int | float]],
    index_metric_file: Path,
    phasing_metric_row: list[list[int | float]],
    phasing_metric_file: Path,
    collapsed_q_metric_row: list[list[int | float]],
    collapsed_q_metric_file: Path,
    quality_metric_row: list[list[int | float]],
    quality_metric_file: Path,
    error_metric_row: list[list[int | float]],
    error_metric_file: Path,
):
    (run_dir / "SampleSheet.csv").touch()

    ior = InterOpReader(run_dir)
    files_present = ior.check_files_present([
        MetricFile.CORRECTED_INTENSITY_METRICS,
        MetricFile.ERROR_METRICS,
        MetricFile.EXTENDED_TILE_METRICS,
        MetricFile.EXTRACTION_METRICS,
        MetricFile.IMAGE_METRICS,
        MetricFile.PHASING_METRICS,
        MetricFile.QUALITY_METRICS,
        MetricFile.TILE_METRICS,
        MetricFile.COLLAPSED_Q_METRICS,
        MetricFile.INDEX_METRICS,


    ])

    assert files_present

    check_records = [
        (tile_metric_row,MetricFile.EXTENDED_TILE_METRICS),
        (tile_metric_row,MetricFile.TILE_METRICS),
        (extraction_metric_row,MetricFile.EXTRACTION_METRICS),
        (corrected_intensity_metric_row,MetricFile.CORRECTED_INTENSITY_METRICS),
        (image_metric_row,MetricFile.IMAGE_METRICS),
        (index_metric_row,MetricFile.INDEX_METRICS),
        (phasing_metric_row,MetricFile.PHASING_METRICS),
        (collapsed_q_metric_row,MetricFile.COLLAPSED_Q_METRICS),
        (quality_metric_row,MetricFile.QUALITY_METRICS),
        (error_metric_row,MetricFile.ERROR_METRICS),
    ]
    for record in check_records:
        data, kind = record
        records = ior._read_file(kind)

        assert len(records) == len(data)

        for row in records:
            assert isinstance(row, kind.value.model)
