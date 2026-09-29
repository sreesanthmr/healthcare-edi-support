import os
from pathlib import Path

import paramiko
from dotenv import load_dotenv


load_dotenv()


def connect_sftp():

    host = os.getenv("SFTP_HOST")
    port = int(os.getenv("SFTP_PORT", "22"))
    username = os.getenv("SFTP_USERNAME")
    password = os.getenv("SFTP_PASSWORD")

    transport = paramiko.Transport((host, port))

    transport.connect(
        username=username,
        password=password
    )

    sftp = paramiko.SFTPClient.from_transport(
        transport
    )

    return transport, sftp


def list_remote_files(sftp, remote_directory: str):

    return sftp.listdir(remote_directory)


def download_file(sftp, remote_path: str, local_path: str):

    Path(local_path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    sftp.get(
        remote_path,
        local_path
    )

def move_remote_file(sftp, source_path: str, destination_path: str):
    sftp.rename(
        source_path,
        destination_path
    )