from pathlib import Path


def read_edi_file(file_path: str) -> list[str]:
    """
    Read an EDI file and return cleaned segments.
    """

    content = Path(file_path).read_text(
        encoding="utf-8"
    )

    segments = content.strip().split("~")

    return [
        segment.strip()
        for segment in segments
        if segment.strip()
    ]


def find_element(
    segments: list[str],
    mapping: dict
) -> str | None:
    """
    Find a value from EDI segments based on
    carrier-specific mapping.
    """

    target_segment = mapping["segment"]
    target_element = mapping["element"]

    for segment in segments:

        elements = segment.split("*")

        if elements[0] != target_segment:
            continue

        if len(elements) <= target_element:
            continue

        if "qualifier_element" in mapping:

            qualifier_element = (
                mapping["qualifier_element"]
            )

            qualifier_value = (
                mapping["qualifier_value"]
            )

            if len(elements) <= qualifier_element:
                continue

            if (
                elements[qualifier_element]
                != qualifier_value
            ):
                continue

        return elements[target_element]

    return None


def parse_834(
    file_path: str,
    carrier_config: dict
) -> list[dict]:
    """
    Parse an 834 file using carrier-specific
    configuration.
    """

    segments = read_edi_file(file_path)

    mapping = carrier_config["mapping"]

    member_groups = []

    current_group = []

    for segment in segments:

        segment_id = segment.split("*")[0]

        if segment_id == "INS":

            if current_group:
                member_groups.append(
                    current_group
                )

            current_group = [segment]

        elif current_group:

            current_group.append(segment)

    if current_group:
        member_groups.append(
            current_group
        )

    members = []

    for group in member_groups:

        member = {}

        for field_name, field_mapping in mapping.items():

            member[field_name] = find_element(
                group,
                field_mapping
            )

        members.append(member)

    return members