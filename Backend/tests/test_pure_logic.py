"""Pure-function tests — no database needed, so these always run fast."""
import uuid

import pytest
from fastapi import HTTPException

from main import _parse_uuid, _is_available_today


class TestParseUuid:
    def test_valid_uuid_string(self):
        value = "6615a115-1ab3-42c7-96ac-ebaa57ca5472"
        assert _parse_uuid(value, "restaurant_id") == uuid.UUID(value)

    @pytest.mark.parametrize("bad_value", ["not-a-uuid", "12345", "", "  ", None])
    def test_malformed_input_raises_422_not_a_db_error(self, bad_value):
        """This is the whole point of _parse_uuid (see its docstring in
        main.py): garbage input must fail as a clean 422 before anything
        ever opens a DB session — not as an unhandled exception."""
        with pytest.raises(HTTPException) as exc_info:
            _parse_uuid(bad_value, "restaurant_id")
        assert exc_info.value.status_code == 422


class TestDayGating:
    def test_ungated_category_always_available(self):
        assert _is_available_today("Recommended", None) is True

    def test_gated_category_matches_string_comparison(self):
        # _is_available_today compares datetime.now().strftime("%A") against
        # required_day verbatim — this locks in that contract so a future
        # refactor (e.g. to weekday() ints) doesn't silently break it.
        import main

        real_today = main.datetime.now().strftime("%A")
        assert _is_available_today("WEDNESDAY EXCLUSIVES", real_today) is True

        other_day = "Monday" if real_today != "Monday" else "Tuesday"
        assert _is_available_today("WEDNESDAY EXCLUSIVES", other_day) is False
