import os
import re
from pathlib import Path
from random import Random

import pytest
from interop_reader import InterOpReader, MetricFile


@pytest.fixture(scope="session")
def seeded_rng() -> Random:
    return Random(12345)


@pytest.fixture
def random_interop_folder(seeded_rng: Random) -> Path:
    runspath = Path("/media/raw_data/MiSeq/runs")
    possible_folders: list[Path] = []
    for folder in runspath.glob("*"):
        if not folder.is_dir():
            continue
        if re.search(r"\d{6}_M\d{5}_\d{4}_0{9}-[A-Z0-0]{5}", folder.name):
            if not (folder / "InterOp").exists():
                continue
            possible_folders.append(folder)

    return seeded_rng.choice(possible_folders)


@pytest.mark.skipif(
    condition=not Path("/media/raw_data/MiSeq/runs").exists(),
    reason="Unable to perform test without access to the raw_data drive",
)
@pytest.mark.skipif(
    condition=os.getenv("CI", None) is not None,
    reason="Unable to perform test in CI.",
)
def test_read_interop_dir(random_interop_folder: Path):
    ior = InterOpReader(random_interop_folder)
    print(f"Testing with {ior.run_name}")
    files_present = ior.check_files_present(
        {MetricFile.ERROR_METRICS, MetricFile.QUALITY_METRICS, MetricFile.TILE_METRICS}
    )

    assert files_present
    assert ior.qc_uploaded
    assert ior.needs_processing

    for metric in [
        MetricFile.ERROR_METRICS,
        MetricFile.QUALITY_METRICS,
        MetricFile.TILE_METRICS,
        MetricFile.SUMMARY_RUN,
    ]:
        if metric == MetricFile.SUMMARY_RUN:
            with pytest.raises(ReferenceError):
                records = ior.read_file(metric)
                for record in records:
                    assert isinstance(record, metric.value.model)
        else:
            records = ior.read_file(metric)
            for record in records:
                assert isinstance(record, metric.value.model)
