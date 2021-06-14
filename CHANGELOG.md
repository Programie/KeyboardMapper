## 2.4 (2021-06-14)

* Do not show tree lines in shortcut list
* Show icons in shortcut list (if configured for shortcut)

## 2.3 (2021-03-26)

* Build single file executable (containing all resources)
* Translate the message "Keyboard Mapper is already running!"
* Show error message (instead of throwing an exception) if shortcuts can't be loaded due to an error in the YAML file
* Store and reload list sorting
* Track the number of executions as well as the date/time of the last execution per shortcut
* Allow printing of labels for shortcuts (to glue them on your macro keyboard)
* Added action to duplicate an existing shortcut
* Added search field to filter the shortcut list

## 2.2 (2020-07-18)

* Fixed throwing exception while sorting desktop files if desktop file can't be read
* Prevent application quit after showing error message box if only the tray icon is visible
* Added "Execute" menu item to directly execute shortcut action
* Catch UnicodeDecodeError while parsing desktop files

## 2.1 (2019-08-19)

* Skip desktop files which can't be parsed

## 2.0 (2019-04-10)

* Rewrite in Python with Qt 5
* Added support for multiple languages (currently only English and German)

**Note:** This release uses YAML to store the shortcut configuration. Previously configured shortcuts will be automatically converted to the new format.

## 1.0 (2018-12-16)

Initial release