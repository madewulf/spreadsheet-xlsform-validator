"""
odk_validate.py
A python wrapper around ODK Validate
"""

import logging
import os
import sys
from typing import TYPE_CHECKING

from xlsform_validator.odk_validate.utils import (
    XFORM_SPEC_PATH,
    check_readable,
    run_popen_with_timeout,
)

if TYPE_CHECKING:
    from xlsform_validator.odk_validate.utils import PopenResult

BINARY_NAME = "validate"
CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ODK_VALIDATE_PATH = os.path.join(CURRENT_DIRECTORY, "bin", BINARY_NAME)


class ODKValidateError(Exception):
    """ODK Validation exception error."""


def install_exists():
    """Returns True if ODK_VALIDATE_PATH exists."""
    return os.path.exists(ODK_VALIDATE_PATH)


def _call_validator(path_to_xform, answers, bin_file_path=ODK_VALIDATE_PATH) -> "PopenResult":
    return run_popen_with_timeout([bin_file_path, "-x", path_to_xform, "-a", answers], 100)


def install_ok(bin_file_path=ODK_VALIDATE_PATH):
    """
    Check if ODK Validate functions as expected.
    """
    check_readable(file_path=XFORM_SPEC_PATH)
    result = _call_validator(
        path_to_xform=XFORM_SPEC_PATH,
        answers="{}",
        bin_file_path=bin_file_path,
    )
    if result.return_code == 1:
        return False

    return True


def check_xform(path_to_xform, answers):
    """Run ODK Validate against the XForm in `path_to_xform`."""
    # resultcode indicates validity of the form
    # timeout indicates whether validation ran out of time to complete
    # stdout is not used because it has some warnings that always
    # appear and can be ignored.
    # stderr is treated as a warning if the form is valid or an error
    # if it is invalid.
    result = _call_validator(path_to_xform=path_to_xform, answers=answers)

    if result.timeout:
        return ["XForm took to long to completely validate."]
    elif result.return_code > 0:  # Error invalid
        raise ODKValidateError(result.stderr)
    elif result.return_code < 0:
        return ["Bad return code from ODK Validate."]

    return result.stdout


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    logger.info(__doc__)

    check_xform(sys.argv[1], sys.argv[2])