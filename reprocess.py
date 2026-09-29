import sys

from app.reprocessor import reprocess_file


def main():

    if len(sys.argv) != 3:

        print(
            "Usage: "
            "python reprocess.py <carrier> <file_name>"
        )

        return

    carrier_key = sys.argv[1]
    file_name = sys.argv[2]

    reprocess_file(
        carrier_key,
        file_name
    )


if __name__ == "__main__":
    main()