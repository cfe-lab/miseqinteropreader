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
def interop_dir(run_dir: Path) -> Path:
    interop_dir = run_dir / "InterOp"
    if not interop_dir.exists():
        interop_dir.mkdir()
    return interop_dir

@pytest.fixture
def rng() -> Random:
    return Random()

@pytest.fixture(params=[
    pytest.param(1, id="1 row per file"),
    pytest.param(5, id="5 row per file"),
    pytest.param(10, id="10 row per file"),
    pytest.param(100, id="100 row per file"),
])
def num_rows(request: pytest.FixtureRequest) -> int:
    return request.param

# tile metrics/extended tile metrics

@pytest.fixture(scope="session")
def tile_metric_generator() -> TileRecordGenerator:
    return TileRecordGenerator()

@pytest.fixture
def tile_metric_row(request: pytest.FixtureRequest, tile_metric_generator: TileRecordGenerator, rng: Random, num_rows: int) -> list[list[int | float]]:
    return [tile_metric_generator.generate_row(rng) for _ in range(num_rows)]

@pytest.fixture
def tile_metric_bytes(tile_metric_generator: TileRecordGenerator, tile_metric_row: list[list[int | float]]) -> list[bytes]:
    return list(tile_metric_generator.generate_binary(tile_metric_row))

@pytest.fixture
def tile_metric_file(tile_metric_generator: TileRecordGenerator, interop_dir: Path, tile_metric_bytes: list[bytes]) -> Path:
    file = interop_dir / "TileMetricsOut.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    tile_metric_generator.write_file(file, None, tile_metric_bytes)
    return file

@pytest.fixture
def extended_tile_metric_file(tile_metric_generator: TileRecordGenerator, interop_dir: Path, tile_metric_bytes: list[bytes]) -> Path:
    file = interop_dir / "ExtendedTileMetrics.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    tile_metric_generator.write_file(file, None, tile_metric_bytes)
    return file

# error metrics

@pytest.fixture(scope="session")
def error_metric_generator() -> ErrorRecordGenerator:
    return ErrorRecordGenerator()

@pytest.fixture
def error_metric_row(request: pytest.FixtureRequest, error_metric_generator: ErrorRecordGenerator, rng: Random, num_rows: int) -> list[list[int | float]]:
    return [error_metric_generator.generate_row(rng) for _ in range(num_rows)]

@pytest.fixture
def error_metric_bytes(error_metric_generator: ErrorRecordGenerator, error_metric_row: list[list[int | float]]) -> list[bytes]:
    return list(error_metric_generator.generate_binary(error_metric_row))

@pytest.fixture
def error_metric_file(error_metric_generator: ErrorRecordGenerator, interop_dir: Path, error_metric_bytes: list[bytes]) -> Path:
    file = interop_dir / "ErrorMetricsOut.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    error_metric_generator.write_file(file, None, error_metric_bytes)
    return file

# quality metrics

@pytest.fixture(scope="session")
def quality_metric_generator() -> QualityRecordGenerator:
    return QualityRecordGenerator()

@pytest.fixture
def quality_metric_row(request: pytest.FixtureRequest, quality_metric_generator: QualityRecordGenerator, rng: Random, num_rows: int) -> list[list[int | float]]:
    return [quality_metric_generator.generate_row(rng) for _ in range(num_rows)]

@pytest.fixture
def quality_metric_bytes(quality_metric_generator: QualityRecordGenerator, quality_metric_row: list[list[int | float]]) -> list[bytes]:
    return list(quality_metric_generator.generate_binary(quality_metric_row))

@pytest.fixture
def quality_metric_file(quality_metric_generator: QualityRecordGenerator, interop_dir: Path, quality_metric_bytes: list[bytes]) -> Path:
    file = interop_dir / "QMetrics.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    quality_metric_generator.write_file(file, None, quality_metric_bytes)
    return file

# collapsed-q metrics

@pytest.fixture(scope="session")
def collapsed_q_generator() -> CollapsedQRecordGenerator:
    return CollapsedQRecordGenerator()


@pytest.fixture
def collapsed_q_metric_row(
    request: pytest.FixtureRequest,
    collapsed_q_generator: CollapsedQRecordGenerator,
    rng: Random, num_rows: int,
) -> list[list[int | float]]:
    return [collapsed_q_generator.generate_row(rng) for _ in range(num_rows)]


@pytest.fixture
def collapsed_q_metric_bytes(
    collapsed_q_generator: CollapsedQRecordGenerator,
    collapsed_q_metric_row: list[list[int | float]],
) -> list[bytes]:
    return list(collapsed_q_generator.generate_binary(collapsed_q_metric_row))


@pytest.fixture
def collapsed_q_metric_file(
    collapsed_q_generator: CollapsedQRecordGenerator,
    interop_dir: Path,
    collapsed_q_metric_bytes: list[bytes],
) -> Path:
    file = interop_dir / "QMetrics2030.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    collapsed_q_generator.write_file(file, None, collapsed_q_metric_bytes)
    return file

# phasing metrics

@pytest.fixture(scope="session")
def phasing_generator() -> PhasingRecordGenerator:
    return PhasingRecordGenerator()


