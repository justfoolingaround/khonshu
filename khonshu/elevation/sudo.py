import os
import subprocess
import sys


def is_elevated():
    return os.geteuid() == 0


def elevate(password: str):
    if is_elevated():
        return True

    process = subprocess.Popen(
        args=["sudo", sys.executable] + sys.argv,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    process.communicate(password.encode("utf-8"))

    return exit(process.returncode)
