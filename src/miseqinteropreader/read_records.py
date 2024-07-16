from enum import Enum
from io import BufferedReader
from struct import unpack
from typing import Iterator

from .models import (
    CorrectedIntensityRecord,
    ErrorRecord,
    ExtractionRecord,
    QualityRecord,
    TileMetricRecord,
)


class BinaryFormat(Enum):
    HEADER = ("!BB", None, None)
    ERROR = ("<HHHfLLLLL", 30, 3)
    TILE = ("<HHHf", 10, 2)
    QUALITY = ("<HHH" + "L" * 50, 206, 4)
    CORRECTEDINTENSITY = ("<HHH" + "H" * 9 + "I" * 5 + "f", 48, 2)
    EXTRACTION = ("<HHHffffHHHHQ", 38, 2)
    IMAGE = ("<HHHHHH", 12, 1)
    PHASING = ("<HHHff", 14, 1)

    def __init__(self, format: str, length: int, min_version: int):
        self.format = format
        self.length = length
        self.min_version = min_version


def read_records(data_file: BufferedReader, min_version: int) -> Iterator[bytes]:
    """Read records from an Illumina Interop file.
    :param file data_file: an open file-like object. Needs to have a two-byte
    header with the file version and the length of each record, followed by the
    records.
    :param int min_version: the minimum accepted file version.
    :return: an iterator over the records in the file. Each record will be a raw
    byte string of the length from the header.
    """
    header = data_file.read(2)
    version, record_length = unpack(BinaryFormat.HEADER.format, header)
    if version < min_version:
        raise IOError(
            "File version {} is less than minimum version {} in {}.".format(
                version, min_version, data_file.name
            )
        )
    while True:
        data = data_file.read(record_length)
        read_length = len(data)
        if read_length == 0:
            break
        if read_length < record_length:
            raise IOError(
                "Partial record of length {} found in {}.".format(
                    read_length, data_file.name
                )
            )
        yield data


def read_errors(data_file: BufferedReader) -> Iterator[ErrorRecord]:
    """Read error rate data from a phiX data file.

    :param file data_file: an open file-like object. Needs to have a two-byte
    header with the file version and the length of each record, followed by the
    records.
    :return: an iterator over the records of data in the file. Each record is a
    dictionary with the following keys:
    - lane [uint16]
    - tile [uint16]
    - cycle [uint16]
    - error_rate [float]
    - num_0_errors [uint32]
    - num_1_error [uint32]
    - num_2_errors [uint32]
    - num_3_errors [uint32]
    - num_4_errors [uint32]
    """
    for data in read_records(data_file, min_version=BinaryFormat.ERROR.min_version):
        fields = unpack(BinaryFormat.ERROR.format, data[: BinaryFormat.ERROR.length])
        yield ErrorRecord(
            lane=fields[0],
            tile=fields[1],
            cycle=fields[2],
            error_rate=fields[3],
            num_0_errors=fields[4],
            num_1_errors=fields[5],
            num_2_errors=fields[6],
            num_3_errors=fields[7],
            num_4_errors=fields[8],
        )


def read_tiles(data_file: BufferedReader) -> Iterator[TileMetricRecord]:
    """Read a tile metrics data file.

    :param file data_file: an open file-like object. Needs to have a two-byte
    header with the file version and the length of each record, followed by the
    records.
    :return: an iterator over the records of data in the file. Each record is a
    dictionary with the following keys:
    - lane [uint16]
    - tile [uint16]
    - metric_code [uint16]
    - metric_value [float32]
    """
    for data in read_records(data_file, min_version=BinaryFormat.TILE.min_version):
        fields = unpack(BinaryFormat.TILE.format, data[: BinaryFormat.TILE.length])
        yield TileMetricRecord(
            lane=fields[0],
            tile=fields[1],
            metric_code=fields[2],
            metric_value=fields[3],
        )


