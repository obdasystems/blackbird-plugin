import sys

from PyQt5.QtWidgets import QMainWindow, QApplication

from eddy.core.functions.fsystem import fread
from eddy.core.plugin import PluginSpec, PluginManager
from eddy.plugins.blackbird.blackbird import BlackbirdPlugin

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = QMainWindow()
    spec = PluginSpec(PluginManager.spec(fread('./plugin.spec')))
    bbp = BlackbirdPlugin(spec, mw)
    bbp.showDialog("Blackbird")
    app.exec_()
