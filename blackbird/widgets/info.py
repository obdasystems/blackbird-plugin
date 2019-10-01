# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Blackbird: An ontology to relational schema translator                #
#  Copyright (C) 2019 OBDA Systems                                       #
#                                                                        #
#  ####################################################################  #
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
##########################################################################


from abc import ABCMeta, abstractmethod

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets
)

from eddy.core.datatypes.qt import Font
from eddy.core.functions.misc import clamp, first
from eddy.core.functions.signals import connect, disconnect
from eddy.core.output import getLogger
from eddy.ui.fields import IntegerField, StringField, ComboBox

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.diagram import BlackBirdDiagram
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.items.edges import ForeignKeyEdge
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.items.nodes import TableNode
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import ForeignKeyConstraint
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalSchema
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalTable
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.ui.mdi import BlackBirdMdiSubWindow

LOGGER = getLogger()


class BBInfoWidget(QtWidgets.QScrollArea):
    """
    This class implements the information box widget.
    """

    def __init__(self, plugin):
        """
        Initialize the info box.
        :type plugin: Info
        """
        super().__init__(plugin.session)

        self.diagram = None
        self.plugin = plugin

        self.stacked = QtWidgets.QStackedWidget(self)
        self.stacked.setContentsMargins(0, 0, 0, 0)
        self.infoEmpty = QtWidgets.QWidget(self.stacked)

        # self.schemaInfo = SchemaInfo(self)
        self.schemaInfo = SchemaInfo(plugin.session, self.stacked)
        connect(plugin.sgnSchemaChanged, self.onSchemaChanged)
        connect(plugin.sgnFocusTable, self.doSelectTable)
        connect(plugin.sgnFocusForeignKey, self.doSelectForeignKey)

        # self.tableInfo = TableInfo(plugin.session,self.stacked)
        self.tableInfo = SimpleTableInfo(plugin.session, self.stacked)

        self.fkInfo = ForeignKeyInfo(plugin.session, self.stacked)

        self.stacked.addWidget(self.schemaInfo)
        self.stacked.addWidget(self.tableInfo)
        self.stacked.addWidget(self.fkInfo)

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(QtCore.QSize(216, 112))
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setWidget(self.stacked)
        self.setWidgetResizable(True)

        self.setStyleSheet("""
        BBInfoWidget {
          background: #FFFFFF;
        }
        BBInfoWidget BBHeader {
          background: #5A5050;
          padding-left: 4px;
          color: #FFFFFF;
        }
        BBInfoWidget BBKey {
          background: #BBDEFB;
          border-top: none;
          border-right: none;
          border-bottom: 1px solid #BBDEFB;
          border-left: none;
          padding: 0 0 0 4px;
        }
        BBInfoWidget BBButton,
        BBInfoWidget BBButton:focus,
        BBInfoWidget BBButton:hover,
        BBInfoWidget BBButton:hover:focus,
        BBInfoWidget BBButton:pressed,
        BBInfoWidget BBButton:pressed:focus,
        BBInfoWidget BBInteger,
        BBInfoWidget BBString,
        BBInfoWidget BBSelect,
        BBInfoWidget BBParent {
          background: #E3F2FD;
          border-top: none;
          border-right: none;
          border-bottom: 1px solid #BBDEFB !important;
          border-left: 1px solid #BBDEFB !important;
          padding: 0 0 0 4px;
          text-align:left;
        }
        BBInfoWidget BBButton::menu-indicator {
          image: none;
        }
        BBInfoWidget BBSelect:!editable,
        BBInfoWidget BBSelect::drop-down:editable {
          background: #FFFFFF;
        }
        BBInfoWidget BBSelect:!editable:on,
        BBInfoWidget BBSelect::drop-down:editable:on {
          background: #FFFFFF;
        }
        BBInfoWidget QCheckBox {
          background: #FFFFFF;
          spacing: 0;
          margin-left: 4px;
          margin-top: 2px;
        }
        BBInfoWidget QCheckBox::indicator:disabled {
          background-color: #BABABA;
        }
        """)

        scrollbar = self.verticalScrollBar()
        scrollbar.installEventFilter(self)

        connect(self.plugin.session.mdi.subWindowActivated, self.onSubWindowActivated)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def schema(self):
        return self.plugin.schema

    @property
    def project(self):
        """
        Returns the reference to the active project.
        :rtype: Session
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the reference to the active session.
        :rtype: Session
        """
        return self.plugin.parent()

    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source, event):
        """
        Filter incoming events.
        :type source: QObject
        :type event: QtCore.QEvent
        """
        if source is self.verticalScrollBar():
            if event.type() in {QtCore.QEvent.Show, QtCore.QEvent.Hide}:
                self.redraw()
        return super().eventFilter(source, event)

    def resizeEvent(self, a0: QtGui.QResizeEvent):
        self.redraw()
        super().resizeEvent(a0)

    #############################################
    #   INTERFACE
    #################################

    def redraw(self):
        """
        Redraw the content of the widget.
        """
        width = self.width()
        scrollbar = self.verticalScrollBar()
        if scrollbar.isVisible():
            width -= scrollbar.width()
        widget = self.stacked.currentWidget()
        if widget:
            widget.setFixedWidth(width)
            sizeHint = widget.sizeHint()
            height = sizeHint.height()
            self.stacked.setFixedWidth(width)
            self.stacked.setFixedHeight(clamp(height, 0))

    def setDiagram(self, diagram):
        """
        Sets the widget to inspect the given diagram.
        :type diagram: diagram
        """
        self.diagram = diagram

    def stack(self, infoItem):
        """
        Set the current stacked widget.
        """
        if infoItem:
            if isinstance(infoItem, RelationalSchema):
                show = self.schemaInfo
            elif isinstance(infoItem, RelationalTable):
                show = self.tableInfo
            elif isinstance(infoItem, ForeignKeyConstraint):
                show = self.fkInfo
            elif isinstance(infoItem, BlackBirdDiagram):
                show = None  # TODO RIPARTI DA QUI
                selected = infoItem.selectedItems()
                if not selected or len(selected) > 1:
                    show = self.schemaInfo
                    show.updateData(len(infoItem.schema.tables), len(infoItem.schema.foreignKeys))
                else:
                    diagramItem = first(selected)
                    # if diagramItem.type() is Item.TableNode:
                    if isinstance(diagramItem, TableNode):
                        show = self.tableInfo
                        show.updateData(diagramItem.relationalTable)
                    # elif diagramItem.type() is Item.ForeignkeyEdge:
                    elif isinstance(diagramItem, ForeignKeyEdge):
                        show = self.fkInfo
                        show.updateData(diagramItem.foreignKey)
        else:
            show = self.infoEmpty
        prev = self.stacked.currentWidget()
        self.stacked.setCurrentWidget(show)
        self.redraw()
        if prev is not show:
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(0)

    @QtCore.pyqtSlot(QtWidgets.QMdiSubWindow)
    def onSubWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :type subwindow: MdiSubWindow
        """
        if subwindow and isinstance(subwindow, BlackBirdMdiSubWindow):
            if self.diagram:
                # If the info widget is currently inspecting a
                # diagram, detach signals from the subwindow which
                # is going out of focus, before connecting new ones.
                LOGGER.debug('Disconnecting from diagram: %s', self.diagram.name)
                disconnect(self.diagram.selectionChanged, self.onDiagramSelectionChanged)
                # disconnect(self.diagram.sgnUpdated, self.onDiagramUpdated)
            # Attach the new view/diagram to the info widget.
            LOGGER.debug('Connecting to diagram: %s', subwindow.diagram.name)
            connect(subwindow.diagram.selectionChanged, self.onDiagramSelectionChanged)
            # connect(subwindow.diagram.sgnUpdated, self.onDiagramUpdated)
            self.setDiagram(subwindow.diagram)
            self.stack(self.diagram)
        else:
            if not self.session.mdi.subWindowList():
                # If we don't have any active subwindow (which means that
                # they have been all closed and not just out of focus) we
                # detach the widget from the last inspected diagram.
                if self.diagram:
                    LOGGER.debug('Disconnecting from diagram: %s', self.diagram.name)
                    disconnect(self.diagram.selectionChanged, self.onDiagramSelectionChanged)
                    # disconnect(self.diagram.sgnUpdated, self.onDiagramUpdated)
                self.setDiagram(None)
                # self.stack(None)

    @QtCore.pyqtSlot()
    def onDiagramSelectionChanged(self):
        """
        Executed whenever the selection of the active diagram changes.
        """
        self.stack(self.sender())

    @QtCore.pyqtSlot(RelationalSchema)
    def onSchemaChanged(self, schema):
        tables = schema.tables
        foreignKeys = schema.foreignKeys
        self.schemaInfo.updateData(len(tables), len(foreignKeys))
        self.stack(schema)

    @QtCore.pyqtSlot(RelationalTable)
    def doSelectTable(self, table):
        self.tableInfo.updateData(table)
        self.stack(table)

    @QtCore.pyqtSlot(ForeignKeyConstraint)
    def doSelectForeignKey(self, fk):
        self.fkInfo.updateData(fk)
        self.stack(fk)


#############################################
#   INFO WIDGETS
#################################

class BBAbstractInfo(QtWidgets.QWidget):
    """
    This class implements the base information box.
    """
    __metaclass__ = ABCMeta

    def __init__(self, session, parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.session = session
        self.setContentsMargins(0, 0, 0, 0)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the project loaded in the current session.
        :rtype: Project
        """
        return self.session.project

    #############################################
    #   INTERFACE
    #################################

    @abstractmethod
    def updateData(self, **kwargs):
        """
        Fetch new information and fill the widget with data.
        """
        pass


