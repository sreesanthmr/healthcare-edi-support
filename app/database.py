import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def save_members(members: list[dict], source_file: str) -> int:
    """
    Save all members in one database transaction.

    If any insert/update fails, the whole transaction is rolled back.
    """

    query = """
        INSERT INTO members (
            member_id,
            first_name,
            last_name,
            date_of_birth,
            gender,
            health_plan,
            effective_date,
            source_file
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        ON CONFLICT (member_id)
        DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            date_of_birth = EXCLUDED.date_of_birth,
            gender = EXCLUDED.gender,
            health_plan = EXCLUDED.health_plan,
            effective_date = EXCLUDED.effective_date,
            source_file = EXCLUDED.source_file;
    """

    with get_connection() as conn:

        with conn.cursor() as cur:

            for member in members:

                cur.execute(
                    query,
                    (
                        member["member_id"],
                        member["first_name"],
                        member["last_name"],
                        member["date_of_birth"],
                        member["gender"],
                        member["health_plan"],
                        member["effective_date"],
                        source_file,
                    )
                )

    return len(members)


def log_file_processing(
    file_name: str,
    status: str,
    record_count: int = 0,
    error_message: str | None = None,
    processing_type: str = "INITIAL",
    carrier_name: str | None = None,
    file_hash: str | None = None,
):
    query = """
        INSERT INTO file_processing_log (
            file_name,
            status,
            record_count,
            error_message,
            attempt_number,
            processing_type,
            carrier_name,
            file_hash
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            (
                SELECT COALESCE(
                    MAX(attempt_number), 0
                ) + 1
                FROM file_processing_log
                WHERE file_name = %s
                  AND carrier_name = %s
            ),
            %s,
            %s,
            %s
        );
    """

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                query,
                (
                    file_name,
                    status,
                    record_count,
                    error_message,
                    file_name,
                    carrier_name,
                    processing_type,
                    carrier_name,
                    file_hash,
                )
            )


def is_duplicate_file(
    carrier_name: str,
    file_hash: str
) -> bool:

    query = """
        SELECT 1
        FROM file_processing_log
        WHERE carrier_name = %s
          AND file_hash = %s
          AND status IN (
              'SUCCESS',
              'REPROCESSED'
          )
        LIMIT 1;
    """

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                query,
                (
                    carrier_name,
                    file_hash,
                )
            )

            return cur.fetchone() is not None