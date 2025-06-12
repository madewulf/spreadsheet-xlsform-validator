"""
The validators utility functions.
"""

import logging
import os
import signal
import subprocess
import tempfile
import threading
import time
from subprocess import PIPE, Popen
from typing import NamedTuple

HERE = os.path.abspath(os.path.dirname(__file__))
XFORM_SPEC_PATH = os.path.join(HERE, "xlsform_spec_test.xml")


class PopenResult:
    """Result data for run_popen_with_timeout"""

    def __init__(
        self, return_code: int, timeout: bool, stdout: bytes, stderr: bytes
    ) -> None:
        self.return_code: int = return_code
        self.timeout: bool = timeout
        self.stdout: str = decode_stream(stream=stdout)
        self.stderr: str = decode_stream(stream=stderr)


# Adapted from:
# http://betabug.ch/blogs/ch-athens/1093
def run_popen_with_timeout(command, timeout) -> "PopenResult":
    """
    Run a sub-program in subprocess.Popen, pass it the input_data,
    kill it if the specified timeout has passed.
    returns a tuple of resultcode, timeout, stdout, stderr
    """
    kill_check = threading.Event()

    def _kill_process_after_a_timeout(pid):
        os.kill(pid, signal.SIGTERM)
        kill_check.set()  # tell the main routine that we had to kill
        # use SIGKILL if hard to kill...

    startup_info = None
    env = None
    if os.name == "nt":
        # Workarounds for pyinstaller
        # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-subprocess
        # disable command window when run from pyinstaller
        startup_info = subprocess.STARTUPINFO()
        # Less fancy version of bitwise-or-assignment (x |= y) shown in ref url.
        if startup_info.dwFlags == 1 or subprocess.STARTF_USESHOWWINDOW == 1:
            startup_info.dwFlags = 1
        else:
            startup_info.dwFlags = 0

        # Workaround for Java sometimes not being able to use the temp directory.
        # https://docs.oracle.com/javase/8/docs/api/java/io/File.html
        # CreateTempFile refers to "java.io.tmpdir" which refers to env vars.
        env = {
            k: v if v is not None else tempfile.gettempdir()
            for k, v in {k: os.environ.get(k) for k in ("TEMP", "TMP", "TMPDIR")}.items()
        }

    p = Popen(
        command, env=env, stdin=PIPE, stdout=PIPE, stderr=PIPE, startupinfo=startup_info
    )
    watchdog = threading.Timer(timeout, _kill_process_after_a_timeout, args=(p.pid,))
    watchdog.start()
    (stdout, stderr) = p.communicate()
    watchdog.cancel()  # if it's still waiting to run
    timeout = kill_check.is_set()
    kill_check.clear()
    return PopenResult(
        return_code=p.returncode, timeout=timeout, stdout=stdout, stderr=stderr
    )


def decode_stream(stream):
    """
    Decode a stream, e.g. stdout or stderr.

    On Windows, stderr may be latin-1; in which case utf-8 decode will fail.
    If both utf-8 and latin-1 decoding fail then raise all as IOError.
    If the above validate jar call fails, add make sure that the java path
    is set, e.g. PATH=C:\\Program Files (x86)\\Java\\jre1.8.0_71\\bin
    """
    try:
        return stream.decode("utf-8")
    except UnicodeDecodeError as ude:
        try:
            return stream.decode("latin-1")
        except BaseException as be:
            msg = "Failed to decode validate stderr as utf-8 or latin-1."
            raise OSError(msg, ude, be) from be

def check_readable(file_path, retry_limit=10, wait_seconds=0.5):
    """
    Check if a file is readable: True if so, IOError if not. Retry as per args.

    If a file that needs to be read may be locked by some other process (such
    as for reading or writing), this can help avoid an error by waiting for the
    lock to clear.

    :param file_path: Path to file to check.
    :param retry_limit: Number of attempts to read the file.
    :param wait_seconds: Amount of sleep time between read attempts.
    :return: True or raise IOError.
    """

    def catch_try():
        try:
            with open(file_path):
                return True
        except OSError:
            return False

    tries = 0
    while not catch_try():
        if tries < retry_limit:
            tries += 1
            time.sleep(wait_seconds)
        else:
            raise OSError(f"Could not read file: {file_path}")
    return True