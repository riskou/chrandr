# -*- coding: utf-8 -*-

"""
chrandr - Change screen configuration in a gui.
"""

import os
import os.path
import sys
import logging
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
