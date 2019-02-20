# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <danielepantaleone@me.com>      #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
#  #####################                          #####################  #
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################

"""Blackbird: Ontology to relational schema translator plugin."""
from abc import ABCMeta, abstractmethod
from enum import unique
from math import radians

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import QRectF, QObject, QAbstractTableModel, QPointF, QSize, QEvent
from PyQt5.QtGui import QPen, QBrush, QIcon, QMouseEvent
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QTableView, QGraphicsWidget, QGraphicsProxyWidget, \
    QVBoxLayout, QTableWidget, QWidget, QGroupBox, QGraphicsItem, QFrame, QAbstractItemView, QTableWidgetItem, QLabel, \
    QLineEdit, QStyledItemDelegate, QStyle, QPushButton, QComboBox, QGraphicsRectItem

from eddy import ORGANIZATION, APPNAME, WORKSPACE
from eddy.core.commands.edges import CommandEdgeAnchorMove, CommandEdgeBreakpointMove
from eddy.core.commands.labels import CommandLabelChange
from eddy.core.datatypes.common import IntEnum_, Enum_
from eddy.core.datatypes.graphol import Item, Identity, Special
from eddy.core.datatypes.qt import Font
from eddy.core.functions.misc import first, isEmpty, rstrip, snapF, snap
from eddy.core.functions.path import expandPath
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.diagram import Diagram
from eddy.core.functions.signals import connect, disconnect
from eddy.core.items.common import AbstractLabel, Polygon
from eddy.core.items.edges.common.base import AbstractEdge
from eddy.core.items.edges.inclusion import InclusionEdge
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.common.label import PredicateLabel
from eddy.core.items.nodes.concept import ConceptNode
from eddy.core.items.nodes.facet import FacetNode
from eddy.core.plugin import AbstractPlugin
from eddy.core.project import Project

from math import sin, cos, radians, pi as M_PI

from eddy.core.functions.geometry import createArea, distance, projection
from eddy.core.regex import RE_CAMEL_SPACE, RE_ITEM_PREFIX


class BlackbirdPlugin(AbstractPlugin):
    """
    This plugin provides integration with Blackbird, a tool for translating an ontology into a relational schema.
    """

    def __init__(self, spec, session):
        """
        Initialises a new instance of the Blackbird plugin.
        :type spec: PluginSpec
        :type session: Session
        """
        super().__init__(spec, session)

    def initActions(self):
        #############################################
        #   MenuBar Actions
        #################################
        self.addAction(QtWidgets.QAction('Open', objectName='open', triggered=self.doOpen))
        self.addAction(QtWidgets.QAction('Save', objectName='save', triggered=self.doSave))
        self.addAction(QtWidgets.QAction('Save as', objectName='save_as', triggered=self.doSaveAs))
        self.addAction(QtWidgets.QAction('Settings', objectName='settings', triggered=self.doOpenSettings))
        self.addAction(QtWidgets.QAction('Ontology Analysis', objectName='open_ontology_analysis',
                                         triggered=self.doOpenOntologyAnalysis))
        self.addAction(QtWidgets.QAction('Entity Filter', objectName='open_entity_filter',
                                         triggered=self.doOpenEntityFilter))
        self.addAction(QtWidgets.QAction('Recap Schema Selections', objectName='open_schema_selections',
                                         triggered=self.doOpenSchemaSelections))
        self.addAction(QtWidgets.QAction('Generate Preview Schema', objectName='generate_preview_schema',
                                         triggered=self.doGeneratePreviewSchema))
        self.addAction(QtWidgets.QAction('Export Mappings', objectName='export_mappings',
                                         triggered=self.doExportMappings))
        self.addAction(QtWidgets.QAction('Export SQL Script', objectName='export_sql',
                                         triggered=self.doExportSQLScript))
        self.addAction(QtWidgets.QAction('Export Schema Diagrams', objectName='export_schema_diagrams',
                                         triggered=self.doExportSchemaDiagrams))

    def initMenus(self):
        #############################################
        #   MenuBar QMenu
        #################################
        menu = QtWidgets.QMenu('&Blackbird', objectName='menubar_menu')
        menu.addAction(self.action('open'))
        menu.addAction(self.action('save'))
        menu.addAction(self.action('save_as'))
        menu.addSeparator()
        menu.addAction(self.action('settings'))
        menu.addSeparator()
        menu.addAction(self.action('open_ontology_analysis'))
        menu.addAction(self.action('open_entity_filter'))
        menu.addAction(self.action('open_schema_selections'))
        menu.addSeparator()
        menu.addAction(self.action('generate_preview_schema'))
        menu.addAction(self.action('export_mappings'))
        menu.addAction(self.action('export_sql'))
        menu.addAction(self.action('export_diagrams'))
        self.addMenu(menu)
        # Add blackbird menu to session's menu bar
        self.session.menuBar().insertMenu(self.session.menu('tools').menuAction(), self.menu('menubar_menu'))

    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.
        :type source: QObject
        :type event: QtCore.QEvent
        :rtype: bool
        """
        if event.type() == QtCore.QEvent.Resize:
            widget = source.widget()
            widget.redraw()
        return super().eventFilter(source, event)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot('QGraphicsScene')
    def onDiagramAdded(self, diagram):
        """
        Executed whenever a diagram is added to the active project.
        """
        # connect(diagram.sgnMenuCreated, self.onMenuCreated)
        # self.showMessage("You have added a new diagram named: {}".format(diagram.name))

    @QtCore.pyqtSlot('QGraphicsScene')
    def onDiagramRemoved(self, diagram):
        """
        Executed whenever a diagram is removed from the active project.
        """
        disconnect(diagram.sgnMenuCreated, self.onMenuCreated)
        # self.showMessage("You have deleted the diagram named: {}".format(diagram.name))

    @QtCore.pyqtSlot()
    def onDiagramSelectionChanged(self):
        """
        Executed whenever the selection of the active diagram changes.
        """
        # self.showMessage("Selection changed on diagram {}".format(self.mdiSubWindow.diagram.name))

    @QtCore.pyqtSlot()
    def onDiagramUpdated(self):
        """
        Executed whenever the active diagram is updated.
        """
        # self.showMessage("Diagram {} has changed".format(self.mdiSubWindow.diagram.name))

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def onProjectItemAdded(self, diagram, item):
        """
        Executed whenever a new element is added to the active project.
        """

    # self.showMessage("Added item {} to diagram {}".format(item, diagram.name))

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def onProjectItemRemoved(self, diagram, item):
        """
        Executed whenever a new element is removed from the active project.
        """
        # self.showMessage("Removed item {} from diagram {}".format(item, diagram.name))

    @QtCore.pyqtSlot()
    def onProjectUpdated(self):
        """
        Executed whenever the current project is updated.
        """
        # self.showMessage("Project {} has been updated".format(self.session.project.name))

    @QtCore.pyqtSlot()
    def onSessionReady(self):
        """
        Executed whenever the main session completes the startup sequence.
        """
        self.debug('Connecting to project: %s', self.project.name)
        connect(self.project.sgnUpdated, self.onProjectUpdated)
        connect(self.project.sgnDiagramAdded, self.onDiagramAdded)
        connect(self.project.sgnDiagramRemoved, self.onDiagramRemoved)
        connect(self.project.sgnItemAdded, self.onProjectItemAdded)
        connect(self.project.sgnItemRemoved, self.onProjectItemRemoved)

        # self.showMessage("Blackbird plugin initialized!")

    @QtCore.pyqtSlot('QMenu', list, 'QPointF')
    def onMenuCreated(self, menu, items, pos=None):
        # self.showMessage("Constructed menu {}".format(menu))
        pass

    @QtCore.pyqtSlot()
    def doOpen(self):
        """
        Open a project in the current session.
        """
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        workspace = settings.value('workspace/home', WORKSPACE, str)
        dialog = QtWidgets.QFileDialog(self.session)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setDirectory(expandPath(workspace))
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
            self.debug('Open file requested: {}'.format(expandPath(first(dialog.selectedFiles()))))

    @QtCore.pyqtSlot()
    def doSave(self):
        """
        Save the current project.
        """
        pass

    @QtCore.pyqtSlot()
    def doSaveAs(self):
        """
        Save a copy of the current project.
        """
        pass

    @QtCore.pyqtSlot()
    def doOpenSettings(self):
        """
        Open plugin settings dialog.
        """
        pass

    @QtCore.pyqtSlot()
    def doOpenOntologyAnalysis(self):
        """
        Open ontology analysis dialog.
        """
        pass

    @QtCore.pyqtSlot()
    def doOpenEntityFilter(self):
        """
        Open entity filter dialog.
        """
        pass

    @QtCore.pyqtSlot()
    def doOpenSchemaSelections(self):
        """
        Open schema selections dialog.
        """
        pass

    @QtCore.pyqtSlot()
    def doGeneratePreviewSchema(self):
        """
        Generate a preview schema for the current project.
        """
        self.showDialog()

    @QtCore.pyqtSlot()
    def doExportMappings(self):
        """
        Export mappings for the current project.
        """
        pass

    @QtCore.pyqtSlot()
    def doExportSQLScript(self):
        """
        Export the SQL script generated for the current project.
        """
        pass

    @QtCore.pyqtSlot()
    def doExportSchemaDiagrams(self):
        """
        Export schema diagrams from the current project.
        """
        pass

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
        # DISCONNECT FROM CURRENT PROJECT
        self.debug('Disconnecting from project: %s', self.project.name)
        disconnect(self.project.sgnUpdated, self.onProjectUpdated)
        disconnect(self.project.sgnDiagramAdded, self.onDiagramAdded)
        disconnect(self.project.sgnDiagramRemoved, self.onDiagramRemoved)
        disconnect(self.project.sgnItemAdded, self.onProjectItemAdded)
        disconnect(self.project.sgnItemRemoved, self.onProjectItemRemoved)

        # DISCONNECT FROM ACTIVE SESSION
        self.debug('Disconnecting from active session')
        disconnect(self.session.sgnReady, self.onSessionReady)

    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Starting Blackbird plugin')

        # INITIALIZE ACTIONS AND MENUS
        self.initActions()
        self.initMenus()

        # CONFIGURE SIGNAL/SLOTS
        self.debug('Connecting to active session')
        connect(self.session.sgnReady, self.onSessionReady)

    #############################################
    #   UTILITIES
    #################################

    def showMessage(self, message):
        """
        Displays the given message in a new dialog.
        :type message: str
        """
        label = QtWidgets.QLabel(message)
        confirmation = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        confirmation.setContentsMargins(10, 0, 10, 10)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(confirmation)
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Blackbird Plugin")
        dialog.setModal(False)
        dialog.setLayout(layout)
        connect(confirmation.accepted, lambda: dialog.accept())
        dialog.show()
        # Executes dialog event loop synchronously with the rest of the ui (locks until the dialog is dismissed)
        # use the `raise_()` method if you want the dialog to run its own event thread.
        dialog.exec_()

    def showDialog(self):
        scene = BlackBirdDiagram("BlackBird Diagram", parent=self.session.project)
        rows = []
        row0 = BBTableRow(name='Nome')
        rows.append(row0)
        row1 = BBTableRow(name='Cognome')
        rows.append(row1)
        row2 = BBTableRow(name='Codice_Fiscale', primaryKey=True)
        rows.append(row2)
        row3 = BBTableRow(name='Data_di_nascita', type='DATETIME')
        rows.append(row3)

        relTable0 = RelationalTable(diagram=scene,tableName='Persona',rows=rows, plugin=self)
        #relTable0.defineTableWidget()

        #relTable0.establishConnections()

        view = QGraphicsView(scene)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(view)
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Blackbird Diagram")
        dialog.setModal(False)
        dialog.setLayout(layout)
        dialog.show()

        # Executes dialog event loop synchronously with the rest of the ui (locks until the dialog is dismissed)
        # use the `raise_()` method if you want the dialog to run its own event thread.
        dialog.exec_()


class DCComboBox(QComboBox):
    def __init__(self,diagram=None, id='', *args,**kwargs):
        super().__init__(*args,**kwargs)
        self.diagram = diagram
        self.installEventFilter(diagram)
        self.id = id

    def eventFilter(self, object, event):
        if event.type() is QEvent.MouseButtonPress:
            print("sono qui")
            return True
        elif event.type() is QEvent.GraphicsSceneMousePress:
            print("sono qui 2")
            return True
        elif event is QMouseEvent:
            print("sono qui 3")
            return True
        else:
            return super().eventFilter(object,event)

    def focusInEvent(self, focusEvent):
        print(focusEvent)
        focusEvent.type()

    # def mousePressEvent(self, QMouseEvent):
    #     print("ciccio sono nel mouse press event qcombobox")
    #     self.clearFocus()
    #     return

    def wheelEvent(self, event):
        print("ciccio sono nel wheel event qcombobox")
        self.lineEdit().clearFocus()
        self.clearFocus()
        #event.accept()
        return

class DCLineEdit(QLineEdit):
    def __init__(self,diagram=None,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.installEventFilter(diagram)

    def eventFilter(self, object, event):
        if event.type() is QEvent.MouseButtonPress:
            print("sono qui")
            return True
        elif event.type() is QEvent.GraphicsSceneMousePress:
            print("sono qui 2")
            return True
        elif event is QMouseEvent:
            print("sono qui 3")
            return True
        else:
            return super().eventFilter(object,event)

    def mousePressEvent(self, event):
        print("ciccio sono nel mouse press event qlineedit")
        self.clearFocus()
        return

    def focusInEvent(self, focusEvent):
        print(focusEvent)
        focusEvent.type()

    def focusOutEvent(self, focusEvent):
        if self.isModified():
            self.setModified(False)
            self.returnPressed.emit()
        super().focusOutEvent(focusEvent)

    def textChanged(self, p_str):
        if self.isModified():
            self.setModified(False)
            self.returnPressed.emit()
            #super().focusOutEvent(focusEvent)


    # def wheelEvent(self, event):
    #     print("ciccio sono nel wheel event qlineedit")
    #     self.focusProxy().clearFocus()
    #     self.clearFocus()
    #     event.accept()
    #     return

class BlackBirdDiagram(Diagram):
    """
    Extension of Diagram which implements a single Graphol diagram.
    """

    def __init__(self, name, parent):
        """
        Initialize the diagram.
        :type name: str
        :type parent: Project
        """
        super().__init__(name, parent)

class RelationalTable(QObject):
    DefaultRowHeight = 55
    DefaultAttrPropWidth = 60
    DefaultAttrNameWidth = 150
    DefaultAttrTypeWidth = 150

    def __init__(self, diagram=None, tableName='Name of table', xPos=0, yPos=0, rows=None, rowHeight=55, attrPropColWidth=50,
                 attrNameColWidth=150, attrTypeColWidth=100, headHeight=60, plugin=None, **kwargs):
        super().__init__(**kwargs)
        self.plugin = plugin

        self.diagram = diagram
        self.tableName = tableName

        if rows is None:
            self.rows = []
        else:
            self.rows = rows

        self.comboLineEdits = []
        self.combos = []

        self.rowHeight = max(RelationalTable.DefaultRowHeight, rowHeight)
        self.attrPropColWidth = max(RelationalTable.DefaultAttrPropWidth, attrPropColWidth)
        self.attrNameColWidth = max(RelationalTable.DefaultAttrNameWidth, attrNameColWidth)
        self.attrTypeColWidth = max(RelationalTable.DefaultAttrTypeWidth, attrTypeColWidth)
        self.totalWidth = self.attrPropColWidth + self.attrNameColWidth +self.attrTypeColWidth + 2
        self.totalHeight = headHeight + (self.rowHeight*len(rows))
        self.labelHeight = headHeight
        self.labelWidth = self.totalWidth - 60

        containerId = 'Table_'+tableName
        self.container = ContainerNode(diagram=diagram, id=containerId, tableName=tableName, width=self.totalWidth, height=self.totalHeight)
        self.container.setPos(QtCore.QPointF(xPos,yPos))
        labelId = 'Label_'+tableName
        self.labelNode = BBLabelNode(diagram=diagram, id=labelId, tableName=tableName, width=self.labelWidth, height=headHeight)
        self.labelNode.setParentItem(self.container)
        self.labelNode.setPos(QtCore.QPointF(self.labelNode.parentItem().topLeft().x() + (self.labelNode.parentItem().width() / 4) + 67,
                                             self.labelNode.parentItem().topLeft().y() + (self.labelNode.height() / 2)+4))

        self.tableWidget = QTableWidget()
        self.defineTableWidget()

        self.expandButton = QPushButton()
        self.expandButton.setToolTip("Expand Table")
        expandIcon = QIcon('resources/images/arrow_expanded.png')
        self.expandButton.setIcon(expandIcon)
        self.expandButton.setIconSize(QSize(40, 40))
        self.expandButton.resize(QSize(40, 40))
        self.expandButtonProxy = diagram.addWidget(self.expandButton)
        self.expandButtonProxy.setParentItem(self.container)
        self.expandButtonProxy.setPos(self.expandButtonProxy.parentItem().topRight())
        self.expandButtonProxy.setPos(QtCore.QPointF(self.expandButtonProxy.parentItem().topRight().x() - 50,
                                                     self.expandButtonProxy.parentItem().topRight().y() + 8))
        self.expandButtonProxy.setVisible(False)


        self.collapseButton = QPushButton()
        self.collapseButton.setToolTip("Collapse Table")
        collapseIcon = QIcon('resources/images/arrow_collapsed.png')
        self.collapseButton.setIcon(collapseIcon)
        self.collapseButton.setIconSize(QSize(40, 40))
        self.collapseButton.resize(QSize(40, 40))
        self.collapseButtonProxy = diagram.addWidget(self.collapseButton)
        self.collapseButtonProxy.setParentItem(self.container)
        self.collapseButtonProxy.setPos(QtCore.QPointF(self.collapseButtonProxy.parentItem().topRight().x() - 50,
                                                     self.collapseButtonProxy.parentItem().topRight().y() + 8))
        self.establishConnections()


        self.diagram.addItem(self.container)

    def establishConnections(self):
        connect(self.expandButton.clicked, self.onClickExpand)
        connect(self.collapseButton.clicked, self.onClickCollapse)


    def defineTableWidget(self):
        #self.defineTableWidget()
        self.tableWidgetProxy = self.diagram.addWidget(self.tableWidget)
        self.tableWidgetProxy.setParentItem(self.container)
        self.tableWidgetProxy.setPos(QtCore.QPointF(self.tableWidgetProxy.parentItem().topLeft().x() + 5,
                                                    self.tableWidgetProxy.parentItem().topLeft().y() + self.labelHeight+5))
        self.tableWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableWidget.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.tableWidget.setColumnCount(3)
        self.tableWidget.setColumnWidth(0, self.attrPropColWidth)
        self.tableWidget.setColumnWidth(1, self.attrNameColWidth)
        self.tableWidget.setColumnWidth(2, self.attrTypeColWidth)
        rowCount = len(self.rows)
        self.tableWidget.setRowCount(rowCount)
        for i in range(rowCount):
            self.tableWidget.setRowHeight(i, self.rowHeight)

        tableSize = self.getQTableWidgetSize()
        self.tableWidget.setMaximumSize(tableSize)
        self.tableWidget.setMinimumSize(tableSize)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)
        self.tableWidget.setShowGrid(False)
        # tableW.setFrameStyle(QFrame.NoFrame)
        self.tableWidget.setEditTriggers(QAbstractItemView.DoubleClicked)
        colDelegate1 = CustomSelectColorDelegate()
        self.tableWidget.setItemDelegateForColumn(1, colDelegate1)
        for i in range(rowCount):
            self.defineRow(i)
        self.tableWidget.setIconSize(QSize(35, 35))
        connect(self.tableWidget.cellChanged, self.modifiedCell)
        connect(self.tableWidget.cellDoubleClicked, self.doubleClickedCell)

    def defineRow(self,index):
        row = self.rows[index]
        #prop column
        iconWidgItem = QTableWidgetItem()
        iconWidgItem.setSizeHint(QSize(self.attrPropColWidth, self.rowHeight))
        if row.primaryKey:
            icon = QIcon('resources/images/primary_key_1.png')
            iconWidgItem.setIcon(icon)
        #iconWidgItem.setSizeHint(QSize(100, 100))
        flags = iconWidgItem.flags()
        flags ^= QtCore.Qt.ItemIsEditable
        flags ^= ~QtCore.Qt.ItemIsSelectable
        iconWidgItem.setFlags(flags)
        self.tableWidget.setItem(index,0,iconWidgItem)
        #name column
        nameWidgItem = QTableWidgetItem(row.name)
        nameWidgItem.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.tableWidget.setItem(index, 1, nameWidgItem)
        #type column
        lineEdit = DCLineEdit(diagram=self.diagram)
        lineEdit.setText(row.type)
        connect(lineEdit.returnPressed,self.dcLineEdited)
        self.comboLineEdits.append(lineEdit)

        comboId = 'combo_'+self.tableName+'_index'
        comboBox = DCComboBox(diagram=self.diagram, id=comboId)
        comboBox.setLineEdit(lineEdit)
        comboBox.addItems(['VARCHAR(255)','TEXT','INT','REAL','DATE','DATETIME'])
        comboBox.setEditable(True)
        comboBox.setInsertPolicy(QComboBox.NoInsert)
        comboBox.setEditText(row.type)
        connect(comboBox.activated[str], self.dcComboActivated)
        self.combos.append(comboBox)
        self.tableWidget.setCellWidget(index,2,comboBox)

    def getQTableWidgetSize(self):
        w = 0  # qTable.verticalHeader().width() + 4  # +4 seems to be needed
        for i in range(self.tableWidget.columnCount()):
            w += self.tableWidget.columnWidth(i)  # seems to include gridline (on my machine)
        h = 0  # qTable.horizontalHeader().height() + 4
        for i in range(self.tableWidget.rowCount()):
            h += self.tableWidget.rowHeight(i)
        return QtCore.QSize(w, h)
    ######################
    #                    #
    #        SLOTS       #
    #                    #
    ######################
    @QtCore.pyqtSlot()
    def onClickExpand(self):
        self.tableWidgetProxy.setVisible(True)
        self.expandButtonProxy.setVisible(False)
        self.collapseButtonProxy.setVisible(True)

    @QtCore.pyqtSlot()
    def onClickCollapse(self):
        self.tableWidgetProxy.setVisible(False)
        self.collapseButtonProxy.setVisible(False)
        self.expandButtonProxy.setVisible(True)

    @QtCore.pyqtSlot(int, int)
    def doubleClickedCell(self, row, column):
        table = self.sender()
        item = table.item(row, column)
        message = "La cella in posizione ({},{}) è stata double clicked con testo {}"
        self.plugin.showMessage(message.format(row, column, item.text()))

    @QtCore.pyqtSlot(int, int)
    def modifiedCell(self, row, column):
        table = self.sender()
        item = table.item(row, column)
        message = "La cella in posizione ({},{}) è stata modificata con testo {}"
        self.plugin.showMessage(message.format(row, column, item.text()))

    @QtCore.pyqtSlot()
    def dcLineEdited(self):
        dcLine = self.sender()
        index = self.comboLineEdits.index(dcLine)
        message = "La dclineEdit in riga {} è stata modificata con testo {}"
        self.plugin.showMessage(message.format(index,dcLine.text()))

    @QtCore.pyqtSlot(str)
    def dcComboActivated(self, activated):
        dcCombo = self.sender()
        index = self.combos.index(dcCombo)
        message = "In DCCombo con id={} in riga {} è stata selezionata la voce {}"
        self.plugin.showMessage(message.format(dcCombo.id,index,activated))

class CustomSelectColorDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(CustomSelectColorDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        painter.save()

        # set background color
        painter.setPen(QtCore.Qt.NoPen)
        if option.state & QStyle.State_Selected:
            painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
        else:
            painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
        painter.drawRect(option.rect)

        # set text color
        if option.state & QStyle.State_Selected:
            painter.setPen(QtGui.QPen(QtCore.Qt.black))
        else:
            painter.setPen(QtGui.QPen(QtCore.Qt.black))

        value = index.data(QtCore.Qt.DisplayRole)
        if value:
            text = value
            painter.drawText(option.rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter, text)

        painter.restore()

class ContainerNode(AbstractNode):
    DefaultBrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
    DefaultPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap,
                            QtCore.Qt.RoundJoin)
    ContainerPen = QtGui.QPen(QtCore.Qt.red)

    Identities = {Identity.Concept}
    Type = Item.ConceptNode

    def __init__(self, tableName='Table Name', width=300, height=800, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)
        w = max(width, 110)
        h = max(height, 50)
        brush = brush or ContainerNode.DefaultBrush
        pen = ContainerNode.DefaultPen
        self.background = Polygon(QtCore.QRectF(-(w + 8) / 2, -(h + 8) / 2, w + 8, h + 8))
        self.selection = Polygon(QtCore.QRectF(-(w + 8) / 2, -(h + 8) / 2, w + 8, h + 8))
        self.polygon = Polygon(QtCore.QRectF(-w / 2, -h / 2, w, h), brush, pen)

        self.label = None
        self.updateNode()

    #############################################
    #   INTERFACE
    #################################

    def topRight(self):
        """
        Returns the point at the top right of the shape in item's coordinate.
        :rtype: QPointF
        """
        return self.boundingRect().topRight()

    def topLeft(self):
        """
        Returns the point at the top left of the shape in item's coordinate.
        :rtype: QPointF
        """
        return self.boundingRect().topLeft()

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QtCore.QRectF
        """
        path = QtGui.QPainterPath()
        path.addRect(self.selection.geometry())
        return path.boundingRect()
        #return self.container.geometry()
        #return self.selection.geometry()

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        node = diagram.factory.create(self.type(), **{
            'id': self.id,
            'brush': self.brush(),
            'height': self.height(),
            'width': self.width()
        })
        node.setPos(self.pos())
        #node.setText(self.text())
        #node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
        return node

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon.geometry().height()

    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Concept

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the diagram.
        :type painter: QPainter
        :type option: QStyleOptionGraphicsItem
        :type widget: QWidget
        """
        # SET THE RECT THAT NEEDS TO BE REPAINTED
        painter.setClipRect(option.exposedRect)
        # SELECTION AREA
        painter.setPen(self.selection.pen())
        painter.setBrush(self.selection.brush())
        painter.drawRect(self.selection.geometry())
        # SYNTAX VALIDATION
        painter.setPen(self.background.pen())
        painter.setBrush(self.background.brush())
        painter.drawRect(self.background.geometry())
        # ITEM SHAPE
        painter.setPen(self.polygon.pen())
        painter.setBrush(self.polygon.brush())
        painter.drawRect(self.polygon.geometry())

        # # RESIZE HANDLES
        # painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # for polygon in self.handles:
        #     painter.setPen(polygon.pen())
        #     painter.setBrush(polygon.brush())
        #     painter.drawEllipse(polygon.geometry())

    def painterPath(self):
        """
        Returns the current shape as QtGui.QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addRect(self.polygon.geometry())
        return path

    def setIdentity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        pass
        # self.label.setText(text)
        # self.label.setAlignment(QtCore.Qt.AlignCenter)

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        pass
        #self.label.setPos(pos)

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addRect(self.polygon.geometry())
        # for polygon in self.handles:
        #     path.addEllipse(polygon.geometry())
        return path

    def special(self):
        """
        Returns the special type of this node.
        :rtype: Special
        """
        return Special.valueOf(self.text())

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        pass
        #return self.label.text()

    def textPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        pass
        #return self.label.pos()

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        pass
        #self.label.updatePos(*args, **kwargs)

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygon.geometry().width()

    def __repr__(self):
        """
        Returns repr(self).
        """
        return '{0}:{1}:{2}'.format(self.__class__.__name__, self.text(), self.id)