class SchemaInfo(BBAbstractInfo):
    def __init__(self, session, parent=None):
        super().__init__(session, parent)

        self.header = BBHeader('Schema Info')
        self.header.setFont(Font('Roboto', 12))

        self.tableCountKey = BBKey('Tables count')
        self.tableCountKey.setFont(Font('Roboto', 12))
        self.tableCountField = BBInteger(self)
        self.tableCountField.setFont(Font('Roboto', 12))
        self.tableCountField.setReadOnly(True)

        self.fkCountKey = BBKey('FKs count')
        self.fkCountKey.setFont(Font('Roboto', 12))
        self.fkCountField = BBInteger(self)
        self.fkCountField.setFont(Font('Roboto', 12))
        self.fkCountField.setReadOnly(True)

        self.layout = QtWidgets.QFormLayout()
        self.layout.setSpacing(0)
        self.layout.addRow(self.tableCountKey, self.tableCountField)
        self.layout.addRow(self.fkCountKey, self.fkCountField)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.header)
        self.mainLayout.addLayout(self.layout)

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, tableCount, fkCount):
        """
        Fetch new information and fill the widget with data.
        :type tableCount: int
        :type fkCount: int
        """
        self.tableCountField.setValue(str(tableCount))
        self.fkCountField.setValue(str(fkCount))


