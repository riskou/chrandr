# -*- coding: utf-8 -*-
"""
chrandr - Configuration classes
"""

import os
import os.path
import sys
import logging
import re
import pprint

import configparser
import json


# TODO Instead, use xdg lib and create directory
"""Default configuration filename in ~/.config/ directory."""
DEFAULT_CONFIG_FILENAME = '~/.config/chrandr/chrandr.conf'
# TODO Instead, use xdg lib and create directory in /run/user/$UID/chrandr
DEFAULT_STATUS_FILENAME = '~/.config/chrandr/chrandr.state'


class XrandrConfig:
    """
    Represents a XRandR configuration.

    Fields:
        * code (str): Configuration code
        * title (str): Configuration title (used in the radio button)
        * ports (str list): List of xrandr ports, ie ['VGA', 'HDMI']
        * commands (str list): List of commands to execute
        * widget (Gtk.RadioButton): Gtk button, None after constructor
    """

    def __init__(self, code, title, ports, commands):
        """Constructs a xrandr configuration."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.code = code
        self.title = title
        self.ports = ports
        self.commands = commands

    def __str__(self):
        return "XrandrConfig(code={})".format(self.code)
    def __repr__(self):
        return self.__str__()

    def available(self, connected_outputs):
        """
        Returns if this configuration is available (True) or not (False).

        Args:
            * connected_outputs (list of str): List of connected
              outputs, ie ['VGA', 'DVI']
        Returns:
            True if this configuration is available,
            False otheriwse.
        """
        for port in self.ports:
            if port not in connected_outputs:
                return False
        return True

    def execute(self):
        """
        Execute all commands associated with this configuration.
        """
        try:
            for cmd in self.commands:
                self.logger.debug("Executing command: %s", cmd)
                subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                    universal_newlines=True, shell=True)
        except subprocess.CalledProcessError as e:
            self.logger.error("xrandr error: %s", e.output, exc_info=True)
            # TODO ERROR CHECK : re-raise the exception


class ChrandrConfig:
    """
    Chrandr configuration.
    Loaded from an ini-like configuration file (using configparser.ConfigParser).

    Fields:
        * filename (str) : Chrandr configuration filename
        * status_filename (str): Chrandr status filename
        * randr (XrandrConfig list): List of defined xrandr configurations
        * active (str): Current active configuration code
    """

    def __init__(self, filename=DEFAULT_CONFIG_FILENAME):
        """
        Initialize a configuration.

        Args:
            filename (str): Filename to load, default to DEFAULT_CONFIG_FILENAME
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.filename = os.path.expanduser(filename)
        self.status_filename = os.path.expanduser(DEFAULT_STATUS_FILENAME)
        self.randr = []
        self.active = None

    def create(self):
        """
        Create the default configuration.
        """
        # example configuration
        title = 'This is an chrandr configuration example'
        ports = []
        commands = [ "xmessage \"You've launch the example configuration :)\"",
            "echo \"Another command of the example\"" ]
        self.randr.append(XrandrConfig('example', title, ports, commands))
        self.logger.debug("Configuration created")
        # save the newly configuration
        self.save()

    def load(self):
        """
        Load the configuration from a file.

        Raises:
            FileNotFoundError: If filename cannot be read.
        """
        if not os.access(self.filename, os.R_OK):
            raise FileNotFoundError("Cannot open or read the file: " + self.filename)
        self.logger.debug("Loading the configuration file : %s", self.filename)
        config = configparser.ConfigParser()
        config.add_section('chrandr')
        config.read(self.filename, encoding='UTF-8')

        self.status_filename = os.path.expanduser(config.get('chrandr', 'status_file',
            fallback=DEFAULT_STATUS_FILENAME))
        # read all randr configurations
        self.randr = []
        for code in config.sections():
            if code != 'chrandr': # ignore general configuration
                # TODO Check that all items exists in the current section
                title = config.get(code, 'title', fallback=code)
                ports_raw = config.get(code, 'ports')
                ports = list(filter(None, (x.strip() for x in ports_raw.split(','))))
                commands_raw = config.get(code, 'commands', fallback='')
                commands = list(filter(None, (x.strip() for x in commands_raw.split(','))))
                self.randr.append(XrandrConfig(code, title, ports, commands))
                self.logger.debug("Output %s needs ports: %s", code, pprint.pformat(ports))
        self.logger.debug("%d randr outputs loaded", len(self.randr))

        # read the active configuration
        self.logger.debug("Loading status file in %s", self.status_filename)
        status = configparser.ConfigParser()
        status.read(self.status_filename, encoding='UTF-8')
        if status.has_option('chrandr', 'active'):
            self.active = status.get('chrandr', 'active')
        else:
            self.active = None
        self.logger.debug("Active configuration code loaded is : %s", self.active)

    def save(self):
        """
        Save the configuration.

        Important: Due to ConfigParser implementation, all comments are removed when writing the file.
        """
        config = configparser.ConfigParser()
        config.add_section('chrandr')
        config.read(self.filename, encoding='UTF-8')
        # set configurations values into the configparser
        config.set('chrandr', 'status_file', self.status_filename)
        for randr in self.randr:
            if not config.has_section(randr.code):
                config.add_section(randr.code)
            config.set(randr.code, 'title', randr.title)
            config.set(randr.code, 'ports', ','.join(randr.ports))
            config.set(randr.code, 'commands', ',\n'.join(randr.commands))
        with open(self.filename, 'w') as configfile:
            config.write(configfile, space_around_delimiters=True)
        self.logger.debug("Configuration saved")

    def save_active_randr(self, randr_config):
        """
        Save the current active XrandrConfig configuration in the status file.

        Important: Due to ConfigParser implementation, all comments are removed when writing the file.

        Args:
            randr_config (XrandrConfig): Configuration to set as active
        """
        status = configparser.ConfigParser()
        status.add_section('chrandr')
        if randr_config is None:
            status.set('chrandr', 'active', '')
            self.active = None
        else:
            status.set('chrandr', 'active', randr_config.code)
            self.active = randr_config.code
        with open(self.status_filename, 'w') as statusfile:
            status.write(statusfile, space_around_delimiters=True)
        self.logger.debug("Active configuration (code %s) saved", self.active)
