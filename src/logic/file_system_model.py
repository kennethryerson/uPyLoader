from PyQt5.QtCore import Qt, QModelIndex,QFileInfo
from PyQt5.QtGui import QStandardItem
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QFileIconProvider
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QMenu

from src.connection.connection import Connection
from src.gui.icons import Icons
from src.utility.exceptions import OperationError

import os

class FileSystemModel(QStandardItemModel):
    class _Data:
        def __init__(self, path, is_dir=False):
            self.path = path
            self.is_dir = is_dir

    def __init__(self, parent=None, is_local=True):
        super().__init__(parent)
        self.is_local = is_local
        self.setHorizontalHeaderLabels(["Name"])

    def isDir(self, index):
        return self.data(index, Qt.UserRole).is_dir

    def filePath(self, index):
        return self.data(index, Qt.UserRole).path

    def index(self, row_or_path, column: int = 0, parent: QModelIndex = ...):
        # For integer row, use existing implementation
        if isinstance(row_or_path, int):
            return super().index(row_or_path, column, parent)
        if not isinstance(row_or_path, str):
            raise ValueError("First argument not integer nor string")

        # Find path in model
        path = row_or_path
        items_path = [QModelIndex()]
        while items_path:
            for r in range(self.rowCount(items_path[0])):
                idx = self.index(r, 0, items_path[0])
                if self.filePath(idx) == path:
                    return idx
                if self.hasChildren(idx):
                    # noinspection PyTypeChecker
                    items_path.append(idx)
            items_path.pop(0)
        return QModelIndex()

    @staticmethod
    def _assign_icon(filename, is_dir):
        if filename.endswith("py"):
            # py and mpy
            icon = Icons().tree_python
        else:
            iconProvider = QFileIconProvider()
            if is_dir:
                fileInfo= iconProvider.Folder
            else:
                fileInfo = QFileInfo(filename)
            icon = iconProvider.icon(fileInfo)

        return icon

    def _add_entry(self, file_path, parent):
        if self.is_local:
            # Here we can use the path
            is_dir = os.path.isdir(file_path)
            _,fn = os.path.split(file_path)
        else:
            fn = file_path[1:]
            if file_path[0] == "#":
                is_dir = True
            else:
                is_dir = False

        item = QStandardItem(fn)
        item.setIcon(self._assign_icon(fn, is_dir))
        item.setData(self._Data(fn,is_dir), Qt.UserRole)
        item.setEditable(False)
        parent.appendRow(item)
        return item

    def _process_list(self, file_list):
        for x in file_list:
            self._add_entry(x, self)

    def refresh(self, connection, folder):
        self.removeRows(0, self.rowCount())
        if self.is_local:
            #Sanitize and join the parent folder
            output = []
            try:
                folder_list = os.listdir(folder)
            except Exception as e:
                #Handle access denied and other issues
                print(e)
                folder_list = []

            for fn in ['..']+folder_list:
                if fn.startswith(".git") or fn == '__pycache__' or \
                        fn.startswith('.ipynb') or fn.endswith('.bak') or \
                        fn.endswith('~') or fn.endswith('.pyc'):
                    continue
                output.append(os.path.join(folder,fn))

            if os.path.split(folder)[1] == '':
                output.pop(0)
        else:
            assert isinstance(connection, Connection)
            try:
                output = connection.list_files(folder)
                if folder != "/":
                    output = ["#.."]+output
            except OperationError:
                # Ignore error now, we have fallback option
                output = []

        self._process_list(output)