class SimpleTableInfo(BBAbstractInfo):
    def __init__(self, session, parent=None):
        super().__init__(session, parent)

        self.header = BBHeader('')
        self.header.setFont(Font('Roboto', 12))

        self.tableWidget = QtWidgets.QTableWidget(self)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)
        # self.tableWidget.resizeColumnsToContents()

        #prova
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.header)
        self.mainLayout.addWidget(self.tableWidget)

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, table):
        """
        Fetch new information and fill the widget with data.
        :type tableCount: RelationalTable
        """
        self.table = table
        self.tableName = table.name
        self.columns = table.columns
        self.primaryKey = table.primaryKey

        pkColNames = self.primaryKey.columns

        self.header.setText('TABLE: ' + self.tableName)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(len(self.columns))

        rowIndex = 0
        notPkCols = []

        for column in self.columns:
            if column.columnName in pkColNames:
                nameStr = column.columnName
                typeStr = column.columnType
                self.tableWidget.setItem(rowIndex, 0, QtWidgets.QTableWidgetItem(nameStr))
                self.tableWidget.setItem(rowIndex, 1, QtWidgets.QTableWidgetItem(typeStr))
                rowIndex += 1
            else:
                notPkCols.append(column)

        for notPkCol in notPkCols:
            nameStr = notPkCol.columnName
            typeStr = notPkCol.columnType
            self.tableWidget.setItem(rowIndex, 0, QtWidgets.QTableWidgetItem(nameStr))
            self.tableWidget.setItem(rowIndex, 1, QtWidgets.QTableWidgetItem(typeStr))
            rowIndex += 1

        # align text
        for row in range(self.tableWidget.rowCount()):
            nameItem = self.tableWidget.item(row, 0)
            nameItem.setTextAlignment(QtCore.Qt.AlignLeft)
            nameItem.setTextAlignment(QtCore.Qt.AlignVCenter)
            typeItem = self.tableWidget.item(row, 1)
            typeItem.setTextAlignment(QtCore.Qt.AlignRight)
            typeItem.setTextAlignment(QtCore.Qt.AlignVCenter)
            if row < len(pkColNames):
                nameItem.setForeground(QtGui.QBrush(QtCore.Qt.red))
            else:
                nameItem.setForeground(QtGui.QBrush(QtCore.Qt.black))
            typeItem.setForeground(QtGui.QBrush(QtCore.Qt.black))

            # nameItem.setBackground(QtGui.QBrush(QtCore.Qt.black))
            # typeItem.setBackground(QtGui.QBrush(QtCore.Qt.black))

            nameItem.setBackground(QtGui.QBrush(QtGui.QColor('#BBDEFB')))
            typeItem.setBackground(QtGui.QBrush(QtGui.QColor('#E3F2FD')))

            nameItem.setFlags(QtCore.Qt.ItemIsEnabled)
            typeItem.setFlags(QtCore.Qt.ItemIsEnabled)

        # Remove headers
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)
        self.tableWidget.setShowGrid(False)

        # Do the resize of the columns by content
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)


