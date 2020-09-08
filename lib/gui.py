import copy
import enum
import os
import subprocess
import sys
from typing import List, Union

from PySide2 import QtWidgets, QtGui, QtCore, QtPrintSupport

from lib.config import Config
from lib.constants import APP_WEBSITE, DEVICES_BASE_DIR, APP_NAME, APP_DESCRIPTION, ICONS_DIR, APP_VERSION, APP_COPYRIGHT
from lib.desktopfiles import DesktopFilesFinder, DesktopFile
from lib.keylistener_manager import KeyListenerManager, AllowedActions
from lib.shortcut import Shortcuts, Shortcut, Actions, Action
from lib.xtestwrapper import XKeys
from lib.utils import LengthUnit

translate = QtWidgets.QApplication.translate


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
        Shortcuts.instance.lock_keys.connect(self.toggle_lock_keys)
        Shortcuts.instance.execution_error.connect(lambda message: QtWidgets.QMessageBox.critical(self, APP_NAME, message))

        self.setGeometry(QtWidgets.QStyle.alignedRect(QtCore.Qt.LeftToRight, QtCore.Qt.AlignCenter, self.size(), QtWidgets.QApplication.desktop().availableGeometry()))

        menu_bar = QtWidgets.QMenuBar()

        file_menu = QtWidgets.QMenu(translate("main_window_menu", "File"))
        file_menu.addAction(translate("main_window_menu", "Settings..."), self.show_settings)
        file_menu.addAction(translate("main_window_menu", "Print labels..."), self.print_labels, QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_P))
        file_menu.addSeparator()
        file_menu.addAction(translate("main_window_menu", "Quit"), self.quit)

        self.add_shortcut_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-new"), translate("main_window_menu", "Add shortcut..."))
        self.add_shortcut_action.triggered.connect(self.add_shortcut)

        self.edit_shortcut_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-edit"), translate("main_window_menu", "Edit shortcut..."))
        self.edit_shortcut_action.triggered.connect(self.edit_shortcut)

        self.duplicate_shortcut_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-copy"), translate("main_window_menu", "Duplicate shortcut..."))
        self.duplicate_shortcut_action.triggered.connect(self.duplicate_shortcut)

        self.remove_shortcut_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("delete"), translate("main_window_menu", "Remove shortcut..."))
        self.remove_shortcut_action.setShortcut(QtGui.QKeySequence("Del"))
        self.remove_shortcut_action.triggered.connect(self.remove_shortcut)

        self.execute_shortcut_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("system-run"), translate("main_window_menu", "Execute"))
        self.execute_shortcut_action.triggered.connect(self.execute_shortcut)

        self.edit_menu = QtWidgets.QMenu(translate("main_window_menu", "Edit"))
        self.edit_menu.addAction(self.add_shortcut_action)
        self.edit_menu.addAction(self.edit_shortcut_action)
        self.edit_menu.addAction(self.duplicate_shortcut_action)
        self.edit_menu.addAction(self.remove_shortcut_action)
        self.edit_menu.addSeparator()
        self.edit_menu.addAction(self.execute_shortcut_action)

        help_menu = QtWidgets.QMenu(translate("main_window_menu", "Help"))
        help_menu.addAction(translate("main_window_menu", "Help"), self.show_help).setShortcut(QtGui.QKeySequence("F1"))
        help_menu.addSeparator()
        help_menu.addAction(translate("main_window_menu", "About"), self.show_about)

        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(self.edit_menu)
        menu_bar.addMenu(help_menu)

        self.setMenuBar(menu_bar)

        toolbar = self.addToolBar(translate("main_window_menu", "Edit"))

        toolbar.addAction(self.add_shortcut_action)
        toolbar.addAction(self.edit_shortcut_action)
        toolbar.addAction(self.duplicate_shortcut_action)
        toolbar.addAction(self.remove_shortcut_action)

        statusbar = QtWidgets.QStatusBar()
        self.statusbar_text = QtWidgets.QLabel()
        self.statusbar_lock_state = QtWidgets.QPushButton()
        self.statusbar_lock_state.setIcon(QtGui.QIcon.fromTheme("object-locked"))
        self.statusbar_lock_state.setToolTip(translate("main_window", "Shortcuts locked, click to unlock"))
        self.statusbar_lock_state.hide()
        self.statusbar_lock_state.clicked.connect(self.toggle_lock_keys)
        statusbar.addWidget(self.statusbar_text)
        statusbar.addPermanentWidget(self.statusbar_lock_state)
        self.setStatusBar(statusbar)

        self.shortcut_tree_view = QtWidgets.QTreeView()
        self.shortcut_tree_view.setAlternatingRowColors(True)
        self.shortcut_tree_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.shortcut_tree_view_model = QtGui.QStandardItemModel(0, 4)
        self.shortcut_tree_view_model.setHeaderData(ShortcutListHeader.NAME.value, QtCore.Qt.Horizontal, translate("shortcut_list_column", "Name"))
        self.shortcut_tree_view_model.setHeaderData(ShortcutListHeader.ACTION.value, QtCore.Qt.Horizontal, translate("shortcut_list_column", "Action"))
        self.shortcut_tree_view_model.setHeaderData(ShortcutListHeader.KEY.value, QtCore.Qt.Horizontal, translate("shortcut_list_column", "Key"))
        self.shortcut_tree_view_model.setHeaderData(ShortcutListHeader.DEVICE.value, QtCore.Qt.Horizontal, translate("shortcut_list_column", "Device"))
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

        tray_menu.addAction(translate("tray_menu", "Show window"), self.show)
        tray_menu.addSeparator()
        tray_menu.addAction(translate("tray_menu", "Quit"), self.quit)

        self.tray_icon = QtWidgets.QSystemTrayIcon(parent=self)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.handle_tray_icon_activation)

    def update_status_bar(self):
        message = []

        shortcuts = len(self.shortcuts.get_list())
        if shortcuts == 1:
            message.append(translate("main_window_statusbar", "1 Shortcut"))
        else:
            message.append(translate("main_window_statusbar", "{} shortcuts").format(shortcuts))

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

    def edit_item(self, model_index: QtCore.QModelIndex = None, duplicate: bool = False):
        if model_index is None:
            shortcut = None
        else:
            device = model_index.siblingAtColumn(ShortcutListHeader.DEVICE.value).data()
            key = model_index.siblingAtColumn(ShortcutListHeader.KEY.value).data()
            shortcut = self.shortcuts.get_by_device_key(device, key)

        EditShortcutWindow(self, shortcut, duplicate)

    def show_settings(self):
        SettingsWindow(self)

    def print_labels(self):
        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)

        print_dialog = QtPrintSupport.QPrintPreviewDialog(printer)
        print_dialog.paintRequested.connect(self.shortcuts.print_labels_to_printer)
        print_dialog.exec_()

    def quit(self):
        QtGui.QGuiApplication.quit()

    def add_shortcut(self):
        self.edit_item(None)

    def edit_shortcut(self):
        selected_indexes: List[QtCore.QModelIndex] = self.shortcut_tree_view.selectedIndexes()

        if len(selected_indexes) == 0:
            return

        self.edit_item(selected_indexes[0])

    def duplicate_shortcut(self):
        selected_indexes: List[QtCore.QModelIndex] = self.shortcut_tree_view.selectedIndexes()

        if len(selected_indexes) == 0:
            return

        self.edit_item(selected_indexes[0], True)

    def remove_shortcut(self):
        selected_indexes: List[QtCore.QModelIndex] = self.shortcut_tree_view.selectedIndexes()

        if len(selected_indexes) == 0:
            return

        response = QtWidgets.QMessageBox.question(self, translate("main_window", "Remove shortcut"), translate("main_window", "Are you sure to remove the shortcut '{}'?").format(selected_indexes[0].siblingAtColumn(ShortcutListHeader.NAME.value).data()))

        if response != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        index = selected_indexes[0]
        device = index.siblingAtColumn(ShortcutListHeader.DEVICE.value).data()
        key = index.siblingAtColumn(ShortcutListHeader.KEY.value).data()

        self.shortcuts.remove_by_device_key(device, key)
        self.shortcut_tree_view_model.removeRow(index.row())
        self.shortcuts.save()
        self.update_status_bar()

    def execute_shortcut(self):
        selected_indexes: List[QtCore.QModelIndex] = self.shortcut_tree_view.selectedIndexes()

        if len(selected_indexes) == 0:
            return

        model_index = selected_indexes[0]

        device = model_index.siblingAtColumn(ShortcutListHeader.DEVICE.value).data()
        key = model_index.siblingAtColumn(ShortcutListHeader.KEY.value).data()
        shortcut = self.shortcuts.get_by_device_key(device, key)

        if shortcut is None:
            return

        shortcut.execute()

    def show_help(self):
        subprocess.run(["xdg-open", APP_WEBSITE])

    def show_about(self):
        AboutDialog(self)

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
        else:
            self.quit()

    def toggle_lock_keys(self):
        if self.key_listener_manager.allowed_actions == AllowedActions.ALL:
            self.key_listener_manager.allowed_actions = AllowedActions.LOCK_KEYS
            self.statusbar_lock_state.show()
        elif self.key_listener_manager.allowed_actions == AllowedActions.LOCK_KEYS:
            self.key_listener_manager.allowed_actions = AllowedActions.ALL
            self.statusbar_lock_state.hide()

        self.update_tray_icon()


