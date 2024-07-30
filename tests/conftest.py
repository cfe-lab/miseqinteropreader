import string
from pathlib import Path
from random import Random
from struct import pack

import pytest
from miseqinteropreader.interoptestgenerator import (
    CollapsedQRecordGenerator,
    CorrectedIntensityRecordGenerator,
    ErrorRecordGenerator,
    ExtractionRecordGenerator,
    ImageRecordGenerator,
    IndexRecordGenerator,
    PhasingRecordGenerator,
    QualityRecordGenerator,
    TileRecordGenerator,
)
from miseqinteropreader.read_records import BinaryFormat

num_rows = [
    pytest.param(1, id="1 row"),
    pytest.param(5, id="5 rows"),
    pytest.param(10, id="10 rows"),
    pytest.param(100, id="100 rows"),
]

@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / "MiSeq" / "Runs" / "012345_M01234_0123_000000000-ABCDE"
    run_dir.mkdir(parents=True)

    interop_dir = run_dir / "InterOp"
    interop_dir.mkdir()

    needsprocessing_marker = run_dir / "needsprocessing"
    needsprocessing_marker.touch()
    qc_uploaded_marker = run_dir / "qc_uploaded"
    qc_uploaded_marker.touch()

    return run_dir

@pytest.fixture
def rng() -> Random:
    return Random()

# tile metrics/extended tile metrics

@pytest.fixture(scope="session")
def tile_metric_generator() -> TileRecordGenerator:
    return TileRecordGenerator()

@pytest.fixture(params=num_rows)
def tile_metric_row(request: pytest.FixtureRequest, tile_metric_generator: TileRecordGenerator, rng: Random) -> list[list[int | float]]:
    return [tile_metric_generator.generate_row(rng) for _ in range(request.param)]

@pytest.fixture
def tile_metric_bytes(tile_metric_generator: TileRecordGenerator, tile_metric_row: list[list[int | float]]) -> list[bytes]:
    return list(tile_metric_generator.generate_binary(tile_metric_row))

@pytest.fixture
def tile_metric_file(tile_metric_generator: TileRecordGenerator, run_dir: Path, tile_metric_bytes: list[bytes]) -> Path:
    file = run_dir / "InterOp" / "TileMetricsOut.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    tile_metric_generator.write_file(file, None, tile_metric_bytes)
    return file

# error metrics

@pytest.fixture(scope="session")
def error_metric_generator() -> ErrorRecordGenerator:
    return ErrorRecordGenerator()

@pytest.fixture(params=num_rows)
def error_metric_row(request: pytest.FixtureRequest, error_metric_generator: ErrorRecordGenerator, rng: Random) -> list[list[int | float]]:
    return [error_metric_generator.generate_row(rng) for _ in range(request.param)]

@pytest.fixture
def error_metric_bytes(error_metric_generator: ErrorRecordGenerator, error_metric_row: list[list[int | float]]) -> list[bytes]:
    return list(error_metric_generator.generate_binary(error_metric_row))

@pytest.fixture
def error_metric_file(error_metric_generator: ErrorRecordGenerator, run_dir: Path, error_metric_bytes: list[bytes]) -> Path:
    file = run_dir / "InterOp" / "ErrorMetricsOut.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    error_metric_generator.write_file(file, None, error_metric_bytes)
    return file

# quality metrics

@pytest.fixture(scope="session")
def quality_metric_generator() -> QualityRecordGenerator:
    return QualityRecordGenerator()

@pytest.fixture(params=num_rows)
def quality_metric_row(request: pytest.FixtureRequest, quality_metric_generator: QualityRecordGenerator, rng: Random) -> list[list[int | float]]:
    return [quality_metric_generator.generate_row(rng) for _ in range(request.param)]

@pytest.fixture
def quality_metric_bytes(quality_metric_generator: QualityRecordGenerator, quality_metric_row: list[list[int | float]]) -> list[bytes]:
    return list(quality_metric_generator.generate_binary(quality_metric_row))

@pytest.fixture
def quality_metric_file(quality_metric_generator: QualityRecordGenerator, run_dir: Path, quality_metric_bytes: list[bytes]) -> Path:
    file = run_dir / "InterOp" / "QualityMetricsOut.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    quality_metric_generator.write_file(file, None, quality_metric_bytes)
    return file


# index metrics

@pytest.fixture(scope="session")
def index_metric_generator() -> IndexRecordGenerator:
    return IndexRecordGenerator()

@pytest.fixture(params=num_rows)
def index_metric_row(request: pytest.FixtureRequest, index_metric_generator: IndexRecordGenerator, rng: Random) -> list[list[int | bytes]]:
    return [index_metric_generator.generate_row(rng) for _ in range(request.param)]

@pytest.fixture
def index_metric_bytes(index_metric_generator: IndexRecordGenerator, index_metric_row: list[list[int | bytes]]) -> list[bytes]:
    return list(index_metric_generator.generate_binary(index_metric_row))

@pytest.fixture
def index_metric_file(index_metric_generator: IndexRecordGenerator, run_dir: Path, index_metric_bytes: list[bytes]) -> Path:
    file = run_dir / "InterOp" / "QualityMetricsOut.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    index_metric_generator.write_file(file, None, index_metric_bytes)
    return file
