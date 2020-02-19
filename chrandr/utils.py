# -*- coding: utf-8 -*-
"""
chrandr - Various utilities
"""

import os
import os.path
import sys
import logging
import subprocess
import re
import pkg_resources


class ProcessException(Exception):
    def __init__(self, cmd, exit_code=None, output=None):
        self.cmd = cmd
        self.exit_code = exit_code
        self.output = output
    def __str__(self):
        return str(self.__cause__)


def get_connected_outputs():
    """Returns the list of connected outputs."""
    logger = logging.getLogger('get_connected_outputs')
    # execute xrandr query command
    xrandr_output = subprocess.check_output(args=["xrandr", "--query"], universal_newlines=True)
    # logger.debug("xrandr --query output :\n%s", xrandr_output)
    # match output to find all connected outputs
    connected_outputs = re.findall(r"^([\w\d-]*) connected .*$", xrandr_output, re.MULTILINE)
    if connected_outputs:
        logger.debug("Connected outputs: %s", connected_outputs)
        return connected_outputs
    return []


def execute_commands(commands):
    """
    Execute a list of commands, one by one.
    Returns on first error, and following commands are not executed.

    Args:
        * commands (list of str) : List of commands to execute
    Raises:
        ProcessException : If a command fails.
    """
    logger = logging.getLogger('execute_commands')
    try:
        for cmd in commands:
            logger.debug("Executing command: %s", cmd)
            subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                universal_newlines=True, shell=True)
    except subprocess.CalledProcessError as e:
        logger.debug("Command error: %s", e.cmd, exc_info=True)
        raise ProcessException(e.cmd, e.returncode, e.output) from e
