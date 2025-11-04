import csv
import math
import os
import sys
from itertools import groupby
from operator import itemgetter

from .models import ErrorMetricsSummary


def _yield_cycles(records, read_lengths: tuple[int, int, int] | None = None):
    sorted_records = sorted(map(itemgetter("tile", "cycle", "error_rate"), records))
    max_forward_cycle = read_lengths and read_lengths[0] or sys.maxsize
    min_reverse_cycle = read_lengths and sum(read_lengths[:-1]) + 1 or sys.maxsize
    for record in sorted_records:
        cycle = record[1]
        if cycle >= min_reverse_cycle:
            cycle = min_reverse_cycle - cycle - 1
        elif cycle > max_forward_cycle:
            continue
        rate = round(record[2], 4)
        yield record[0], cycle, rate


def _record_grouper(record):
    # Group by tile and sign of cycle (forward or reverse).
    return (record[0], int(math.copysign(1, record[1])))


def write_phix_csv(out_file, records, read_lengths: tuple[int, int, int] | None = None):
    """Write phiX error rate data to a comma-separated-values file.

    Missing cycles are written with blank error rates, index reads are not
    written, and reverse reads are written with negative cycles.
    :param out_file: an open file to write to
    :param records: a sequence of dictionaries like those yielded from
    read_phix().
    :param read_lengths: a list of lengths for each type of read: forward,
    indexes, and reverse
    :param dict summary: a dictionary to hold the summary values:
    error_rate_fwd and error_rate_rev.
    """
    writer = csv.writer(out_file, lineterminator=os.linesep)
    writer.writerow(["tile", "cycle", "errorrate"])

    error_sums = [0.0, 0.0]
    error_counts = [0, 0]
    for (_tile, sign), group in groupby(
        _yield_cycles(records, read_lengths), _record_grouper
    ):
        previous_cycle = 0
        record = None
        for record in group:
            cycle = record[1]
            previous_cycle += sign
            while previous_cycle * sign < cycle * sign:
                writer.writerow((record[0], previous_cycle, ""))
                previous_cycle += sign
            writer.writerow(record)
            summary_index = (sign + 1) // 2
            error_sums[summary_index] += record[2]
            error_counts[summary_index] += 1
        if read_lengths and record is not None:
            read_length = read_lengths[0] if sign == 1 else -read_lengths[-1]
            while previous_cycle * sign < read_length * sign:
                previous_cycle += sign
                writer.writerow((record[0], previous_cycle, ""))

    return ErrorMetricsSummary(
        error_sum_forward=error_sums[1],
        error_count_forward=error_counts[1],
        error_sum_reverse=error_sums[0],
        error_count_reverse=error_counts[0],
    )