@pytest.fixture
def phasing_metric_row(
    request: pytest.FixtureRequest,
    phasing_generator: PhasingRecordGenerator,
    rng: Random, num_rows: int,
) -> list[list[int | float]]:
    return [phasing_generator.generate_row(rng) for _ in range(num_rows)]


@pytest.fixture
def phasing_metric_bytes(
    phasing_generator: PhasingRecordGenerator,
    phasing_metric_row: list[list[int | float]],
) -> list[bytes]:
    return list(phasing_generator.generate_binary(phasing_metric_row))


@pytest.fixture
def phasing_metric_file(
    phasing_generator: PhasingRecordGenerator,
    interop_dir: Path,
    phasing_metric_bytes: list[bytes],
) -> Path:
    file = interop_dir / "EmpiricalPhasingMetrics.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    phasing_generator.write_file(file, None, phasing_metric_bytes)
    return file

# index metrics

@pytest.fixture(scope="session")
def index_metric_generator() -> IndexRecordGenerator:
    return IndexRecordGenerator()

@pytest.fixture
def index_metric_row(request: pytest.FixtureRequest, index_metric_generator: IndexRecordGenerator, rng: Random, num_rows: int) -> list[list[int | bytes]]:
    return [index_metric_generator.generate_row(rng) for _ in range(num_rows)]

@pytest.fixture
def index_metric_bytes(index_metric_generator: IndexRecordGenerator, index_metric_row: list[list[int | bytes]]) -> list[bytes]:
    return list(index_metric_generator.generate_binary(index_metric_row))

@pytest.fixture
def index_metric_file(index_metric_generator: IndexRecordGenerator, interop_dir: Path, index_metric_bytes: list[bytes]) -> Path:
    file = interop_dir / "IndexMetrics.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    index_metric_generator.write_file(file, None, index_metric_bytes)
    return file

# image metrics

@pytest.fixture(scope="session")
def image_metric_generator() -> ImageRecordGenerator:
    return ImageRecordGenerator()

@pytest.fixture
def image_metric_row(request: pytest.FixtureRequest, image_metric_generator: ImageRecordGenerator, rng: Random, num_rows: int) -> list[list[int | bytes]]:
    return [image_metric_generator.generate_row(rng) for _ in range(num_rows)]

@pytest.fixture
def image_metric_bytes(image_metric_generator: ImageRecordGenerator, image_metric_row: list[list[int | bytes]]) -> list[bytes]:
    return list(image_metric_generator.generate_binary(image_metric_row))

@pytest.fixture
def image_metric_file(image_metric_generator: ImageRecordGenerator, interop_dir: Path, image_metric_bytes: list[bytes]) -> Path:
    file = interop_dir / "ImageMetrics.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    image_metric_generator.write_file(file, None, image_metric_bytes)
    return file

# corrected_intensity metrics

@pytest.fixture(scope="session")
def corrected_intensity_metric_generator() -> CorrectedIntensityRecordGenerator:
    return CorrectedIntensityRecordGenerator()

@pytest.fixture
def corrected_intensity_metric_row(request: pytest.FixtureRequest, corrected_intensity_metric_generator: CorrectedIntensityRecordGenerator, rng: Random, num_rows: int) -> list[list[int | bytes]]:
    return [corrected_intensity_metric_generator.generate_row(rng) for _ in range(num_rows)]

@pytest.fixture
def corrected_intensity_metric_bytes(corrected_intensity_metric_generator: CorrectedIntensityRecordGenerator, corrected_intensity_metric_row: list[list[int | bytes]]) -> list[bytes]:
    return list(corrected_intensity_metric_generator.generate_binary(corrected_intensity_metric_row))

@pytest.fixture
def corrected_intensity_metric_file(corrected_intensity_metric_generator: CorrectedIntensityRecordGenerator, interop_dir: Path, corrected_intensity_metric_bytes: list[bytes]) -> Path:
    file = interop_dir / "CorrectedIntMetrics.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    corrected_intensity_metric_generator.write_file(file, None, corrected_intensity_metric_bytes)
    return file

# extraction metrics

@pytest.fixture(scope="session")
def extraction_metric_generator() -> ExtractionRecordGenerator:
    return ExtractionRecordGenerator()

@pytest.fixture
def extraction_metric_row(request: pytest.FixtureRequest, extraction_metric_generator: ExtractionRecordGenerator, rng: Random, num_rows: int) -> list[list[int | bytes]]:
    return [extraction_metric_generator.generate_row(rng) for _ in range(num_rows)]

@pytest.fixture
def extraction_metric_bytes(extraction_metric_generator: ExtractionRecordGenerator, extraction_metric_row: list[list[int | bytes]]) -> list[bytes]:
    return list(extraction_metric_generator.generate_binary(extraction_metric_row))

@pytest.fixture
def extraction_metric_file(extraction_metric_generator: ExtractionRecordGenerator, interop_dir: Path, extraction_metric_bytes: list[bytes]) -> Path:
    file = interop_dir / "ExtractionMetrics.bin"
    if not file.parent.exists():
        file.parent.mkdir(parents=True)
    extraction_metric_generator.write_file(file, None, extraction_metric_bytes)
    return file
