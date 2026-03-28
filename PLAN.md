```m
Dirs:
  CONF_FILES:
    - ${XDG_CONFIG_HOME:-$HOME/.config}/mydehq/myctl.yml
    - /etc/xdg/myctl/myctl.yml

  LIB_DIRS:
    - $HOME/.local/lib/myctl
    - /usr/lib/myctl

  SRC_DIRS:
    - $HOME/.local/src/myctl
    - /usr/src/myctl

  PLUGIN_DIRS:
    - $XDG_DATA_HOME/myctl/plugins
    - /usr/share/myctl/plugins
    - /usr/local/share/myctl/plugins
```

~/.config/myde -> /etc/myde
~/.cache/myde -> /var/cache/myde
~/.local/bin -> /usr/bin
~/.local/lib -> /usr/lib
~/.local/src -> /usr/src
~/.local/share -> /usr/share

## Module permissions

```
audio        # volume, mic, sinks, sources
display      # brightness, wallpapers, display config
input        # keyboard, mouse, touchpad
network      # wifi, bluetooth, networking
power        # suspend, hibernate, power profiles
services     # systemctl --user, loginctl, services
notification # notifications

filesystem::user   # read/write files outside module scope in user scope
filesystem::root   # read/write files outside module scope in root scope

process      # kill, nice, renice, signals
hardware     # direct hardware control (rfkill, backlight sysfs)

package      # install/remove packages
privileged   # requires sudo or elevated rights
```

# ADD breaking changes prompt in cz commit
