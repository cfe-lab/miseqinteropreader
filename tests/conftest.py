from pathlib import Path
from random import Random
from struct import pack

import pytest

from interop_reader.read_records import BinaryFormat


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


def generate_numeric_sequence(binary_format: str) -> list[int | float]:
    rng = Random()
    outlist: list[int | float] = []
    for char in binary_format:
        if char == "<":
            continue
        elif char == "H":
            outlist.append(rng.randint(0, 2**16 - 1))
        elif char == "f":
            outlist.append(rng.random())
        elif char == "L":
            outlist.append(rng.randint(0, 2**64 - 1))
    return outlist


@pytest.fixture
def tile_metric_data() -> list[int | float]:
    return generate_numeric_sequence(BinaryFormat.TILE.format)


@pytest.fixture
def tile_metric_row(tile_metric_data: list[int | float]) -> bytes:
    return pack(BinaryFormat.TILE.format, *tile_metric_data)


@pytest.fixture
def error_metric_data() -> list[int | float]:
    return generate_numeric_sequence(BinaryFormat.ERROR.format)


@pytest.fixture
def error_metric_row(error_metric_data: list[int | float]) -> bytes:
    return pack(BinaryFormat.ERROR.format, *error_metric_data)


@pytest.fixture
def quality_metric_data() -> list[int | float]:
    return generate_numeric_sequence(BinaryFormat.QUALITY.format)


@pytest.fixture
def quality_metric_row(quality_metric_data: list[int | float]) -> bytes:
    return pack(
        BinaryFormat.QUALITY.format,
        *quality_metric_data,
    )


@pytest.fixture
def tile_metric_file(run_dir: Path, tile_metric_row: bytes) -> Path:
    file = run_dir / "InterOp" / "TileMetricOut.bin"
    with open(file, "wb") as f:
        f.write(pack("!BB", BinaryFormat.TILE.min_version, BinaryFormat.TILE.length))
        f.write(tile_metric_row)
    print(file.read_bytes())

    return file
