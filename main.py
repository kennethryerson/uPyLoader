import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from src.helpers.pyinstaller_helper import PyInstallerHelper
from src.utility.settings import Settings

__author__ = "Ivan Sevcik"

def onHotswap():
    """Called when the source of this module has changed.
    When a function named 'onHotswap' is present in a module,
    this function is called after the module is reloaded.
    This should be used to trigger a redisplay of the screen or
    in general to discard cached results that are to be calculated
    again using the new method definitions.
    If onHotswap is not defined the module is reloaded anyway, but afterwards
    no further actions are performed. In this case the changed code has to be
    activated some other way like minimizing and restoring the window to be
    repainted.
    """
    print("Update!")
    for widget in myApp.allWidgets():
        widget.update()

# Main Function
def main(argv=None):
    if argv is None:
        import sys

        argv = sys.argv
    # Create main app
    global myApp
    myApp = QApplication(sys.argv)
    myApp.setQuitOnLastWindowClosed(True)

    path = PyInstallerHelper.resource_path("icons\\main.png")

    icon = QIcon(path)
    myApp.setWindowIcon(icon)

    try:
        sys.argv.index("--debug")
        Settings().debug_mode = True
    except ValueError:
        pass

    ex2 = MainWindow()
    ex2.show()

    # Execute the Application and Exit
    sys.exit(myApp.exec_())

if __name__ == '__main__':
    main()
