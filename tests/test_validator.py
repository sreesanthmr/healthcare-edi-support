from app.parser import read_edi_file
from app.validator import (
    validate_edi_envelope,
    validate_member,
)


VALID_FILE = "samples/valid_834.txt"


def test_valid_edi_envelope():

    segments = read_edi_file(
        VALID_FILE
    )

    errors = validate_edi_envelope(
        segments
    )

    assert errors == []


def test_missing_required_envelope_segments():

    segments = [
        "NM1*IL*1*DOE*JOHN****MI*10001",
        "DMG*D8*19900115*M",
    ]

    errors = validate_edi_envelope(
        segments
    )

    assert "Missing required segment: ISA" in errors
    assert "Missing required segment: GS" in errors
    assert "Missing required segment: ST" in errors


def test_wrong_transaction_type():

    segments = [
        "ISA*00*",
        "GS*BE*",
        "ST*837*0001",
        "SE*1*0001",
        "GE*1*1",
        "IEA*1*000000001",
    ]

    errors = validate_edi_envelope(
        segments
    )

    assert (
        "Unsupported transaction type: 837"
        in errors
    )


def test_mismatched_control_number():

    segments = [
        "ISA*00*",
        "GS*BE*CARRIER*CLIENT*20260930*1200*1*X*005010",
        "ST*834*0001",
        "SE*1*9999",
        "GE*1*1",
        "IEA*1*000000001",
    ]

    errors = validate_edi_envelope(
        segments
    )

    assert (
        "ST and SE control numbers do not match"
        in errors
    )


def test_valid_member():

    member = {
        "member_id": "10001",
        "first_name": "JOHN",
        "last_name": "DOE",
        "date_of_birth": "19900115",
        "gender": "M",
        "health_plan": "GOLD",
        "effective_date": "20261001",
    }

    errors = validate_member(
        member
    )

    assert errors == []


def test_missing_member_id():

    member = {
        "member_id": "",
        "first_name": "JOHN",
        "last_name": "DOE",
        "date_of_birth": "19900115",
        "gender": "M",
        "health_plan": "GOLD",
        "effective_date": "20261001",
    }

    errors = validate_member(
        member
    )

    assert "Missing required field: member_id" in errors