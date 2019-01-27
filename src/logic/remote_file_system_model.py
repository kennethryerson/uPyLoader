from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QStandardItem
from PyQt5.QtGui import QStandardItemModel

from src.connection.connection import Connection
from src.gui.icons import Icons
from src.utility.exceptions import OperationError


class RemoteFileSystemModel(QStandardItemModel):
    class _Data:
        def __init__(self, path, is_dir=False):
            self.path = path
            self.is_dir = is_dir

    def __init__(self, parent=None):
        super().__init__(parent)
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
        icon = Icons().tree_file
        if is_dir:
            icon = Icons().tree_folder
        elif filename.endswith(".py"):
            icon = Icons().tree_python
        return icon

    def _add_entry(self, mcu_path, parent):
        fn = mcu_path[1:]
        if mcu_path[0] == "#":
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
        assert isinstance(connection, Connection)
        try:
            output = connection.list_files(folder)
            print(folder, output)

            if folder != "/":
                output = ["#.."]+output

            self._process_list(output)
            return
        # Ignore error now, we have fallback option
        except OperationError:
            pass

