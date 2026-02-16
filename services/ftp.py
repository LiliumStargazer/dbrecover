# services/ftp.py

import os
from .sftp_client import SftpClient
from utils.errors import internal_error


def connect_sftp() -> SftpClient:
    host = os.getenv("SFTP_HOST")
    port_str = os.getenv("SFTP_PORT", "22")
    username = os.getenv("SFTP_USER")
    password = os.getenv("SFTP_PASSWORD")

    if host is None or username is None or password is None:
        raise internal_error("Variabili SFTP mancanti")

    port = int(port_str)

    return SftpClient(host, port, username, password)
