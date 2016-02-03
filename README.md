# chrandr

Change (x)randr screen configuration in a gui.

Currently in (slow) development.

##### Features

- Display a list of configurations (HDMI+laptop, only laptop, ...).
- Only availables options are selectables (i.e. if HDMI is not connected).
- When applied, an option executes a list of shell commands (defined in configuration file).

##### History (my life)

To activate HDMI, I used shell scripts to run xrandr/amixer/pulseaudio commands. It worked...
Later, to learn python, I decided to create a gui to launch these commands.

You see the result : A gui to launch shell commands, wow it's a revolution :)

## Dependencies

- Python 3
- GTK 3 (3.12 or more)
- xrandr
- `gi` module (gobject introspection or python3-gi)
- Optionnaly `xdg` module.

## Installation

- Clone repository and install chrandr :
```sh
$ git clone --recursive git@github.com:riskou/chrandr.git
$ cd chrandr/
$ python3 setup.py install
```
- Execute `chrandr`.
- Modify the created configuration file : see [Configuration](#configuration).

## Documentation

### Configuration

Sorry no configuration gui, you have to edit the configuration file manually.

Configuration filename could be set with `chrandr --config <filename>`.
By default `~/.config/chrandr/chrandr.conf`.

An example is available in [docs/chrandr.conf](docs/chrandr.conf).

## TODO list

- Get command output and check return code.
- Use Xlib module to get randr informations instead of executing xrandr.
- Better gui.
- Configuration gui.

## License

chrandr is licensed under the [MIT license](LICENSE).
