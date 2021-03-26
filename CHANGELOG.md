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