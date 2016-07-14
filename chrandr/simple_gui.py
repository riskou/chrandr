# -*- coding: utf-8 -*-
"""
chrandr - Very simple gui.

Let the user to choose randr configuration in a radio button list.
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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gi.repository import Gtk

import chrandr.utils
import chrandr.config
from chrandr.config import ChrandrConfig


class ChRandrErrorDialog:
    """
    Error dialog with command output
    """
    def __init__(self, parent_window):
        # self._logger = logging.getLogger(self.__class__.__name__)
        builder = Gtk.Builder()
        # load glade file using pkg_resources
        glade_path = os.path.join('ui', 'error_dialog.glade')
        glade_content = pkg_resources.resource_string(__name__, glade_path)
        builder.add_from_string(str(glade_content, encoding='utf-8'))
        self.dialog = builder.get_object('dialog_error')
        self._entry_command = builder.get_object('entry_command')
        self._textbuffer_output = builder.get_object('textbuffer_output')
        # connect callbacks signals
        builder.connect_signals(self)
        self.dialog.set_transient_for(parent_window)

    def on_click_close(self, *args, **kwargs):
        self.dialog.response(Gtk.ResponseType.CLOSE)

    def show(self, command, output=None):
        self._entry_command.set_text(str(command))
        if output:
            self._textbuffer_output.set_text(str(output), -1)
        else:
            self._textbuffer_output.set_text("", -1)
        self.dialog.run()
        self.dialog.destroy()



class ChRandrSimpleUI:
    """
    A very simple gui for chrandr.

    Fields:
        * config (ChrandrConfig) : Configuration used in the UI
        * window (Gtk.Window) : The GTK Window
    """

    def __init__(self, config):
        """
        Constructor with the configuration.

        Args:
            * config (ChrandrConfig) : Configuration to use
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self._widgets = []
        builder = Gtk.Builder()
        # load glade file using pkg_resources
        glade_path = os.path.join('ui', 'simple_gui.glade')
        glade_content = pkg_resources.resource_string(__name__, glade_path)
        builder.add_from_string(str(glade_content, encoding='utf-8'))
        self._logger.debug("Loading GTK UI from pkg resource")
        self.window = builder.get_object('chrandr')
        self._box_content = builder.get_object('box_content')
        # connect callbacks signals
        builder.connect_signals(self)

    def _apply_randr(self, widget, randr):
        """
        Execute commands associated with the selected choice.

        Args:
            * widget (Gtk.ToggleButton) : Button widget
            * randr (RandrConfig) : Configuration to apply
        """
        self._logger.debug("Apply the output code '%s' : %s", randr.code, randr.title)
        # search previous selected button and unselect it
        for wid in self._widgets:
            if wid.get_active() and wid != widget:
                wid.set_active(False)

        try:
            if not randr.commands:
                self._logger.debug("Code '%s' : No command to execute.", randr.code);
            else:
                chrandr.utils.execute_commands(randr.commands)
        except chrandr.utils.ProcessException as e:
            self.config.save_active_randr(None)
            widget.set_active(False)
            # display the error
            popup = ChRandrErrorDialog(self.window)
            popup.show(e.cmd, e.output)
        else:
            # update the active configuration in the status file
            self.config.save_active_randr(randr)

    def on_select_choice(self, widget, cfg_data):
        """
        Gtk callback when a button is clicked.

        Args:
            widget (Gtk.ToggleButton): the clicked button
            cfg_data (XrandrConfig): the randr configuration associated with the button
        """
        if widget.get_active():
            # self._logger.debug("Output code '%s' is selected", cfg_data.code)
            self._apply_randr(widget, cfg_data)

    def on_click_refresh(self, *args, **kwargs):
        """
        Refresh UI with availables configurations or not.
        Gtk callback when refresh button is pressed, method name defined in glade file.
        """
        self._logger.debug("Refresh availables configurations...")
        outputs = chrandr.utils.get_connected_outputs()
        # Destroy previous widgets
        for wid in self._widgets:
            wid.destroy()
        self.widgets = []

        availables = filter(lambda r: r.available(outputs), self.config.randr)
        for cfg in availables:
            if cfg.title:
                widget = Gtk.ToggleButton.new_with_label(cfg.title)
            else:
                widget = Gtk.ToggleButton.new()
            if cfg.icon and cfg.icon != "":
                widget.set_image(Gtk.Image.new_from_file(cfg.icon))
                widget.set_image_position(Gtk.PositionType.TOP)
            # select the active configuration
            if self.config.active is not None and cfg.code == self.config.active:
                widget.set_active(True)
            widget.connect('toggled', self.on_select_choice, cfg)
            self._widgets.append(widget)
            self._box_content.pack_start(widget, True, True, 0)
        self._box_content.show_all()

    def on_click_close(self, *args, **kwargs):
        """Gtk callback when close button is pressed, method name defined in glade file."""
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
        log_root.setLevel(logging.WARN)
        log_handler = logging.StreamHandler(sys.stderr)
        log_formatter = logging.Formatter(
            os.path.basename(sys.argv[0]) + ": %(asctime)s:%(levelname)s:%(name)s: %(message)s",
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

    if args.config is None:
        config_filename = chrandr.config.DEFAULT_CONFIGURATION_FILENAME
        if not os.path.exists(config_filename):
            logger.info("Create default configuration file: %s", config_filename)
            try:
                chrandr.config.create_default_configuration(config_filename)
            except Exception as e:
                logger.error("Failed to create default configuration", exc_info=True)
                sys.stderr.write(sys.argv[0] + ": Failed to create the configuration file : " + str(e) + "\n")
                sys.exit(1)
    else:
        config_filename = os.path.expanduser(args.config)

    config = ChrandrConfig(config_filename)
    try:
        config.load()
    except FileNotFoundError as e:
        sys.stderr.write(sys.argv[0] + ": Failed to open the configuration file : " + str(e) + "\n")
        sys.exit(1)

    # initialize GTK, create and open the window
    Gtk.init()
    ui = ChRandrSimpleUI(config)
    # first refresh of availables configurations
    GObject.idle_add(lambda ui:ui.on_click_refresh(), ui)
    ui.window.show_all()
    Gtk.main()

