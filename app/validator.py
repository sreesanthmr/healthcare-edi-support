from datetime import datetime


def validate_member(member: dict) -> list[str]:
    errors = []

    required_fields = [
        "member_id",
        "first_name",
        "last_name",
        "date_of_birth",
        "health_plan",
        "effective_date",
    ]

    for field in required_fields:
        if not member.get(field):
            errors.append(f"Missing required field: {field}")

    if member.get("gender") not in {"M", "F"}:
        errors.append("Invalid gender")

    if member.get("date_of_birth"):
        try:
            datetime.strptime(
                member["date_of_birth"],
                "%Y%m%d"
            )
        except ValueError:
            errors.append("Invalid date of birth")

    if member.get("effective_date"):
        try:
            datetime.strptime(
                member["effective_date"],
                "%Y%m%d"
            )
        except ValueError:
            errors.append("Invalid effective date")

    return errors


def validate_edi_envelope(
    segments: list[str],
) -> list[str]:
    """
    Perform basic structural validation of an
    X12 834-style EDI file.

    This is a project-level validation and is not
    a complete X12 implementation.
    """

    errors = []

    if not segments:
        return ["EDI file is empty"]

    # -------------------------------------------------
    # Check required envelope segments
    # -------------------------------------------------

    segment_ids = [
        segment.split("*")[0]
        for segment in segments
    ]

    required_segments = [
        "ISA",
        "GS",
        "ST",
        "SE",
        "GE",
        "IEA",
    ]

    for required in required_segments:

        if required not in segment_ids:

            errors.append(
                f"Missing required segment: {required}"
            )

    if errors:
        return errors

    # -------------------------------------------------
    # Validate ISA
    # -------------------------------------------------

    isa = segments[0].split("*")

    if isa[0] != "ISA":
        errors.append(
            "EDI file must start with ISA segment"
        )

    # -------------------------------------------------
    # Validate GS
    # -------------------------------------------------

    gs_index = segment_ids.index("GS")
    gs = segments[gs_index].split("*")

    if len(gs) <= 1 or gs[1] != "BE":

        errors.append(
            "Expected BE functional group for 834 transaction"
        )

    # -------------------------------------------------
    # Validate ST
    # -------------------------------------------------

    st_index = segment_ids.index("ST")
    st = segments[st_index].split("*")

    if len(st) <= 1:

        errors.append(
            "ST segment is missing transaction type"
        )

    elif st[1] != "834":

        errors.append(
            f"Unsupported transaction type: {st[1]}"
        )

    # -------------------------------------------------
    # Validate ST/SE control number
    # -------------------------------------------------

    se_index = segment_ids.index("SE")
    se = segments[se_index].split("*")

    if len(st) > 2 and len(se) > 2:

        if st[2] != se[2]:

            errors.append(
                "ST and SE control numbers do not match"
            )

    # -------------------------------------------------
    # Validate GS/GE control number
    # -------------------------------------------------

    ge_index = segment_ids.index("GE")
    ge = segments[ge_index].split("*")

    if len(gs) > 6 and len(ge) > 1:

        if gs[6] != ge[1]:

            errors.append(
                "GS and GE control numbers do not match"
            )

    # -------------------------------------------------
    # Validate ISA/IEA control number
    # -------------------------------------------------

    iea_index = segment_ids.index("IEA")
    iea = segments[iea_index].split("*")

    if len(isa) > 13 and len(iea) > 2:

        if isa[13] != iea[2]:

            errors.append(
                "ISA and IEA control numbers do not match"
            )

    return errors