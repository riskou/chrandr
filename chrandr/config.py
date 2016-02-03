# -*- coding: utf-8 -*-
"""
chrandr - Configuration classes/utils
"""

import os
import os.path
import logging
import pprint

import configparser


# Generate the default configuration filename
try:
    from xdg import BaseDirectory
    _config_dir = BaseDirectory.save_config_path('chrandr')
except ImportError:
    logger = logging.getLogger(__name__)
    logger.info("xdg module not found")
    _config_dir = os.path.expanduser(os.path.join('~', '.config', 'chrandr'))
DEFAULT_CONFIGURATION_FILENAME = os.path.join(_config_dir, 'chrandr.conf')


def _get_status_filename():
    """
    Get the status filename.
    Filename generated from xdg module, in $XDG_RUNTIME_DIR or in /tmp (in this order).
    """
    logger = logging.getLogger('_get_status_filename')
    status_basename = 'chrandr.state'
    runtime_dir = None
    try:
        from xdg import BaseDirectory
        runtime_dir = BaseDirectory.get_runtime_dir()
    except ImportError:
        logger.info("xdg module not found")
        runtime_dir = os.getenv('XDG_RUNTIME_DIR')
    except KeyError:
        pass
    if runtime_dir is None:
        logger.debug("No environment variable XDG_RUNTIME_DIR")
        # no runtime dir, use /tmp
        import tempfile
        runtime_dir = tempfile.gettempdir()
        status_basename = 'chrandr.' + str(os.getuid()) + '.state'
    filename = os.path.join(runtime_dir, status_basename)
    logger.debug("Status filename: %s", filename)
    return filename


class RandrConfig:
    """
    Represents a RandR configuration.

    Fields:
        * code (str): Configuration code
        * title (str): Configuration title (used in the radio button)
        * ports (str list): List of xrandr ports, ie ['VGA', 'HDMI']
        * commands (str list): List of commands to execute
    """

    def __init__(self, code, title=None, ports=None, commands=None):
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
            * connected_outputs (list of str): List of connected outputs, ie ['VGA', 'DVI']
        Returns:
            True if this configuration is available,
            False otheriwse.
        """
        if self.ports:
            for port in self.ports:
                if port not in connected_outputs:
                    return False
        return True


class ChrandrConfig:
    """
    Chrandr configuration.
    Loaded from an ini-like configuration file (using configparser.ConfigParser).

    Fields:
        * filename (str) : Chrandr configuration filename
        * status_filename (str): Chrandr status filename
        * default (str) : Default randr configuration code to use if no active choice
        * fallback (RandrConfig) : The fallback configuration
        * randr (RandrConfig list): List of defined xrandr configurations
        * active (str): Current active configuration code
    """

    def __init__(self, filename):
        """
        Initialize a configuration.

        Args:
            filename (str): Filename to load
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self.filename = os.path.expanduser(filename)
        self.status_filename = _get_status_filename()
        self.default = None
        self.fallback = None
        self.randr = []
        self.active = None

    def _load_randr(self, config, section_name):
        """Load a RandrConfig from the ConfigParser in argument and return it."""
        title = config.get(section_name, 'title', fallback=section_name)
        ports_raw = config.get(section_name, 'ports', fallback=None)
        ports = None
        if ports_raw is not None:
            ports = list(filter(None, (x.strip() for x in ports_raw.split(','))))
        commands_raw = config.get(section_name, 'commands', fallback='')
        commands = list(filter(None, (x.strip() for x in commands_raw.split('\n'))))
        return RandrConfig(section_name, title, ports, commands)

    def _save_randr(self, config, rc):
        """Save a RandrConfig (rc) into the ConfigParser (config)."""
        if rc.code not in config:
            config[rc.code] = {}
        if rc.title is not None:
            config[rc.code]['title'] = rc.title
        if rc.ports is not None:
            config[rc.code]['ports'] = ','.join(rc.ports)
        config[rc.code]['commands'] = '\n'.join(rc.commands)

    def load(self):
        """
        Load the configuration from a file.

        Raises:
            FileNotFoundError: If filename cannot be read.
        """
        if not os.access(self.filename, os.R_OK):
            raise FileNotFoundError("Cannot open or read the file: " + self.filename)
        self._logger.debug("Loading the configuration file : %s", self.filename)
        config = configparser.ConfigParser()
        config['general'] = {}
        config.read(self.filename, encoding='UTF-8')

        # general options
        self.default = config.get('general', 'default', fallback=None)
        if 'fallback' in config:
            self.fallback = self._load_randr(config, 'fallback')
        # read all randr configurations
        self.randr = []
        for code in config.sections():
            if code != 'general' and code != 'fallback':
                self.randr.append(self._load_randr(config, code))
        self._logger.debug("%d randr outputs loaded", len(self.randr))

        # read the active configuration
        self._logger.debug("Loading status file in %s", self.status_filename)
        status = configparser.ConfigParser()
        status.read(self.status_filename, encoding='UTF-8')
        if 'chrandr' in status and 'active' in status['chrandr']:
            self.active = status['chrandr']['active']
        else:
            # state file does not exist (or does not contain active value) => use default
            self.active = self.default
        self._logger.debug("Active configuration code is : %s", self.active)

    def save(self):
        """
        Save the configuration.

        Important: Due to ConfigParser implementation, all comments are removed when writing the file.
        """
        config = configparser.ConfigParser()
        config['general'] = {}
        config.read(self.filename, encoding='UTF-8')
        # set configurations values into the configparser
        if self.default is not None:
            config['general']['default'] = self.default
        if self.fallback is not None:
            self._save_randr(config, self.fallback)
        for i in self.randr:
            self._save_randr(config, i)
        with open(self.filename, 'w') as fd:
            config.write(fd, space_around_delimiters=True)
        self._logger.debug("Configuration saved")

    def save_active_randr(self, randr_config):
        """
        Save the current active configuration in the status file.

        Important: Due to ConfigParser implementation, all comments are removed when writing the file.

        Args:
            * randr_config (RandrConfig): Configuration to set as active
        """
        status = configparser.ConfigParser()
        status['chrandr'] = {}
        if randr_config is None:
            status['chrandr']['active'] = ''
            self.active = None
        else:
            status['chrandr']['active'] = randr_config.code
            self.active = randr_config.code
        with open(self.status_filename, 'w') as statusfile:
            status.write(statusfile, space_around_delimiters=True)
        self._logger.debug("Active configuration (code '%s') saved", self.active)


def create_default_configuration(filename):
    """
    Create the default configuration.

    Args;
        * filename (str) : Filename to create.
    """
    logger = logging.getLogger('create_default_configuration')
    config_dir = os.path.dirname(filename)
    if not os.path.isdir(config_dir):
        logger.debug("Create configuration directory %s", config_dir)
        os.makedirs(config_dir, 0o700)
    cfg = ChrandrConfig(filename)
    cfg.default = 'example'
    cfg.fallback = RandrConfig('fallback', commands=[])
    # example configuration
    title = 'This is an chrandr configuration example'
    ports = []
    commands = [ "xmessage \"You've launch the example configuration :)\"",
        "echo \"Another command of the example\"" ]
    cfg.randr.append(RandrConfig('example', title, ports, commands))
    # save the newly configuration
    cfg.save()
