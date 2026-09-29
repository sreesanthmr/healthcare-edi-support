from pathlib import Path

from app.database import save_members
from app.logger import logger
from app.parser import (
    parse_834,
    read_edi_file,
)
from app.validator import (
    validate_edi_envelope,
    validate_member,
)


def process_file(
    file_path: Path,
    carrier_config: dict
) -> tuple[bool, str, int]:

    logger.info(
        f"Processing started: {file_path.name}"
    )

    try:

        # =================================================
        # Read EDI segments
        # =================================================

        segments = read_edi_file(
            str(file_path)
        )

        # =================================================
        # Validate EDI envelope
        # =================================================

        envelope_errors = validate_edi_envelope(
            segments
        )

        if envelope_errors:

            error = "; ".join(
                envelope_errors
            )

            logger.error(
                f"{file_path.name}: "
                f"EDI envelope validation failed: "
                f"{error}"
            )

            return False, error, 0

        # =================================================
        # Parse EDI
        # =================================================

        members = parse_834(
            str(file_path),
            carrier_config
        )

        if not members:

            error = (
                "No enrollment records found"
            )

            logger.error(
                f"{file_path.name}: {error}"
            )

            return False, error, 0

        # =================================================
        # Validate members
        # =================================================

        for member in members:

            errors = validate_member(
                member
            )

            if errors:

                error = "; ".join(
                    errors
                )

                logger.error(
                    f"{file_path.name}: "
                    f"Member validation failed: "
                    f"{error}"
                )

                return False, error, 0

        # =================================================
        # Save records in one transaction
        # =================================================

        record_count = save_members(
            members,
            file_path.name
        )

        logger.info(
            f"Processing successful: "
            f"{file_path.name} | "
            f"{record_count} records"
        )

        return True, "", record_count

    except Exception:

        logger.exception(
            f"Processing failed: "
            f"{file_path.name}"
        )

        return False, (
            "Unexpected processing error"
        ), 0