class TableInfo(BBAbstractInfo):
    def __init__(self, session, parent=None):
        super().__init__(session, parent)

        self.header = BBHeader('')
        self.header.setFont(Font('Roboto', 12))

        self.tableWidget = QtWidgets.QTableWidget(self)
        self.tableWidget.setColumnCount(6)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)
        self.tableWidget.resizeColumnsToContents()

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.header)
        self.mainLayout.addWidget(self.tableWidget)

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, table):
        """
        Fetch new information and fill the widget with data.
        :type tableCount: RelationalTable
        """
        self.table = table
        self.tableName = table.name
        self.columns = table.columns
        self.primaryKey = table.primaryKey
        self.uniques = table.uniques
        self.foreignKeys = table.foreignKeys
        self.actions = table.actions

        pkColNames = self.primaryKey.columns

        fkIndexToRowIndexes = {}
        iSrc = 0
        for fk in self.foreignKeys:
            if fk.srcTable == self.tableName:
                fkColumnNames = fk.srcColumns
                fkRowIndexes = []
                for column in self.columns:
                    if column.columnName in fkColumnNames:
                        fkRowIndexes.append(self.columns.index(column))
                fkIndexToRowIndexes[iSrc] = fkRowIndexes
                iSrc += 1

        uniqueIndexToRowIndexes = {}
        iSrc = 0
        for unq in self.uniques:
            uniqueNames = unq.columns
            uniqueRowIndexes = []
            for column in self.columns:
                if column.columnName in uniqueNames:
                    uniqueRowIndexes.append(self.columns.index(column))
            uniqueIndexToRowIndexes[iSrc] = uniqueRowIndexes
            iSrc += 1

        self.header.setText(self.tableName)
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setRowCount(len(self.columns))

        for column in self.columns:
            rowIndex = self.columns.index(column)
            nameStr = column.columnName
            typeStr = column.columnType

            nullable = column.isNullable
            nullStr = " NULLABLE "
            if not nullable:
                nullStr = " NOT NULL "

            pkStr = " - "
            if nameStr in pkColNames:
                pkStr = " PK "

            fkStr = " - "
            fks = []
            for k, v in fkIndexToRowIndexes.items():
                if rowIndex in v:
                    fks.append(k)
            if len(fks) > 0:
                fkIndexes = ",".join(map(str, fks))
                fkStr = "FK {}".format(fkIndexes)

            uqStr = " - "
            uqs = []
            for k, v in uniqueIndexToRowIndexes.items():
                if rowIndex in v:
                    uqs.append(k)
            if len(uqs) > 0:
                uqsIndexes = ",".join(map(str, uqs))
                uqStr = "UQ {}".format(uqsIndexes)

            self.tableWidget.setItem(rowIndex, 0, QtWidgets.QTableWidgetItem(pkStr))
            self.tableWidget.setItem(rowIndex, 1, QtWidgets.QTableWidgetItem(fkStr))
            self.tableWidget.setItem(rowIndex, 2, QtWidgets.QTableWidgetItem(uqStr))
            self.tableWidget.setItem(rowIndex, 3, QtWidgets.QTableWidgetItem(nameStr))
            self.tableWidget.setItem(rowIndex, 4, QtWidgets.QTableWidgetItem(typeStr))
            self.tableWidget.setItem(rowIndex, 5, QtWidgets.QTableWidgetItem(nullStr))

        # Remove headers
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)

        # Do the resize of the columns by content
        self.tableWidget.resizeColumnsToContents()