class BBTableRow:
    """
    This class implements represents a row in a relational table.
    """

    def __init__(self, name="AttributeName", type="VARCHAR(255)", nullable=False, primaryKey=False, indexed=False,
                 foreignKey=False):
        self.__name = name
        self.__type = type
        self.__nullable = nullable
        self.__primaryKey = primaryKey
        self.__indexed = indexed
        self.__foreignKey = foreignKey

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, type):
        self.__type = type

    @property
    def nullable(self):
        return self.__nullable

    @name.setter
    def nullable(self, nullable):
        self.__nullable = nullable

    @property
    def primaryKey(self):
        return self.__primaryKey

    @primaryKey.setter
    def primaryKey(self, primaryKey):
        self.__primaryKey = primaryKey

    @property
    def indexed(self):
        return self.__indexed

    @indexed.setter
    def indexed(self, indexed):
        self.__indexed = indexed

    @property
    def foreignKey(self):
        return self.__foreignKey

    @foreignKey.setter
    def foreignKey(self, foreignKey):
        self.__foreignKey = foreignKey

class BBLabelNode(AbstractNode):
    #DefaultBrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
    DefaultBrush = QtGui.QBrush(QtGui.QBrush(QtCore.Qt.green))
    DefaultPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap,
                            QtCore.Qt.RoundJoin)
    ContainerPen = QtGui.QPen(QtCore.Qt.red)

    Identities = {Identity.Concept}
    Type = Item.ConceptNode

    def __init__(self, tableName='Table Name', width=150, height=50, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)
        w = max(width, 110)
        h = max(height, 50)
        brush = brush or BBLabelNode.DefaultBrush
        pen = BBLabelNode.DefaultPen
        self.background = Polygon(QtCore.QRectF(-(w + 8) / 2, -(h + 8) / 2, w + 8, h + 8))
        self.selection = Polygon(QtCore.QRectF(-(w + 8) / 2, -(h + 8) / 2, w + 8, h + 8))
        self.polygon = Polygon(QtCore.QRectF(-w / 2, -h / 2, w, h), brush, pen)


        #labelPos = QtCore.QPointF(self.topLeft().x()+10,self.topLeft().y()+10)

        self.label = PredicateLabel(template=tableName, pos=self.center, parent=self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        #self.label.setAlignment(QtCore.Qt.AlignLeft)
        self.updateNode()
        self.updateTextPos()

    #############################################
    #   INTERFACE
    #################################

    def isTableNode(self):
        return True

    def topRight(self):
        """
        Returns the point at the top right of the shape in item's coordinate.
        :rtype: QPointF
        """
        return self.boundingRect().topRight()

    def topLeft(self):
        """
        Returns the point at the top left of the shape in item's coordinate.
        :rtype: QPointF
        """
        return self.boundingRect().topLeft()

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QtCore.QRectF
        """
        path = QtGui.QPainterPath()
        #path.addRect(self.selection.geometry())
        path.addRect(self.polygon.geometry())
        return path.boundingRect()
        #return self.container.geometry()
        #return self.selection.geometry()

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        node = diagram.factory.create(self.type(), **{
            'id': self.id,
            'brush': self.brush(),
            'height': self.height(),
            'width': self.width()
        })
        node.setPos(self.pos())
        node.setText(self.text())
        node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
        return node

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon.geometry().height()

    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Concept

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the diagram.
        :type painter: QPainter
        :type option: QStyleOptionGraphicsItem
        :type widget: QWidget
        """
        # SET THE RECT THAT NEEDS TO BE REPAINTED
        painter.setClipRect(option.exposedRect)
        # SELECTION AREA
        painter.setPen(self.selection.pen())
        painter.setBrush(self.selection.brush())
        painter.drawRect(self.selection.geometry())
        # SYNTAX VALIDATION
        painter.setPen(self.background.pen())
        painter.setBrush(self.background.brush())
        painter.drawRect(self.background.geometry())
        # ITEM SHAPE
        painter.setPen(self.polygon.pen())
        painter.setBrush(self.polygon.brush())
        painter.drawRect(self.polygon.geometry())


        # # RESIZE HANDLES
        # painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # for polygon in self.handles:
        #     painter.setPen(polygon.pen())
        #     painter.setBrush(polygon.brush())
        #     painter.drawEllipse(polygon.geometry())

    def painterPath(self):
        """
        Returns the current shape as QtGui.QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addRect(self.polygon.geometry())
        return path

    def setIdentity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        self.label.setText(text)
        self.label.setAlignment(QtCore.Qt.AlignCenter)

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        self.label.setPos(pos)

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addRect(self.polygon.geometry())
        # for polygon in self.handles:
        #     path.addEllipse(polygon.geometry())
        return path

    def special(self):
        """
        Returns the special type of this node.
        :rtype: Special
        """
        return Special.valueOf(self.text())

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        return self.label.text()

    def textPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        return self.label.pos()

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.label.updatePos(*args, **kwargs)

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygon.geometry().width()

    def __repr__(self):
        """
        Returns repr(self).
        """
        return '{0}:{1}:{2}'.format(self.__class__.__name__, self.text(), self.id)
# #############################################
# #                                           #
# #           ENUMERATORS                     #
# #                                           #
# #############################################
#
# @unique
# class BlackBirdItem(IntEnum_):
#     """
#     This class defines all the available elements for blackbird diagrams.
#     """
#     TableNode = 70001
#     TableHeaderNode = 70002
#
#     ForeignKeyEdge = 80001
#
#     Lable = 90001
#
#     Undefined = 99999
#
#     @property
#     def realName(self):
#         """
#         Returns the item readable name, i.e: attribute node, concept node.
#         :rtype: str
#         """
#         return RE_CAMEL_SPACE.sub('\g<1> \g<2>', self.name).lower()
#
#     @property
#     def shortName(self):
#         """
#         Returns the item short name, i.e: attribute, concept.
#         :rtype: str
#         """
#         return rstrip(self.realName, ' node', ' edge')
#
#
# @unique
# class BlackBirdIdentity(Enum_):
#     Table = "Table"
#     TableHeader = "TableHeader"
#
#
# @unique
# class BlackBirdDiagramMode(IntEnum_):
#     Idle = 0
#     ExpandingRegularTable = 1
#     ReducingExpandedTable = 2
#     MergingTables = 3
#     ModifyingTable = 4
#     EditingTableHeader = 5
#     EditingTableAttributeName = 6
#     EditingTableAttributeType = 7
#
#
# #############################################
# #                                           #
# #               DIAGRAM                     #
# #                                           #
# #############################################
# class BlackBirdDiagram(Diagram):
#     """
#     Extension of Diagram which implements a single Graphol diagram.
#     """
#
#     def __init__(self, name, parent):
#         """
#         Initialize the diagram.
#         :type name: str
#         :type parent: Project
#         """
#         super().__init__(name, parent)
#
#
# class BBGUID(QtCore.QObject):
#     """
#     Class used to generate sequential ids for diagram elements.
#     """
#
#     def __init__(self, parent=None):
#         """
#         Initialize the the unique id generator.
#         :type parent: QObject
#         """
#         super().__init__(parent)
#         self.ids = dict()
#
#     def next(self, prefix):
#         """
#         Returns the next id available prepending the given prefix.
#         :type prefix: str
#         :rtype: str
#         """
#         try:
#             uid = self.ids[prefix]
#         except KeyError:
#             self.ids[prefix] = 0
#         else:
#             self.ids[prefix] = uid + 1
#         return '{}{}'.format(prefix, self.ids[prefix])
#
#     @staticmethod
#     def parse(uid):
#         """
#         Parse the given unique id returning a tuple in the format (prefix -> str, value -> int).
#         :type uid: str
#         :rtype: tuple
#         """
#         match = RE_ITEM_PREFIX.match(uid)
#         if not match:
#             raise ValueError('invalid id supplied ({0})'.format(uid))
#         return match.group('prefix'), int(match.group('value'))
#
#     def update(self, uid):
#         """
#         Update the last incremental value according to the given id.
#         :type uid: str
#         """
#         prefix, value = self.parse(uid)
#         try:
#             uid = self.ids[prefix]
#         except KeyError:
#             self.ids[prefix] = value
#         else:
#             self.ids[prefix] = max(uid, value)
#
#     def __repr__(self):
#         """
#         Return repr(self).
#         """
#         return 'BBGUID<{0}>'.format(','.join(['{0}:{1}'.format(k, v) for k, v in self.ids.items()]))
#
#
# #############################################
# #                                           #
# #           GENERAL INTERFACES              #
# #                                           #
# #############################################
# class BlackBirdDiagramItemMixin:
#     """
#     Mixin implementation for all the diagram elements (nodes, edges and labels).
#     """
#
#     #############################################
#     #   PROPERTIES
#     #################################
#
#     @property
#     def diagram(self):
#         """
#         Returns the diagram holding this item (alias for BlackBirdDiagramItemMixin.scene()).
#         :rtype: BlackBirdDiagram
#         """
#         return self.scene()
#
#     @property
#     def project(self):
#         """
#         Returns the project this item belongs to (alias for BlackBirdDiagramItemMixin.diagram.parent()).
#         :rtype: Project
#         """
#         return self.diagram.parent()
#
#     @property
#     def session(self):
#         """
#         Returns the session this item belongs to (alias for DiagramItemMixin.project.parent()).
#         :rtype: Session
#         """
#         return self.project.parent()
#
#     #############################################
#     #   INTERFACE
#     #################################
#
#     def isEdge(self):
#         """
#         Returns True if this element is an edge, False otherwise.
#         :rtype: bool
#         """
#         return BlackBirdItem.ForeignKeyEdge is self.type()
#
#     def isLabel(self):
#         """
#         Returns True if this element is a label, False otherwise.
#         :rtype: bool
#         """
#         return self.type() is BlackBirdItem.Label
#
#     def isNode(self):
#         """
#         Returns True if this element is a node, False otherwise.
#         :rtype: bool
#         """
#         return BlackBirdItem.TableNode <= self.type() < BlackBirdItem.ForeignKeyEdge
#
#
# class BlackBirdAbstractItem(QtWidgets.QGraphicsItem, BlackBirdDiagramItemMixin):
#     """
#     Base class for all the diagram items.
#     """
#     __metaclass__ = ABCMeta
#
#     Prefix = 'i'
#     Type = BlackBirdItem.Undefined
#
#     def __init__(self, diagram, id=None, **kwargs):
#         """
#         Initialize the item.
#         :type diagram: BlackBirdDiagram
#         :type id: str
#         """
#         super().__init__(**kwargs)
#         self.id = id or diagram.guid.next(self.Prefix)
#         #self.diagram = diagram
#
#     #############################################
#     #   PROPERTIES
#     #################################
#
#     @property
#     def name(self):
#         """
#         Returns the item readable name.
#         :rtype: str
#         """
#         item = self.type()
#         return item.realName
#
#     #############################################
#     #   INTERFACE
#     #################################
#
#     @abstractmethod
#     def copy(self, diagram):
#         """
#         Create a copy of the current item.
#         :type diagram: Diagram
#         """
#         pass
#
#     @abstractmethod
#     def painterPath(self):
#         """
#         Returns the current shape as QtGui.QPainterPath (used for collision detection).
#         :rtype: QPainterPath
#         """
#         pass
#
#     @abstractmethod
#     def setText(self, text):
#         """
#         Set the label text.
#         :type text: str
#         """
#         pass
#
#     @abstractmethod
#     def setTextPos(self, pos):
#         """
#         Set the label position.
#         :type pos: QPointF
#         """
#         pass
#
#     @abstractmethod
#     def text(self):
#         """
#         Returns the label text.
#         :rtype: str
#         """
#         pass
#
#     @abstractmethod
#     def textPos(self):
#         """
#         Returns the current label position.
#         :rtype: QPointF
#         """
#         pass
#
#     def type(self):
#         """
#         Returns the type of this item.
#         :rtype: Item
#         """
#         return self.Type
#
#     def updateEdge(self, *args, **kwargs):
#         """
#         Update the edge geometry if this item is an edge.
#         """
#         pass
#
#     def updateNode(self, *args, **kwargs):
#         """
#         Update the node geometry if this item is a node.
#         """
#         pass
#
#     def updateEdgeOrNode(self, *args, **kwargs):
#         """
#         Convenience method which calls node or edge update function depending on the type of the item.
#         """
#         if self.isNode():
#             self.updateNode(*args, **kwargs)
#         elif self.isEdge():
#             self.updateEdge(*args, **kwargs)
#
#     def __repr__(self):
#         """
#         Returns repr(self).
#         """
#         return '{0}:{1}'.format(self.__class__.__name__, self.id)
#
#
# class BlackBirdAbstractNode(BlackBirdAbstractItem):
#     """
#     Base class for all the diagram nodes.
#     """
#     __metaclass__ = ABCMeta
#
#     Prefix = 'n'
#
#     def __init__(self, **kwargs):
#         """
#         Initialize the node.
#         """
#         super().__init__(**kwargs)
#
#         #self._identity = BlackBirdIdentity.Neutral
#
#         self._identity = Identity.Neutral
#
#         self.anchors = dict()
#         self.edges = set()
#
#         self.background = None  # BACKGROUND POLYGON
#         self.selection = None  # SELECTION POLYGON
#         self.polygon = None  # MAIN POLYGON
#         self.label = None  # ATTACHED LABEL
#
#         self.setAcceptHoverEvents(True)
#         self.setCacheMode(BlackBirdAbstractItem.DeviceCoordinateCache)
#         self.setFlag(BlackBirdAbstractItem.ItemIsSelectable, True)
#
#     #############################################
#     #   PROPERTIES
#     #################################
#
#     @property
#     def identityName(self):
#         """
#         Returns the name of the identity of this item (i.e: Table,TableHeader ...).
#         :rtype: str
#         """
#         identity = self.identity()
#         return identity.value
#
#     #############################################
#     #   INTERFACE
#     #################################
#
#     def addEdge(self, edge):
#         """
#         Add the given edge to the current node.
#         :type edge: BlackBirdAbstractEdge
#         """
#         self.edges.add(edge)
#
#     def adjacentNodes(self, filter_on_edges=lambda x: True, filter_on_nodes=lambda x: True):
#         """
#         Returns the set of adjacent nodes.
#         :type filter_on_edges: callable
#         :type filter_on_nodes: callable
#         :rtype: set
#         """
#         return {x for x in [e.other(self) for e in self.edges if filter_on_edges(e)] if filter_on_nodes(x)}
#
#     def anchor(self, edge):
#         """
#         Returns the anchor point of the given edge in scene coordinates.
#         :type edge: BlackBirdAbstractEdge
#         :rtype: QPointF
#         """
#         try:
#             return self.anchors[edge]
#         except KeyError:
#             self.anchors[edge] = self.mapToScene(self.center())
#             return self.anchors[edge]
#
#     def brush(self):
#         """
#         Returns the brush used to paint the shape of this node.
#         :rtype: QtGui.QBrush
#         """
#         return self.polygon.brush()
#
#     def center(self):
#         """
#         Returns the point at the center of the shape in item's coordinate.
#         :rtype: QPointF
#         """
#         return self.boundingRect().center()
#
#     @abstractmethod
#     def copy(self, diagram):
#         """
#         Create a copy of the current item.
#         :type diagram: Diagram
#         """
#         pass
#
#     def definition(self):
#         """
#         Returns the list of nodes which contribute to the definition of this very node.
#         :rtype: set
#         """
#         return set()
#
#     def geometry(self):
#         """
#         Returns the geometry of the shape of this node.
#         :rtype: QtGui.QPolygonF
#         """
#         return self.polygon.geometry()
#
#     @abstractmethod
#     def height(self):
#         """
#         Returns the height of the shape.
#         :rtype: int
#         """
#         pass
#
#     @classmethod
#     def identities(cls):
#         """
#         Returns the set of identities supported by this node.
#         :rtype: set
#         """
#         return cls.Identities
#
#     def identify(self):
#         """
#         Perform the node identification step for the current node.
#         Nodes who compute their identity without inheriting it from a direct connection,
#         MUST provide an implementation of this method, which MUST be invoked only during
#         the process which aims to identify a set of connected nodes.
#         Any attempt to call this method from outside this process may cause inconsistencies.
#         This method will compute the identity of the node according to it's configuration,
#         and will return a tuple composed of 3 elements, whose purpose is to dynamically adapt
#         the node identification algorithm behaviour according to the specific diagram configuration:
#
#         * 1) A set of nodes to be added to the STRONG set (usually the node itself, when identified correctly).
#         * 2) A set of nodes to be removed from the STRONG set (nodes that contribute only to the identity of this node)
#         * 3) A set of nodes to be added to the EXCLUDED set (nodes that to not partecipate with inheritance in the identification step)
#
#         If no identification is performed, the method MUST return None.
#         :rtype: tuple
#         """
#         return None
#
#     def identity(self):
#         """
#         Returns the identity of the current node.
#         :rtype: BlackBirdIdentity
#         """
#         return self._identity
#
#     def incomingNodes(self, filter_on_edges=lambda x: True, filter_on_nodes=lambda x: True):
#         """
#         Returns the set of incoming nodes.
#         :type filter_on_edges: callable
#         :type filter_on_nodes: callable
#         :rtype: set
#         """
#         # TODO REIMPLEMENTA
#         return {x for x in [e.other(self) for e in self.edges \
#                             if (e.target is self or e.type() is Item.EquivalenceEdge) \
#                             and filter_on_edges(e)] if filter_on_nodes(x)}
#
#     def intersection(self, line):
#         """
#         Returns the intersection of the shape with the given line (in scene coordinates).
#         :type line: QtCore.QLineF
#         :rtype: QPointF
#         """
#         intersection = QtCore.QPointF()
#         path = self.painterPath()
#         polygon = self.mapToScene(path.toFillPolygon(self.transform()))
#         for i in range(0, polygon.size() - 1):
#             polyline = QtCore.QLineF(polygon[i], polygon[i + 1])
#             if polyline.intersect(line, intersection) == QtCore.QLineF.BoundedIntersection:
#                 return intersection
#         return None
#
#     def intersections(self, line):
#         """
#         Returns the list of intersections of the shape with the given line (in scene coordinates).
#         :type line: QtCore.QLineF
#         :rtype: list
#         """
#         intersections = []
#         path = self.painterPath()
#         polygon = self.mapToScene(path.toFillPolygon(self.transform()))
#         for i in range(0, polygon.size() - 1):
#             intersection = QtCore.QPointF()
#             polyline = QtCore.QLineF(polygon[i], polygon[i + 1])
#             if polyline.intersect(line, intersection) == QtCore.QLineF.BoundedIntersection:
#                 intersections.append(intersection)
#         return intersections
#
#     def isConstructor(self):
#         """
#         Returns True if this node is a contructor node, False otherwise.
#         :rtype: bool
#         """
#         return Item.DomainRestrictionNode <= self.type() <= Item.FacetNode
#
#     def isMeta(self):
#         """
#         Returns True iff we should memorize metadata for this item, False otherwise.
#         :rtype: bool
#         """
#         item = self.type()
#         identity = self.identity()
#         return False
#         # TODO REIMPLEMENTA
#         # return item is Item.ConceptNode or \
#         #    item is Item.RoleNode or \
#         #    item is Item.AttributeNode or \
#         #    item is Item.IndividualNode and identity is not Identity.Value
#
#     def isBackGroundNode(self):
#         """
#         Returns True if this node is a container node, False otherwise.
#         :rtype: bool
#         """
#         return BlackBirdItem.TableNode is self.type()
#
#     def moveBy(self, x, y):
#         """
#         Move the node by the given deltas.
#         :type x: T <= float | int
#         :type y: T <= float | int
#         """
#         move = QtCore.QPointF(x, y)
#         self.setPos(self.pos() + move)
#         self.anchors = {edge: pos + move for edge, pos in self.anchors.items()}
#
#     def outgoingNodes(self, filter_on_edges=lambda x: True, filter_on_nodes=lambda x: True):
#         """
#         Returns the set of outgoing nodes.
#         :type filter_on_edges: callable
#         :type filter_on_nodes: callable
#         :rtype: set
#         """
#         # TODO REIMPLEMENTA
#         return {x for x in [e.other(self) for e in self.edges \
#                             if (e.source is self or e.type() is Item.EquivalenceEdge) \
#                             and filter_on_edges(e)] if filter_on_nodes(x)}
#
#     @abstractmethod
#     def painterPath(self):
#         """
#         Returns the current shape as QPainterPath (used for collision detection).
#         :rtype: QPainterPath
#         """
#         pass
#
#     def pen(self):
#         """
#         Returns the pen used to paint the shape of this node.
#         :rtype: QtGui.QPen
#         """
#         return self.polygon.pen()
#
#     # def pos(self):
#     #     """
#     #     Returns the position of this node in scene coordinates.
#     #     :rtype: QPointF
#     #     """
#     #     return self.mapToScene(self.center())
#
#     def removeEdge(self, edge):
#         """
#         Remove the given edge from the current node.
#         :type edge: AbstractEdge
#         """
#         self.edges.discard(edge)
#
#     def setAnchor(self, edge, pos):
#         """
#         Set the given position as anchor for the given edge.
#         :type edge: AbstractEdge
#         :type pos: QPointF
#         """
#         self.anchors[edge] = pos
#
#     def setBrush(self, brush):
#         """
#         Set the brush used to paint the shape of this node.
#         :type brush: QBrush
#         """
#         self.polygon.setBrush(brush)
#
#     def setGeometry(self, geometry):
#         """
#         Set the geometry used to paint the shape of this node.
#         :type geometry: T <= QtCore.QRectF|QtGui.QPolygonF
#         """
#         self.polygon.setGeometry(geometry)
#
#     def setIdentity(self, identity):
#         """
#         Set the identity of the current node.
#         :type identity: Identity
#         """
#         if identity not in self.identities():
#             identity = Identity.Unknown
#         self._identity = identity
#
#     def setPen(self, pen):
#         """
#         Set the pen used to paint the shape of this node.
#         :type pen: QtGui.QPen
#         """
#         self.polygon.setPen(pen)
#
#     # def setPos(self, *__args):
#     #     """
#     #     Set the item position.
#     #     QGraphicsItem.setPos(QtCore.QPointF)
#     #     QGraphicsItem.setPos(float, float)
#     #     """
#     #     if len(__args) == 1:
#     #         pos = __args[0]
#     #     elif len(__args) == 2:
#     #         pos = QtCore.QPointF(__args[0], __args[1])
#     #     else:
#     #         raise TypeError('too many arguments; expected {0}, got {1}'.format(2, len(__args)))
#     #     # TODO REIMPLEMENTA
#     #     super().setPos(pos)
#     #     #super().setPos(pos + super().pos() - self.pos())
#     #     # super().setPos(pos)
#
#     def updateEdges(self):
#         """
#         Update all the edges attached to the node.
#         """
#         for edge in self.edges:
#             edge.updateEdge()
#
#     def updateNode(self, selected=None, valid=None, **kwargs):
#         """
#         Update the current node.
#         :type selected: bool
#         :type valid: bool
#         """
#
#         # ITEM SELECTION (BRUSH)
#         brush = QtGui.QBrush(QtCore.Qt.NoBrush)
#         if selected:
#             brush = QtGui.QBrush(QtGui.QColor(248, 255, 72, 255))
#         self.selection.setBrush(brush)
#
#         # SYNTAX VALIDATION (BACKGROUND BRUSH)
#         brush = QtGui.QBrush(QtCore.Qt.NoBrush)
#         if valid is not None:
#             brush = QtGui.QBrush(QtGui.QColor(179, 12, 12, 160))
#             if valid:
#                 brush = QtGui.QBrush(QtGui.QColor(43, 173, 63, 160))
#
#         self.background.setBrush(brush)
#
#         # FORCE CACHE REGENERATION
#         self.setCacheMode(BlackBirdAbstractItem.NoCache)
#         self.setCacheMode(BlackBirdAbstractItem.DeviceCoordinateCache)
#
#         # SCHEDULE REPAINT
#         #self.update(self.boundingRect())
#
#     @abstractmethod
#     def updateTextPos(self, *args, **kwargs):
#         """
#         Update the label position.
#         """
#         pass
#
#     @abstractmethod
#     def width(self):
#         """
#         Returns the width of the shape.
#         :rtype: int
#         """
#         pass
#
#     #############################################
#     #   EVENTS
#     #################################
#
#     def itemChange(self, change, value):
#         """
#         Executed whenever the item change state.
#         :type change: int
#         :type value: QVariant
#         :rtype: QVariant
#         """
#         if change == BlackBirdAbstractItem.ItemSelectedHasChanged:
#             self.updateNode(selected=value)
#         return super().itemChange(change, value)
#
#     def mousePressEvent(self, mouseEvent):
#         """
#         Executed when the mouse is pressed on the item (EXCLUDED).
#         :type mouseEvent: QGraphicsSceneMouseEvent
#         """
#         pass
#
#     def mouseMoveEvent(self, mouseEvent):
#         """
#         Executed when the mouse is being moved over the item while being pressed (EXCLUDED).
#         :type mouseEvent: QGraphicsSceneMouseEvent
#         """
#         pass
#
#     def mouseReleaseEvent(self, mouseEvent):
#         """
#         Executed when the mouse is released from the item (EXCLUDED).
#         :type mouseEvent: QGraphicsSceneMouseEvent
#         """
#         pass
#
#
# class BlackBirdAbstractLabel(QtWidgets.QGraphicsTextItem, BlackBirdDiagramItemMixin):
#     """
#     Base class for the diagram labels.
#     """
#     __metaclass__ = ABCMeta
#
#     Type = BlackBirdItem.Lable
#
#     def __init__(self, template='', movable=True, editable=True, parent=None):
#         """
#         Initialize the label.
#         :type template: str
#         :type movable: bool
#         :type editable: bool
#         :type parent: QObject
#         """
#         self._alignment = QtCore.Qt.AlignCenter
#         self._editable = bool(editable)
#         self._movable = bool(movable)
#         self._parent = parent
#
#         super().__init__(parent)
#         self.focusInData = None
#         self.template = template
#         self.setDefaultTextColor(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)).color())
#         #self.setFlag(BlackBirdAbstractLabel.ItemIsFocusable, self.isEditable())
#         self.setFont(Font('Roboto', 12, Font.Light))
#         # self.setText(self.template)
#         self.setPlainText(self.template)
#         # self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
#
#         document = self.document()
#         #connect(document.contentsChange[int, int, int], self.onContentsChanged)
#
#     #############################################
#     #   EVENTS
#     #################################
#
#     def focusInEvent(self, focusEvent):
#         """
#         Executed when the text item is focused.
#         :type focusEvent: QFocusEvent
#         """
#         # FOCUS ONLY ON DOUBLE CLICK
#         if focusEvent.reason() == QtCore.Qt.OtherFocusReason:
#             self.focusInData = self.text()
#             self.diagram.clearSelection()
#             #self.diagram.setMode(DiagramMode.LabelEdit)
#             self.setSelectedText(True)
#             super().focusInEvent(focusEvent)
#         else:
#             self.clearFocus()
#
#     def focusOutEvent(self, focusEvent):
#         """
#         Executed when the text item loses the focus.
#         :type focusEvent: QFocusEvent
#         """
#         if self.diagram.mode is BlackBirdDiagramMode.EditingTableHeader:
#
#             if isEmpty(self.text()):
#                 self.setText(self.template)
#
#             focusInData = self.focusInData
#             currentData = self.text()
#
#             ###########################################################
#             # IMPORTANT!                                              #
#             # ####################################################### #
#             # The code below is a bit tricky: to be able to properly  #
#             # update the node in the project index we need to force   #
#             # the value of the label to it's previous one and let the #
#             # command implementation update the index.                #
#             ###########################################################
#
#             self.setText(focusInData)
#
#             # TODO REIMPLEMENTA
#             # if focusInData and focusInData != currentData:
#             #     node = self.parentItem()
#             #     command = CommandLabelChange(self.diagram, node, focusInData, currentData)
#             #     self.session.undostack.push(command)
#
#             self.focusInData = None
#             self.setSelectedText(False)
#             self.setAlignment(self.alignment())
#             self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
#             self.diagram.setMode(DiagramMode.Idle)
#             self.diagram.sgnUpdated.emit()
#
#         super().focusOutEvent(focusEvent)
#
#     def hoverMoveEvent(self, moveEvent):
#         """
#         Executed when the mouse move over the text area (NOT PRESSED).
#         :type moveEvent: QGraphicsSceneHoverEvent
#         """
#         if self.isEditable() and self.hasFocus():
#             self.setCursor(QtCore.Qt.IBeamCursor)
#             super().hoverMoveEvent(moveEvent)
#
#     def hoverLeaveEvent(self, moveEvent):
#         """
#         Executed when the mouse leaves the text area (NOT PRESSED).
#         :type moveEvent: QGraphicsSceneHoverEvent
#         """
#         self.setCursor(QtCore.Qt.ArrowCursor)
#         super().hoverLeaveEvent(moveEvent)
#
#     def keyPressEvent(self, keyEvent):
#         """
#         Executed when a key is pressed.
#         :type keyEvent: QKeyEvent
#         """
#         if keyEvent.key() in {QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return}:
#             if keyEvent.modifiers() & QtCore.Qt.ShiftModifier:
#                 super().keyPressEvent(keyEvent)
#             else:
#                 self.clearFocus()
#         else:
#             super().keyPressEvent(keyEvent)
#
#     def mouseDoubleClickEvent(self, mouseEvent):
#         """
#         Executed when the mouse is double clicked on the text item.
#         :type mouseEvent: QGraphicsSceneMouseEvent
#         """
#         if self.isEditable():
#             super().mouseDoubleClickEvent(mouseEvent)
#             self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
#             self.setFocus()
#
#     #############################################
#     #   SLOTS
#     #################################
#
#     @QtCore.pyqtSlot(int, int, int)
#     def onContentsChanged(self, position, charsRemoved, charsAdded):
#         """
#         Executed whenever the content of the text item changes.
#         :type position: int
#         :type charsRemoved: int
#         :type charsAdded: int
#         """
#         self.setAlignment(self.alignment())
#
#     #############################################
#     #   INTERFACE
#     #################################
#
#     def alignment(self):
#         """
#         Returns the text alignment.
#         :rtype: int
#         """
#         return self._alignment
#
#     def center(self):
#         """
#         Returns the point at the center of the shape.
#         :rtype: QPointF
#         """
#         return self.boundingRect().center()
#
#     def height(self):
#         """
#         Returns the height of the text label.
#         :rtype: int
#         """
#         return self.boundingRect().height()
#
#     def isEditable(self):
#         """
#         Returns True if the label is editable, else False.
#         :rtype: bool
#         """
#         return self._editable
#
#     def isMovable(self):
#         """
#         Returns True if the label is movable, else False.
#         :rtype: bool
#         """
#         return self._movable
#
#     def pos(self):
#         """
#         Returns the position of the label in parent's item coordinates.
#         :rtype: QPointF
#         """
#         return self.mapToParent(self.center())
#
#     def setEditable(self, editable):
#         """
#         Set the editable status of the label.
#         :type editable: bool.
#         """
#         self._editable = bool(editable)
#         self.setFlag(BlackBirdAbstractLabel.ItemIsFocusable, self._editable)
#
#     def setMovable(self, movable):
#         """
#         Set the movable status of the Label.
#         :type movable: bool.
#         """
#         self._movable = bool(movable)
#
#     def setSelectedText(self, selected=True):
#         """
#         Select/deselect the text in the label.
#         :type selected: bool
#         """
#         cursor = self.textCursor()
#         if selected:
#             cursor.movePosition(QtGui.QTextCursor.Start, QtGui.QTextCursor.MoveAnchor)
#             cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)
#             cursor.select(QtGui.QTextCursor.Document)
#         else:
#             cursor.clearSelection()
#             cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
#         self.setTextCursor(cursor)
#
#     def setAlignment(self, alignment):
#         """
#         Set the text alignment.
#         :type alignment: int
#         """
#         self._alignment = alignment
#         self.setTextWidth(-1)
#         self.setTextWidth(self.boundingRect().width())
#         format_ = QtGui.QTextBlockFormat()
#         format_.setAlignment(alignment)
#         cursor = self.textCursor()
#         position = cursor.position()
#         selected = cursor.selectedText()
#         startPos = cursor.selectionStart()
#         endPos = cursor.selectionEnd()
#         cursor.select(QtGui.QTextCursor.Document)
#         cursor.mergeBlockFormat(format_)
#         if selected:
#             cursor.setPosition(startPos, QtGui.QTextCursor.MoveAnchor)
#             cursor.setPosition(endPos, QtGui.QTextCursor.KeepAnchor)
#             cursor.select(QtGui.QTextCursor.BlockUnderCursor)
#         else:
#             cursor.setPosition(position)
#         self.setTextCursor(cursor)
#
#     def setPos(self, *__args):
#         """
#         Set the item position.
#         QtWidgets.QGraphicsItem.setPos(QtCore.QPointF)
#         QtWidgets.QGraphicsItem.setPos(float, float)
#         """
#         if len(__args) == 1:
#             pos = __args[0]
#         elif len(__args) == 2:
#             pos = QtCore.QPointF(__args[0], __args[1])
#         else:
#             raise TypeError('too many arguments; expected {0}, got {1}'.format(2, len(__args)))
#         super().setPos(pos - QtCore.QPointF(self.width() / 2, self.height() / 2))
#
#     def setText(self, text):
#         """
#         Set the given text as plain text.
#         :type text: str.
#         """
#         self.setPlainText(text)
#
#     def shape(self):
#         """
#         Returns the shape of this item as a QPainterPath in local coordinates.
#         :rtype: QPainterPath
#         """
#         path = QtGui.QPainterPath()
#         path.addRect(self.boundingRect())
#         return path
#
#     def text(self):
#         """
#         Returns the text of the label.
#         :rtype: str
#         """
#         return self.toPlainText().strip()
#
#     def type(self):
#         """
#         Returns the type of this item.
#         :rtype: Item
#         """
#         return self.Type
#
#     @abstractmethod
#     def updatePos(self, *args, **kwargs):
#         """
#         Update the label position.
#         """
#         pass
#
#     def width(self):
#         """
#         Returns the width of the text label.
#         :rtype: int
#         """
#         return self.boundingRect().width()
#
#     def __repr__(self):
#         """
#         Returns repr(self).
#         """
#         return 'Label<{0}:{1}>'.format(self.parentItem().__class__.__name__, self.parentItem().id)
#
#
# class BlackBirdNodeLabel(BlackBirdAbstractLabel):
#     """
#     This class implements the label to be attached to the graphol nodes.
#     """
#
#     def __init__(self, template='', pos=None, movable=True, editable=True, parent=None):
#         """
#         Initialize the label.
#         :type template: str
#         :type pos: callable
#         :type movable: bool
#         :type editable: bool
#         :type parent: QObject
#         """
#         defaultPos = lambda: QtCore.QPointF(0, 0)
#         self.defaultPos = pos or defaultPos
#         super().__init__(template, movable, editable, parent=parent)
#         self.setPos(self.defaultPos())
#
#     #############################################
#     #   EVENTS
#     #################################
#
#     def keyPressEvent(self, keyEvent):
#         """
#         Executed when a key is pressed.
#         :type keyEvent: QKeyEvent
#         """
#         moved = self.isMoved()
#         super().keyPressEvent(keyEvent)
#         self.updatePos(moved)
#
#     def mousePressEvent(self, mouseEvent):
#         """
#         Executed when the mouse is pressed on the text item.
#         :type mouseEvent: QGraphicsSceneMouseEvent
#         """
#         # TODO REIMPLEMENTA
#         # if self.diagram.mode is DiagramMode.LabelEdit:
#         #     super().mousePressEvent(mouseEvent)
#         super().mousePressEvent(mouseEvent)
#
#     #############################################
#     #   INTERFACE
#     #################################
#
#     def isMoved(self):
#         """
#         Returns True if the label has been moved from its default location, else False.
#         :return: bool
#         """
#         return (self.pos() - self.defaultPos()).manhattanLength() >= 1
#
#     def setText(self, text):
#         """
#         Set the given text as plain text.
#         :type text: str.
#         """
#         moved = self.isMoved()
#         super().setText(text)
#         self.updatePos(moved)
#
#     def updatePos(self, moved=False):
#         """
#         Update the current text position with respect to its parent node.
#         :type moved: bool.
#         """
#         if not moved:
#             self.setPos(self.defaultPos())
#
#
# class BlackBirdAbstractEdge(BlackBirdAbstractItem):
#     """
#     Base class for all the diagram edges.
#     """
#     __metaclass__ = ABCMeta
#
#     Prefix = 'e'
#
#     def __init__(self, source, target=None, breakpoints=None, **kwargs):
#         """
#         Initialize the edge.
#         :type source: BlackBirdAbstractNode
#         :type target: BlackBirdAbstractNode
#         :type breakpoints: list
#         """
#         super().__init__(**kwargs)
#
#         self.source = source
#         self.target = target
#
#         self.anchors = {}  # {AbstractNode: Polygon}
#         self.breakpoints = breakpoints or []  # [QtCore.QPointF]
#         self.handles = []  # [Polygon]
#         self.head = Polygon(QtGui.QPolygonF())
#         self.path = Polygon(QtGui.QPainterPath())
#         self.selection = Polygon(QtGui.QPainterPath())
#
#         self.mp_AnchorNode = None
#         self.mp_AnchorNodePos = None
#         self.mp_BreakPoint = None
#         self.mp_BreakPointPos = None
#         self.mp_Pos = None
#
#         self.setAcceptHoverEvents(True)
#         self.setCacheMode(BlackBirdAbstractItem.DeviceCoordinateCache)
#         self.setFlag(BlackBirdAbstractItem.ItemIsSelectable, True)
#
#     #############################################
#     #   INTERFACE
#     #################################
#
#     def anchorAt(self, point):
#         """
#         Returns the key of the anchor whose handle is being pressed.
#         :type point: AbstractNode
#         """
#         size = QtCore.QPointF(3, 3)
#         area = QtCore.QRectF(point - size, point + size)
#         for k, v, in self.anchors.items():
#             if v.geometry().intersects(area):
#                 return k
#         return None
#
#     def anchorMove(self, node, mousePos):
#         """
#         Move the selected anchor point.
#         :type node: AbstractNode
#         :type mousePos: QtCore.QPointF
#         """
#         # Only allow anchor movement for concept nodes
#         # TODO REIMPLEMENTA
#         # if node.type() != Item.ConceptNode:
#         #     node.setAnchor(self, node.pos())
#         #     return
#
#         nodePos = node.pos()
#         snapToGrid = self.session.action('toggle_grid').isChecked()
#         mousePos = snap(mousePos, self.diagram.GridSize, snapToGrid)
#         path = self.mapFromItem(node, node.painterPath())
#         breakpoint = (self.breakpoints[-1] if node == self.target else self.breakpoints[0]) \
#             if len(self.breakpoints) > 0 else self.other(node).anchor(self)
#
#         if path.contains(breakpoint):
#             # If the source is inside the node then there will be no intersection
#             if path.contains(self.other(node).anchor(self)):
#                 return
#
#             # Breakpoint is inside the shape => use the source anchor
#             breakpoint = self.other(node).anchor(self)
#
#         if path.contains(mousePos):
#             # Mouse is inside the shape => use its position as the endpoint.
#             endpoint = mousePos
#         else:
#             # Mouse is outside the shape => use the intersection as the endpoint.
#             endpoint = node.intersection(QtCore.QLineF(nodePos, mousePos))
#
#         if distance(nodePos, endpoint) < 10.0:
#             # When close enough use the node center as the anchor point.
#             pos = nodePos
#         else:
#             # Otherwise compute the closest intersection between the breakpoint and the endpoint.
#             pos = node.intersection(QtCore.QLineF(breakpoint, endpoint))
#             minDistance = distance(breakpoint, pos)
#             for intersection in node.intersections(QtCore.QLineF(breakpoint, endpoint)):
#                 intersDistance = distance(breakpoint, intersection)
#                 if (intersDistance < minDistance):
#                     minDistance = intersDistance
#                     pos = intersection
#
#             if not path.contains(pos):
#                 # Ensure anchor is inside the path
#                 lineToBreakpoint = QtCore.QLineF(breakpoint, endpoint)
#                 direction = lineToBreakpoint.unitVector()
#                 normal = lineToBreakpoint.normalVector().unitVector()
#                 if path.contains(pos + QtCore.QPointF(direction.dx(), direction.dy())):
#                     pos = pos + QtCore.QPointF(direction.dx(), direction.dy())
#                 elif path.contains(pos - QtCore.QPointF(direction.dx(), direction.dy())):
#                     pos = pos - QtCore.QPointF(direction.dx(), direction.dy())
#                 elif path.contains(pos + QtCore.QPointF(normal.dx(), normal.dy())):
#                     pos = pos + QtCore.QPointF(normal.dx(), normal.dy())
#                 elif path.contains(pos - QtCore.QPointF(normal.dx(), normal.dy())):
#                     pos = pos - QtCore.QPointF(normal.dx(), normal.dy())
#                 else:  # Lower right corner
#                     pos = pos - QtCore.QPointF(0.5, 0.5)
#
#         node.setAnchor(self, pos)
#
#     def breakPointAdd(self, mousePos):
#         """
#         Create a new breakpoint from the given mouse position returning its index.
#         :type mousePos: QtCore.QPointF
#         :rtype: int
#         """
#         index = 0
#         point = None
#         between = None
#         shortest = 999
#
#         source = self.source.anchor(self)
#         target = self.target.anchor(self)
#         points = [source] + self.breakpoints + [target]
#
#         # Estimate between which breakpoints the new one is being added.
#         for subpath in (QtCore.QLineF(points[i], points[i + 1]) for i in range(len(points) - 1)):
#             dis, pos = projection(subpath, mousePos)
#             if dis < shortest:
#                 point = pos
#                 shortest = dis
#                 between = subpath.p1(), subpath.p2()
#
#         # If there is no breakpoint the new one will be appended.
#         for i, breakpoint in enumerate(self.breakpoints):
#
#             if breakpoint == between[1]:
#                 # In case the new breakpoint is being added between
#                 # the source node of this edge and the last breakpoint.
#                 index = i
#                 break
#
#             if breakpoint == between[0]:
#                 # In case the new breakpoint is being added between
#                 # the last breakpoint and the target node of this edge.
#                 index = i + 1
#                 break
#
#         # TODO REIMPLEMENTA
#         # self.session.undostack.push(CommandEdgeBreakpointAdd(self.diagram, self, index, point))
#         return index
#
#     def breakPointAt(self, point):
#         """
#         Returns the index of the breakpoint whose handle is being pressed.
#         :type point: QtCore.QPointF
#         :rtype: int
#         """
#         size = QtCore.QPointF(3, 3)
#         area = QtCore.QRectF(point - size, point + size)
#         for polygon in self.handles:
#             if polygon.geometry().intersects(area):
#                 return self.handles.index(polygon)
#         return None
#
#     def breakPointMove(self, breakpoint, mousePos):
#         """
#         Move the selected breakpoint.
#         :type breakpoint: int
#         :type mousePos: QtCore.QPointF
#         """
#         snapToGrid = self.session.action('toggle_grid').isChecked()
#         mousePos = snap(mousePos, self.diagram.GridSize, snapToGrid)
#         source = self.source
#         target = self.target
#         breakpointPos = self.breakpoints[breakpoint]
#         sourcePath = self.mapFromItem(source, source.painterPath())
#         targetPath = self.mapFromItem(target, target.painterPath())
#         if sourcePath.contains(mousePos):
#             # Mouse is inside the source node, use the intersection as the breakpoint position if it exists.
#             pos = source.intersection(QtCore.QLineF(source.pos(), breakpointPos)) or mousePos
#         elif targetPath.contains(mousePos):
#             # Mouse is inside the target node, use the intersection as the breakpoint position if it exists.
#             pos = target.intersection(QtCore.QLineF(target.pos(), breakpointPos)) or mousePos
#         else:
#             # Mouse is outside both source and target node, use this as the breakpoint position.
#             pos = mousePos
#
#         self.breakpoints[breakpoint] = pos
#
#     def canDraw(self):
#         """
#         Check whether we have to draw the edge or not.
#         :rtype: bool
#         """
#         if not self.diagram:
#             return False
#
#         if self.target:
#             source = self.source
#             target = self.target
#             sp = self.mapFromItem(source, source.painterPath())
#             tp = self.mapFromItem(target, target.painterPath())
#             if sp.intersects(tp):
#                 for point in self.breakpoints:
#                     if not source.contains(self.mapToItem(source, point)):
#                         if not target.contains(self.mapToItem(target, point)):
#                             return True
#                 return False
#         return True
#
#     @abstractmethod
#     def copy(self, diagram):
#         """
#         Create a copy of the current item.
#         :type diagram: Diagram
#         """
#         pass
#
#     def createPath(self, source, target, points):
#         """
#         Returns a list of QtCore.QLineF instance representing all the visible edge pieces.
#         Subpaths which are obscured by the source or target shape are excluded by this method.
#         :type source: BlackBirdAbstractNode
#         :type target: BlackBirdAbstractNode
#         :type points: list
#         :rtype: list
#         """
#         # Get the source node painter path (the source node is always available).
#         A = self.mapFromItem(source, source.painterPath())
#         B = self.mapFromItem(target, target.painterPath()) if target else None
#         # Exclude all the "subpaths" which are not visible (obscured by the shapes).
#         return [x for x in (QtCore.QLineF(points[i], points[i + 1]) for i in range(len(points) - 1)) \
#                 if (not A.contains(x.p1()) or not A.contains(x.p2())) and \
#                 (not B or (not B.contains(x.p1()) or not B.contains(x.p2())))]
#
#     def isSwapAllowed(self):
#         """
#         Returns True if this edge can be swapped, False otherwise.
#         :rtype: bool
#         """
#         return self.project.profile.checkEdge(self.target, self, self.source).isValid()
#
#     def moveBy(self, x, y):
#         """
#         Move the edge by the given deltas.
#         :type x: float
#         :type y: float
#         """
#         self.breakpoints = [p + QtCore.QPointF(x, y) for p in self.breakpoints]
#
#     def other(self, node):
#         """
#         Returns the opposite endpoint of the given node.
#         :raise AttributeError: if the given node is not an endpoint of this edge.
#         :type node: AttributeNode
#         :rtype: Node
#         """
#         if node is self.source:
#             return self.target
#         elif node is self.target:
#             return self.source
#         raise AttributeError('node {0} is not attached to edge {1}'.format(node, self))
#
#     def updateEdge(self, selected=None, visible=None, breakpoint=None, anchor=None, **kwargs):
#         """
#         Update the current edge.
#         :type selected: bool
#         :type visible: bool
#         :type breakpoint: int
#         :type anchor: BlackBirdAbstractNode
#         """
#         if selected is None:
#             selected = self.isSelected()
#         if visible is None:
#             visible = self.canDraw()
#
#         source = self.source
#         target = self.target
#
#         ## ANCHORS (GEOMETRY) --> NB: THE POINTS ARE IN THE ENDPOINTS
#         if source and target:
#             p = source.anchor(self)
#             self.anchors[source] = Polygon(QtCore.QRectF(p.x() - 4, p.y() - 4, 8, 8))
#             p = target.anchor(self)
#             self.anchors[target] = Polygon(QtCore.QRectF(p.x() - 4, p.y() - 4, 8, 8))
#
#         ## BREAKPOINTS (GEOMETRY)
#         self.handles = [Polygon(QtCore.QRectF(p.x() - 4, p.y() - 4, 8, 8)) for p in self.breakpoints]
#
#         ## ANCHORS + BREAKPOINTS + SELECTION (BRUSH + PEN)
#         if visible and selected:
#             apBrush = QtGui.QBrush(QtGui.QColor(66, 165, 245, 255))
#             apPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap,
#                                QtCore.Qt.RoundJoin)
#             bpBrush = QtGui.QBrush(QtGui.QColor(66, 165, 245, 255))
#             bpPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap,
#                                QtCore.Qt.RoundJoin)
#             selectionBrush = QtGui.QBrush(QtGui.QColor(248, 255, 72, 255))
#         else:
#             apBrush = QtGui.QBrush(QtCore.Qt.NoBrush)
#             apPen = QtGui.QPen(QtCore.Qt.NoPen)
#             bpBrush = QtGui.QBrush(QtCore.Qt.NoBrush)
#             bpPen = QtGui.QPen(QtCore.Qt.NoPen)
#             selectionBrush = QtGui.QBrush(QtCore.Qt.NoBrush)
#         for polygon in self.anchors.values():
#             polygon.setBrush(apBrush)
#             polygon.setPen(apPen)
#         for polygon in self.handles:
#             polygon.setBrush(bpBrush)
#             polygon.setPen(bpPen)
#         self.selection.setBrush(selectionBrush)
#
#         ## Z-VALUE (DEPTH)
#         try:
#             zValue = max(*(x.zValue() for x in self.collidingItems())) + 0.1
#         except TypeError:
#             zValue = source.zValue() + 0.1
#             if source.label:
#                 zValue = max(zValue, source.label.zValue())
#             if target:
#                 zValue = max(zValue, target.zValue())
#                 if target.label:
#                     zValue = max(zValue, target.label.zValue())
#         self.setZValue(zValue)
#
#         ## FORCE CACHE REGENERATION
#         self.setCacheMode(BlackBirdAbstractItem.NoCache)
#         self.setCacheMode(BlackBirdAbstractItem.DeviceCoordinateCache)
#
#     #############################################
#     #   EVENTS
#     #################################
#
#     def hoverEnterEvent(self, hoverEvent):
#         """
#         Executed when the mouse enters the shape (NOT PRESSED).
#         :type hoverEvent: QGraphicsSceneHoverEvent
#         """
#         self.setCursor(QtCore.Qt.PointingHandCursor)
#         super().hoverEnterEvent(hoverEvent)
#
#     def hoverMoveEvent(self, hoverEvent):
#         """
#         Executed when the mouse moves over the shape (NOT PRESSED).
#         :type hoverEvent: QGraphicsSceneHoverEvent
#         """
#         self.setCursor(QtCore.Qt.PointingHandCursor)
#         super().hoverMoveEvent(hoverEvent)
#
#     def hoverLeaveEvent(self, hoverEvent):
#         """
#         Executed when the mouse leaves the shape (NOT PRESSED).
#         :type hoverEvent: QGraphicsSceneHoverEvent
#         """
#         self.setCursor(QtCore.Qt.ArrowCursor)
#         super().hoverLeaveEvent(hoverEvent)
#
#     def itemChange(self, change, value):
#         """
#         Executed whenever the item change state.
#         :type change: GraphicsItemChange
#         :type value: QVariant
#         :rtype: QVariant
#         """
#         if change == BlackBirdAbstractEdge.ItemSelectedHasChanged:
#             self.updateEdge(selected=value)
#         return super().itemChange(change, value)
#
#     def mousePressEvent(self, mouseEvent):
#         """
#         Executed when the mouse is pressed on the selection box.
#         :type mouseEvent: QGraphicsSceneMouseEvent
#         """
#         self.mp_Pos = mouseEvent.pos()
#
#         # TODO REIMPLEMENTA
#         # if self.diagram.mode is DiagramMode.Idle:
#         #     # Check first if we need to start an anchor point movement: we need
#         #     # to evaluate anchor points first because we may be in the situation
#         #     # where we are trying to select the anchor point, but if the code for
#         #     # breakpoint retrieval is executed first, no breakpoint is found
#         #     # and hence a new one will be added upon mouseMoveEvent.
#         #     anchorNode = self.anchorAt(self.mp_Pos)
#         #     if anchorNode is not None:
#         #         self.diagram.clearSelection()
#         #         self.diagram.setMode(DiagramMode.EdgeAnchorMove)
#         #         self.setSelected(True)
#         #         self.mp_AnchorNode = anchorNode
#         #         self.mp_AnchorNodePos = QtCore.QPointF(anchorNode.anchor(self))
#         #         self.updateEdge(selected=True, anchor=anchorNode)
#         #     else:
#         #         breakPoint = self.breakPointAt(self.mp_Pos)
#         #         if breakPoint is not None:
#         #             self.diagram.clearSelection()
#         #             self.diagram.setMode(DiagramMode.EdgeBreakPointMove)
#         #             self.setSelected(True)
#         #             self.mp_BreakPoint = breakPoint
#         #             self.mp_BreakPointPos = QtCore.QPointF(self.breakpoints[breakPoint])
#         #             self.updateEdge(selected=True, breakpoint=breakPoint)
#
#         super().mousePressEvent(mouseEvent)
#
#     # noinspection PyTypeChecker
#     def mouseMoveEvent(self, mouseEvent):
#         """
#         Executed when the mouse is being moved over the item while being pressed.
#         :type mouseEvent: QGraphicsSceneMouseEvent
#         """
#         mousePos = mouseEvent.pos()
#
#         # TODO REIMPLEMENTA
#         # if self.diagram.mode is DiagramMode.EdgeAnchorMove:
#         #     self.anchorMove(self.mp_AnchorNode, mousePos)
#         #     self.updateEdge()
#         # else:
#         #
#         #     if self.diagram.mode is DiagramMode.Idle:
#         #
#         #         try:
#         #             # If we are still idle we didn't succeeded in
#         #             # selecting a breakpoint so we need to create
#         #             # a new one and switch the operational mode.
#         #             breakPoint = self.breakPointAdd(self.mp_Pos)
#         #         except:
#         #             pass
#         #         else:
#         #             self.diagram.clearSelection()
#         #             self.diagram.setMode(DiagramMode.EdgeBreakPointMove)
#         #             self.setSelected(True)
#         #             self.mp_BreakPoint = breakPoint
#         #             self.mp_BreakPointPos = QtCore.QPointF(self.breakpoints[breakPoint])
#         #
#         #     if self.diagram.mode is DiagramMode.EdgeBreakPointMove:
#         #         self.breakPointMove(self.mp_BreakPoint, mousePos)
#         #         self.updateEdge()
#
#     def mouseReleaseEvent(self, mouseEvent):
#         """
#         Executed when the mouse is released from the selection box.
#         :type mouseEvent: QGraphicsSceneMouseEvent
#         """
#         # TODO REIMPLEMENTA
#         # if self.diagram.mode is DiagramMode.EdgeAnchorMove:
#         #     anchorNode = self.mp_AnchorNode
#         #     anchorNodePos = QtCore.QPointF(anchorNode.anchor(self))
#         #     if anchorNodePos != self.mp_AnchorNodePos:
#         #         data = {'undo': self.mp_AnchorNodePos, 'redo': anchorNodePos}
#         #         self.session.undostack.push(CommandEdgeAnchorMove(self.diagram, self, anchorNode, data))
#         # elif self.diagram.mode is DiagramMode.EdgeBreakPointMove:
#         #     breakPoint = self.mp_BreakPoint
#         #     breakPointPos = self.breakpoints[breakPoint]
#         #     if breakPointPos != self.mp_BreakPointPos:
#         #         data = {'undo': self.mp_BreakPointPos, 'redo': breakPointPos}
#         #         self.session.undostack.push(CommandEdgeBreakpointMove(self.diagram, self, breakPoint, data))
#
#         self.mp_AnchorNode = None
#         self.mp_AnchorNodePos = None
#         self.mp_BreakPoint = None
#         self.mp_BreakPointPos = None
#         self.mp_Pos = None
#
#         # TODO REIMPLEMENTA
#         # self.diagram.setMode(DiagramMode.Idle)
#         self.updateEdge()
#
#
# #############################################
# #                                           #
# #               LABELS                      #
# #                                           #
# #############################################
# class BlackBirdTableHeaderLabel(BlackBirdNodeLabel):
#     """
#     This class implements the label of table header nodes.
#     """
#
#     def __init__(self, **kwargs):
#         """
#         Initialize the label.
#         :type kwargs: dict
#         """
#         super().__init__(**kwargs)
#
#     #############################################
#     #   EVENTS
#     #################################
#
#     def focusInEvent(self, focusEvent):
#         """
#         Executed when the text item is focused.
#         :type focusEvent: QFocusEvent
#         """
#         # FOCUS ONLY ON DOUBLE CLICK
#         if focusEvent.reason() == QtCore.Qt.OtherFocusReason:
#             self.focusInData = self.text()
#             self.diagram.clearSelection()
#             #self.diagram.setMode(DiagramMode.LabelEdit)
#             self.setSelectedText(True)
#             super().focusInEvent(focusEvent)
#         else:
#             self.clearFocus()
#
#     def focusOutEvent(self, focusEvent):
#         """
#         Executed when the text item loses the focus.
#         :type focusEvent: QFocusEvent
#         """
#         # TODO REIMPLEMENTA
#         # if self.diagram.mode is DiagramMode.LabelEdit:
#         #
#         #     if isEmpty(self.text()):
#         #         self.setText(self.template)
#         #
#         #     focusInData = self.focusInData
#         #
#         #     ###########################################################
#         #     # IMPORTANT!                                              #
#         #     # ####################################################### #
#         #     # The code below is a bit tricky: to be able to properly  #
#         #     # update the node in the project index we need to force   #
#         #     # the value of the label to it's previous one and let the #
#         #     # command implementation update the index.                #
#         #     ###########################################################
#         #
#         #     # Validate entered IRI
#         #     prefixManager = self.project.prefixManager
#         #     text = self.text()
#         #     repairedIRI = text.replace('\n', '')
#         #     shortForm = prefixManager.getShortForm(repairedIRI)
#         #     if shortForm != repairedIRI:
#         #         currentData = shortForm
#         #     else:
#         #         currentData = self.text()
#         #
#         #     if focusInData and focusInData != currentData:
#         #         command = CommandLabelChange(self.diagram, self.parentItem(), focusInData, currentData)
#         #         self.session.undostack.push(command)
#         #
#         #     self.focusInData = None
#         #     self.setSelectedText(False)
#         #     self.setAlignment(self.alignment())
#         #     self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
#         #     self.diagram.setMode(DiagramMode.Idle)
#         #     self.diagram.sgnUpdated.emit()
#
#         super().focusOutEvent(focusEvent)
#
#
# #############################################
# #                                           #
# #                NODES                      #
# #                                           #
# #############################################
# class BlackBirdTableHeaderNode(BlackBirdAbstractNode):
#     """
#     This class implements the table header node.
#     """
#     DefaultBrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
#     DefaultPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap,
#                              QtCore.Qt.RoundJoin)
#     #DefaultBrush = QtGui.QBrush(QtCore.Qt.NoBrush)
#     #DefaultPen = QtGui.QPen(QtCore.Qt.NoPen)
#     Identities = {BlackBirdIdentity.TableHeader}
#     Type = BlackBirdItem.TableHeaderNode
#
#     def __init__(self, tableName="TableName", width=300, height=50, brush=None, **kwargs):
#         """
#         Initialize the node.
#         :type parent: BlackBirdTableNode
#         :type width: int
#         :type height: int
#         :type brush: QBrush
#         """
#         super().__init__(**kwargs)
#         w = max(width, 300)
#         h = max(height, 50)
#         brush = brush or BlackBirdTableHeaderNode.DefaultBrush
#         pen = BlackBirdTableHeaderNode.DefaultPen
#         self.background = Polygon(QtCore.QRectF(-(w + 8) / 2, -(h + 8) / 2, w + 8, h + 8))
#         self.selection = Polygon(QtCore.QRectF(-(w + 8) / 2, -(h + 8) / 2, w + 8, h + 8))
#         self.polygon = Polygon(QtCore.QRectF(-w / 2, -h / 2, w, h), brush, pen)
#
#         pos = self.pos()
#
#         self.label = BlackBirdTableHeaderLabel(template=tableName, pos=pos, parent=self)
#         self.label.setAlignment(QtCore.Qt.AlignCenter)
#         #self.updateNode()
#         #self.updateTextPos()
#
#     #############################################
#     #   INTERFACE
#     #################################
#
#     def setPosWRTParent(self):
#         parentPos = self.parentItem().pos()
#         rowCount = self.parentItem().rowCount()
#         delta = (25+((rowCount-1)*25))
#         print("delta=",delta)
#         self.setPos(QPointF(parentPos.x(), parentPos.y() + 25))
#         self.label.setPos(QPointF(parentPos.x(), parentPos.y() + 25))
#         print("parentPos: x=", parentPos.x(), " y=", parentPos.y())
#         print("headerPos: x=", self.pos().x(), " y=", self.pos().y())
#         # self.setPos(self.mapToScene(QPointF(parentPos.x(), parentPos.y()+25)))
#         # self.label.setPos(self.mapToScene(QPointF(parentPos.x(), parentPos.y()+25)))
#         #self.setTextPos(self.center)
#
#     def boundingRect(self):
#         """
#         Returns the shape bounding rectangle.
#         :rtype: QtCore.QRectF
#         """
#         return self.selection.geometry()
#     #
#     # # def copy(self, diagram):
#     # #     """
#     # #     Create a copy of the current item.
#     # #     :type diagram: BlackBirdDiagram
#     # #     """
#     # #     node = diagram.factory.create(self.type(), **{
#     # #         'id': self.id,
#     # #         'brush': self.brush(),
#     # #         'height': self.height(),
#     # #         'width': self.width()
#     # #     })
#     # #     node.setPos(self.pos())
#     # #     node.setText(self.text())
#     # #     node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
#     # #     return node
#     #
#     # def height(self):
#     #     """
#     #     Returns the height of the shape.
#     #     :rtype: int
#     #     """
#     #     return self.polygon.geometry().height()
#     #
#     # def identity(self):
#     #     """
#     #     Returns the identity of the current node.
#     #     :rtype: Identity
#     #     """
#     #     return Identity.Concept
#     #
#     def paint(self, painter, option, widget=None):
#         """
#         Paint the node in the diagram.
#         :type painter: QPainter
#         :type option: QStyleOptionGraphicsItem
#         :type widget: QWidget
#         """
#         # SET THE RECT THAT NEEDS TO BE REPAINTED
#         painter.setClipRect(option.exposedRect)
#         # SELECTION AREA
#         painter.setPen(self.selection.pen())
#         painter.setBrush(self.selection.brush())
#         painter.drawRect(self.selection.geometry())
#         # SYNTAX VALIDATION
#         painter.setPen(self.background.pen())
#         painter.setBrush(self.background.brush())
#         painter.drawRect(self.background.geometry())
#         # ITEM SHAPE
#         painter.setPen(self.polygon.pen())
#         painter.setBrush(self.polygon.brush())
#         painter.drawRect(self.polygon.geometry())
#         # RESIZE HANDLES
#         painter.setRenderHint(QtGui.QPainter.Antialiasing)
#         # for polygon in self.handles:
#         #     painter.setPen(polygon.pen())
#         #     painter.setBrush(polygon.brush())
#         #     painter.drawEllipse(polygon.geometry())
#
#     def painterPath(self):
#         """
#         Returns the current shape as QtGui.QPainterPath (used for collision detection).
#         :rtype: QPainterPath
#         """
#         path = QtGui.QPainterPath()
#         path.addRect(self.polygon.geometry())
#         return path
#
#     # def resize(self, mousePos):
#     #     """
#     #     Handle the interactive resize of the shape.
#     #     :type mousePos: QtCore.QPointF
#     #     """
#     #     snap = self.session.action('toggle_grid').isChecked()
#     #     size = self.diagram.GridSize
#     #     moved = self.label.isMoved()
#     #     background = self.background.geometry()
#     #     selection = self.selection.geometry()
#     #     polygon = self.polygon.geometry()
#     #
#     #     R = QtCore.QRectF(self.boundingRect())
#     #     D = QtCore.QPointF(0, 0)
#     #
#     #     mbrh = 58
#     #     mbrw = 118
#     #
#     #     self.prepareGeometryChange()
#     #
#     #     if self.mp_Handle == self.HandleTL:
#     #
#     #         fromX = self.mp_Bound.left()
#     #         fromY = self.mp_Bound.top()
#     #         toX = fromX + mousePos.x() - self.mp_Pos.x()
#     #         toY = fromY + mousePos.y() - self.mp_Pos.y()
#     #         toX = snapF(toX, size, -4, snap)
#     #         toY = snapF(toY, size, -4, snap)
#     #         D.setX(toX - fromX)
#     #         D.setY(toY - fromY)
#     #         R.setLeft(toX)
#     #         R.setTop(toY)
#     #
#     #         ## CLAMP SIZE
#     #         if R.width() < mbrw:
#     #             D.setX(D.x() - mbrw + R.width())
#     #             R.setLeft(R.left() - mbrw + R.width())
#     #         if R.height() < mbrh:
#     #             D.setY(D.y() - mbrh + R.height())
#     #             R.setTop(R.top() - mbrh + R.height())
#     #
#     #         background.setLeft(R.left())
#     #         background.setTop(R.top())
#     #         selection.setLeft(R.left())
#     #         selection.setTop(R.top())
#     #         polygon.setLeft(R.left() + 4)
#     #         polygon.setTop(R.top() + 4)
#     #
#     #     elif self.mp_Handle == self.HandleTM:
#     #
#     #         fromY = self.mp_Bound.top()
#     #         toY = fromY + mousePos.y() - self.mp_Pos.y()
#     #         toY = snapF(toY, size, -4, snap)
#     #         D.setY(toY - fromY)
#     #         R.setTop(toY)
#     #
#     #         ## CLAMP SIZE
#     #         if R.height() < mbrh:
#     #             D.setY(D.y() - mbrh + R.height())
#     #             R.setTop(R.top() - mbrh + R.height())
#     #
#     #         background.setTop(R.top())
#     #         selection.setTop(R.top())
#     #         polygon.setTop(R.top() + 4)
#     #
#     #     elif self.mp_Handle == self.HandleTR:
#     #
#     #         fromX = self.mp_Bound.right()
#     #         fromY = self.mp_Bound.top()
#     #         toX = fromX + mousePos.x() - self.mp_Pos.x()
#     #         toY = fromY + mousePos.y() - self.mp_Pos.y()
#     #         toX = snapF(toX, size, +4, snap)
#     #         toY = snapF(toY, size, -4, snap)
#     #         D.setX(toX - fromX)
#     #         D.setY(toY - fromY)
#     #         R.setRight(toX)
#     #         R.setTop(toY)
#     #
#     #         ## CLAMP SIZE
#     #         if R.width() < mbrw:
#     #             D.setX(D.x() + mbrw - R.width())
#     #             R.setRight(R.right() + mbrw - R.width())
#     #         if R.height() < mbrh:
#     #             D.setY(D.y() - mbrh + R.height())
#     #             R.setTop(R.top() - mbrh + R.height())
#     #
#     #         background.setRight(R.right())
#     #         background.setTop(R.top())
#     #         selection.setRight(R.right())
#     #         selection.setTop(R.top())
#     #         polygon.setRight(R.right() - 4)
#     #         polygon.setTop(R.top() + 4)
#     #
#     #     elif self.mp_Handle == self.HandleML:
#     #
#     #         fromX = self.mp_Bound.left()
#     #         toX = fromX + mousePos.x() - self.mp_Pos.x()
#     #         toX = snapF(toX, size, -4, snap)
#     #         D.setX(toX - fromX)
#     #         R.setLeft(toX)
#     #
#     #         ## CLAMP SIZE
#     #         if R.width() < mbrw:
#     #             D.setX(D.x() - mbrw + R.width())
#     #             R.setLeft(R.left() - mbrw + R.width())
#     #
#     #         background.setLeft(R.left())
#     #         selection.setLeft(R.left())
#     #         polygon.setLeft(R.left() + 4)
#     #
#     #     elif self.mp_Handle == self.HandleMR:
#     #
#     #         fromX = self.mp_Bound.right()
#     #         toX = fromX + mousePos.x() - self.mp_Pos.x()
#     #         toX = snapF(toX, size, +4, snap)
#     #         D.setX(toX - fromX)
#     #         R.setRight(toX)
#     #
#     #         ## CLAMP SIZE
#     #         if R.width() < mbrw:
#     #             D.setX(D.x() + mbrw - R.width())
#     #             R.setRight(R.right() + mbrw - R.width())
#     #
#     #         background.setRight(R.right())
#     #         selection.setRight(R.right())
#     #         polygon.setRight(R.right() - 4)
#     #
#     #     elif self.mp_Handle == self.HandleBL:
#     #
#     #         fromX = self.mp_Bound.left()
#     #         fromY = self.mp_Bound.bottom()
#     #         toX = fromX + mousePos.x() - self.mp_Pos.x()
#     #         toY = fromY + mousePos.y() - self.mp_Pos.y()
#     #         toX = snapF(toX, size, -4, snap)
#     #         toY = snapF(toY, size, +4, snap)
#     #         D.setX(toX - fromX)
#     #         D.setY(toY - fromY)
#     #         R.setLeft(toX)
#     #         R.setBottom(toY)
#     #
#     #         ## CLAMP SIZE
#     #         if R.width() < mbrw:
#     #             D.setX(D.x() - mbrw + R.width())
#     #             R.setLeft(R.left() - mbrw + R.width())
#     #         if R.height() < mbrh:
#     #             D.setY(D.y() + mbrh - R.height())
#     #             R.setBottom(R.bottom() + mbrh - R.height())
#     #
#     #         background.setLeft(R.left())
#     #         background.setBottom(R.bottom())
#     #         selection.setLeft(R.left())
#     #         selection.setBottom(R.bottom())
#     #         polygon.setLeft(R.left() + 4)
#     #         polygon.setBottom(R.bottom() - 4)
#     #
#     #     elif self.mp_Handle == self.HandleBM:
#     #
#     #         fromY = self.mp_Bound.bottom()
#     #         toY = fromY + mousePos.y() - self.mp_Pos.y()
#     #         toY = snapF(toY, size, +4, snap)
#     #         D.setY(toY - fromY)
#     #         R.setBottom(toY)
#     #
#     #         ## CLAMP SIZE
#     #         if R.height() < mbrh:
#     #             D.setY(D.y() + mbrh - R.height())
#     #             R.setBottom(R.bottom() + mbrh - R.height())
#     #
#     #         background.setBottom(R.bottom())
#     #         selection.setBottom(R.bottom())
#     #         polygon.setBottom(R.bottom() - 4)
#     #
#     #     elif self.mp_Handle == self.HandleBR:
#     #
#     #         fromX = self.mp_Bound.right()
#     #         fromY = self.mp_Bound.bottom()
#     #         toX = fromX + mousePos.x() - self.mp_Pos.x()
#     #         toY = fromY + mousePos.y() - self.mp_Pos.y()
#     #         toX = snapF(toX, size, +4, snap)
#     #         toY = snapF(toY, size, +4, snap)
#     #         D.setX(toX - fromX)
#     #         D.setY(toY - fromY)
#     #         R.setRight(toX)
#     #         R.setBottom(toY)
#     #
#     #         ## CLAMP SIZE
#     #         if R.width() < mbrw:
#     #             D.setX(D.x() + mbrw - R.width())
#     #             R.setRight(R.right() + mbrw - R.width())
#     #         if R.height() < mbrh:
#     #             D.setY(D.y() + mbrh - R.height())
#     #             R.setBottom(R.bottom() + mbrh - R.height())
#     #
#     #         background.setRight(R.right())
#     #         background.setBottom(R.bottom())
#     #         selection.setRight(R.right())
#     #         selection.setBottom(R.bottom())
#     #         polygon.setRight(R.right() - 4)
#     #         polygon.setBottom(R.bottom() - 4)
#     #
#     #     self.background.setGeometry(background)
#     #     self.selection.setGeometry(selection)
#     #     self.polygon.setGeometry(polygon)
#     #
#     #     self.updateNode(selected=True, handle=self.mp_Handle, anchors=(self.mp_Data, D))
#     #     self.updateTextPos(moved=moved)
#
#     def setIdentity(self, identity):
#         """
#         Set the identity of the current node.
#         :type identity: Identity
#         """
#         pass
#
#     def setText(self, text):
#         """
#         Set the label text.
#         :type text: str
#         """
#         self.label.setText(text)
#         self.label.setAlignment(QtCore.Qt.AlignCenter)
#
#     def setTextPos(self, pos):
#         """
#         Set the label position.
#         :type pos: QPointF
#         """
#         self.label.setPos(pos)
#
#     def shape(self):
#         """
#         Returns the shape of this item as a QPainterPath in local coordinates.
#         :rtype: QPainterPath
#         """
#         path = QtGui.QPainterPath()
#         path.addRect(self.polygon.geometry())
#         # for polygon in self.handles:
#         #     path.addEllipse(polygon.geometry())
#         return path
#
#     def special(self):
#         """
#         Returns the special type of this node.
#         :rtype: Special
#         """
#         return Special.valueOf(self.text())
#
#     def text(self):
#         """
#         Returns the label text.
#         :rtype: str
#         """
#         return self.label.text()
#
#     def textPos(self):
#         """
#         Returns the current label position in item coordinates.
#         :rtype: QPointF
#         """
#         return self.label.pos()
#
#     def setAlignment(self, alignment):
#         self.label.setAlignment(alignment)
#
#     def updateTextPos(self, *args, **kwargs):
#         """
#         Update the label position.
#         """
#         self.label.updatePos(*args, **kwargs)
#
#     def width(self):
#         """
#         Returns the width of the shape.
#         :rtype: int
#         """
#         return self.polygon.geometry().width()
#
#     def __repr__(self):
#         """
#         Returns repr(self).
#         """
#         return '{0}:{1}:{2}'.format(self.__class__.__name__, self.text(), self.id)
#
#
# class BlackBirdTableNode(BlackBirdAbstractNode):
#     """
#         This class implements the table node.
#         """
#     DefaultBrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
#     DefaultPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap,QtCore.Qt.RoundJoin)
#
#     Identities = {BlackBirdIdentity.Table}
#     Type = BlackBirdItem.TableNode
#
#     def __init__(self, rows=None, parent=None, tableName='TableName', width=300, height=150, brush=None, **kwargs):
#         """
#         Initialize the node.
#         :type parent: BlackBirdTableNode
#         :type width: int
#         :type height: int
#         :type brush: QBrush
#         """
#         super().__init__(**kwargs)
#         if rows is None:
#             self.rows = []
#
#         w = max(width, 110)
#         h = max(height, 50)
#         h = 3*50
#         brush = brush or BlackBirdTableNode.DefaultBrush
#         pen = BlackBirdTableNode.DefaultPen
#         self.background = Polygon(QtCore.QRectF(-(w + 8) / 2, -(h + 8) / 2, w + 8, h + 8))
#         self.selection = Polygon(QtCore.QRectF(-(w + 8) / 2, -(h + 8) / 2, w + 8, h + 8))
#         self.polygon = Polygon(QtCore.QRectF(-w / 2, -h / 2, w, h), brush, pen)
#         self.updateNode()
#         # self.updateTextPos()
#
#         #self.header = BlackBirdTableHeaderNode(diagram=self.diagram ,tableName=tableName, parent=self)
#
#     #############################################
#     #   INTERFACE
#     #################################
#
#     def rowCount(self):
#         return 2
#
#     def boundingRect(self):
#         """
#         Returns the shape bounding rectangle.
#         :rtype: QtCore.QRectF
#         """
#         return self.selection.geometry()
#
#     #
#     # def copy(self, diagram):
#     #     """
#     #     Create a copy of the current item.
#     #     :type diagram: Diagram
#     #     """
#     #     node = diagram.factory.create(self.type(), **{
#     #         'id': self.id,
#     #         'brush': self.brush(),
#     #         'height': self.height(),
#     #         'width': self.width()
#     #     })
#     #     node.setPos(self.pos())
#     #     node.setText(self.text())
#     #     node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
#     #     return node
#     #
#     #
#     # def height(self):
#     #     """
#     #     Returns the height of the shape.
#     #     :rtype: int
#     #     """
#     #     return self.polygon.geometry().height()
#     #
#     #
#     # def identity(self):
#     #     """
#     #     Returns the identity of the current node.
#     #     :rtype: Identity
#     #     """
#     #     return BlackBirdIdentity.Table
#     #
#     #
#     def paint(self, painter, option, widget=None):
#         """
#         Paint the node in the diagram.
#         :type painter: QPainter
#         :type option: QStyleOptionGraphicsItem
#         :type widget: QWidget
#         """
#         # SET THE RECT THAT NEEDS TO BE REPAINTED
#         painter.setClipRect(option.exposedRect)
#         # SELECTION AREA
#         painter.setPen(self.selection.pen())
#         painter.setBrush(self.selection.brush())
#         painter.drawRect(self.selection.geometry())
#         # SYNTAX VALIDATION
#         painter.setPen(self.background.pen())
#         painter.setBrush(self.background.brush())
#         painter.drawRect(self.background.geometry())
#         # ITEM SHAPE
#         painter.setPen(self.polygon.pen())
#         painter.setBrush(self.polygon.brush())
#         painter.drawRect(self.polygon.geometry())
#         # RESIZE HANDLES
#         painter.setRenderHint(QtGui.QPainter.Antialiasing)
#         # for polygon in self.handles:
#         #     painter.setPen(polygon.pen())
#         #     painter.setBrush(polygon.brush())
#         #     painter.drawEllipse(polygon.geometry())
#
#
#     def painterPath(self):
#         """
#         Returns the current shape as QtGui.QPainterPath (used for collision detection).
#         :rtype: QPainterPath
#         """
#         path = QtGui.QPainterPath()
#         path.addRect(self.polygon.geometry())
#         return path
#
#
#     # def resize(self, mousePos):
#     #     """
#     #     Handle the interactive resize of the shape.
#     #     :type mousePos: QtCore.QPointF
#     #     """
#     #     snap = self.session.action('toggle_grid').isChecked()
#     #     size = self.diagram.GridSize
#     #     moved = self.label.isMoved()
#     #     background = self.background.geometry()
#     #     selection = self.selection.geometry()
#     #     polygon = self.polygon.geometry()
#     #
#     #     R = QtCore.QRectF(self.boundingRect())
#     #     D = QtCore.QPointF(0, 0)
#     #
#     #     mbrh = 58
#     #     mbrw = 118
#     #
#     #     self.prepareGeometryChange()
#     #
#     #     if self.mp_Handle == self.HandleTL:
#     #
#     #         fromX = self.mp_Bound.left()
#     #         fromY = self.mp_Bound.top()
#     #         toX = fromX + mousePos.x() - self.mp_Pos.x()
#     #         toY = fromY + mousePos.y() - self.mp_Pos.y()
#     #         toX = snapF(toX, size, -4, snap)
#     #         toY = snapF(toY, size, -4, snap)
#     #         D.setX(toX - fromX)
#     #         D.setY(toY - fromY)
#     #         R.setLeft(toX)
#     #         R.setTop(toY)
#     #
#     #         ## CLAMP SIZE
#     #         if R.width() < mbrw:
#     #             D.setX(D.x() - mbrw + R.width())
#     #             R.setLeft(R.left() - mbrw + R.width())
#     #         if R.height() < mbrh:
#     #             D.setY(D.y() - mbrh + R.height())
#     #             R.setTop(R.top() - mbrh + R.height())
#     #
#     #         background.setLeft(R.left())
#     #         background.setTop(R.top())
#     #         selection.setLeft(R.left())
#     #         selection.setTop(R.top())
#     #         polygon.setLeft(R.left() + 4)
#     #         polygon.setTop(R.top() + 4)
#     #
#     #     elif self.mp_Handle == self.HandleTM:
#     #
#     #         fromY = self.mp_Bound.top()
#     #         toY = fromY + mousePos.y() - self.mp_Pos.y()
#     #         toY = snapF(toY, size, -4, snap)
#     #         D.setY(toY - fromY)
#     #         R.setTop(toY)
#     #
#     #         ## CLAMP SIZE
#     #         if R.height() < mbrh:
#     #             D.setY(D.y() - mbrh + R.height())
#     #             R.setTop(R.top() - mbrh + R.height())
#     #
#     #         background.setTop(R.top())
#     #         selection.setTop(R.top())
#     #         polygon.setTop(R.top() + 4)
#     #
#     #     elif self.mp_Handle == self.HandleTR:
#     #
#     #         fromX = self.mp_Bound.right()
#     #         fromY = self.mp_Bound.top()
#     #         toX = fromX + mousePos.x() - self.mp_Pos.x()
#     #         toY = fromY + mousePos.y() - self.mp_Pos.y()
#     #         toX = snapF(toX, size, +4, snap)
#     #         toY = snapF(toY, size, -4, snap)
#     #         D.setX(toX - fromX)
#     #         D.setY(toY - fromY)
#     #         R.setRight(toX)
#     #         R.setTop(toY)
#     #
#     #         ## CLAMP SIZE
#     #         if R.width() < mbrw:
#     #             D.setX(D.x() + mbrw - R.width())
#     #             R.setRight(R.right() + mbrw - R.width())
#     #         if R.height() < mbrh:
#     #             D.setY(D.y() - mbrh + R.height())
#     #             R.setTop(R.top() - mbrh + R.height())
#     #
#     #         background.setRight(R.right())
#     #         background.setTop(R.top())
#     #         selection.setRight(R.right())
#     #         selection.setTop(R.top())
#     #         polygon.setRight(R.right() - 4)
#     #         polygon.setTop(R.top() + 4)
#     #
#     #     elif self.mp_Handle == self.HandleML:
#     #
#     #         fromX = self.mp_Bound.left()
#     #         toX = fromX + mousePos.x() - self.mp_Pos.x()
#     #         toX = snapF(toX, size, -4, snap)
#     #         D.setX(toX - fromX)
#     #         R.setLeft(toX)
#     #
#     #         ## CLAMP SIZE
#     #         if R.width() < mbrw:
#     #             D.setX(D.x() - mbrw + R.width())
#     #             R.setLeft(R.left() - mbrw + R.width())
#     #
#     #         background.setLeft(R.left())
#     #         selection.setLeft(R.left())
#     #         polygon.setLeft(R.left() + 4)
#     #
#     #     elif self.mp_Handle == self.HandleMR:
#     #
#     #         fromX = self.mp_Bound.right()
#     #         toX = fromX + mousePos.x() - self.mp_Pos.x()
#     #         toX = snapF(toX, size, +4, snap)
#     #         D.setX(toX - fromX)
#     #         R.setRight(toX)
#     #
#     #         ## CLAMP SIZE
#     #         if R.width() < mbrw:
#     #             D.setX(D.x() + mbrw - R.width())
#     #             R.setRight(R.right() + mbrw - R.width())
#     #
#     #         background.setRight(R.right())
#     #         selection.setRight(R.right())
#     #         polygon.setRight(R.right() - 4)
#     #
#     #     elif self.mp_Handle == self.HandleBL:
#     #
#     #         fromX = self.mp_Bound.left()
#     #         fromY = self.mp_Bound.bottom()
#     #         toX = fromX + mousePos.x() - self.mp_Pos.x()
#     #         toY = fromY + mousePos.y() - self.mp_Pos.y()
#     #         toX = snapF(toX, size, -4, snap)
#     #         toY = snapF(toY, size, +4, snap)
#     #         D.setX(toX - fromX)
#     #         D.setY(toY - fromY)
#     #         R.setLeft(toX)
#     #         R.setBottom(toY)
#     #
#     #         ## CLAMP SIZE
#     #         if R.width() < mbrw:
#     #             D.setX(D.x() - mbrw + R.width())
#     #             R.setLeft(R.left() - mbrw + R.width())
#     #         if R.height() < mbrh:
#     #             D.setY(D.y() + mbrh - R.height())
#     #             R.setBottom(R.bottom() + mbrh - R.height())
#     #
#     #         background.setLeft(R.left())
#     #         background.setBottom(R.bottom())
#     #         selection.setLeft(R.left())
#     #         selection.setBottom(R.bottom())
#     #         polygon.setLeft(R.left() + 4)
#     #         polygon.setBottom(R.bottom() - 4)
#     #
#     #     elif self.mp_Handle == self.HandleBM:
#     #
#     #         fromY = self.mp_Bound.bottom()
#     #         toY = fromY + mousePos.y() - self.mp_Pos.y()
#     #         toY = snapF(toY, size, +4, snap)
#     #         D.setY(toY - fromY)
#     #         R.setBottom(toY)
#     #
#     #         ## CLAMP SIZE
#     #         if R.height() < mbrh:
#     #             D.setY(D.y() + mbrh - R.height())
#     #             R.setBottom(R.bottom() + mbrh - R.height())
#     #
#     #         background.setBottom(R.bottom())
#     #         selection.setBottom(R.bottom())
#     #         polygon.setBottom(R.bottom() - 4)
#     #
#     #     elif self.mp_Handle == self.HandleBR:
#     #
#     #         fromX = self.mp_Bound.right()
#     #         fromY = self.mp_Bound.bottom()
#     #         toX = fromX + mousePos.x() - self.mp_Pos.x()
#     #         toY = fromY + mousePos.y() - self.mp_Pos.y()
#     #         toX = snapF(toX, size, +4, snap)
#     #         toY = snapF(toY, size, +4, snap)
#     #         D.setX(toX - fromX)
#     #         D.setY(toY - fromY)
#     #         R.setRight(toX)
#     #         R.setBottom(toY)
#     #
#     #         ## CLAMP SIZE
#     #         if R.width() < mbrw:
#     #             D.setX(D.x() + mbrw - R.width())
#     #             R.setRight(R.right() + mbrw - R.width())
#     #         if R.height() < mbrh:
#     #             D.setY(D.y() + mbrh - R.height())
#     #             R.setBottom(R.bottom() + mbrh - R.height())
#     #
#     #         background.setRight(R.right())
#     #         background.setBottom(R.bottom())
#     #         selection.setRight(R.right())
#     #         selection.setBottom(R.bottom())
#     #         polygon.setRight(R.right() - 4)
#     #         polygon.setBottom(R.bottom() - 4)
#     #
#     #     self.background.setGeometry(background)
#     #     self.selection.setGeometry(selection)
#     #     self.polygon.setGeometry(polygon)
#     #
#     #     self.updateNode(selected=True, handle=self.mp_Handle, anchors=(self.mp_Data, D))
#     #     self.updateTextPos(moved=moved)
#
#
#     def setIdentity(self, identity):
#         """
#         Set the identity of the current node.
#         :type identity: Identity
#         """
#         pass
#
#
#     def setText(self, text):
#         """
#         Set the label text.
#         :type text: str
#         """
#         self.header.setText(text)
#         self.header.setAlignment(QtCore.Qt.AlignCenter)
#
#
#     def setTextPos(self, pos):
#         """
#         Set the label position.
#         :type pos: QPointF
#         """
#         self.header.setPos(pos)
#
#
#     def shape(self):
#         """
#         Returns the shape of this item as a QPainterPath in local coordinates.
#         :rtype: QPainterPath
#         """
#         path = QtGui.QPainterPath()
#         path.addRect(self.polygon.geometry())
#         # for polygon in self.handles:
#         #     path.addEllipse(polygon.geometry())
#         return path
#
#
#     def special(self):
#         """
#         Returns the special type of this node.
#         :rtype: Special
#         """
#         return Special.valueOf(self.header.text())
#
#
#     def text(self):
#         """
#         Returns the label text.
#         :rtype: str
#         """
#         return self.header.text()
#
#
#     def textPos(self):
#         """
#         Returns the current label position in item coordinates.
#         :rtype: QPointF
#         """
#         return self.header.label.pos()
#
#
#     def updateTextPos(self, *args, **kwargs):
#         """
#         Update the label position.
#         """
#         self.header.label.updatePos(*args, **kwargs)
#
#
#     def width(self):
#         """
#         Returns the width of the shape.
#         :rtype: int
#         """
#         return self.polygon.geometry().width()
#
#
#     def __repr__(self):
#         """
#         Returns repr(self).
#         """
#         return '{0}:{1}:{2}'.format(self.__class__.__name__, self.text(), self.id)
#
# #############################################
# #                                           #
# #                 ROWS                      #
# #                                           #
# #############################################
# class BlackBirdTableRow:
#     """
#     This class implements represents a row in a relational table.
#     """
#
#     def __init__(self, name="AttributeName", type="VARCHAR(255)", nullable=False, primaryKey=False, indexed=False,
#                  foreignKey=False):
#         self.name = name
#         self.type = type
#         self.nullable = nullable
#         self.primaryKey = primaryKey
#         self.indexed = indexed
#         self.foreignKey = foreignKey
#
#     @property
#     def name(self):
#         return self.name
#
#     @name.setter
#     def name(self, name):
#         self.name = name
#
#     @property
#     def type(self):
#         return self.type
#
#     @property
#     def nullable(self):
#         return self.nullable
#
#     @property
#     def primaryKey(self):
#         return self.primaryKey
#
#     @property
#     def indexed(self):
#         return self.indexed
#
#     @property
#     def foreignKey(self):
#         return self.foreignKey
#
# # #############################################
# # #                                           #
# # #                EDGES                      #
# # #                                           #
# # #############################################
# # class BlackBirdForeignKeyEdge(AbstractEdge):
# #     """
# #     This class implements the 'Inclusion' edge.
# #     """
# #     Type = BlackBirdItem.ForeignKeyEdge
# #
# #     def __init__(self, **kwargs):
# #         """
# #         Initialize the edge.
# #         """
# #         super().__init__(**kwargs)
# #
# #     #############################################
# #     #   INTERFACE
# #     #################################
# #
#     def boundingRect(self):
#         """
#         Returns the shape bounding rect.
#         :rtype: QRectF
#         """
#         path = QtGui.QPainterPath()
#         path.addPath(self.selection.geometry())
#         path.addPolygon(self.head.geometry())
#         if hasattr(self, "handles"):
#             for polygon in self.handles:
#                 path.addEllipse(polygon.geometry())
#         for polygon in self.anchors.values():
#             path.addEllipse(polygon.geometry())
#         return path.controlPointRect()
# #
# #     def copy(self, diagram):
# #         """
# #         Create a copy of the current item.
# #         :type diagram: BlackBirdDiagram
# #         """
# #         return diagram.factory.create(self.type(), **{
# #             'id': self.id,
# #             'source': self.source,
# #             'target': self.target,
# #             'breakpoints': self.breakpoints[:],
# #         })
# #
# #     @staticmethod
# #     def createHead(p1, angle, size):
# #         """
# #         Create the head polygon.
# #         :type p1: QPointF
# #         :type angle: float
# #         :type size: int
# #         :rtype: QPolygonF
# #         """
# #         rad = radians(angle)
# #         p2 = p1 - QtCore.QPointF(sin(rad + M_PI / 3.0) * size, cos(rad + M_PI / 3.0) * size)
# #         p3 = p1 - QtCore.QPointF(sin(rad + M_PI - M_PI / 3.0) * size, cos(rad + M_PI - M_PI / 3.0) * size)
# #         return QtGui.QPolygonF([p1, p2, p3])
# #
#     def paint(self, painter, option, widget=None):
#         """
#         Paint the edge in the diagram scene.
#         :type painter: QPainter
#         :type option: QStyleOptionGraphicsItem
#         :type widget: QWidget
#         """
#         # SET THE RECT THAT NEEDS TO BE REPAINTED
#         painter.setClipRect(option.exposedRect)
#         # SELECTION AREA
#         painter.setRenderHint(QtGui.QPainter.Antialiasing)
#         painter.fillPath(self.selection.geometry(), self.selection.brush())
#         # EDGE LINE
#         painter.setPen(self.path.pen())
#         painter.drawPath(self.path.geometry())
#         # HEAD POLYGON
#         painter.setPen(self.head.pen())
#         painter.setBrush(self.head.brush())
#         painter.drawPolygon(self.head.geometry())
#         # BREAKPOINTS
#         if hasattr(self, "handles"):
#             for polygon in self.handles:
#                 painter.setPen(polygon.pen())
#                 painter.setBrush(polygon.brush())
#                 painter.drawEllipse(polygon.geometry())
#         # ANCHOR POINTS
#         for polygon in self.anchors.values():
#             painter.setPen(polygon.pen())
#             painter.setBrush(polygon.brush())
#             painter.drawEllipse(polygon.geometry())
# #
# #     def painterPath(self):
# #         """
# #         Returns the current shape as QtGui.QPainterPath (used for collision detection).
# #         :rtype: QPainterPath
# #         """
# #         path = QtGui.QPainterPath()
# #         path.addPath(self.path.geometry())
# #         path.addPolygon(self.head.geometry())
# #         return path
# #
# #     def setText(self, text):
# #         """
# #         Set the label text.
# #         :type text: str
# #         """
# #         pass
# #
# #     def setTextPos(self, pos):
# #         """
# #         Set the label position.
# #         :type pos: QPointF
# #         """
# #         pass
# #
# #     def shape(self):
# #         """
# #         Returns the shape of this item as a QPainterPath in local coordinates.
# #         :rtype: QPainterPath
# #         """
# #         path = QtGui.QPainterPath()
# #         path.addPath(self.selection.geometry())
# #         path.addPolygon(self.head.geometry())
# #         if self.isSelected():
# #             if hasattr(self, "handles"):
# #                 for polygon in self.handles:
# #                     path.addEllipse(polygon.geometry())
# #             for polygon in self.anchors.values():
# #                 path.addEllipse(polygon.geometry())
# #         return path
# #
# #     def text(self):
# #         """
# #         Returns the label text.
# #         :rtype: str
# #         """
# #         pass
# #
# #     def textPos(self):
# #         """
# #         Returns the current label position.
# #         :rtype: QPointF
# #         """
# #         pass
# #
# #     def updateEdge(self, selected=None, visible=None, breakpoint=None, anchor=None, target=None, **kwargs):
# #         """
# #         Update the current edge.
# #         :type selected: bool
# #         :type visible: bool
# #         :type breakpoint: int
# #         :type anchor: AbstractNode
# #         :type target: QtCore.QPointF
# #         """
# #         if visible is None:
# #             visible = self.canDraw()
# #
# #         sourceNode = self.source
# #         targetNode = self.target
# #         sourcePos = sourceNode.anchor(self)
# #         targetPos = target
# #         if targetPos is None:
# #             targetPos = targetNode.anchor(self)
# #
# #         self.prepareGeometryChange()
# #
# #         ##########################################
# #         # PATH, SELECTION, HEAD, TAIL (GEOMETRY)
# #         #################################
# #
# #         collection = self.createPath(sourceNode, targetNode, [sourcePos] + self.breakpoints + [targetPos])
# #
# #         selection = QtGui.QPainterPath()
# #         path = QtGui.QPainterPath()
# #         head = QtGui.QPolygonF()
# #
# #         if len(collection) == 1:
# #             subpath = collection[0]
# #             p1 = sourceNode.intersection(subpath)
# #             p2 = targetNode.intersection(subpath) if targetNode else subpath.p2()
# #             if p1 is not None and p2 is not None:
# #                 path.moveTo(p1)
# #                 path.lineTo(p2)
# #                 selection.addPolygon(createArea(p1, p2, subpath.angle(), 8))
# #                 head = self.createHead(p2, subpath.angle(), 12)
# #         elif len(collection) > 1:
# #             subpath1 = collection[0]
# #             subpathN = collection[-1]
# #             p11 = sourceNode.intersection(subpath1)
# #             p22 = targetNode.intersection(subpathN)
# #             if p11 and p22:
# #                 p12 = subpath1.p2()
# #                 p21 = subpathN.p1()
# #                 path.moveTo(p11)
# #                 path.lineTo(p12)
# #                 selection.addPolygon(createArea(p11, p12, subpath1.angle(), 8))
# #                 for subpath in collection[1:-1]:
# #                     p1 = subpath.p1()
# #                     p2 = subpath.p2()
# #                     path.moveTo(p1)
# #                     path.lineTo(p2)
# #                     selection.addPolygon(createArea(p1, p2, subpath.angle(), 8))
# #                 path.moveTo(p21)
# #                 path.lineTo(p22)
# #                 selection.addPolygon(createArea(p21, p22, subpathN.angle(), 8))
# #                 head = self.createHead(p22, subpathN.angle(), 12)
# #
# #         self.selection.setGeometry(selection)
# #         self.path.setGeometry(path)
# #         self.head.setGeometry(head)
# #
# #         ##########################################
# #         # PATH, HEAD, TAIL (BRUSH)
# #         #################################
# #
# #         headBrush = QtGui.QBrush(QtCore.Qt.NoBrush)
# #         headPen = QtGui.QPen(QtCore.Qt.NoPen)
# #         pathPen = QtGui.QPen(QtCore.Qt.NoPen)
# #
# #         if visible:
# #             headBrush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 255))
# #             headPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
# #             pathPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
# #
# #         self.head.setBrush(headBrush)
# #         self.head.setPen(headPen)
# #         self.path.setPen(pathPen)
# #
# #         super().updateEdge(selected, visible, breakpoint, anchor, **kwargs)
