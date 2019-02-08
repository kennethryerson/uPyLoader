from threading import Timer

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtWidgets import QListView


class FileListView(QListView):
    def __init__(self, parent=None, is_local=True):
        super().__init__(parent)

        self.is_local = is_local
        self.context_menu = QMenu(self)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        # We keep a dictionary of actions...
        self.actions = {}


    def _add_menu_action(self, title, handler):
        if title.startswith("|"):
            title = title[1:]
            self.context_menu.addSeparator()

        action = QAction(title, self.context_menu)
        action.triggered.connect(handler)
        self.context_menu.addAction(action)
        self.actions[title] = action

        return action

    def showContextMenu(self, pt):
        self.context_menu.exec_(QCursor.pos())
