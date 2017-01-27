from PyQt5.QtCore import QDir
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QKeySequenceEdit
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QWidgetItem

from gui.settings import Ui_SettingsDialog
from src.setting import Settings


class SettingsDialog(QDialog, Ui_SettingsDialog):
    def __init__(self, parent):
        super(SettingsDialog, self).__init__(parent, Qt.WindowCloseButtonHint)
        self.setupUi(self)
        self.setModal(True)

        # Workaround because UI compiler doesn't recognize QKeySequenceEdit
        # Create new items
        new_line_key_edit = SettingsDialog.one_key_sequence_edit(self.terminalGroupBox, "newLineKeyEdit")
        send_key_edit = SettingsDialog.one_key_sequence_edit(self.terminalGroupBox, "sendKeyEdit")
        # Replace old items in layout
        self.terminalFormLayout.replaceWidget(self.newLineKeyEdit, new_line_key_edit)
        self.terminalFormLayout.replaceWidget(self.sendKeyEdit, send_key_edit)
        # Set parent to None effectively removing old items
        self.newLineKeyEdit.setParent(None)
        self.sendKeyEdit.setParent(None)
        # Replace references
        self.newLineKeyEdit = new_line_key_edit
        self.sendKeyEdit = send_key_edit

        if Settings().external_editor_path:
            self.externalPathLineEdit.setText(Settings().external_editor_path)
        if Settings().external_editor_args:
            self.externalCommandLineEdit.setText(Settings().external_editor_args)
        self.externalPathBrowseButton.clicked.connect(self.browse_external_editor)

        self.newLineKeyEdit.setKeySequence(Settings().new_line_key)
        self.sendKeyEdit.setKeySequence(Settings().send_key)
        self.tabSpacesSpinBox.setValue(Settings().terminal_tab_spaces)
        self.holdAutoscrollCheckBox.setChecked(Settings().terminal_hold_scroll)

        self.accepted.connect(self.save_settings)

    def browse_external_editor(self):
        path = QFileDialog().getOpenFileName(
            caption="Select external editor",
            directory=QDir().homePath(),
            options=QFileDialog.ReadOnly)

        if path[0]:
            self.externalPathLineEdit.setText(path[0])

    def save_settings(self):
        Settings().external_editor_path = self.externalPathLineEdit.text()
        Settings().external_editor_args = self.externalCommandLineEdit.text()
        Settings().new_line_key = self.newLineKeyEdit.keySequence()
        Settings().send_key = self.sendKeyEdit.keySequence()
        Settings().terminal_tab_spaces = self.tabSpacesSpinBox.value()
        Settings().terminal_hold_scroll = self.holdAutoscrollCheckBox.isChecked()

    @staticmethod
    def one_key_sequence_edit(parent, name):
        edit = QKeySequenceEdit(parent)
        edit.setObjectName(name)

        return edit
