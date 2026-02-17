# services/fs_ops.py
import os
import shutil
from utils.errors import internal_error


def purge_dir_contents(dir_path: str) -> None:
    """
    Svuota completamente una directory (cancella tutto dentro),
    ma lascia la directory esistente.
    """
    if not dir_path:
        raise internal_error("dir_path mancante")

    if not os.path.isdir(dir_path):
        # se non esiste non è un problema
        return

    try:
        for name in os.listdir(dir_path):
            full_path = os.path.join(dir_path, name)

            if os.path.isfile(full_path) or os.path.islink(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)

    except Exception as e:
        raise internal_error(f"Impossibile pulire directory {dir_path}: {e}")
