# chrandr

Graphical command launcher for screen configuration.

### Features

- Display a list of configurations (HDMI and laptop, only laptop, ...).
- Only availables options are displayed. Availability depends on connected screens.
- When an option is selected, configured shell commands are executed.

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

An example is available in [docs/chrandr.conf](docs/chrandr.conf).

## License

chrandr is licensed under the [MIT license](LICENSE).
