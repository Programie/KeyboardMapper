# Keyboard Mapper

A tool for Linux desktops to map keys of a dedicated keyboard to specific actions.

[RSBasic](https://www.rsbasic.de) developed a similar application for Windows which got me to the idea of developing something like that for Linux.

## Installation

Download the latest release from the release page on GitLab.

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

There are three possible actions available for each shortcut:

* Execute command: Execute the specified command (including all arguments which should be passed to it)
* Open folder: Select any folder you would like to open in your default file explorer
* Input text: Send any text to the currently active window (**not implemented yet!**)