# Keyboard Mapper

A tool for Linux desktops to map keys of dedicated keyboards to specific actions.

[RSBasic](https://www.rsbasic.de) developed a similar application for Windows which got me to the idea of developing something like that for Linux.

## Requirements

* Python 3.6+
* Python modules: See [requirements.txt](requirements.txt) (`pip3 install -r requirements.txt`)

## Installation

* Download the [latest release](https://github.com/Programie/KeyboardMapper/releases/latest)
* Install Python modules using pip: `pip3 install -r requirements.txt`

## Initial configuration

Usually, you want your desktop session to ignore any input from the device you want to use for Keyboard Mapper.

In case of X11, just add a new InputClass section to your X server configuration:

```
Section "InputClass"
	Identifier      "some unique identifier choosen by you"
	MatchIsKeyboard "on"
	MatchProduct    "The product name of the input device (see "xinput list")"
	Option          "Ignore" "true"
EndSection
```

For Wayland, the easiest way to ignore the device is to assign it to a different seat using a udev rule (for example using seat1 instead of seat0):

```
ACTION=="add", SUBSYSTEM=="input", KERNEL=="event*", ATTRS{idVendor}=="ID_OF_THE_VENDOR", ATTRS{idProduct}=="ID_OF_THE_PRODUCT", ENV{ID_SEAT}="seat1"
```

In both cases, also make sure your user has the permission to access the device files (located in `/dev/input`). This can be done by adding your user to the `input` group or set ACLs on the used input devices to allow your user to read them.

After that, you can start the application and select the input devices to use in the settings as shown bellow.

![](screenshots/Settings.png)

## Usage

Starting the application will present you the main window:

![](screenshots/Main_Window.png)

Add your first entry by clicking the "Add shortcut" button in the toolbar or selecting it from the application menu. This action will open the "Edit shortcut" window:

![](screenshots/Edit_Shortcut.png)

Click the "Click to set shortcut" button which will prompt you to press the key (or multiple keys in combination) on the input device to use for your shortcut.

After that, select one of the following actions to do once you press the key:

* Launch application: Select one of your installed applications to launch
* Execute command: Execute the specified command (including all arguments which should be passed to it)
* Open folder: Select any folder you would like to open in your default file browser
* Input text: Send any text to the currently active window (uses the clipboard and sends Ctrl+V to the currently active window)
* Input key sequence: Send any sequence of key combinations to the currently active window (e.g. "Control_L+N Control_L+W" would send Ctrl+N and Ctrl+W)
* Lock keys: Toggle locking of all other actions (only respond to shortcuts with the "Lock keys" action)

## Known issues

### Application theme is different from other applications

When installing PyQt5 using pip, it's possible that the application does not use the native desktop theme. In that case, simply install PyQt5 using your package manager.

In case of Debian based Linux distributions (e.g. Ubuntu, Mint, etc.) install PyQt5 using the following command:

```
sudo apt-get install python3-pyqt5
```

After that you should remove PyQt5 which has been installed by pip using `pip3 uninstall PyQt5`. Otherwise, the application continues to use PyQt5 installed with pip.
