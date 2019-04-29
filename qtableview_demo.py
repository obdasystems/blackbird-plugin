''' pqt_tableview3.py
explore PyQT's QTableView Model
using QAbstractTableModel to present tabular data
allow table sorting by clicking on the header title
used the Anaconda package (comes with PyQt4) on OS X
(dns)
'''

# coding=utf-8

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import QRectF, QObject, QAbstractTableModel, QPointF
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QTableView, QGraphicsWidget, QGraphicsProxyWidget, \
    QVBoxLayout, QTableWidget, QWidget, QGroupBox, QGraphicsItem, QFrame, QAbstractItemView, QTableWidgetItem, QLabel, \
    QApplication

from eddy import ORGANIZATION, APPNAME, WORKSPACE
from eddy.core.datatypes.common import IntEnum_, Enum_
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.functions.misc import first, isEmpty, rstrip, snapF
from eddy.core.functions.path import expandPath
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.diagram import Diagram
from eddy.core.functions.signals import connect, disconnect
from eddy.core.items.common import AbstractLabel, Polygon
from eddy.core.items.edges.common.base import AbstractEdge
from eddy.core.items.edges.inclusion import InclusionEdge
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.concept import ConceptNode
from eddy.core.items.nodes.facet import FacetNode
from eddy.core.plugin import AbstractPlugin
from eddy.core.project import Project

from math import sin, cos, radians, pi as M_PI

from eddy.core.functions.geometry import createArea
from eddy.core.regex import RE_CAMEL_SPACE


class MyWindow(QWidget):
    def __init__(self, widget,*args):
        QWidget.__init__(self, *args)
        # setGeometry(x_pos, y_pos, width, height)
        self.setGeometry(70, 150, 1326, 582)
        self.setWindowTitle("ORKAVAKKA!!")


        layout = QVBoxLayout(self)
        layout.addWidget(widget)
        self.setLayout(layout)

    @staticmethod
    def getQTableWidgetSize(qTable):
        w = 0  # qTable.verticalHeader().width() + 4  # +4 seems to be needed
        for i in range(qTable.columnCount()):
            w += qTable.columnWidth(i)  # seems to include gridline (on my machine)
        h = 0  # qTable.horizontalHeader().height() + 4
        for i in range(qTable.rowCount()):
            h += qTable.rowHeight(i)
        return QtCore.QSize(w, h)


if __name__ == '__main__':
    app = QApplication([])

    tableW = QTableWidget()
    tableW.setRowCount(5)
    tableW.setColumnCount(3)
    tableW.setColumnWidth(0, 100)
    tableW.setColumnWidth(1, 300)
    tableW.setColumnWidth(2, 300)
    tableW.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    tableW.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    tableW.setMaximumSize(MyWindow.getQTableWidgetSize(qTable=tableW))
    tableW.setMinimumSize(MyWindow.getQTableWidgetSize(qTable=tableW))
    tableW.verticalHeader().setVisible(False)
    tableW.horizontalHeader().setVisible(False)
    tableW.setShowGrid(False)
    tableW.setFrameStyle(QFrame.NoFrame)
    tableW.setEditTriggers(QAbstractItemView.DoubleClicked)
    tableW.setSelectionMode(QAbstractItemView.SingleSelection)
    # tableW.setEditTriggers(QAbstractItemView.NoEditTriggers)
    # tableW.setStyleSheet("QTableView {selection-background-color: red;}")

    widgItem = QTableWidgetItem("AZZAROLA!!!")
    flags = widgItem.flags()
    flags ^= QtCore.Qt.ItemIsEditable
    flags ^= QtCore.Qt.ItemIsSelectable
    flags ^= QtCore.Qt.ItemIsUserCheckable
    widgItem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
    #widgItem.setFlags(flags)

    tableW.setItem(1, 1, widgItem)

    win = MyWindow(tableW)
    win.show()
    # win.table_model.setDataList(dataList)
    # timer = threading.Timer(10, timer_func, (win, dataList2))
    # timer.start()
    app.exec_()