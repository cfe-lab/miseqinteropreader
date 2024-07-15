import logging
from enum import Enum
from io import BufferedReader
from pathlib import Path
from typing import Callable, Iterator

from pydantic import BaseModel

from interop_reader.read_records import read_errors, read_quality, read_tiles

from .models import (
    BaseMetric,
    CorrectedIntensityRecord,
    ErrorRecord,
    ExtractionRecord,
    ImageRecord,
    PhasingRecord,
    QualityRecord,
    TileMetricRecord,
)


class Metric(BaseModel):
    files: list[str]
    model: type[BaseMetric]
    read_method: Callable[[BufferedReader], Iterator[BaseMetric]] | None = None

    def get_file(self, interop_dir: Path) -> Path:
        for filename in self.files:
            if (interop_dir / filename).exists():
                return interop_dir / filename
        raise FileNotFoundError(
            f"Could not find {'/'.join(self.files)} in {interop_dir}"
        )

    def read_file(self, interop_dir: Path) -> list[BaseMetric]:
        if self.read_method is None:
            raise ReferenceError("No associated read method for this type!")
        with open(self.get_file(interop_dir), mode="rb") as f:
            return list(self.read_method(f))


class MetricFile(Enum):
    CORRECTED_INTENSITY_METRICS = Metric(
        files=[
            "CorrectedIntMetrics.bin",
            "CorrectedIntMetricsOut.bin",
        ],
        model=CorrectedIntensityRecord,
    )
    ERROR_METRICS = Metric(
        files=["ErrorMetrics.bin", "ErrorMetricsOut.bin"],
        model=ErrorRecord,
        read_method=read_errors,
    )
    EXTENDED_TILE_METRICS = Metric(
        files=["ExtendedTileMetrics.bin", "ExtendedTileMetricsOut.bin"],
        model=TileMetricRecord,
        read_method=read_tiles,
    )
    EXTRACTION_METRICS = Metric(
        files=["ExtractionMetrics.bin", "ExtractionMetricsOut.bin"],
        model=ExtractionRecord,
    )
    IMAGE_METRICS = Metric(
        files=["ImageMetrics.bin", "ImageMetricsOut.bin"],
        model=ImageRecord,
    )
    PHASING_METRICS = Metric(
        files=["EmpiricalPhasingMetrics.bin", "EmpiricalPhasingMetricsOut.bin"],
        model=PhasingRecord,
    )
    QUALITY_METRICS = Metric(
        files=["QMetrics.bin", "QMetricsOut.bin"],
        model=QualityRecord,
        read_method=read_quality,
    )
    TILE_METRICS = Metric(
        files=["TileMetrics.bin", "TileMetricsOut.bin"],
        model=TileMetricRecord,
        read_method=read_tiles,
    )
    COLLAPSED_Q_METRICS = Metric(
        files=["QMetrics2030.bin", "QMetrics2030Out.bin"],
        model=QualityRecord,
    )
    SUMMARY_RUN = Metric(
        files=["SummaryRun.bin", "SummaryRunOut.bin"],
        model=BaseMetric,
    )


class InterOpReader:
    def __init__(self, run_dir: str | Path):
        if isinstance(run_dir, str):
            run_dir = Path(run_dir)

        if not run_dir.exists():
            raise FileNotFoundError("Filepath does not exist.")
        if not run_dir.is_dir():
            raise NotADirectoryError("Filepath provided is not a directory.")

        samplesheet_path = run_dir / "SampleSheet.csv"
        if not samplesheet_path.exists():
            raise FileNotFoundError(f"SampleSheet.csv does not exist in {run_dir}")

        interop_dir = run_dir / "InterOp"
        if interop_dir.exists() and interop_dir.is_dir():
            self.interop_dir = interop_dir
        else:
            raise FileNotFoundError(f"InterOp directory does not exist in {run_dir}")

        needs_processing_marker = run_dir / "needsprocessing"
        qc_uploaded_marker = run_dir / "qc_uploaded"

        self.run_name = run_dir.name
        self.needs_processing = needs_processing_marker.exists()
        self.qc_uploaded = qc_uploaded_marker.exists()

    def check_files_present(self, metric_files: set[MetricFile]) -> bool:
        try:
            for metric in metric_files:
                metric.value.get_file(self.interop_dir)
            return True
        except FileNotFoundError as e:
            logging.error(e)
            return False

    def read_file(self, metric: MetricFile) -> list[BaseMetric]:
        return metric.value.read_file(self.interop_dir)
