import hashlib
from pathlib import Path


def calculate_file_hash(
    file_path: Path
) -> str:
    """
    Calculate the SHA-256 hash of a file.
    """

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:

        while chunk := file.read(65536):
            sha256.update(chunk)

    return sha256.hexdigest()