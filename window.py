import enum
import subprocess
import sys
from typing import List

from PySide2.QtCore import Qt, QModelIndex, QFile, QDir, QFileInfo
from PySide2.QtGui import QStandardItemModel, QKeySequence, QIcon, QCloseEvent, QWindow
from PySide2.QtWidgets import QTreeView, QMenuBar, QMenu, QMainWindow, QMessageBox, QAbstractItemView, QSystemTrayIcon, QDialog, QGroupBox, QListWidget, QVBoxLayout, QDialogButtonBox, QListWidgetItem, QComboBox, QCheckBox

from config import Config
from shortcut import Shortcut, Shortcuts


class MainWindow(QMainWindow):
    class ShortcutListHeader(enum.Enum):
        NAME, ACTION, KEY = range(3)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Keyboard Mapper")

        menu_bar = QMenuBar()

        file_menu = QMenu("File")
        file_menu.addAction("Settings...", self.show_settings)
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.quit)

        edit_menu = QMenu("Edit")
        edit_menu.addAction("Add shortcut...", self.add_shortcut)
        edit_menu.addAction("Edit shortcut...", self.edit_shortcut)
        edit_menu.addAction("Remove shortcut", self.remove_shortcut)

        help_menu = QMenu("Help")
        help_menu.addAction("Help", self.show_help).setShortcut(QKeySequence("F1"))
        help_menu.addSeparator()
        help_menu.addAction("About", self.show_about)

        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(edit_menu)
        menu_bar.addMenu(help_menu)

        self.setMenuBar(menu_bar)

        self.shortcut_tree_view = QTreeView()
        self.shortcut_tree_view.setAlternatingRowColors(True)
        self.shortcut_tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.shortcut_tree_view_model = QStandardItemModel(0, 3)
        self.shortcut_tree_view_model.setHeaderData(self.ShortcutListHeader.NAME.value, Qt.Horizontal, "Name")
        self.shortcut_tree_view_model.setHeaderData(self.ShortcutListHeader.ACTION.value, Qt.Horizontal, "Action")
        self.shortcut_tree_view_model.setHeaderData(self.ShortcutListHeader.KEY.value, Qt.Horizontal, "Key")
        self.shortcut_tree_view.setModel(self.shortcut_tree_view_model)

        self.shortcut_tree_view.doubleClicked.connect(lambda model_index: self.edit_item(model_index.row()))

        self.setCentralWidget(self.shortcut_tree_view)

        self.tray_icon = None
        self.init_tray_icon()

    def init_tray_icon(self):
        if Config.use_tray_icon and QSystemTrayIcon.isSystemTrayAvailable():
            tray_menu = QMenu()

            tray_menu.addAction("Show window", self.show)
            tray_menu.addSeparator()
            tray_menu.addAction("Quit", self.quit)

            self.tray_icon = QSystemTrayIcon(QIcon("icons/appicon-bright.png"))
            self.tray_icon.show()
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.handle_tray_icon_activation)

    def add_list_item(self, shortcut: Shortcut):
        model = self.shortcut_tree_view_model

        model.insertRow(0)
        model.setData(model.index(0, self.ShortcutListHeader.NAME.value), shortcut.name)
        model.setData(model.index(0, self.ShortcutListHeader.ACTION.value), shortcut.get_action_name())
        model.setData(model.index(0, self.ShortcutListHeader.KEY.value), shortcut.key)

    def load_from_shortcuts(self, shortcuts: Shortcuts):
        self.shortcut_tree_view_model.removeRows(0, self.shortcut_tree_view_model.rowCount())

        for shortcut in shortcuts.get_list().values():
            self.add_list_item(shortcut)

    def edit_item(self, row=None):
        print("Edit row {}".format(row))

    def show_settings(self):
        SettingsWindow(self)

    def quit(self):
        sys.exit()

    def add_shortcut(self):
        self.edit_item(None)

    def edit_shortcut(self):
        selected_indexes: List[QModelIndex] = self.shortcut_tree_view.selectedIndexes()

        if len(selected_indexes) == 0:
            return

        self.edit_item(selected_indexes[0].row())

    def remove_shortcut(self):
        pass

    def show_help(self):
        subprocess.run(["xdg-open", "https://gitlab.com/Programie/KeyboardMapper"])

    def show_about(self):
        QMessageBox.aboutQt(self, "About")

    def handle_tray_icon_activation(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    def closeEvent(self, event: QCloseEvent):
        # Only hide if the tray icon is available
        if self.tray_icon:
            self.hide()
            event.ignore()


class SettingsWindow(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Settings")

        self.dialog_layout = QVBoxLayout()
        self.setLayout(self.dialog_layout)

        self.input_device_list: QListWidget = None
        self.add_keyboard_input_device_settings()

        self.icon_theme_list: QComboBox = None
        self.add_icon_theme_settings()

        self.use_tray_icon_checkbox = QCheckBox("Enable tray icon")
        self.use_tray_icon_checkbox.setEnabled(QSystemTrayIcon.isSystemTrayAvailable())
        self.use_tray_icon_checkbox.setChecked(Config.use_tray_icon)
        self.dialog_layout.addWidget(self.use_tray_icon_checkbox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.dialog_layout.addWidget(button_box)

        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.close)

        self.show()

    def add_keyboard_input_device_settings(self):
        group_box = QGroupBox("Keyboard input device")
        self.dialog_layout.addWidget(group_box)

        self.input_device_list = QListWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.input_device_list)
        group_box.setLayout(layout)

        if Config.keyboard_input_device is None:
            active_device_file = None
        else:
            active_device_file = QFileInfo(Config.keyboard_input_device)

        file_list: List[QFileInfo] = QDir("/dev/input/by-id").entryInfoList()
        for item in file_list:
            if item.isDir():
                continue

            name = item.baseName()

            list_item = QListWidgetItem(name)
            self.input_device_list.addItem(list_item)

            if active_device_file and active_device_file.baseName() == name:
                self.input_device_list.setCurrentItem(list_item)

    def add_icon_theme_settings(self):
        group_box = QGroupBox("Icon theme")
        self.dialog_layout.addWidget(group_box)

        self.icon_theme_list = QComboBox()
        self.icon_theme_list.addItem("bright")
        self.icon_theme_list.addItem("dark")

        self.icon_theme_list.setCurrentText(Config.icons)

        layout = QVBoxLayout()
        layout.addWidget(self.icon_theme_list)
        group_box.setLayout(layout)

    def save(self):
        input_device_items: List[QListWidgetItem] = self.input_device_list.selectedItems()

        if len(input_device_items) == 0:
            QMessageBox.critical(self, "No keyboard input device selected", "Please selected the input device to use!")

        Config.keyboard_input_device = input_device_items[0].text()
        Config.icons = self.icon_theme_list.currentText()
        Config.use_tray_icon = self.use_tray_icon_checkbox.checkState() == Qt.Checked

        Config.save()

        self.close()
