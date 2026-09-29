from pathlib import Path

from app.processor import process_file


SAMPLE_FILE = Path(
    "samples/valid_834.txt"
)

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


def test_successful_processing(monkeypatch):

    saved_members = []

    def fake_save_members(
        members,
        source_file
    ):
        saved_members.extend(members)
        return len(members)

    monkeypatch.setattr(
        "app.processor.save_members",
        fake_save_members
    )

    success, error, count = process_file(
        SAMPLE_FILE,
        CARRIER_CONFIG
    )

    assert success is True
    assert error == ""
    assert count == 2

    assert len(saved_members) == 2


def test_invalid_file_fails(monkeypatch):

    invalid_file = Path(
        "samples/malformed_834.txt"
    )

    success, error, count = process_file(
        invalid_file,
        CARRIER_CONFIG
    )

    assert success is False
    assert count == 0
    assert error != ""