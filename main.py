import shutil
from pathlib import Path

from app.config_loader import (
    load_carrier_config,
    load_carriers_config,
)
from app.database import (
    is_duplicate_file,
    log_file_processing,
)
from app.file_utils import calculate_file_hash
from app.logger import logger
from app.processor import process_file
from app.sftp_client import (
    connect_sftp,
    download_file,
    list_remote_files,
    move_remote_file,
)


# =========================================================
# GENERAL CONFIGURATION
# =========================================================

CARRIERS_CONFIG = "config/carriers.json"


# =========================================================
# PROCESS A SINGLE CARRIER
# =========================================================

def process_carrier(
    sftp,
    carrier_key: str,
    carrier_config: dict
):
    """
    Process all EDI files belonging to one carrier.
    """

    carrier_name = carrier_config["name"]

    edi_config_path = carrier_config["config"]

    # -----------------------------------------------------
    # Remote SFTP directories
    # -----------------------------------------------------

    remote_incoming = carrier_config[
        "remote_incoming"
    ]

    remote_archive = carrier_config[
        "remote_archive"
    ]

    remote_errors = carrier_config[
        "remote_errors"
    ]

    # -----------------------------------------------------
    # Load carrier-specific EDI configuration
    # -----------------------------------------------------

    edi_config = load_carrier_config(
        edi_config_path
    )

    logger.info(
        f"Loaded carrier configuration: "
        f"{carrier_name}"
    )

    # -----------------------------------------------------
    # Local carrier directories
    #
    # data/
    #   └── <carrier>/
    #       ├── incoming/
    #       ├── archive/
    #       └── errors/
    # -----------------------------------------------------

    local_incoming = (
        Path("data")
        / carrier_key
        / "incoming"
    )

    local_archive = (
        Path("data")
        / carrier_key
        / "archive"
    )

    local_errors = (
        Path("data")
        / carrier_key
        / "errors"
    )

    # Create directories if they don't exist.

    local_incoming.mkdir(
        parents=True,
        exist_ok=True
    )

    local_archive.mkdir(
        parents=True,
        exist_ok=True
    )

    local_errors.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Get files from remote incoming directory
    # -----------------------------------------------------

    files = list_remote_files(
        sftp,
        remote_incoming
    )

    edi_files = [
        file_name
        for file_name in files
        if file_name.endswith(".txt")
    ]

    logger.info(
        f"{carrier_name}: "
        f"Found {len(edi_files)} EDI file(s) "
        f"in {remote_incoming}"
    )

    # -----------------------------------------------------
    # Process each EDI file
    # -----------------------------------------------------

    for file_name in edi_files:

        remote_path = (
            f"{remote_incoming}/{file_name}"
        )

        local_path = (
            local_incoming / file_name
        )

        local_archive_path = (
            local_archive / file_name
        )

        local_error_path = (
            local_errors / file_name
        )

        logger.info(
            f"{carrier_name}: "
            f"Starting file processing: "
            f"{file_name}"
        )

        try:

            # =============================================
            # DOWNLOAD
            # =============================================

            download_file(
                sftp,
                remote_path,
                str(local_path)
            )

            logger.info(
                f"{carrier_name}: "
                f"Downloaded file: "
                f"{file_name}"
            )

            # =============================================
            # CALCULATE FILE HASH
            # =============================================

            file_hash = calculate_file_hash(
                local_path
            )

            logger.info(
                f"{carrier_name}: "
                f"Calculated SHA-256 hash: "
                f"{file_name}"
            )

            # =============================================
            # DUPLICATE CHECK
            # =============================================

            if is_duplicate_file(
                carrier_name,
                file_hash
            ):

                logger.warning(
                    f"{carrier_name}: "
                    f"Duplicate file detected: "
                    f"{file_name}"
                )

                # -----------------------------------------
                # Record duplicate
                # -----------------------------------------

                log_file_processing(
                    file_name=file_name,
                    status="DUPLICATE",
                    record_count=0,
                    error_message=(
                        "File content has already been "
                        "successfully processed"
                    ),
                    processing_type="INITIAL",
                    carrier_name=carrier_name,
                    file_hash=file_hash,
                )

                # -----------------------------------------
                # Remote:
                #
                # incoming → archive
                # -----------------------------------------

                move_remote_file(
                    sftp,
                    remote_path,
                    f"{remote_archive}/{file_name}"
                )

                logger.warning(
                    f"{carrier_name}: "
                    f"Duplicate remote file archived: "
                    f"{file_name}"
                )

                # -----------------------------------------
                # Local:
                #
                # incoming → archive
                # -----------------------------------------

                shutil.move(
                    str(local_path),
                    str(local_archive_path)
                )

                logger.warning(
                    f"{carrier_name}: "
                    f"Duplicate local file archived: "
                    f"{file_name}"
                )

                # -----------------------------------------
                # Move to next file
                # -----------------------------------------

                continue

            # =============================================
            # NORMAL PROCESSING
            # =============================================

            success, error, record_count = (
                process_file(
                    local_path,
                    edi_config
                )
            )

            # =============================================
            # SUCCESS
            # =============================================

            if success:

                # -----------------------------------------
                # Record successful processing
                # -----------------------------------------

                log_file_processing(
                    file_name=file_name,
                    status="SUCCESS",
                    record_count=record_count,
                    processing_type="INITIAL",
                    carrier_name=carrier_name,
                    file_hash=file_hash,
                )

                # -----------------------------------------
                # Remote:
                #
                # incoming → archive
                # -----------------------------------------

                move_remote_file(
                    sftp,
                    remote_path,
                    f"{remote_archive}/{file_name}"
                )

                logger.info(
                    f"{carrier_name}: "
                    f"Remote file archived: "
                    f"{file_name}"
                )

                # -----------------------------------------
                # Local:
                #
                # incoming → archive
                # -----------------------------------------

                shutil.move(
                    str(local_path),
                    str(local_archive_path)
                )

                logger.info(
                    f"{carrier_name}: "
                    f"Local file archived: "
                    f"{file_name}"
                )

                logger.info(
                    f"{carrier_name}: "
                    f"File processing completed "
                    f"successfully: "
                    f"{file_name} | "
                    f"Records: {record_count}"
                )

            # =============================================
            # FAILURE
            # =============================================

            else:

                # -----------------------------------------
                # Record failed processing
                # -----------------------------------------

                log_file_processing(
                    file_name=file_name,
                    status="FAILED",
                    record_count=0,
                    error_message=error,
                    processing_type="INITIAL",
                    carrier_name=carrier_name,
                    file_hash=file_hash,
                )

                # -----------------------------------------
                # Remote:
                #
                # incoming → errors
                # -----------------------------------------

                move_remote_file(
                    sftp,
                    remote_path,
                    f"{remote_errors}/{file_name}"
                )

                logger.error(
                    f"{carrier_name}: "
                    f"Remote file moved to errors: "
                    f"{file_name}"
                )

                # -----------------------------------------
                # Local:
                #
                # incoming → errors
                # -----------------------------------------

                shutil.move(
                    str(local_path),
                    str(local_error_path)
                )

                logger.error(
                    f"{carrier_name}: "
                    f"Local file moved to errors: "
                    f"{file_name}"
                )

                logger.error(
                    f"{carrier_name}: "
                    f"File processing failed: "
                    f"{file_name} | "
                    f"Reason: {error}"
                )

        except Exception:

            logger.exception(
                f"{carrier_name}: "
                f"Unexpected error while processing "
                f"{file_name}"
            )


