from pathlib import Path

from app.sftp_client import (
    connect_sftp,
    list_remote_files,
    download_file,
)


REMOTE_DIR = "data"
LOCAL_DIR = Path("data/incoming")


def main():

    transport = None
    sftp = None

    try:

        transport, sftp = connect_sftp()

        print("Connected to SFTP")

        files = list_remote_files(
            sftp,
            REMOTE_DIR
        )

        for file_name in files:

            if not file_name.endswith(".txt"):
                continue

            remote_path = (
                f"{REMOTE_DIR}/{file_name}"
            )

            local_path = (
                LOCAL_DIR / file_name
            )

            download_file(
                sftp,
                remote_path,
                str(local_path)
            )

            print(
                f"Downloaded: {file_name}"
            )

    finally:

        if sftp:
            sftp.close()

        if transport:
            transport.close()


if __name__ == "__main__":
    main()