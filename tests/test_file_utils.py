from pathlib import Path

from app.file_utils import calculate_file_hash


def test_same_file_has_same_hash():

    file_path = Path(
        "samples/valid_834.txt"
    )

    hash_one = calculate_file_hash(
        file_path
    )

    hash_two = calculate_file_hash(
        file_path
    )

    assert hash_one == hash_two


def test_hash_is_sha256_length():

    file_path = Path(
        "samples/valid_834.txt"
    )

    file_hash = calculate_file_hash(
        file_path
    )

    assert len(file_hash) == 64