class ForeignKeyInfo(BBAbstractInfo):
    def __init__(self, session, parent=None):
        super().__init__(session, parent)

        self.header = BBHeader('')
        self.header.setFont(Font('Roboto', 12))

        # self.fkNameKey = BBKey('FK Name')
        # self.fkNameKey.setFont(Font('Roboto', 12))
        # self.fkNameField = BBString(self)
        # self.fkNameField.setFont(Font('Roboto', 12))
        # self.fkNameField.setReadOnly(True)

        self.srcTableKey = BBKey('SRC Table')
        self.srcTableKey.setFont(Font('Roboto', 12))
        self.srcTableField = BBString(self)
        self.srcTableField.setFont(Font('Roboto', 12))
        self.srcTableField.setReadOnly(True)

        self.srcColumnsKey = BBKey('SRC Columns')
        self.srcColumnsKey.setFont(Font('Roboto', 12))
        self.srcColumnsField = BBString(self)
        self.srcColumnsField.setFont(Font('Roboto', 12))
        self.srcColumnsField.setReadOnly(True)

        self.tgtTableKey = BBKey('TGT Table')
        self.tgtTableKey.setFont(Font('Roboto', 12))
        self.tgtTableField = BBString(self)
        self.tgtTableField.setFont(Font('Roboto', 12))
        self.tgtTableField.setReadOnly(True)

        self.tgtColumnsKey = BBKey('TGT Columns')
        self.tgtColumnsKey.setFont(Font('Roboto', 12))
        self.tgtColumnsField = BBString(self)
        self.tgtColumnsField.setFont(Font('Roboto', 12))
        self.tgtColumnsField.setReadOnly(True)

        self.axiomKey = BBKey('Axiom Type')
        self.axiomKey.setFont(Font('Roboto', 12))
        self.axiomField = BBString(self)
        self.axiomField.setFont(Font('Roboto', 12))
        self.axiomField.setReadOnly(True)

        self.layout = QtWidgets.QFormLayout()
        self.layout.setSpacing(0)
        # self.layout.addRow(self.fkNameKey,self.fkNameField)
        self.layout.addRow(self.srcTableKey, self.srcTableField)
        self.layout.addRow(self.srcColumnsKey, self.srcColumnsField)
        self.layout.addRow(self.tgtTableKey, self.tgtTableField)
        self.layout.addRow(self.tgtColumnsKey, self.tgtColumnsField)
        self.layout.addRow(self.axiomKey, self.axiomField)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.header)
        self.mainLayout.addLayout(self.layout)

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, fk):
        """
        Fetch new information and fill the widget with data.
        :type tableCount: ForeignKeyConstraint
        """
        self.header.setText(fk.name)
        # self.fkNameField.setValue(fk.name)
        self.srcTableField.setValue(fk.srcTable)
        srcColumnsStr = ', '.join(map(str, fk.srcColumns))
        self.srcColumnsField.setValue(srcColumnsStr)
        self.tgtTableField.setValue(fk.tgtTable)
        tgtColumnsStr = ', '.join(map(str, fk.tgtColumns))
        self.tgtColumnsField.setValue(tgtColumnsStr)
        self.axiomField.setValue(fk.axiomType)


#############################################
#   COMPONENTS
#################################

class BBHeader(QtWidgets.QLabel):
    """
    This class implements the header of properties section.
    """

    def __init__(self, *args):
        """
        Initialize the header.
        """
        super().__init__(*args)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.setFixedHeight(24)


class BBKey(QtWidgets.QLabel):
    """
    This class implements the key of an info field.
    """

    def __init__(self, *args):
        """
        Initialize the key.
        """
        super().__init__(*args)
        self.setFixedSize(88, 20)


class BBButton(QtWidgets.QPushButton):
    """
    This class implements the button to which associate a QtWidgets.QMenu instance of an info field.
    """

    def __init__(self, *args):
        """
        Initialize the button.
        """
        super().__init__(*args)


class BBInteger(IntegerField):
    """
    This class implements the integer value of an info field.
    """

    def __init__(self, *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)


class BBString(StringField):
    """
    This class implements the string value of an info field.
    """

    def __init__(self, *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)


class BBSelect(ComboBox):
    """
    This class implements the selection box of an info field.
    """

    def __init__(self, *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setScrollEnabled(False)
