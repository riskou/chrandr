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
from chrandr.config import ChrandrConfig


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

