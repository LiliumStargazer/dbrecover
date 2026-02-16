import os
import paramiko
from typing import Optional
from utils.errors import AppError


class SftpClient:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.transport = paramiko.Transport((host, port))

        self.sftp: Optional[paramiko.SFTPClient] = None

        try:
            self.transport.connect(username=username, password=password)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)

            if self.sftp is None:
                raise Exception("Impossibile creare sessione SFTP")

        except Exception as e:
            raise AppError("FTP_ERROR", "Impossibile connettersi al server FTP", 500, e)

    def exists(self, remote_path: str) -> bool:
        try:
            assert self.sftp is not None
            self.sftp.stat(remote_path)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            raise AppError("FTP_ERROR", f"Errore verifica path: {remote_path}", 500, e)

    def list(self, remote_path: str):
        try:
            assert self.sftp is not None
            return self.sftp.listdir_attr(remote_path)
        except Exception as e:
            raise AppError("FTP_ERROR", f"Errore listing path: {remote_path}", 500, e)

    def download(self, remote_path: str, local_path: str):
        try:
            assert self.sftp is not None
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.sftp.get(remote_path, local_path)
        except Exception as e:
            raise AppError("FTP_ERROR", f"Errore download {remote_path}", 500, e)

    def create_path(self, remote_dir: str):
        try:
            assert self.sftp is not None
            self._mkdir_recursive(remote_dir)
        except Exception as e:
            raise AppError("FTP_ERROR", f"Errore creazione directory: {remote_dir}", 500, e)

    def _mkdir_recursive(self, remote_dir: str):
        assert self.sftp is not None

        dirs = []
        while remote_dir not in ("", "/"):
            dirs.append(remote_dir)
            remote_dir = os.path.dirname(remote_dir)

        for d in reversed(dirs):
            try:
                self.sftp.mkdir(d)
            except IOError:
                pass

    def upload(self, local_path: str, remote_path: str):
        try:
            assert self.sftp is not None
            remote_dir = os.path.dirname(remote_path)
            self._mkdir_recursive(remote_dir)
            self.sftp.put(local_path, remote_path)
        except Exception as e:
            raise AppError("FTP_ERROR", f"Errore upload {remote_path}", 500, e)

    def close(self):
        if self.sftp:
            self.sftp.close()
        self.transport.close()