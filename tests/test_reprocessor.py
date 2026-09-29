from pathlib import Path

from app.reprocessor import reprocess_file


def test_missing_file_does_not_process(
    monkeypatch,
    tmp_path
):

    monkeypatch.setattr(
        "app.reprocessor.LOCAL_DATA_DIR",
        tmp_path
    )

    reprocess_file(
        "abc",
        "does_not_exist.txt"
    )

    expected_file = (
        tmp_path
        / "abc"
        / "errors"
        / "does_not_exist.txt"
    )

    assert not expected_file.exists()