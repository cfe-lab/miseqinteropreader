from pathlib import Path

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


def test_interopreader(run_dir: Path, tile_metric_file: Path):
    (run_dir / "SampleSheet.csv").touch()

    ior = InterOpReader(run_dir)
    files_present = ior.check_files_present({MetricFile.TILE_METRICS})

    assert files_present

    records = ior.read_file(MetricFile.TILE_METRICS)

    assert len(records) == 1

    for record in records:
        assert isinstance(record, TileMetricRecord)