class EditShortcutWindow(QtWidgets.QDialog):
    def __init__(self, main_window: MainWindow, shortcut: Shortcut, duplicate: bool = False):
        super().__init__(main_window)

        self.main_window = main_window

        # Only store reference to original shortcut if no duplication is requested
        if duplicate:
            self.original_shortcut = None
        else:
            self.original_shortcut = shortcut

        if shortcut:
            self.shortcut = copy.copy(shortcut)
            if duplicate:
                self.setWindowTitle(translate("edit_shortcut", "Add shortcut"))
            else:
                self.setWindowTitle(translate("edit_shortcut", "Edit shortcut"))
        else:
            self.shortcut = Shortcut()
            self.setWindowTitle(translate("edit_shortcut", "Add shortcut"))

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

        self.label_icon_use_checkbox: QtWidgets.QCheckBox = None
        self.label_icon_path_field: QtWidgets.QLineEdit = None
        self.label_icon_browse_button: QtWidgets.QPushButton = None
        self.label_size_use_specific_checkbox: QtWidgets.QCheckBox = None
        self.label_size_width_field: QtWidgets.QSpinBox = None
        self.label_size_height_field: QtWidgets.QSpinBox = None
        self.add_label_options()

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.dialog_layout.addWidget(button_box)

        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.close)

        self.show()
        self.setFixedSize(self.size())

    def add_shortcut_button(self):
        group_box = QtWidgets.QGroupBox(translate("edit_shortcut", "Shortcut"))
        self.dialog_layout.addWidget(group_box)

        self.shortcut_button = QtWidgets.QPushButton()
        self.update_shortcut_button()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.shortcut_button)
        group_box.setLayout(layout)

        self.shortcut_button.clicked.connect(self.request_shortcut)

    def add_name_field(self):
        group_box = QtWidgets.QGroupBox(translate("edit_shortcut", "Name"))
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
        group_box = QtWidgets.QGroupBox(translate("edit_shortcut", "Action"))
        self.dialog_layout.addWidget(group_box)

        layout = QtWidgets.QGridLayout()
        group_box.setLayout(layout)

        # TODO: This also completes filenames but we only want directories :(
        dir_completer = QtWidgets.QCompleter()
        dir_model = QtWidgets.QFileSystemModel(dir_completer)
        dir_model.setRootPath("/")
        dir_completer.setModel(dir_model)

        self.action_launch_application_list = QtWidgets.QComboBox()
        self.execute_command_field = QtWidgets.QLineEdit()
        self.open_folder_field = QtWidgets.QLineEdit()
        self.input_text_field = QtWidgets.QLineEdit()
        self.input_key_sequence_field = QtWidgets.QLineEdit()

        self.open_folder_field.setCompleter(dir_completer)

        desktop_files_exceptions = []
        desktop_files = list(DesktopFilesFinder.load_in_known_paths(skip_on_error=True, exceptions=desktop_files_exceptions))
        desktop_files.sort(key=lambda item: item.name)

        if desktop_files_exceptions:
            message = [
                translate("edit_shortcut", "An error occurred while parsing the desktop files."),
                "",
                translate("edit_shortcut", "Errors") + ":",
            ]

            for exception in desktop_files_exceptions[:5]:
                message.append(exception)

            if len(desktop_files_exceptions) > 5:
                message.append(translate("edit_shortcut", "And {} more errors".format(len(desktop_files_exceptions))))

            message.append("")
            message.append(translate("edit_shortcut", "Those files will be skipped."))

            QtWidgets.QMessageBox.critical(self, translate("edit_shortcut", "Loading desktop files failed"), "\n".join(message))

        application_items = {}

        index = 0
        for desktop_file in desktop_files:
            if not desktop_file.is_visible():
                continue

            self.action_launch_application_list.addItem(desktop_file.get_icon(), desktop_file.name, desktop_file)

            application_items[desktop_file.filename] = index

            index += 1

        select_folder_button = QtWidgets.QPushButton(translate("edit_shortcut", "Browse..."))
        select_folder_button.clicked.connect(self.select_folder)

        build_key_sequence_button = QtWidgets.QPushButton(translate("edit_shortcut", "Edit..."))
        build_key_sequence_button.clicked.connect(self.open_key_sequence_builder)

        self.action_options = [
            [None, Actions.LAUNCH_APPLICATION, [self.action_launch_application_list]],
            [None, Actions.EXECUTE_COMMAND, [self.execute_command_field]],
            [None, Actions.OPEN_FOLDER, [self.open_folder_field, select_folder_button]],
            [None, Actions.INPUT_TEXT, [self.input_text_field]],
            [None, Actions.INPUT_KEY_SEQUENCE, [self.input_key_sequence_field, build_key_sequence_button]],
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

    def add_label_options(self):
        group_box = QtWidgets.QGroupBox(translate("edit_shortcut", "Label options"))
        self.dialog_layout.addWidget(group_box)

        layout = QtWidgets.QGridLayout()
        group_box.setLayout(layout)

        self.label_icon_use_checkbox = QtWidgets.QCheckBox(translate("edit_shortcut", "Icon"))
        self.label_icon_use_checkbox.setChecked(True if self.shortcut.label.icon_path else False)
        self.label_icon_use_checkbox.stateChanged.connect(self.update_label_widget_states)
        layout.addWidget(self.label_icon_use_checkbox, 0, 0)

        self.label_size_use_specific_checkbox = QtWidgets.QCheckBox(translate("edit_shortcut", "Size"))
        self.label_size_use_specific_checkbox.setChecked(True if self.shortcut.label.width or self.shortcut.label.height else False)
        self.label_size_use_specific_checkbox.stateChanged.connect(self.update_label_widget_states)
        layout.addWidget(self.label_size_use_specific_checkbox, 1, 0)

        self.label_background_use_checkbox = QtWidgets.QCheckBox(translate("edit_shortcut", "Background"))
        self.label_background_use_checkbox.setChecked(True if self.shortcut.label.background_color else False)
        self.label_background_use_checkbox.stateChanged.connect(self.update_label_widget_states)
        layout.addWidget(self.label_background_use_checkbox, 2, 0)

        layout.addWidget(QtWidgets.QLabel(translate("edit_shortcut", "Preview")), 3, 0)

        self.label_icon_path_field = QtWidgets.QLineEdit()
        self.label_icon_path_field.setText(self.shortcut.label.icon_path)
        layout.addWidget(self.label_icon_path_field, 0, 1)

        self.label_icon_browse_button = QtWidgets.QPushButton(translate("edit_shortcut", "Browse..."))
        self.label_icon_browse_button.clicked.connect(self.select_label_icon)
        layout.addWidget(self.label_icon_browse_button, 0, 2)

        size_layout = QtWidgets.QHBoxLayout()
        self.label_size_width_field = QtWidgets.QSpinBox()
        self.label_size_width_field.setMaximum(10000)
        self.label_size_width_field.setSuffix("mm")

        if self.shortcut.label.width is None:
            self.label_size_width_field.setValue(Config.default_label_width)
        else:
            self.label_size_width_field.setValue(self.shortcut.label.width)

        size_layout.addWidget(self.label_size_width_field, 1)

        size_layout.addWidget(QtWidgets.QLabel("x"))
        size_layout.setMargin(0)

        self.label_size_height_field = QtWidgets.QSpinBox()
        self.label_size_height_field.setMaximum(10000)
        self.label_size_height_field.setSuffix("mm")

        if self.shortcut.label.height is None:
            self.label_size_height_field.setValue(Config.default_label_height)
        else:
            self.label_size_height_field.setValue(self.shortcut.label.height)

        size_layout.addWidget(self.label_size_height_field, 1)

        layout.addLayout(size_layout, 1, 1, 1, -1)

        self.label_background_field = QtWidgets.QPushButton(translate("edit_shortcut", "Click to change color"))
        self.label_background_field.setFlat(True)
        self.label_background_field.setAutoFillBackground(True)
        self.label_background_field.clicked.connect(self.select_label_background_color)

        if self.shortcut.label.background_color:
            background_field_palette = self.label_background_field.palette()
            background_field_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(self.shortcut.label.background_color))
            self.label_background_field.setPalette(background_field_palette)

        layout.addWidget(self.label_background_field, 2, 1, 1, -1)

        self.label_preview_widget = QtWidgets.QLabel()
        self.label_preview_widget.setAutoFillBackground(True)
        self.label_preview_widget.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.label_preview_widget, 3, 1, 1, -1)

        self.update_label_preview()
        self.update_label_widget_states()

    def select_label_icon(self):
        filepath = QtWidgets.QFileDialog.getOpenFileName(self, translate("edit_shortcut", "Open label icon"), self.label_icon_path_field.text())[0]

        if filepath:
            self.label_icon_path_field.setText(filepath)
            self.update_label_preview()

    def select_label_background_color(self):
        color_dialog = QtWidgets.QColorDialog(self.label_background_field.palette().color(QtGui.QPalette.Button), self)

        if color_dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        palette = self.label_background_field.palette()
        palette.setColor(QtGui.QPalette.Button, color_dialog.selectedColor())
        self.label_background_field.setPalette(palette)
        self.update_label_preview()

    def request_shortcut(self):
        shortcut_requester = ShortcutRequester(self, self.main_window.key_listener_manager, self.shortcut)
        shortcut_requester.accepted.connect(self.update_shortcut_button)

    def update_shortcut_button(self):
        if self.shortcut.key is None:
            text = translate("edit_shortcut", "Click to set shortcut")
        else:
            text = str(self.shortcut.key)

        self.shortcut_button.setText(text)

    def update_action_states(self):
        for action in self.action_options:
            radio_button, action, fields = action

            enabled = radio_button.isChecked()

            for field in fields:
                field.setEnabled(enabled)

    def update_label_widget_states(self):
        self.label_icon_path_field.setEnabled(self.label_icon_use_checkbox.isChecked())
        self.label_icon_browse_button.setEnabled(self.label_icon_use_checkbox.isChecked())
        self.label_size_width_field.setEnabled(self.label_size_use_specific_checkbox.isChecked())
        self.label_size_height_field.setEnabled(self.label_size_use_specific_checkbox.isChecked())
        self.label_background_field.setEnabled(self.label_background_use_checkbox.isChecked())

        self.update_label_preview()

    def update_label_preview(self):
        if self.label_icon_use_checkbox.isChecked() and self.label_icon_path_field.text():
            self.label_preview_widget.setPixmap(QtGui.QPixmap(self.label_icon_path_field.text()).scaled(32, 32))

            if self.label_background_use_checkbox.isChecked():
                color = self.label_background_field.palette().color(QtGui.QPalette.Button)
            else:
                color = QtGui.QColor("white")
        else:
            self.label_preview_widget.setPixmap(QtGui.QPixmap().scaled(32, 32))
            color = QtGui.QColor("white")

        preview_palette = self.label_preview_widget.palette()
        preview_palette.setColor(QtGui.QPalette.Background, color)
        self.label_preview_widget.setPalette(preview_palette)

    def select_folder(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, translate("edit_shortcut", "Select folder to open"), self.open_folder_field.text(), QtWidgets.QFileDialog.DontUseNativeDialog | QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks)

        if path:
            self.open_folder_field.setText(path)

    def open_key_sequence_builder(self):
        key_sequence_builder = KeySequenceBuilder(self, self.input_key_sequence_field.text().strip())

        key_sequence_builder.accepted.connect(lambda: self.input_key_sequence_field.setText(key_sequence_builder.get_sequence_as_string()))

    def get_selected_action(self) -> Union[Action, None]:
        for action in self.action_options:
            radio_button, action, fields = action

            if radio_button.isChecked():
                return action

        return None

    def save(self):
        self.shortcut.name = self.name_field.text().strip()

        if self.shortcut.key is None:
            QtWidgets.QMessageBox.critical(self, translate("edit_shortcut", "No key defined"), translate("edit_shortcut", "Please define a key to use for this shortcut!"))
            return

        existing_shortcut = self.main_window.shortcuts.get_by_device_key(self.shortcut.device, self.shortcut.key)

        if existing_shortcut and existing_shortcut != self.original_shortcut:
            QtWidgets.QMessageBox.critical(self, translate("edit_shortcut", "Duplicate shortcut"), translate("edit_shortcut", "Another shortcut for key '{}' already exists!").format(self.shortcut.key))
            return

        action = self.get_selected_action()

        if action is None:
            QtWidgets.QMessageBox.critical(self, translate("edit_shortcut", "No action selected"), translate("edit_shortcut", "Please select an action to do!"))
            return

        self.shortcut.action = action.name

        if action == Actions.LAUNCH_APPLICATION:
            desktop_file: DesktopFile = self.action_launch_application_list.currentData(QtCore.Qt.ItemDataRole.UserRole)
            if desktop_file is None:
                QtWidgets.QMessageBox.critical(self, translate("edit_shortcut", "Missing application"), translate("edit_shortcut", "Please select the application to launch!"))
                return

            self.shortcut.data = desktop_file.filename
        elif action == Actions.EXECUTE_COMMAND:
            command = self.execute_command_field.text().strip()
            if command == "":
                QtWidgets.QMessageBox.critical(self, translate("edit_shortcut", "Missing command"), translate("edit_shortcut", "Please specify the command to execute!"))
                return

            self.shortcut.data = command
        elif action == Actions.OPEN_FOLDER:
            folder = self.open_folder_field.text().strip()
            if folder == "":
                QtWidgets.QMessageBox.critical(self, translate("edit_shortcut", "Missing folder path"), translate("edit_shortcut", "Please select the path to the folder to open!"))
                return

            self.shortcut.data = folder
        elif action == Actions.INPUT_TEXT:
            text = self.input_text_field.text()
            if text == "":
                QtWidgets.QMessageBox.critical(self, translate("edit_shortcut", "Missing text"), translate("edit_shortcut", "Please specify the text to input!"))
                return

            self.shortcut.data = text
        elif action == Actions.INPUT_KEY_SEQUENCE:
            key_sequence = self.input_key_sequence_field.text().strip()
            if key_sequence == "":
                QtWidgets.QMessageBox.critical(self, translate("edit_shortcut", "Missing text"), translate("edit_shortcut", "Please specify the key sequence to input!"))
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

        if self.label_icon_use_checkbox.isChecked():
            self.shortcut.label.icon_path = self.label_icon_path_field.text()
        else:
            self.shortcut.label.icon_path = None

        if self.label_size_use_specific_checkbox.isChecked():
            self.shortcut.label.width = self.label_size_width_field.value()
            self.shortcut.label.height = self.label_size_height_field.value()
        else:
            self.shortcut.label.width = None
            self.shortcut.label.height = None

        if self.label_background_use_checkbox.isChecked():
            self.shortcut.label.background_color = self.label_background_field.palette().color(QtGui.QPalette.Button).name()
        else:
            self.shortcut.label.background_color = None

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

        self.setWindowTitle(translate("shortcut_requester", "Configure key"))
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QtWidgets.QLabel(translate("shortcut_requester", "Press the key to use.")))

        cancel_button = QtWidgets.QPushButton(translate("shortcut_requester", "Cancel"))
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        self.show()
        self.setFixedSize(self.size())

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


