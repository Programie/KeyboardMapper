# Keyboard Mapper

A tool for Linux desktops to map keys of a dedicated keyboard to specific actions.

[RSBasic](https://www.rsbasic.de) developed a similar application for Windows which got me to the idea of developing something like that for Linux.

## How does it look like?

Main window:

![](screenshots/Main_Window.png)

Edit shortcut:

![](screenshots/Edit_Shortcut.png)

Settings:

![](screenshots/Settings.png)

## Installation

Download the latest release from the [release page on GitLab](https://gitlab.com/Programie/KeyboardMapper/tags).

## Initial configuration

In order to let the X server ignore the input from the keyboard used dedicated for your actions, you have to configure that in your X server configuration:

```
Section "InputClass"
	Identifier      "some unique identifier choosen by you"
	MatchIsKeyboard "on"
	MatchProduct    "The product name of the keyboard (see "xinput list")"
	Option          "Ignore" "true"
EndSection
```

Also make sure, your user has the permission to access the device files.

After that, you can start the application and select the input device in the settings (usually a device file in `/dev/input`).

## Usage

Add your first entry by clicking the "Add shortcut" button in the toolbar or selecting it from the application menu.

The following actions are available for each shortcut:

* Launch application: Select one of your installed applications to launch
* Execute command: Execute the specified command (including all arguments which should be passed to it)
* Open folder: Select any folder you would like to open in your default file explorer
* Input text: Send any text to the currently active window (uses the clipboard and sends Ctrl+V to the currently active window)
* Input key sequence: Send any sequence of key combinations to the currently active window (e.g. "Control_L+N Control_L+W" would send Ctrl+N and Ctrl+W)
* Lock keys: Toggle locking of all other actions (only respond to shortcuts with the "Lock keys" action)