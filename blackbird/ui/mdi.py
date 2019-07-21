from PyQt5 import QtCore, QtGui
from eddy.ui.mdi import MdiSubWindow


class BlackBirdMdiSubWindow(MdiSubWindow):
    """
    This class implements the MDI area subwindow.
    """
    sgnCloseEvent = QtCore.pyqtSignal()

    def __init__(self, view, label, parent=None):
        """
        Initialize the subwindow
        :type view: DiagramView
        :type parent: QWidget
        """
        super().__init__(view,parent)
        self.setWindowIcon(QtGui.QIcon(':/blackbird/icons/128/ic_blackbird'))
        self.setWindowTitle(label)


    def closeEvent(self, closeEvent: QtGui.QCloseEvent) -> None:
        self.sgnCloseEvent.emit()
        super().closeEvent(closeEvent)