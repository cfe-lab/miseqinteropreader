import string
from pathlib import Path
from random import Random
from struct import pack
from typing import Any, Iterator

from miseqinteropreader.interop_reader import Metric, MetricFile
from miseqinteropreader.read_records import BinaryFormat


class BaseGenerator:
    def __init__(self):
        self._binary_format = BinaryFormat.HEADER
        self.header_format = "!BB"
        self.header_values = (1, 1)
        self.metricfile = MetricFile.SUMMARY_RUN.value

    def _generate_numeric_sequence(
        self, binary_format: str, rng: Random
    ) -> list[int | float]:
        outlist: list[int | float] = []
        for char in binary_format:
            if char == "<":
                continue
            elif char == "H":
                outlist.append(rng.randint(0, 2**16 - 1))
            elif char == "f":
                outlist.append(rng.random())
            elif char == "L":
                outlist.append(rng.randint(0, 2**32 - 1))
            elif char == "I":
                outlist.append(rng.randint(0, 2**32 - 1))
            elif char == "Q":
                outlist.append(rng.randint(0, 2**64 - 1))
        return outlist

    def generate_row(self, rand: Random) -> list[Any]:
        return self._generate_numeric_sequence(self._binary_format.format, rand)

    def generate_binary(self, row_data: list[list[Any]]) -> Iterator[bytes]:
        for row in row_data:
            yield pack(self._binary_format.format, *row)

    def gen_header(
        self, format: str | None = None, values: tuple | None = None
    ) -> bytes:
        if format is None and values is None:
            return pack(self.header_format, *self.header_values)
        elif format is None and values is not None:
            return pack(self.header_format, *values)
        elif format is not None and values is None:
            return pack(format, *self.header_values)
        else:
            return pack(format, *values)  # type: ignore

    def write_file(
        self, file: Path, header: bytes | None, binary_data: list[bytes] | bytes
    ) -> Path:
        filename = file
        if filename.is_dir():
            filename = file / self.metricfile.files[0]

        with open(filename, mode="wb") as f:
            if header is None:
                f.write(self.gen_header())
            else:
                f.write(header)
            if isinstance(binary_data, list):
                for bin in binary_data:
                    f.write(bin)
            else:
                f.write(binary_data)

        return file


class IndexRecordGenerator(BaseGenerator):
    def __init__(self):
        self.header_format = "!B"
        self.header_values = (1,) # type: ignore
        self.metricfile = MetricFile.INDEX_METRICS.value

    def generate_row(self, rand: Random) -> list[int | bytes]:
        sample_name = "".join(
            rand.choices(string.ascii_letters, k=rand.randint(1, 100))
        ).encode()
        index_name = "".join(
            rand.choices(string.ascii_letters, k=rand.randint(1, 100))
        ).encode()
        project_name = "".join(
            rand.choices(string.ascii_letters, k=rand.randint(1, 100))
        ).encode()
        data: list[int | bytes] = [
            rand.randint(0, 2**16 - 1),
            rand.randint(0, 2**16 - 1),
            rand.randint(0, 2**16 - 1),
            len(index_name),
            index_name,
            rand.randint(0, 2**16 - 1),
            len(sample_name),
            sample_name,
            len(project_name),
            project_name,
        ]

        return data

    def generate_binary(self, row_data: list[list[Any]]) -> Iterator[bytes]:
        for row in row_data:
            bytepack = [
                "<HHH",
                "H" + f"{row[3]}s",  # type: ignore
                "I",
                "H" + f"{row[6]}s",  # type: ignore
                "H" + f"{row[8]}s",  # type: ignore
            ]
            data = pack("".join(bytepack), *row)
            yield data


class QualityRecordGenerator(BaseGenerator):
    def __init__(self):
        self._binary_format = BinaryFormat.QUALITY
        self.header_format = "!BB"
        self.header_values = (
            self._binary_format.min_version,
            self._binary_format.length,
        )
        self.metricfile = MetricFile.QUALITY_METRICS.value

class ErrorRecordGenerator(BaseGenerator):
    def __init__(self):
        self._binary_format = BinaryFormat.ERROR
        self.header_format = "!BB"
        self.header_values = (
            self._binary_format.min_version,
            self._binary_format.length,
        )
        self.metricfile = MetricFile.ERROR_METRICS.value

class TileRecordGenerator(BaseGenerator):
    def __init__(self):
        self._binary_format = BinaryFormat.TILE
        self.header_format = "!BB"
        self.header_values = (
            self._binary_format.min_version,
            self._binary_format.length,
        )
        self.metricfile = MetricFile.TILE_METRICS.value

class ExtendedTileRecordGenerator(BaseGenerator):
    def __init__(self):
        self._binary_format = BinaryFormat.TILE
        self.header_format = "!BB"
        self.header_values = (
            self._binary_format.min_version,
            self._binary_format.length,
        )
        self.metricfile = MetricFile.EXTENDED_TILE_METRICS.value

class CorrectedIntensityRecordGenerator(BaseGenerator):
    def __init__(self):
        self._binary_format = BinaryFormat.CORRECTEDINTENSITY
        self.header_format = "!BB"
        self.header_values = (
            self._binary_format.min_version,
            self._binary_format.length,
        )
        self.metricfile = MetricFile.CORRECTED_INTENSITY_METRICS.value

class ExtractionRecordGenerator(BaseGenerator):
    def __init__(self):
        self._binary_format = BinaryFormat.EXTRACTION
        self.header_format = "!BB"
        self.header_values = (
            self._binary_format.min_version,
            self._binary_format.length,
        )
        self.metricfile = MetricFile.EXTRACTION_METRICS.value


    def generate_row(self, rand: Random) -> list[Any]:
        # special handling for this one as the date format is a bit whacky
        row = self._generate_numeric_sequence(self._binary_format.format, rand)
        row[-1] = 2**48 + rand.randint(0, 2**32)
        return row

class ImageRecordGenerator(BaseGenerator):
    def __init__(self):
        self._binary_format = BinaryFormat.IMAGE
        self.header_format = "!BB"
        self.header_values = (
            self._binary_format.min_version,
            self._binary_format.length,
        )
        self.metricfile = MetricFile.IMAGE_METRICS.value


class PhasingRecordGenerator(BaseGenerator):
    def __init__(self):
        self._binary_format = BinaryFormat.PHASING
        self.header_format = "!BB"
        self.header_values = (
            self._binary_format.min_version,
            self._binary_format.length,
        )
        self.metricfile = MetricFile.PHASING_METRICS.value


class CollapsedQRecordGenerator(BaseGenerator):
    def __init__(self):
        self._binary_format = BinaryFormat.COLLAPSEDQ
        self.header_format = "!BB"
        self.header_values = (
            self._binary_format.min_version,
            self._binary_format.length,
        )
        self.metricfile = MetricFile.COLLAPSED_Q_METRICS.value
