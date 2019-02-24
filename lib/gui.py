import copy
import enum
import os
import subprocess
import sys
from typing import List, Union

from PySide2 import QtWidgets, QtGui, QtCore

from lib.config import Config
from lib.constants import APP_WEBSITE, DEVICES_BASE_DIR, APP_NAME, APP_DESCRIPTION, ICONS_DIR
from lib.desktopfiles import DesktopFilesFinder, DesktopFile
from lib.keylistener_manager import KeyListenerManager, AllowedActions
from lib.shortcut import Shortcuts, Shortcut, Actions, Action


class LockKeysEvent(QtCore.QEvent):
    def __init__(self):
        super().__init__(QtCore.QEvent.Type.User)


class ShortcutListHeader(enum.Enum):
    NAME, ACTION, KEY, DEVICE = range(4)


class MainWindow(QtWidgets.QMainWindow):
    instance: "MainWindow" = None

    def __init__(self, shortcuts: Shortcuts, key_listener_manager: KeyListenerManager):
        super().__init__()

        # Required by other classes which don't know this instance
        MainWindow.instance = self

        self.shortcuts = shortcuts
        self.key_listener_manager = key_listener_manager

        # Let shortcuts know how to handle the lock keys action (Shortcuts don't know anything about the Key Listener, Main Window, etc)
        Shortcuts.lock_keys_handler = lambda: QtWidgets.QApplication.postEvent(self, LockKeysEvent())

        self.setGeometry(QtWidgets.QStyle.alignedRect(QtCore.Qt.LeftToRight, QtCore.Qt.AlignCenter, self.size(), QtWidgets.QApplication.desktop().availableGeometry()))

        menu_bar = QtWidgets.QMenuBar()

        file_menu = QtWidgets.QMenu("File")
        file_menu.addAction("Settings...", self.show_settings)
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.quit)

        self.add_shortcut_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-new"), "Add shortcut...")
        self.add_shortcut_action.triggered.connect(self.add_shortcut)

        self.edit_shortcut_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-edit"), "Edit shortcut...")
        self.edit_shortcut_action.triggered.connect(self.edit_shortcut)

        self.remove_shortcut_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("delete"), "Remove shortcut...")
        self.remove_shortcut_action.setShortcut(QtGui.QKeySequence("Del"))
        self.remove_shortcut_action.triggered.connect(self.remove_shortcut)

        self.edit_menu = QtWidgets.QMenu("Edit")
        self.edit_menu.addAction(self.add_shortcut_action)
        self.edit_menu.addAction(self.edit_shortcut_action)
        self.edit_menu.addAction(self.remove_shortcut_action)

        help_menu = QtWidgets.QMenu("Help")
        help_menu.addAction("Help", self.show_help).setShortcut(QtGui.QKeySequence("F1"))
        help_menu.addSeparator()
        help_menu.addAction("About", self.show_about)

        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(self.edit_menu)
        menu_bar.addMenu(help_menu)

        self.setMenuBar(menu_bar)

        toolbar = self.addToolBar("Edit")

        toolbar.addAction(self.add_shortcut_action)
        toolbar.addAction(self.edit_shortcut_action)
        toolbar.addAction(self.remove_shortcut_action)

        statusbar = QtWidgets.QStatusBar()
        self.statusbar_text = QtWidgets.QLabel()
        self.statusbar_lock_state = QtWidgets.QPushButton()
        self.statusbar_lock_state.setIcon(QtGui.QIcon.fromTheme("object-locked"))
        self.statusbar_lock_state.setToolTip("Shortcuts locked, click to unlock")
        self.statusbar_lock_state.hide()
        self.statusbar_lock_state.clicked.connect(self.toggle_lock_keys)
        statusbar.addWidget(self.statusbar_text)
        statusbar.addPermanentWidget(self.statusbar_lock_state)
        self.setStatusBar(statusbar)

        self.shortcut_tree_view = QtWidgets.QTreeView()
        self.shortcut_tree_view.setAlternatingRowColors(True)
        self.shortcut_tree_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.shortcut_tree_view_model = QtGui.QStandardItemModel(0, 4)
        self.shortcut_tree_view_model.setHeaderData(ShortcutListHeader.NAME.value, QtCore.Qt.Horizontal, "Name")
        self.shortcut_tree_view_model.setHeaderData(ShortcutListHeader.ACTION.value, QtCore.Qt.Horizontal, "Action")
        self.shortcut_tree_view_model.setHeaderData(ShortcutListHeader.KEY.value, QtCore.Qt.Horizontal, "Key")
        self.shortcut_tree_view_model.setHeaderData(ShortcutListHeader.DEVICE.value, QtCore.Qt.Horizontal, "Device")
        self.shortcut_tree_view.setModel(self.shortcut_tree_view_model)

        self.shortcut_tree_view.setColumnWidth(ShortcutListHeader.NAME.value, 300)
        self.shortcut_tree_view.setColumnWidth(ShortcutListHeader.ACTION.value, 300)
        self.shortcut_tree_view.setColumnWidth(ShortcutListHeader.KEY.value, 50)
        self.shortcut_tree_view.setColumnWidth(ShortcutListHeader.DEVICE.value, 100)

        self.shortcut_tree_view.selectionModel().selectionChanged.connect(self.update_edit_actions)

        self.shortcut_tree_view.doubleClicked.connect(self.edit_item)

        self.shortcut_tree_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.shortcut_tree_view.customContextMenuRequested.connect(self.show_context_menu)

        self.setCentralWidget(self.shortcut_tree_view)

        self.tray_icon: QtWidgets.QSystemTrayIcon = None
        self.update_tray_icon()

        self.load_from_shortcuts()
        self.shortcut_tree_view.setCurrentIndex(self.shortcut_tree_view_model.index(0, 0))

        self.update_edit_actions()

    def create_tray_icon(self):
        if self.tray_icon:
            return

        tray_menu = QtWidgets.QMenu()

        tray_menu.addAction("Show window", self.show)
        tray_menu.addSeparator()
        tray_menu.addAction("Quit", self.quit)

        self.tray_icon = QtWidgets.QSystemTrayIcon(parent=self)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.handle_tray_icon_activation)

    def update_status_bar(self):
        message = []

        shortcuts = len(self.shortcuts.get_list())
        if shortcuts == 1:
            message.append("1 Shortcut")
        else:
            message.append("{} shortcuts".format(shortcuts))

        self.statusbar_text.setText(" ".join(message))

    def update_tray_icon(self):
        if Config.use_tray_icon and QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            icon_name = ["appicon", Config.icons]

            if self.key_listener_manager.allowed_actions == AllowedActions.LOCK_KEYS:
                icon_name.append("disabled")

            self.create_tray_icon()
            self.tray_icon.setIcon(QtGui.QIcon(os.path.join(ICONS_DIR, "{}.png".format("-".join(icon_name)))))
            self.tray_icon.show()
        elif self.tray_icon:
            self.tray_icon.hide()

    def update_edit_actions(self):
        selected = bool(len(self.shortcut_tree_view.selectedIndexes()))

        self.edit_shortcut_action.setEnabled(selected)
        self.remove_shortcut_action.setEnabled(selected)

    def show_context_menu(self, position):
        self.edit_menu.exec_(self.shortcut_tree_view.mapToGlobal(position))

    def add_list_item(self, shortcut: Shortcut, row: int = None):
        model = self.shortcut_tree_view_model

        if row is None:
            model.appendRow([])
            row = model.rowCount() - 1
        else:
            model.insertRow(row)

        model.setData(model.index(row, ShortcutListHeader.NAME.value), shortcut.name)
        model.setData(model.index(row, ShortcutListHeader.ACTION.value), shortcut.get_action_name())
        model.setData(model.index(row, ShortcutListHeader.KEY.value), shortcut.key)
        model.setData(model.index(row, ShortcutListHeader.DEVICE.value), shortcut.device)

    def load_from_shortcuts(self):
        self.shortcut_tree_view_model.removeRows(0, self.shortcut_tree_view_model.rowCount())

        for shortcut in self.shortcuts.get_list().values():
            self.add_list_item(shortcut)

        self.update_status_bar()

    def edit_item(self, model_index: QtCore.QModelIndex = None):
        if model_index is None:
            shortcut = None
        else:
            device = model_index.siblingAtColumn(ShortcutListHeader.DEVICE.value).data()
            key = model_index.siblingAtColumn(ShortcutListHeader.KEY.value).data()
            shortcut = self.shortcuts.get_by_device_key(device, key)

        EditShortcutWindow(self, shortcut)

    def show_settings(self):
        SettingsWindow(self)

    def quit(self):
        sys.exit()

    def add_shortcut(self):
        self.edit_item(None)

    def edit_shortcut(self):
        selected_indexes: List[QtCore.QModelIndex] = self.shortcut_tree_view.selectedIndexes()

        if len(selected_indexes) == 0:
            return

        self.edit_item(selected_indexes[0])

    def remove_shortcut(self):
        selected_indexes: List[QtCore.QModelIndex] = self.shortcut_tree_view.selectedIndexes()

        if len(selected_indexes) == 0:
            return

        response = QtWidgets.QMessageBox.question(self, "Remove shortcut", "Are you sure to remove the shortcut '{}'?".format(selected_indexes[0].siblingAtColumn(ShortcutListHeader.NAME.value).data()))

        if response != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        index = selected_indexes[0]
        device = index.siblingAtColumn(ShortcutListHeader.DEVICE.value).data()
        key = index.siblingAtColumn(ShortcutListHeader.KEY.value).data()

        self.shortcuts.remove_by_device_key(device, key)
        self.shortcut_tree_view_model.removeRow(index.row())
        self.shortcuts.save()
        self.update_status_bar()

    def show_help(self):
        subprocess.run(["xdg-open", APP_WEBSITE])

    def show_about(self):
        QtWidgets.QMessageBox.aboutQt(self, "About")

    def handle_tray_icon_activation(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    def closeEvent(self, event: QtGui.QCloseEvent):
        # Only hide if the tray icon is available
        if self.tray_icon:
            self.hide()
            event.ignore()

    def event(self, event: QtCore.QEvent):
        if isinstance(event, LockKeysEvent):
            self.toggle_lock_keys()

        return super().event(event)

    def toggle_lock_keys(self):
        if self.key_listener_manager.allowed_actions == AllowedActions.ALL:
            self.key_listener_manager.allowed_actions = AllowedActions.LOCK_KEYS
            self.statusbar_lock_state.show()
        elif self.key_listener_manager.allowed_actions == AllowedActions.LOCK_KEYS:
            self.key_listener_manager.allowed_actions = AllowedActions.ALL
            self.statusbar_lock_state.hide()

        self.update_tray_icon()


class EditShortcutWindow(QtWidgets.QDialog):
    def __init__(self, main_window: MainWindow, shortcut: Shortcut):
        super().__init__(main_window)

        self.main_window = main_window

        self.original_shortcut = shortcut

        if shortcut:
            self.shortcut = copy.copy(shortcut)
            self.setWindowTitle("Edit shortcut")
        else:
            self.shortcut = Shortcut()
            self.setWindowTitle("Add shortcut")

        self.setModal(True)

        self.dialog_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.dialog_layout)

        self.shortcut_button: QtWidgets.QPushButton = None
        self.add_shortcut_button()

        self.name_field: QtWidgets.QLineEdit = None
        self.add_name_field()

        self.action_options = []
        self.action_launch_application_list: QtWidgets.QComboBox = None
        self.execute_command_field: QtWidgets.QLineEdit = None
        self.open_folder_field: QtWidgets.QLineEdit = None
        self.input_text_field: QtWidgets.QLineEdit = None
        self.input_key_sequence_field: QtWidgets.QLineEdit = None
        self.add_action_options()

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.dialog_layout.addWidget(button_box)

        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.close)

        self.show()
        self.setFixedSize(self.size())

    def add_shortcut_button(self):
        group_box = QtWidgets.QGroupBox("Shortcut")
        self.dialog_layout.addWidget(group_box)

        self.shortcut_button = QtWidgets.QPushButton()
        self.update_shortcut_button()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.shortcut_button)
        group_box.setLayout(layout)

        self.shortcut_button.clicked.connect(self.request_shortcut)

    def add_name_field(self):
        group_box = QtWidgets.QGroupBox("Name")
        self.dialog_layout.addWidget(group_box)

        if self.shortcut.name is None:
            text = ""
        else:
            text = self.shortcut.name

        self.name_field = QtWidgets.QLineEdit(text)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.name_field)
        group_box.setLayout(layout)

    def add_action_options(self):
        group_box = QtWidgets.QGroupBox("Action")
        self.dialog_layout.addWidget(group_box)

        layout = QtWidgets.QGridLayout()
        group_box.setLayout(layout)

        self.action_launch_application_list = QtWidgets.QComboBox()
        self.execute_command_field = QtWidgets.QLineEdit()
        self.open_folder_field = QtWidgets.QLineEdit()
        self.input_text_field = QtWidgets.QLineEdit()
        self.input_key_sequence_field = QtWidgets.QLineEdit()

        desktop_files = list(DesktopFilesFinder.load_in_known_paths())
        desktop_files.sort(key=lambda item: item.name)

        application_items = {}

        index = 0
        for desktop_file in desktop_files:
            if not desktop_file.is_visible():
                continue

            self.action_launch_application_list.addItem(desktop_file.get_icon(), desktop_file.name, desktop_file)

            application_items[desktop_file.filename] = index

            index += 1

        select_folder_button = QtWidgets.QPushButton("Browse...")
        select_folder_button.clicked.connect(self.select_folder)

        self.action_options = [
            [None, Actions.LAUNCH_APPLICATION, [self.action_launch_application_list]],
            [None, Actions.EXECUTE_COMMAND, [self.execute_command_field]],
            [None, Actions.OPEN_FOLDER, [self.open_folder_field, select_folder_button]],
            [None, Actions.INPUT_TEXT, [self.input_text_field]],
            [None, Actions.INPUT_KEY_SEQUENCE, [self.input_key_sequence_field]],
            [None, Actions.LOCK_KEYS, []]
        ]

        for row, action in enumerate(self.action_options):
            radio_button, action, fields = action

            radio_button = QtWidgets.QRadioButton(action.title)
            radio_button.clicked.connect(self.update_action_states)
            self.action_options[row][0] = radio_button
            layout.addWidget(radio_button, row, 0)

            for column, field in enumerate(fields, start=1):
                layout.addWidget(field, row, column)

            if self.shortcut.action == action.name:
                radio_button.setChecked(True)

                if action == Actions.LAUNCH_APPLICATION:
                    if self.shortcut.data in application_items:
                        self.action_launch_application_list.setCurrentIndex(application_items[self.shortcut.data])
                elif action == Actions.EXECUTE_COMMAND:
                    self.execute_command_field.setText(self.shortcut.data)
                elif action == Actions.OPEN_FOLDER:
                    self.open_folder_field.setText(self.shortcut.data)
                elif action == Actions.INPUT_TEXT:
                    self.input_text_field.setText(self.shortcut.data)
                elif action == Actions.INPUT_KEY_SEQUENCE:
                    self.input_key_sequence_field.setText(self.shortcut.data)

        self.update_action_states()

    def request_shortcut(self):
        shortcut_requester = ShortcutRequester(self, self.main_window.key_listener_manager, self.shortcut)
        shortcut_requester.accepted.connect(self.update_shortcut_button)

    def update_shortcut_button(self):
        if self.shortcut.key is None:
            text = "Click to set shortcut"
        else:
            text = str(self.shortcut.key)

        self.shortcut_button.setText(text)

    def update_action_states(self):
        for action in self.action_options:
            radio_button, action, fields = action

            enabled = radio_button.isChecked()

            for field in fields:
                field.setEnabled(enabled)

    def select_folder(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder to open", self.open_folder_field.text(), QtWidgets.QFileDialog.DontUseNativeDialog | QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks)

        if path:
            self.open_folder_field.setText(path)

    def get_selected_action(self) -> Union[Action, None]:
        for action in self.action_options:
            radio_button, action, fields = action

            if radio_button.isChecked():
                return action

        return None

    def save(self):
        self.shortcut.name = self.name_field.text().strip()

        if self.shortcut.key is None:
            QtWidgets.QMessageBox.critical(self, "No key defined", "Please define a key to use for this shortcut!")
            return

        existing_shortcut = self.main_window.shortcuts.get_by_device_key(self.shortcut.device, self.shortcut.key)

        if existing_shortcut and existing_shortcut != self.original_shortcut:
            QtWidgets.QMessageBox.critical(self, "Duplicate shortcut", "Another shortcut for key '{}' already exists!".format(self.shortcut.key))
            return

        action = self.get_selected_action()

        if action is None:
            QtWidgets.QMessageBox.critical(self, "No action selected", "Please select an action to do!")
            return

        self.shortcut.action = action.name

        if action == Actions.LAUNCH_APPLICATION:
            desktop_file: DesktopFile = self.action_launch_application_list.currentData(QtCore.Qt.ItemDataRole.UserRole)
            if desktop_file is None:
                QtWidgets.QMessageBox.critical(self, "Missing application", "Please select the application to launch!")
                return

            self.shortcut.data = desktop_file.filename
        elif action == Actions.EXECUTE_COMMAND:
            command = self.execute_command_field.text().strip()
            if command == "":
                QtWidgets.QMessageBox.critical(self, "Missing command", "Please specify the command to execute!")
                return

            self.shortcut.data = command
        elif action == Actions.OPEN_FOLDER:
            folder = self.open_folder_field.text().strip()
            if folder == "":
                QtWidgets.QMessageBox.critical(self, "Missing folder path", "Please select the path to the folder to open!")
                return

            self.shortcut.data = folder
        elif action == Actions.INPUT_TEXT:
            text = self.input_text_field.text()
            if text == "":
                QtWidgets.QMessageBox.critical(self, "Missing text", "Please specify the text to input!")
                return

            self.shortcut.data = text
        elif action == Actions.INPUT_KEY_SEQUENCE:
            key_sequence = self.input_key_sequence_field.text().strip()
            if key_sequence == "":
                QtWidgets.QMessageBox.critical(self, "Missing text", "Please specify the key sequence to input!")
                return

            self.shortcut.data = key_sequence

        if self.original_shortcut:
            self.main_window.shortcuts.remove_by_device_key(self.original_shortcut.device, self.original_shortcut.key)

            list_row = None
            list_items: List[QtGui.QStandardItem] = self.main_window.shortcut_tree_view_model.findItems(str(self.original_shortcut.key), column=ShortcutListHeader.KEY.value)
            for list_item in list_items:
                if list_item.index().siblingAtColumn(ShortcutListHeader.DEVICE.value).data() == self.original_shortcut.device:
                    list_row = list_item.row()
                    break

            self.main_window.shortcut_tree_view_model.removeRow(list_row)
        else:
            list_row = None

        self.main_window.add_list_item(self.shortcut, list_row)
        self.main_window.shortcuts.add(self.shortcut)
        self.main_window.update_status_bar()

        if list_row is not None:
            self.main_window.shortcut_tree_view.setCurrentIndex(self.main_window.shortcut_tree_view_model.index(list_row, 0))

        self.main_window.shortcuts.save()

        self.accept()


class ShortcutRequester(QtWidgets.QDialog):
    def __init__(self, parent, key_listener_manager: KeyListenerManager, shortcut: Shortcut):
        super().__init__(parent)

        self.key_listener_manager = key_listener_manager
        self.shortcut = shortcut

        self.setWindowTitle("Configure key")
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QtWidgets.QLabel("Press the key to use."))

        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        self.show()

        self.key_listener_manager.set_event_handler(self.handle_key_press)

    def handle_key_press(self, device_name, key_code):
        self.shortcut.device = device_name
        self.shortcut.key = key_code
        self.accept()

    def accept(self):
        self.key_listener_manager.use_default_event_handler()
        super().accept()

    def reject(self):
        self.key_listener_manager.use_default_event_handler()
        super().reject()