# =========================================================
# MAIN
# =========================================================

def main():

    transport = None
    sftp = None

    try:

        # -------------------------------------------------
        # Load carrier registry
        # -------------------------------------------------

        carriers_config = load_carriers_config(
            CARRIERS_CONFIG
        )

        logger.info(
            "Carrier registry loaded successfully"
        )

        # -------------------------------------------------
        # Connect to SFTP
        # -------------------------------------------------

        transport, sftp = connect_sftp()

        logger.info(
            "SFTP connection established"
        )

        # -------------------------------------------------
        # Process each configured carrier
        # -------------------------------------------------

        for carrier_key, carrier_config in (
            carriers_config["carriers"].items()
        ):

            try:

                process_carrier(
                    sftp,
                    carrier_key,
                    carrier_config
                )

            except Exception:

                logger.exception(
                    f"Unexpected error while processing "
                    f"carrier: {carrier_key}"
                )

                # Continue with the next carrier.
                continue

    except Exception:

        logger.exception(
            "Unexpected error in main processing"
        )

    finally:

        # -------------------------------------------------
        # Close SFTP connection
        # -------------------------------------------------

        if sftp:
            sftp.close()

        if transport:
            transport.close()

        logger.info(
            "SFTP connection closed"
        )


if __name__ == "__main__":
    main()