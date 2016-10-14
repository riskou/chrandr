# chrandr

Change xrandr screen configuration in a gui.

Currently in (slow) development.

##### Features

- Display a list of configurations (HDMI+laptop, only laptop, ...).
- Only availables options are selectables (i.e. if HDMI is not connected).
- When applied, an option executes a list of shell commands (defined in configuration file).

##### History (my life)

To activate HDMI, I used shell scripts to run xrandr/amixer/pulseaudio commands. It worked...
Later, and to learn python, I decided to create a gui to launch these commands.

You see the result : A gui to launch shell commands, wow it's a revolution :smile:

## Dependencies

- Python 3
- GTK 3 (3.12 or more)
- `xrandr` shell command
- `gi` module (gobject introspection or python3-gi)
- Optionnaly `xdg` module

## Installation

- Clone repository and install chrandr :
```sh
  $ git clone git@github.com:riskou/chrandr.git
  $ cd chrandr/
  $ python3 setup.py install
```
- Execute `chrandr`.
- Modify the created configuration file : see [Configuration](#configuration).

## Documentation

### Configuration

Sorry no configuration gui, you have to edit the configuration file manually.

Default configuration filename is `$XDG_CONFIG_HOME/chrandr/chrandr.conf`
(i.e. `~/.config/chrandr/chrandr.conf`).
You could use another one with `chrandr --config <filename>`.

An example is available in [doc/chrandr.conf](doc/chrandr.conf).

## License

chrandr is licensed under the [MIT license](LICENSE).
