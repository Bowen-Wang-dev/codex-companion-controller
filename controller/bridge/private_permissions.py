"""Equivalent private-file policy: POSIX modes or a current-user Windows DACL."""
import os
import sys


def set_private(path, mode=0o600):
    if sys.platform == 'win32':
        from windows_security import secure_directory, protect_file
        if mode == 0o700:secure_directory(path, restrict_existing=True)
        else:protect_file(path)
    else:os.chmod(path, mode)