class KeySequenceBuilder(QtWidgets.QDialog):
    def __init__(self, parent, initial_sequence: str = None):
        super().__init__(parent)

        self.setWindowTitle(translate("key_sequence_builder", "Build key sequence"))
        self.setModal(True)
        self.resize(500, 300)

        dialog_layout = QtWidgets.QVBoxLayout()
        self.setLayout(dialog_layout)

        scroll_area = QtWidgets.QScrollArea()
        dialog_layout.addWidget(scroll_area)

        scroll_area_widget = QtWidgets.QWidget()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_area_widget)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        scroll_area_widget.setLayout(self.layout)

        add_combination_button = QtWidgets.QPushButton()
        add_combination_button.setIcon(QtGui.QIcon.fromTheme("list-add"))
        add_combination_button.setToolTip(translate("key_sequence_builder", "Add key combination to sequence"))
        self.layout.addWidget(add_combination_button)

        if initial_sequence is None or initial_sequence == "":
            self.add_combination()
        else:
            for combination in initial_sequence.split(" "):
                self.add_combination(combination)

        add_combination_button.clicked.connect(lambda: self.add_combination())

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        dialog_layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.show()

    def add_combination(self, combination: str = ""):
        group_box = QtWidgets.QGroupBox(translate("key_sequence_builder", "Key combination"))
        layout = QtWidgets.QHBoxLayout()
        group_box.setLayout(layout)
        self.layout.insertWidget(self.layout.count() - 1, group_box)

        add_key_button = QtWidgets.QPushButton()
        add_key_button.setIcon(QtGui.QIcon.fromTheme("list-add"))
        add_key_button.setToolTip(translate("key_sequence_builder", "Add key to combination"))
        layout.addWidget(add_key_button)

        remove_combination_button = QtWidgets.QPushButton()
        remove_combination_button.setIcon(QtGui.QIcon.fromTheme("delete"))
        remove_combination_button.setToolTip(translate("key_sequence_builder", "Remove this key combination"))
        layout.addWidget(remove_combination_button)

        if combination == "":
            self.add_key(layout)
        else:
            for key in combination.split("+"):
                self.add_key(layout, key)

        add_key_button.clicked.connect(lambda: self.add_key(layout))
        remove_combination_button.clicked.connect(lambda: self.remove_combination(group_box))

    def remove_combination(self, group_box):
        self.layout.removeWidget(group_box)

    def add_key(self, layout, key: str = ""):
        input_field = QtWidgets.QLineEdit(key)

        completer = QtWidgets.QCompleter(list(XKeys.get_keys()))
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        input_field.setCompleter(completer)

        if layout.count() > 2:
            layout.insertWidget(layout.count() - 2, QtWidgets.QLabel("+"))

        layout.insertWidget(layout.count() - 2, input_field)

    def get_sequence(self):
        sequence = []

        for combination_index in range(self.layout.count() - 1):
            group_box = self.layout.itemAt(combination_index).widget()
            if not isinstance(group_box, QtWidgets.QGroupBox):
                continue

            combination = []

            group_box_layout = group_box.layout()
            for key_index in range(group_box_layout.count() - 1):
                input_field = group_box_layout.itemAt(key_index).widget()
                if not isinstance(input_field, QtWidgets.QLineEdit):
                    continue

                text = input_field.text().strip()
                if text == "":
                    continue

                combination.append(text)

            if not combination:
                continue

            sequence.append(combination)

        return sequence

    def get_sequence_as_string(self):
        sequence = []

        for combination in self.get_sequence():
            sequence.append("+".join(combination))

        return " ".join(sequence)


