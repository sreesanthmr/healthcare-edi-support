import shutil
from pathlib import Path

from app.config_loader import (
    load_carrier_config,
    load_carriers_config,
)
from app.database import log_file_processing
from app.file_utils import calculate_file_hash
from app.logger import logger
from app.processor import process_file
from app.sftp_client import (
    connect_sftp,
    move_remote_file,
)


# =========================================================
# BASE LOCAL DIRECTORY
# =========================================================

LOCAL_DATA_DIR = Path("data")


def reprocess_file(
    carrier_key: str,
    file_name: str
):
    """
    Reprocess a previously failed EDI file
    for a specific carrier.
    """

    # =====================================================
    # Load carrier registry
    # =====================================================

    carriers_config = load_carriers_config()

    if carrier_key not in carriers_config["carriers"]:

        logger.error(
            f"Unknown carrier: {carrier_key}"
        )

        return

    carrier_config = (
        carriers_config["carriers"][carrier_key]
    )

    carrier_name = carrier_config["name"]

    edi_config_path = carrier_config["config"]

    # -----------------------------------------------------
    # Remote directories
    # -----------------------------------------------------

    remote_error_dir = (
        carrier_config["remote_errors"]
    )

    remote_archive_dir = (
        carrier_config["remote_archive"]
    )

    # =====================================================
    # Load carrier-specific EDI configuration
    # =====================================================

    edi_config = load_carrier_config(
        edi_config_path
    )

    # =====================================================
    # Local directories
    #
    # data/
    #   └── <carrier>/
    #       ├── errors/
    #       └── archive/
    # =====================================================

    local_error_dir = (
        LOCAL_DATA_DIR
        / carrier_key
        / "errors"
    )

    local_archive_dir = (
        LOCAL_DATA_DIR
        / carrier_key
        / "archive"
    )

    error_file = (
        local_error_dir / file_name
    )

    archive_file = (
        local_archive_dir / file_name
    )

    # =====================================================
    # Check local failed file
    # =====================================================

    if not error_file.exists():

        logger.error(
            f"{carrier_name}: "
            f"Cannot reprocess {file_name}. "
            f"File not found at {error_file}"
        )

        return

    logger.info(
        f"{carrier_name}: "
        f"Starting reprocessing: "
        f"{file_name}"
    )

    # =====================================================
    # Calculate file hash
    # =====================================================

    file_hash = calculate_file_hash(
        error_file
    )

    logger.info(
        f"{carrier_name}: "
        f"Calculated SHA-256 hash for "
        f"reprocessing: {file_name}"
    )

    transport = None
    sftp = None

    try:

        # =================================================
        # Process failed file
        # =================================================

        success, error, record_count = (
            process_file(
                error_file,
                edi_config
            )
        )

        # =================================================
        # SUCCESS
        # =================================================

        if success:

            # ---------------------------------------------
            # Connect to SFTP
            # ---------------------------------------------

            transport, sftp = connect_sftp()

            logger.info(
                f"{carrier_name}: "
                f"SFTP connection established "
                f"for reprocessing"
            )

            # ---------------------------------------------
            # Remote paths
            #
            # errors → archive
            # ---------------------------------------------

            remote_error_file = (
                f"{remote_error_dir}/{file_name}"
            )

            remote_archive_file = (
                f"{remote_archive_dir}/{file_name}"
            )

            # ---------------------------------------------
            # Move remote file
            # ---------------------------------------------

            move_remote_file(
                sftp,
                remote_error_file,
                remote_archive_file
            )

            logger.info(
                f"{carrier_name}: "
                f"Remote file archived after "
                f"successful reprocessing: "
                f"{file_name}"
            )

            # ---------------------------------------------
            # Make sure local archive exists
            # ---------------------------------------------

            local_archive_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            # ---------------------------------------------
            # Move local file
            #
            # errors → archive
            # ---------------------------------------------

            shutil.move(
                str(error_file),
                str(archive_file)
            )

            logger.info(
                f"{carrier_name}: "
                f"Local file archived after "
                f"successful reprocessing: "
                f"{file_name}"
            )

            # ---------------------------------------------
            # Record successful reprocessing
            # ---------------------------------------------

            log_file_processing(
                file_name=file_name,
                status="REPROCESSED",
                record_count=record_count,
                processing_type="REPROCESS",
                carrier_name=carrier_name,
                file_hash=file_hash,
            )

            logger.info(
                f"{carrier_name}: "
                f"Reprocessing completed successfully: "
                f"{file_name} | "
                f"Records: {record_count}"
            )

        # =================================================
        # FAILURE
        # =================================================

        else:

            # ---------------------------------------------
            # Record failed reprocessing
            # ---------------------------------------------

            log_file_processing(
                file_name=file_name,
                status="REPROCESS_FAILED",
                record_count=0,
                error_message=error,
                processing_type="REPROCESS",
                carrier_name=carrier_name,
                file_hash=file_hash,
            )

            logger.error(
                f"{carrier_name}: "
                f"Reprocessing failed: "
                f"{file_name} | "
                f"Reason: {error}"
            )

            # File remains in:
            #
            # data/<carrier>/errors/
            #
            # so it can be investigated or
            # reprocessed again.

    except Exception:

        logger.exception(
            f"{carrier_name}: "
            f"Unexpected error during "
            f"reprocessing: "
            f"{file_name}"
        )

    finally:

        # -------------------------------------------------
        # Close SFTP connection
        # -------------------------------------------------

        if sftp:
            sftp.close()

        if transport:
            transport.close()

        if sftp or transport:

            logger.info(
                f"{carrier_name}: "
                f"SFTP connection closed "
                f"after reprocessing"
            )