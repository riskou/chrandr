# chrandr - TODO list

#### Various
- Get command output and check return code.
- Change how to get connected ouputs, instead of executing `xrandr` :
  - Use python3-xlib module ?
  - From GDK ? **To try** :
    https://developer.gnome.org/gdk3/3.18/GdkScreen.html#gdk-screen-get-monitor-plug-name

#### GUI
- Better gui.
- Create a configuration gui.

#### Create a daemon mode.
Goal : When a monitor is connected, show a notification permitting to open the gui.

- To detect the monitor plug/unplug, maybe using GDK :
  https://developer.gnome.org/gdk3/3.18/GdkScreen.html#GdkScreen-monitors-changed
