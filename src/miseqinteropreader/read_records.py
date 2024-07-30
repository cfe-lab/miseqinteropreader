from enum import Enum
from io import BufferedReader
from struct import unpack
from typing import Any, Iterator

from .models import (
    CollapsedQRecord,
    CorrectedIntensityRecord,
    ErrorRecord,
    ExtractionRecord,
    ImageRecord,
    IndexRecord,
    PhasingRecord,
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
    SUMMARY = ("<Hffff", None, None)
    COLLAPSEDQ = ("<HHHIIII", 22, 2)

    def __init__(self, format: str, length: int, min_version: int):
        self.format = format
        self.length = length
        self.min_version = min_version


def read_records(
    data_file: BufferedReader, min_version: int
) -> Iterator[tuple[bytes, int]]:
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
        raise ValueError(
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
            raise RuntimeError(
                "Partial record of length {} found in {}.".format(
                    read_length, data_file.name
                )
            )
        yield data, record_length


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
    for data, _ in read_records(data_file, min_version=BinaryFormat.ERROR.min_version):
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
    for data, _ in read_records(data_file, min_version=BinaryFormat.TILE.min_version):
        fields = unpack(BinaryFormat.TILE.format, data[: BinaryFormat.TILE.length])
        yield TileMetricRecord(
            lane=fields[0],
            tile=fields[1],
            metric_code=fields[2],
            metric_value=fields[3],
        )


def read_images(data_file: BufferedReader) -> Iterator[ImageRecord]:
    """Read a image metrics metrics data file.

    :param file data_file: an open file-like object. Needs to have a two-byte
    header with the file version and the length of each record, followed by the
    records.
    :return: an iterator over the records of data in the file. Each record is a
    dictionary with the following keys:
    - lane [uint16]
    - tile [uint16]
    - cycle [uint16]
    - channel_number [uint16]
    - minimum_contrast [uint16]
    - maximum_contrast [uint16]
    """
    for data, _ in read_records(data_file, min_version=BinaryFormat.IMAGE.min_version):
        fields = unpack(BinaryFormat.IMAGE.format, data[: BinaryFormat.IMAGE.length])
        yield ImageRecord(
            lane=fields[0],
            tile=fields[1],
            cycle=fields[2],
            channel_number=fields[3],
            min_contrast=fields[4],
            max_contrast=fields[5],
        )


def read_phasing(data_file: BufferedReader) -> Iterator[PhasingRecord]:
    """Read a phasing metrics metrics data file.

    :param file data_file: an open file-like object. Needs to have a two-byte
    header with the file version and the length of each record, followed by the
    records.
    :return: an iterator over the records of data in the file. Each record is a
    dictionary with the following keys:
    - lane [uint16]
    - tile [uint16]
    - cycle [uint16]
    - phasing_weight [float32]
    - prephasing weight [float32]
    """
    for data, _ in read_records(data_file, min_version=BinaryFormat.PHASING.min_version):
        fields = unpack(BinaryFormat.PHASING.format, data[: BinaryFormat.PHASING.length])
        yield PhasingRecord(
            lane=fields[0],
            tile=fields[1],
            cycle=fields[2],
            phasing_weight=fields[3],
            prephasing_weight=fields[4],
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
    for data, _ in read_records(
        data_file, min_version=BinaryFormat.QUALITY.min_version
    ):
        fields = unpack(
            BinaryFormat.QUALITY.format, data[: BinaryFormat.QUALITY.length]
        )
        yield QualityRecord(
            lane=fields[0],
            tile=fields[1],
            cycle=fields[2],
            quality_bins=list(fields[3:]),
        )


def read_collapsed_q_metric(data_file: BufferedReader) -> Iterator[CollapsedQRecord]:
    """Read a Collapsed Q-metrics data file.

    :param file data_file: an open file-like object. Needs to have a two-byte
    header with the file version and the length of each record, followed by the
    records.
    :return: an iterator over the records of data in the file. Each record is a
    dictionary with the following keys:
    - lane [uint16]
    - tile [uint16]
    - cycle [uint16]
    - q20 [uint32]
    - q30 [uint32]
    - total_count [uint32]
    - median_score [uint32]
    """
    # NOTE: this is the only one we need to dynamically check the record length for
    for data, record_length in read_records(
        data_file, min_version=BinaryFormat.COLLAPSEDQ.min_version
    ):
        fields = unpack(BinaryFormat.COLLAPSEDQ.format, data[:record_length])
        yield CollapsedQRecord(
            lane=fields[0],
            tile=fields[1],
            cycle=fields[2],
            q20=fields[3],
            q30=fields[4],
            total_count=fields[5],
            median_score=fields[6],
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
    for data, _ in read_records(
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
    for data, _ in read_records(
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


def read_index(data_file: BufferedReader) -> Iterator[IndexRecord]:
    """Read from the interop index file, this file is a bit more complicated
    than previous files in that it is a variable length packing scheme. We have
    to iterate through each individual row to make sure we get the right size.

    The method for reading this file is quite fragile, so please remember to
    wrap this in a try/except!

    :param BufferedReader data_file: the open file handler to read.
    :return: an iterator over the records in the file. Each record will be a raw
    byte string of the length from the header.
    """

    header = data_file.read(1)
    version = unpack("<B", header)[0]
    if version < 1:
        raise ValueError(
            "File version {} is less than minimum version {} in {}.".format(
                version, 1, data_file.name
            )
        )
    while True:
        metric = data_file.read(6)
        if len(metric) == 0:
            break
        elif len(metric) < 6:
            raise RuntimeError("Partial record for index file, breaking.")
        lane, tile, read = unpack("<HHH", metric)

        data: dict[str, dict[str, Any]] = {}

        # unfortunately the cluster_count property is embedded in the middle of
        # these other difficult to read bytes.
        cluster_count = -1
        for name in ["index", None, "sample", "project"]:
            if name is None:
                if version == 1:
                    index_cluster_count_bytes = data_file.read(4)
                    cluster_count = unpack("I", index_cluster_count_bytes)[0]
                else:
                    index_cluster_count_bytes = data_file.read(8)
                    print(index_cluster_count_bytes)
                    cluster_count = unpack("Q", index_cluster_count_bytes)[0]
            else:
                data[name] = {}
                data[name]["length_bytes"] = data_file.read(2)
                data[name]["length"] = unpack("H", data[name]["length_bytes"])[0]
                data[name]["name_bytes"] = data_file.read(data[name]["length"])
                data[name]["name"] = unpack(
                    f"{data[name]['length']}s", data[name]["name_bytes"]
                )[0]

        yield IndexRecord(
            lane_number=lane,
            tile_number=tile,
            read_number=read,
            index_name_b=data["index"]["name"],
            index_name_length=data["index"]["length"],
            index_cluster_count=cluster_count,
            sample_name_b=data["sample"]["name"],
            sample_name_length=data["sample"]["length"],
            project_name_b=data["project"]["name"],
            project_name_length=data["project"]["length"],
        )