class SettingsWindow(QtWidgets.QDialog):
    def __init__(self, parent: MainWindow):
        super().__init__(parent)

        self.main_window = parent

        self.autostart_file = os.path.join(os.path.expanduser("~"), ".config", "autostart", "keyboard-mapper.desktop")

        self.setWindowTitle(translate("settings", "Settings"))
        self.setModal(True)

        self.dialog_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.dialog_layout)

        self.input_device_list: QtWidgets.QListWidget = None
        self.add_keyboard_input_device_settings()

        self.icon_theme_list: QtWidgets.QComboBox = None
        self.add_icon_theme_settings()

        self.labels_length_unit_combobox: QtWidgets.QComboBox = None
        self.labels_default_width_field: QtWidgets.QSpinBox = None
        self.labels_default_height_field: QtWidgets.QSpinBox = None
        self.labels_icon_margin_field: QtWidgets.QSpinBox = None
        self.add_labels_settings()

        self.use_tray_icon_checkbox = QtWidgets.QCheckBox(translate("settings", "Enable tray icon"))
        self.use_tray_icon_checkbox.setEnabled(QtWidgets.QSystemTrayIcon.isSystemTrayAvailable())
        self.use_tray_icon_checkbox.setChecked(Config.use_tray_icon)
        self.dialog_layout.addWidget(self.use_tray_icon_checkbox)

        self.single_instance_checkbox = QtWidgets.QCheckBox(translate("settings", "Allow only one instance"))
        self.single_instance_checkbox.setChecked(Config.single_instance)
        self.dialog_layout.addWidget(self.single_instance_checkbox)

        self.autostart_checkbox = QtWidgets.QCheckBox(translate("settings", "Start on login"))
        self.autostart_checkbox.setChecked(os.path.exists(self.autostart_file))
        self.dialog_layout.addWidget(self.autostart_checkbox)

        create_desktop_file_button = QtWidgets.QPushButton(translate("settings", "Create desktop file"))
        create_desktop_file_button.clicked.connect(self.create_app_desktop_file)
        self.dialog_layout.addWidget(create_desktop_file_button)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.dialog_layout.addWidget(button_box)

        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.close)

        self.show()
        self.setFixedSize(self.size())

    def add_keyboard_input_device_settings(self):
        group_box = QtWidgets.QGroupBox(translate("settings", "Keyboard input device"))
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
        group_box = QtWidgets.QGroupBox(translate("settings", "Icon theme"))
        self.dialog_layout.addWidget(group_box)

        self.icon_theme_list = QtWidgets.QComboBox()
        self.icon_theme_list.addItem("bright")
        self.icon_theme_list.addItem("dark")

        self.icon_theme_list.setCurrentText(Config.icons)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.icon_theme_list)
        group_box.setLayout(layout)

    def add_labels_settings(self):
        group_box = QtWidgets.QGroupBox(translate("settings", "Labels"))
        self.dialog_layout.addWidget(group_box)

        layout = QtWidgets.QGridLayout()
        group_box.setLayout(layout)

        layout.addWidget(QtWidgets.QLabel(translate("settings", "Measure unit")), 0, 0)

        self.labels_length_unit_combobox = QtWidgets.QComboBox()

        for name, unit in LengthUnit.units.items():
            self.labels_length_unit_combobox.addItem(unit.title, name)
            if Config.labels_length_unit == name:
                self.labels_length_unit_combobox.setCurrentIndex(self.labels_length_unit_combobox.count() - 1)

        self.labels_length_unit_combobox.currentIndexChanged.connect(self.update_labels_length_unit)

        layout.addWidget(self.labels_length_unit_combobox, 0, 1, 1, -1)

        layout.addWidget(QtWidgets.QLabel(translate("settings", "Default size")), 1, 0)

        size_layout = QtWidgets.QHBoxLayout()
        self.labels_default_width_field = QtWidgets.QSpinBox()
        self.labels_default_width_field.setMaximum(10000)

        if Config.default_label_width is not None:
            self.labels_default_width_field.setValue(Config.default_label_width)

        size_layout.addWidget(self.labels_default_width_field, 1)

        size_layout.addWidget(QtWidgets.QLabel("x"))
        size_layout.setMargin(0)

        self.labels_default_height_field = QtWidgets.QSpinBox()
        self.labels_default_height_field.setMaximum(10000)

        if Config.default_label_height is not None:
            self.labels_default_height_field.setValue(Config.default_label_height)

        size_layout.addWidget(self.labels_default_height_field, 1)

        layout.addLayout(size_layout, 1, 1, 1, -1)

        layout.addWidget(QtWidgets.QLabel(translate("settings", "Icon margin")), 2, 0)

        self.labels_icon_margin_field = QtWidgets.QSpinBox()
        self.labels_icon_margin_field.setMaximum(10000)
        self.labels_icon_margin_field.setValue(Config.label_icon_margin)
        layout.addWidget(self.labels_icon_margin_field, 2, 1, 1, -1)

        self.update_labels_length_unit()

    def update_labels_length_unit(self):
        unit_name = self.labels_length_unit_combobox.currentData(QtCore.Qt.UserRole)

        suffix = LengthUnit.units[unit_name].suffix

        self.labels_default_width_field.setSuffix(suffix)
        self.labels_default_height_field.setSuffix(suffix)
        self.labels_icon_margin_field.setSuffix(suffix)

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
            QtWidgets.QMessageBox.critical(self, translate("settings", "No keyboard input device selected"), translate("settings", "Please select at least one input device to use!"))
            return

        Config.input_devices = selected_input_devices
        Config.icons = self.icon_theme_list.currentText()
        Config.use_tray_icon = self.use_tray_icon_checkbox.checkState() == QtCore.Qt.Checked
        Config.single_instance = self.single_instance_checkbox.checkState() == QtCore.Qt.Checked
        Config.labels_length_unit = self.labels_length_unit_combobox.currentData(QtCore.Qt.UserRole)
        Config.default_label_width = self.labels_default_width_field.value()
        Config.default_label_height = self.labels_default_height_field.value()
        Config.label_icon_margin = self.labels_icon_margin_field.value()

        Config.save()

        if self.autostart_checkbox.checkState() == QtCore.Qt.Checked:
            self.create_desktop_file(self.autostart_file, ["--hidden"])
        elif os.path.exists(self.autostart_file):
            os.remove(self.autostart_file)

        self.main_window.update_tray_icon()
        self.main_window.key_listener_manager.set_device_files(Config.input_devices)

        self.accept()


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle(translate("about", "About"))
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout()
        layout.setMargin(20)
        layout.setSpacing(10)
        self.setLayout(layout)

        icon_pixmap = QtGui.QPixmap(os.path.join(ICONS_DIR, "appicon-{}.png".format(Config.icons)))
        icon_pixmap = icon_pixmap.scaledToHeight(64)

        icon = QtWidgets.QLabel()
        icon.setPixmap(icon_pixmap)
        layout.addWidget(icon, alignment=QtCore.Qt.AlignCenter)

        bold_font = QtGui.QFont()
        bold_font.setBold(True)

        app_name_label = QtWidgets.QLabel(APP_NAME)
        app_name_label.setFont(bold_font)
        layout.addWidget(app_name_label, alignment=QtCore.Qt.AlignCenter)

        app_version_label = QtWidgets.QLabel(APP_VERSION)
        app_version_label.setFont(bold_font)
        layout.addWidget(app_version_label, alignment=QtCore.Qt.AlignCenter)

        app_description_label = QtWidgets.QLabel(APP_DESCRIPTION)
        app_description_label.setWordWrap(True)
        layout.addWidget(app_description_label, alignment=QtCore.Qt.AlignCenter)

        copyright_label = QtWidgets.QLabel(APP_COPYRIGHT)
        layout.addWidget(copyright_label, alignment=QtCore.Qt.AlignCenter)

        website_label = QtWidgets.QLabel("<a href='{}'>{}</a>".format(APP_WEBSITE, translate("about", "View on GitLab")))
        website_label.setTextFormat(QtCore.Qt.RichText)
        website_label.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        website_label.setOpenExternalLinks(True)
        layout.addWidget(website_label, alignment=QtCore.Qt.AlignCenter)

        self.show()
        self.setFixedSize(self.size())
