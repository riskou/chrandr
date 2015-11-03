# -*- coding: utf-8 -*-

"""
chrandr - Change screen configuration in a gui.

Let the user to choose between a few list of outputs configurations.
By default, opens a GUI.

--------------
Configuration
--------------
* By default, stored in ~/.config/chrandr/chrandr.conf
* ini like format
* Outputs configuration must be written by hand.
  Use xrandr command to list ports and to test commands.

Example::
    # general options
    [chrandr]
    status_file = <status filename>

    # output exemple : the output code is 'vga'
    [vga]
    # text shown on the radio button
    title = Use only VGA
    # list (comma separated) of ports needed to be connected
    ports = VGA-1
    # list (comma separated) of shell commands
    commands : xrandr --output LVDS-1 --off --output VGA-1 --auto,
        amixer set Master unmute

With this configuration exemple, if the user selects this choice,
  the 2 xrandr commands are executed (one by one).
"""

import os
import os.path
import sys
import logging
import argparse
import signal
import subprocess
import re
import pprint
import pkg_resources

import configparser
import json

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gi.repository import Gtk

import chrandr

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


class ChRandrUI:
    """
    The chrandr GTK user interface.

    Fields:
        * config (ChrandrConfig) : Configuration used in the UI
        * selected_data (XrandrConfig) : Selected configuration,
          could be None
        * window (Gtk.Window) : The GTK Window
    """

    def __init__(self, config):
        """Constructor with the list of XrandrConfig configurations."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.selected_data = None
        builder = Gtk.Builder()
        # load glade file using pkg_resources
        glade_path = os.path.join('ui', 'simple_gui.glade')
        glade_content = pkg_resources.resource_string(__name__, glade_path)
        builder.add_from_string(str(glade_content, encoding='utf-8'))
        self.logger.debug("Loading GTK UI from pkg resource")
        self.window = builder.get_object('window')
        self._box_choices = builder.get_object('box_radio')
        self._button_apply = builder.get_object('button_apply')
        # radio button not shown to the user, permits to unselect all "reals" radios
        self._fake_radio_button = None
        self._init_choices()
        # connect callbacks signals
        builder.connect_signals(self)

    def _init_choices(self):
        """Initialize choices list (radio buttons) with all configurations."""
        self._fake_radio_button = Gtk.RadioButton.new_with_label_from_widget(None, "(fake button)")
        but = self._fake_radio_button
        for cfg in self.config.randr:
            button = Gtk.RadioButton.new_with_label_from_widget(but, cfg.title)
            button.connect('toggled', self.on_select_choice, cfg)
            cfg.widget = button
            self._box_choices.pack_start(button, True, True, 2)

    def _apply_choice(self):
        """Execute commands associated with the selected choice."""
        if self.selected_data:
            self.logger.debug("Apply the output code '%s' : %s", self.selected_data.code,
                self.selected_data.title)
            # TODO ERROR : encapsulate with try except
            self.selected_data.execute()
            # update the active configuration in the status file
            self.config.save_active_randr(self.selected_data)
            # reset field and button
            self.selected_data = None
            self._button_apply.set_sensitive(False)

    def on_select_choice(self, widget, cfg_data):
        """
        Gtk callback when a radio button is selected.

        Args:
            widget (Gtk.RadioButton): the selected radio button
            cfg_data (XrandrConfig): the randr configuration associated with the radio button
        """
        if widget.get_active():
            self.logger.debug("Output code '%s' (%s) is selected", cfg_data.code, cfg_data.title)
            self.selected_data = cfg_data
            self._button_apply.set_sensitive(True)
        else:
            # maybe not needed, because a radio is unselected only if another is selected
            self.selected_data = None

    def on_click_cancel(self, *args, **kwargs):
        """Gtk callback when cancel button is pressed, method name defined in glade file."""
        Gtk.main_quit()

    def on_click_refresh(self, *args, **kwargs):
        """
        Refresh UI with availables configurations or not.
        Gtk callback when refresh button is pressed, method name defined in glade file.
        """
        self.logger.debug("Refresh availables configurations...")
        connected_outputs = chrandr.get_connected_outputs()
        # active the fake radio to unselect "reals" radios
        self._fake_radio_button.set_active(True)
        for cfg in self.config.randr:
            cfg.widget.set_sensitive(cfg.available(connected_outputs))
            if self.config.active is not None and cfg.code == self.config.active:
                # note: it calls on_select_choice()
                cfg.widget.set_active(True)
        # reset fields set by on_select_choice()
        self.selected_data = None
        self._button_apply.set_sensitive(False)

    def on_click_apply(self, *args, **kwargs):
        """Gtk callback when apply button is pressed, method name defined in glade file."""
        self._apply_choice()

    def on_click_ok(self, *args, **kwargs):
        """Gtk callback when ok button is pressed, method name defined in glade file."""
        self._apply_choice()
        Gtk.main_quit()


def _configure_logging(args):
    """Configure application logging."""
    log_root = logging.getLogger()
    if args.verbose:
        log_root.setLevel(logging.DEBUG)
        log_handler = logging.StreamHandler(sys.stdout)
        log_formatter = logging.Formatter(
            "%(asctime)s:%(levelname)s:%(name)s: %(message)s",
            '%H:%M:%S')
    else:
        log_root.setLevel(logging.INFO)
        log_handler = logging.StreamHandler(sys.stderr)
        log_formatter = logging.Formatter(
            os.path.basename(sys.argv[0]) + ":%(asctime)s:%(levelname)s:%(name)s: %(message)s",
            '%H:%M:%S')
    # add to format for debugging :
    #   function name : %(funcName)s
    log_handler.setFormatter(log_formatter)
    log_root.addHandler(log_handler)


def main():
    """Entry point of chrandr."""
    current_version = pkg_resources.get_distribution('chrandr').version
    if current_version is None:
        current_version = 'dev'
    # command line arguments
    parser = argparse.ArgumentParser(
        description="Change screen configuration."
    )
    parser.add_argument('--version', action='version', version="%(prog)s " + current_version)
    parser.add_argument('--verbose', help="verbose output messages", action='store_true')
    parser.add_argument('--config', help="set the configuration file")

    args = parser.parse_args()
    # configure logging
    _configure_logging(args)
    logger = logging.getLogger(__name__)

    # restore default signal handler on SIGINT
    # see also : https://bugzilla.gnome.org/show_bug.cgi?id=622084
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if args.config:
        config = ChrandrConfig(args.config)
    else: # else load default filename
        config = ChrandrConfig()

    if not os.access(config.filename, os.R_OK):
        logger.info("No configuration file, creating the default...")
        # TODO set a flag into the UI to popup an information dialog
        config.create()
    else:
        config.load()
    #except FileNotFoundError as e:
    #    sys.stderr.write(sys.argv[0] + ": Failed to open the configuration file : " + str(e) + "\n")
    #    sys.exit(1)

    # initialize GTK, create and open the window
    Gtk.init()
    ui = ChRandrUI(config)
    # first refresh of availables configurations
    GObject.idle_add(lambda ui:ui.on_click_refresh(), ui)
    ui.window.show_all()
    Gtk.main()

