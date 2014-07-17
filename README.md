# chrandr
Change (x)randr screen configuration in a gui.

Currently in (slow) development, but it works (at least for me).

## Dependencies
- Python 3 (tested with 3.4.1)
- GTK 3 (tested with 3.12)
- xrandr (tested with 1.4.1)
- Python module gi (gobject introspection or python3-gi)

## Installation
- Install dependencies.
- Download the file [chrandr](chrandr).
- Create configuration file (see [Configuration](#Configuration)).
- Execute `chrandr`.

## Documentation

### Configuration
Sorry no configuration gui, you have to write it manually.
Example in [data/chrandr.conf](data/chrandr.conf).

Configuration filename could be set with `chrandr --config <filename>`.
By default `~/.config/chrandr/chrandr.conf`.

### Preferred configuration
The preferred configuration is used to apply configuration when desktop session starts.

Configuration list is set in configuration file with `preferN` options.
Execute it with `chrandr --prefer`.

## License
chrandr is licensed under the [MIT license](LICENSE).
