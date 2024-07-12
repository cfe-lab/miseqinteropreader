from enum import Enum
from pathlib import Path


class MetricFile(Enum):
    CORRECTED_INTENSITY_METRICS = [
        "CorrectedIntMetrics.bin",
        "CorrectedIntMetricsOut.bin",
    ]
    ERROR_METRICS = ["ErrorMetrics.bin", "ErrorMetricsOut.bin"]
    EXTENDED_TILE_METRICS = ["ExtendedTileMetrics.bin", "ExtendedTileMetricsOut.bin"]
    EXTRACTION_METRICS = ["ExtractionMetrics.bin", "ExtractionMetricsOut.bin"]
    IMAGE_METRICS = ["ImageMetrics.bin", "ImageMetricsOut.bin"]
    PHASING_METRICS = ["EmpiricalPhasingMetrics.bin", "EmpiricalPhasingMetricsOut.bin"]
    QUALITY_METRICS = ["QMetrics.bin", "QMetricsOut.bin"]
    TILE_METRICS = ["TileMetrics.bin", "TileMetricsOut.bin"]
    COLLAPSED_Q_METRICS = ["QMetrics2030.bin", "QMetrics2030Out.bin"]
    SUMMARY_RUN = ["SummaryRun.bin", "SummaryRunOut.bin"]


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
            FileNotFoundError(f"InterOp directory does not exist in {run_dir}")

        needs_processing_marker = run_dir / "needsprocessing"
        qc_uploaded_marker = run_dir / "qc_uploaded"

        self.needs_processing = needs_processing_marker.exists()
        self.qc_uploaded = qc_uploaded_marker.exists()

    def check_files_present(self, metric_files: set[MetricFile]) -> bool:
        for metric_file in metric_files:
            if not any(
                [
                    (self.interop_dir / filename).exists()
                    for filename in MetricFile(metric_file).value
                ]
            ):
                raise FileNotFoundError(
                    f"{'/'.join(MetricFile(metric_file).value)} could not be found in {self.interop_dir}"
                )

        return True
