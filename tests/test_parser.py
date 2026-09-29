from pathlib import Path

from app.parser import (
    parse_834,
    read_edi_file,
)


SAMPLE_FILE = "samples/valid_834.txt"

CARRIER_CONFIG = {
    "carrier_name": "ABC Health",
    "transaction_type": "834",
    "mapping": {
        "member_id": {
            "segment": "NM1",
            "element": 9
        },
        "first_name": {
            "segment": "NM1",
            "element": 4
        },
        "last_name": {
            "segment": "NM1",
            "element": 3
        },
        "date_of_birth": {
            "segment": "DMG",
            "element": 2
        },
        "gender": {
            "segment": "DMG",
            "element": 3
        },
        "health_plan": {
            "segment": "HD",
            "element": 3
        },
        "effective_date": {
            "segment": "DTP",
            "element": 3,
            "qualifier_element": 1,
            "qualifier_value": "348"
        }
    }
}


def test_read_edi_file():

    segments = read_edi_file(
        SAMPLE_FILE
    )

    assert len(segments) > 0
    assert segments[0].startswith("ISA")
    assert segments[-1].startswith("IEA")


def test_parse_834():

    members = parse_834(
        SAMPLE_FILE,
        CARRIER_CONFIG
    )

    assert len(members) == 2

    assert members[0]["member_id"] == "10001"
    assert members[0]["first_name"] == "JOHN"
    assert members[0]["last_name"] == "DOE"

    assert members[1]["member_id"] == "10002"
    assert members[1]["first_name"] == "JANE"
    assert members[1]["last_name"] == "SMITH"


def test_parse_834_returns_expected_fields():

    members = parse_834(
        SAMPLE_FILE,
        CARRIER_CONFIG
    )

    expected_fields = {
        "member_id",
        "first_name",
        "last_name",
        "date_of_birth",
        "gender",
        "health_plan",
        "effective_date",
    }

    assert set(members[0].keys()) == expected_fields