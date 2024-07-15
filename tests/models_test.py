from contextlib import nullcontext
from typing import Any

import pytest
from interop_reader.models import QualityRecord
from pydantic import ValidationError


@pytest.mark.parametrize(
    "record_length, exp_raises",
    [
        pytest.param(49, pytest.raises(ValidationError), id="quality_bins too small"),
        pytest.param(50, nullcontext(), id="quality_bins right size"),
        pytest.param(51, pytest.raises(ValidationError), id="quality_bins too big"),
    ],
)
def test_quality_record_model(record_length: int, exp_raises: Any):
    with exp_raises:
        record = QualityRecord(
            lane=0, tile=1, cycle=2, quality_bins=[i for i in range(record_length)]
        ).model_dump()

        assert "lane" in record
        assert "tile" in record
        assert "cycle" in record

        # Check that we do have a flat model
        for i in range(record_length):
            assert f"{i:02}" in record

        for k, v in record.items():
            assert isinstance(k, str)
            assert isinstance(v, int)
