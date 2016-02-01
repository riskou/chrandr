# -*- coding: utf-8 -*-
"""
chrandr - Various utilities
"""

import os
import os.path
import sys
import logging
import pprint
import subprocess
import re
import pprint
import pkg_resources


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

##
## DEV :
##   Parcourir la liste des randr à la recherche d'un code:
##   results = list(filter(lambda x: x['code'] == randr_code, self.randr))
##   code_unique = results[0}


def execute_commands(commands):
    """
    Execute a list of commands, one by one.
    Stop if a command fails.

    Args:
        * commands (list of str) : List of commands to execute
    Throws:
        TODO : If a command fails.
            The exception ontains command line and execution output.
    """
    logger = logging.getLogger('execute_commands')
    try:
        for cmd in commands:
            logger.debug("Executing command: %s", cmd)
            subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                universal_newlines=True, shell=True)
    except subprocess.CalledProcessError as e:
        logger.error("xrandr error: %s", e.output, exc_info=True)
        # TODO ERROR CHECK : re-raise the exception