class SettingsWindow(QtWidgets.QDialog):
    def __init__(self, parent: MainWindow):
        super().__init__(parent)

        self.main_window = parent

        self.autostart_file = os.path.join(os.path.expanduser("~"), ".config", "autostart", "keyboard-mapper.desktop")

        self.setWindowTitle("Settings")
        self.setModal(True)

        self.dialog_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.dialog_layout)

        self.input_device_list: QtWidgets.QListWidget = None
        self.add_keyboard_input_device_settings()

        self.icon_theme_list: QtWidgets.QComboBox = None
        self.add_icon_theme_settings()

        self.use_tray_icon_checkbox = QtWidgets.QCheckBox("Enable tray icon")
        self.use_tray_icon_checkbox.setEnabled(QtWidgets.QSystemTrayIcon.isSystemTrayAvailable())
        self.use_tray_icon_checkbox.setChecked(Config.use_tray_icon)
        self.dialog_layout.addWidget(self.use_tray_icon_checkbox)

        self.single_instance_checkbox = QtWidgets.QCheckBox("Allow only one instance")
        self.single_instance_checkbox.setChecked(Config.single_instance)
        self.dialog_layout.addWidget(self.single_instance_checkbox)

        self.autostart_checkbox = QtWidgets.QCheckBox("Start on login")
        self.autostart_checkbox.setChecked(os.path.exists(self.autostart_file))
        self.dialog_layout.addWidget(self.autostart_checkbox)

        create_desktop_file_button = QtWidgets.QPushButton("Create desktop file")
        create_desktop_file_button.clicked.connect(self.create_app_desktop_file)
        self.dialog_layout.addWidget(create_desktop_file_button)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.dialog_layout.addWidget(button_box)

        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.close)

        self.show()
        self.setFixedSize(self.size())

    def add_keyboard_input_device_settings(self):
        group_box = QtWidgets.QGroupBox("Keyboard input device")
        self.dialog_layout.addWidget(group_box)

        self.input_device_list = QtWidgets.QListWidget()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.input_device_list)
        group_box.setLayout(layout)

        file_list: List[QtCore.QFileInfo] = QtCore.QDir(DEVICES_BASE_DIR).entryInfoList()
        for item in file_list:
            if item.isDir():
                continue

            name = item.baseName()

            list_item = QtWidgets.QListWidgetItem(name)
            list_item.setFlags(list_item.flags() | QtCore.Qt.ItemIsUserCheckable)

            if name in Config.input_devices:
                list_item.setCheckState(QtCore.Qt.Checked)
            else:
                list_item.setCheckState(QtCore.Qt.Unchecked)

            self.input_device_list.addItem(list_item)

    def add_icon_theme_settings(self):
        group_box = QtWidgets.QGroupBox("Icon theme")
        self.dialog_layout.addWidget(group_box)

        self.icon_theme_list = QtWidgets.QComboBox()
        self.icon_theme_list.addItem("bright")
        self.icon_theme_list.addItem("dark")

        self.icon_theme_list.setCurrentText(Config.icons)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.icon_theme_list)
        group_box.setLayout(layout)

    def create_desktop_file(self, filename: str, arguments: List[str]):
        desktop_file = DesktopFile(filename)

        desktop_file.name = APP_NAME
        desktop_file.comment = APP_DESCRIPTION
        desktop_file.type = "Application"
        desktop_file.categories = ["System"]
        desktop_file.exec = " ".join([os.path.realpath(sys.argv[0])] + arguments)
        desktop_file.icon = os.path.join(ICONS_DIR, "appicon-{}.png".format(Config.icons))

        desktop_file.write()

    def create_app_desktop_file(self):
        self.create_desktop_file(os.path.join(os.path.expanduser("~"), ".local", "share", "applications", "keyboard-mapper.desktop"), [])

    def save(self):
        selected_input_devices = []

        for index in range(self.input_device_list.count()):
            item = self.input_device_list.item(index)
            if item.checkState() == QtCore.Qt.Checked:
                selected_input_devices.append(item.text())

        if len(selected_input_devices) == 0:
            QtWidgets.QMessageBox.critical(self, "No keyboard input device selected", "Please select at least one input device to use!")
            return

        Config.input_devices = selected_input_devices
        Config.icons = self.icon_theme_list.currentText()
        Config.use_tray_icon = self.use_tray_icon_checkbox.checkState() == QtCore.Qt.Checked
        Config.single_instance = self.single_instance_checkbox.checkState() == QtCore.Qt.Checked

        Config.save()

        if self.autostart_checkbox.checkState() == QtCore.Qt.Checked:
            self.create_desktop_file(self.autostart_file, ["--hidden"])
        elif os.path.exists(self.autostart_file):
            os.remove(self.autostart_file)

        self.main_window.update_tray_icon()
        self.main_window.key_listener_manager.set_device_files(Config.input_devices)

        self.accept()
