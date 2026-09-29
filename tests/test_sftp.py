from pathlib import Path

from app.sftp_client import download_file


def test_download_file(tmp_path):

    # -----------------------------------------
    # Fake SFTP client
    # -----------------------------------------

    class FakeSFTP:

        def get(
            self,
            remote_path,
            local_path
        ):
            Path(local_path).write_text(
                "test EDI content"
            )

    # -----------------------------------------
    # Temporary destination
    # -----------------------------------------

    local_file = (
        tmp_path
        / "abc"
        / "incoming"
        / "valid_834.txt"
    )

    # -----------------------------------------
    # Run the function being tested
    # -----------------------------------------

    download_file(
        FakeSFTP(),
        "data/abc/incoming/valid_834.txt",
        str(local_file)
    )

    # -----------------------------------------
    # Verify download
    # -----------------------------------------

    assert local_file.exists()

    assert (
        local_file.read_text()
        == "test EDI content"
    )