def read_quality(data_file: BufferedReader) -> Iterator[QualityRecord]:
    """Read a quality metrics data file.

    :param file data_file: an open file-like object. Needs to have a two-byte
    header with the file version and the length of each record, followed by the
    records.
    :return: an iterator over the records of data in the file. Each record is a
    dictionary with the following keys:
    - lane [uint16]
    - tile [uint16]
    - cycle [uint16]
    - quality_bins [list of 50 uint32, representing quality 1 to 50]
    """
    for data in read_records(data_file, min_version=BinaryFormat.QUALITY.min_version):
        fields = unpack(
            BinaryFormat.QUALITY.format, data[: BinaryFormat.QUALITY.length]
        )
        yield QualityRecord(
            lane=fields[0],
            tile=fields[1],
            cycle=fields[2],
            quality_bins=list(fields[3:]),
        )


def read_corrected_intensities(
    data_file: BufferedReader,
) -> Iterator[CorrectedIntensityRecord]:
    """Read a Corrected Intensity Metrics data file.

    :param file data_file: an open file-like object. Needs to have a two-byte
    header with the file version and the length of each record, followed by the
    records.
    :return: an iterator over the records of data in the file. Each record is a
    dictionary with the following keys:
    - lane [uint16]
    - tile [uint16]
    - cycle [uint16]
    - average cycle intensity [uint16]
    - average corrected intensity for channel A [uint16]
    - average corrected intensity for channel C [uint16]
    - average corrected intensity for channel G [uint16]
    - average corrected intensity for channel T [uint16]
    - average corrected int for called clusters for base A [uint16]
    - average corrected int for called clusters for base C [uint16]
    - average corrected int for called clusters for base G [uint16]
    - average corrected int for called clusters for base T [uint16]
    - average corrected int for No Call [uint32]
    - average number of base calls for base A [uint32]
    - average number of base calls for base C [uint32]
    - average number of base calls for base G [uint32]
    - average number of base calls for base T [uint32]
    - signal to noise ratio [float32]
    """
    for data in read_records(
        data_file, min_version=BinaryFormat.CORRECTEDINTENSITY.min_version
    ):
        fields = unpack(
            BinaryFormat.CORRECTEDINTENSITY.format,
            data[: BinaryFormat.CORRECTEDINTENSITY.length],
        )
        yield CorrectedIntensityRecord(
            lane=fields[0],
            tile=fields[1],
            cycle=fields[2],
            avg_cycle_intensity=fields[3],
            avg_corrected_intensity_a=fields[4],
            avg_corrected_intensity_c=fields[5],
            avg_corrected_intensity_g=fields[6],
            avg_corrected_intensity_t=fields[7],
            avg_corrected_cluster_intensity_a=fields[8],
            avg_corrected_cluster_intensity_c=fields[9],
            avg_corrected_cluster_intensity_g=fields[10],
            avg_corrected_cluster_intensity_t=fields[11],
            num_base_calls_none=fields[12],
            num_base_calls_a=fields[13],
            num_base_calls_c=fields[14],
            num_base_calls_g=fields[15],
            num_base_calls_t=fields[16],
            snr=fields[17],
        )


def read_extractions(
    data_file: BufferedReader,
) -> Iterator[ExtractionRecord]:
    """Read an Extraction Metrics data file.

    :param file data_file: an open file-like object. Needs to have a two-byte
    header with the file version and the length of each record, followed by the
    records.
    :return: an iterator over the records of data in the file. Each record is a
    dictionary with the following keys:
    - lane [uint16]
    - tile [uint16]
    - cycle [uint16]
    - focus for channel A [float32]
    - focus for channel C [float32]
    - focus for channel G [float32]
    - focus for channel T [float32]
    - max intensity for channel A [uint16]
    - max intensity for channel C [uint16]
    - max intensity for channel G [uint16]
    - max intensity for channel T [uint16]
    - date time stamp [uint64]
    """
    for data in read_records(
        data_file, min_version=BinaryFormat.EXTRACTION.min_version
    ):
        fields = unpack(
            BinaryFormat.EXTRACTION.format,
            data[: BinaryFormat.EXTRACTION.length],
        )
        yield ExtractionRecord(
            lane=fields[0],
            tile=fields[1],
            cycle=fields[2],
            focus_a=fields[3],
            focus_c=fields[4],
            focus_g=fields[5],
            focus_t=fields[6],
            max_intensity_a=fields[7],
            max_intensity_c=fields[8],
            max_intensity_g=fields[9],
            max_intensity_t=fields[10],
            datestamp=fields[11],
        )
