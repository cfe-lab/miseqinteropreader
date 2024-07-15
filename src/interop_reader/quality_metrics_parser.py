from .read_records import read_quality


def summarize_quality_records(records, summary, read_lengths=None):
    """Calculate the portion of clusters and cycles with quality >= 30.

    :param records: a sequence of dictionaries like those yielded from
    read_quality().
    :param dict summary: a dictionary to hold the summary values:
    q30_fwd and q30_rev. If read_lengths is None, only fwd_q30 will be set.
    :param list read_lengths: a list of lengths for each type of read: forward,
    indexes, and reverse
    """
    good_count = total_count = 0
    good_reverse = total_reverse = 0
    if read_lengths is None:
        last_forward_cycle = first_reverse_cycle = None
    else:
        last_forward_cycle = read_lengths[0]
        first_reverse_cycle = sum(read_lengths[:-1]) + 1
    for record in records:
        cycle = record["cycle"]
        cycle_clusters = sum(record["quality_bins"])
        cycle_good = sum(record["quality_bins"][29:])

        if last_forward_cycle is None or cycle <= last_forward_cycle:
            total_count += cycle_clusters
            good_count += cycle_good
        elif cycle >= first_reverse_cycle:
            total_reverse += cycle_clusters
            good_reverse += cycle_good

    if total_count > 0:
        summary["q30_fwd"] = good_count / float(total_count)
    if total_reverse > 0:
        summary["q30_rev"] = good_reverse / float(total_reverse)


def summarize_quality(filename, summary, read_lengths=None):
    """Summarize the records from a quality metrics file."""
    with open(filename, "rb") as data_file:
        records = read_quality(data_file)
        summarize_quality_records(records, summary, read_lengths)
        records = read_quality(data_file)
        summarize_quality_records(records, summary, read_lengths)
