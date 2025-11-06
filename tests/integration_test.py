import os
import re
from pathlib import Path
from random import Random

import pytest

from miseqinteropreader import InterOpReader, MetricFile
from miseqinteropreader.models import ErrorRecord, QualityRecord, TileMetricRecord


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
class TestIntegrations:
    def test_read_interop_dir(self, random_interop_folder: Path):
        ior = InterOpReader(random_interop_folder)
        print(f"Testing with {ior.run_name}")
        files_present = ior.check_files_present(
            {
                MetricFile.ERROR_METRICS,
                MetricFile.QUALITY_METRICS,
                MetricFile.TILE_METRICS,
                MetricFile.INDEX_METRICS,
                # MetricFile.COLLAPSED_Q_METRICS,
                # MetricFile.PHASING_METRICS,
                # MetricFile.IMAGE_METRICS,
                MetricFile.EXTRACTION_METRICS,
            }
        )

        assert files_present
        assert ior.qc_uploaded
        assert ior.needsprocessing

        for metric in [
            MetricFile.ERROR_METRICS,
            MetricFile.QUALITY_METRICS,
            MetricFile.TILE_METRICS,
            MetricFile.SUMMARY_RUN,
            MetricFile.INDEX_METRICS,
            # MetricFile.COLLAPSED_Q_METRICS,
            # MetricFile.PHASING_METRICS,
            # MetricFile.IMAGE_METRICS,
            MetricFile.EXTRACTION_METRICS,
        ]:
            if metric == MetricFile.SUMMARY_RUN:
                with pytest.raises(ReferenceError):
                    records = ior._read_file(metric)
                    for record in records:
                        assert isinstance(record, metric.value.model)
            else:
                records = ior._read_file(metric)
                for record in records:
                    assert isinstance(record, metric.value.model)

    def test_summarize_quality_metrics(self, random_interop_folder: Path):
        ior = InterOpReader(random_interop_folder)
        print(f"Testing with {ior.run_name}")
        files_present = ior.check_files_present({MetricFile.QUALITY_METRICS})

        assert files_present
        assert ior.qc_uploaded
        assert ior.needsprocessing

        records = ior.read_quality_records()
        for record in records:
            assert isinstance(record, QualityRecord)

        summary = ior.summarize_quality_records(records)

        assert summary.total_reverse == 0
        assert summary.total_count > 0
        assert summary.good_count > 0
        assert summary.good_reverse == 0
        assert 0 < summary.q30_forward <= 1
        assert summary.q30_forward == (summary.good_count / summary.total_count)
        assert summary.q30_reverse == 0.0

    def test_summarize_tile_metrics(self, random_interop_folder: Path):
        ior = InterOpReader(random_interop_folder)
        print(f"Testing with {ior.run_name}")
        files_present = ior.check_files_present({MetricFile.TILE_METRICS})

        assert files_present
        assert ior.qc_uploaded
        assert ior.needsprocessing

        tile_records = ior.read_tile_records()
        for tile_record in tile_records:
            assert isinstance(tile_record, TileMetricRecord)

        tile_summary = ior.summarize_tile_records(tile_records)
        assert tile_summary.density_count > 0
        assert tile_summary.density_sum > 0
        assert tile_summary.total_clusters > 0
        assert tile_summary.passing_clusters > 0
        assert 0 < tile_summary.pass_rate <= 1
        assert tile_summary.pass_rate == (
            tile_summary.passing_clusters / tile_summary.total_clusters
        )
        assert tile_summary.cluster_density == (
            tile_summary.density_sum / tile_summary.density_count
        )

        quality_records = ior.read_quality_records()
        for quality_record in quality_records:
            assert isinstance(quality_record, QualityRecord)
        quality_summary = ior.summarize_quality_records(quality_records)

        assert quality_summary.total_count >= 0
        assert quality_summary.total_reverse >= 0
        assert quality_summary.good_count >= 0
        assert quality_summary.good_reverse >= 0
        assert quality_summary.q30_forward >= 0
        assert quality_summary.q30_reverse >= 0

    @pytest.mark.parametrize(
        "metricfile",
        [
            pytest.param(MetricFile.TILE_METRICS, id=MetricFile.TILE_METRICS.name),
            pytest.param(MetricFile.ERROR_METRICS, id=MetricFile.ERROR_METRICS.name),
            pytest.param(
                MetricFile.QUALITY_METRICS, id=MetricFile.QUALITY_METRICS.name
            ),
            pytest.param(
                MetricFile.CORRECTED_INTENSITY_METRICS,
                id=MetricFile.CORRECTED_INTENSITY_METRICS.name,
            ),
            pytest.param(
                MetricFile.EXTRACTION_METRICS,
                id=MetricFile.EXTRACTION_METRICS.name,
            ),
        ],
    )
    def test_summarize_tile_metrics_as_df(
        self, metricfile: MetricFile, random_interop_folder: Path
    ):
        ior = InterOpReader(random_interop_folder)
        print(f"Testing with {ior.run_name}")
        files_present = ior.check_files_present({metricfile})

        assert files_present
        assert ior.qc_uploaded
        assert ior.needsprocessing

        results = ior._read_file(metricfile)
        df = ior.read_file_to_dataframe(metricfile)

        assert len(results) == len(df.index)
        assert list(results[0].model_dump().keys()) == list(df)

        random_rows = []
        rng = Random()
        for i in range(50):
            random_rows.append(rng.randint(0, len(results) - 1))

        for row_id in random_rows:
            result = results[row_id].model_dump()
            result_df = df.iloc[row_id].to_dict(into=dict)

            assert result == result_df
