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


import io
import os

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets
)
from PyQt5.QtCore import QFile, QTextStream, QIODevice
from PyQt5.QtWidgets import QFileDialog

from eddy.core.common import HasWidgetSystem
from eddy.core.datatypes.qt import Font
from eddy.core.functions.fsystem import fwrite
from eddy.core.functions.misc import first
from eddy.core.functions.path import openPath
from eddy.core.functions.signals import connect


class BlackbirdLogDialog(QtWidgets.QDialog):
    """
    Extends QtWidgets.QDialog providing a view for the Blackbird translator log.
    """

    def __init__(self, stream=io.StringIO(), parent=None):
        """
        Initialize the dialog.
        :type parent: QWidget
        """
        super().__init__(parent)

        #############################################
        # MESSAGE AREA
        #################################

        self.messageArea = QtWidgets.QPlainTextEdit(self)
        self.messageArea.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.messageArea.setContentsMargins(10, 0, 0, 0)
        self.messageArea.setFont(Font('Roboto Mono', 11))
        self.messageArea.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.messageArea.setMinimumSize(800, 500)
        self.highlighter = LogHighlighter(self.messageArea.document())
        self.messageArea.setPlainText(stream.getvalue())
        self.messageArea.setReadOnly(True)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok, QtCore.Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 0, 0)
        self.confirmationBox.setFont(Font('Roboto', 12))

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.addWidget(self.messageArea)
        self.mainLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        connect(self.confirmationBox.accepted, self.accept)

        self.setWindowIcon(QtGui.QIcon(':/blackbird/icons/128/ic_blackbird'))
        self.setWindowTitle('Blackbird Log')


class LogHighlighter(QtGui.QSyntaxHighlighter):
    """
    Extends QtGui.QSyntaxHighlighter providing a syntax highlighter for log messages.
    """

    def __init__(self, document):
        """
        Initialize the syntax highlighter.
        :type document: QTextDocument
        """
        super().__init__(document)
        self.rules = [
            (QtCore.QRegExp(r'^(\[.+\])\s+DEBUG\s+(.*)$'), 0, self.fmt('#8000AA')),
            (QtCore.QRegExp(r'^(\[.+\])\s+ERROR\s+(.*)$'), 0, self.fmt('#FF0000')),
            (QtCore.QRegExp(r'^(\[.+\])\s+WARN\s+(.*)$'), 0, self.fmt('#FFAE00')),
        ]

    @staticmethod
    def fmt(color):
        """
        Return a QTextCharFormat with the given attributes.
        """
        _color = QtGui.QColor()
        _color.setNamedColor(color)
        _format = QtGui.QTextCharFormat()
        _format.setForeground(_color)
        return _format

    def highlightBlock(self, text):
        """
        Apply syntax highlighting to the given block of text.
        :type text: str
        """
        for exp, nth, fmt in self.rules:
            index = exp.indexIn(text, 0)
            while index >= 0:
                index = exp.pos(nth)
                length = len(exp.cap(nth))
                self.setFormat(index, length, fmt)
                index = exp.indexIn(text, index + length)


class BlackbirdOutputDialog(QtWidgets.QDialog):
    """
    Subclass of QtWidgets.QDialog that shows a side-by-side view
    of the input and output of the schema generation process.
    """

    def __init__(self, owl, schema, parsedSchema, parent=None, **kwargs):
        """
        Initialize the dialog.
        """
        super().__init__(parent, **kwargs)

        #############################################
        # TEXT AREA
        #################################

        owlLabel = QtWidgets.QLabel('OWL', self)
        schemaLabel = QtWidgets.QLabel('JSON', self)
        pythonLabel = QtWidgets.QLabel('Python', self)

        headerLayout = QtWidgets.QHBoxLayout(self)
        headerLayout.addWidget(owlLabel, 1, QtCore.Qt.AlignLeading)
        headerLayout.addWidget(schemaLabel, 1, QtCore.Qt.AlignLeading)
        headerLayout.addWidget(pythonLabel, 1, QtCore.Qt.AlignLeading)

        headerWidget = QtWidgets.QWidget(self)
        headerWidget.setLayout(headerLayout)

        owlText = QtWidgets.QTextEdit(self)
        owlText.setFont(Font('Roboto', 14))
        owlText.setObjectName('owl_text')
        owlText.setReadOnly(True)
        owlText.setText(owl)

        schemaText = QtWidgets.QTextEdit(self)
        schemaText.setFont(Font('Roboto', 14))
        schemaText.setObjectName('schema_text')
        schemaText.setReadOnly(True)
        schemaText.setText(schema)

        pythonText = QtWidgets.QTextEdit(self)
        pythonText.setFont(Font('Roboto', 14))
        pythonText.setObjectName('python_text')
        pythonText.setReadOnly(True)
        pythonText.setText(parsedSchema.__str__())

        innerLayout = QtWidgets.QHBoxLayout(self)
        innerLayout.setContentsMargins(8, 0, 8, 8)
        innerLayout.addWidget(owlText)
        innerLayout.addSpacing(8)
        innerLayout.addWidget(schemaText)
        innerLayout.addSpacing(8)
        innerLayout.addWidget(pythonText)

        textWidget = QtWidgets.QWidget(self)
        textWidget.setLayout(innerLayout)

        #############################################
        # CONFIRMATION AREA
        #################################

        exportBtn = QtWidgets.QPushButton('Export', self)
        confirmation = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close, self)
        buttonLayout = QtWidgets.QHBoxLayout(self)
        buttonLayout.setContentsMargins(10, 0, 10, 10)
        buttonLayout.addWidget(exportBtn)
        buttonLayout.addWidget(confirmation)

        buttonWidget = QtWidgets.QWidget(self)
        buttonWidget.setLayout(buttonLayout)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(headerWidget)
        mainLayout.addWidget(textWidget)
        mainLayout.addWidget(buttonWidget, 0, QtCore.Qt.AlignRight)

        self.setWindowTitle("Schema Generation Output")
        self.setModal(True)
        self.setLayout(mainLayout)
        self.setMinimumSize(1024, 480)

        connect(confirmation.clicked, self.accept)
        connect(exportBtn.clicked, self.doExport)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def doExport(self):
        """
        Export the generated OWL and schema.
        """
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        if dialog.exec_():
            directory = first(dialog.selectedFiles())
            owl = self.findChild(QtWidgets.QTextEdit, 'owl_text').toPlainText()
            fwrite(owl, os.path.join(directory, 'ontology.owl'))
            schema = self.findChild(QtWidgets.QTextEdit, 'schema_text').toPlainText()
            fwrite(schema, os.path.join(directory, 'schema.json'))
            python = self.findChild(QtWidgets.QTextEdit, 'python_text').toPlainText()
            fwrite(python, os.path.join(directory, 'parsedObject.txt'))
            openPath(directory)


class BlackbirdOntologyDialog(QtWidgets.QDialog):
    """
    Subclass of QtWidgets.QDialog that shows the owl ontology used to generate current schema.
    """

    def __init__(self, owl, parent=None, **kwargs):
        """
        Initialize the dialog.
        """
        super().__init__(parent, **kwargs)

        #############################################
        # TEXT AREA
        #################################

        owlLabel = QtWidgets.QLabel('OWL', self)

        headerLayout = QtWidgets.QHBoxLayout(self)
        headerLayout.addWidget(owlLabel, 1, QtCore.Qt.AlignLeading)

        headerWidget = QtWidgets.QWidget(self)
        headerWidget.setLayout(headerLayout)

        owlText = QtWidgets.QTextEdit(self)
        owlText.setFont(Font('Roboto', 14))
        owlText.setObjectName('owl_text')
        owlText.setReadOnly(True)
        owlText.setText(owl)

        innerLayout = QtWidgets.QHBoxLayout(self)
        innerLayout.setContentsMargins(8, 0, 8, 8)
        innerLayout.addWidget(owlText)

        textWidget = QtWidgets.QWidget(self)
        textWidget.setLayout(innerLayout)

        #############################################
        # CONFIRMATION AREA
        #################################

        exportBtn = QtWidgets.QPushButton('Export', self)
        confirmation = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close, self)
        buttonLayout = QtWidgets.QHBoxLayout(self)
        buttonLayout.setContentsMargins(10, 0, 10, 10)
        buttonLayout.addWidget(exportBtn)
        buttonLayout.addWidget(confirmation)

        buttonWidget = QtWidgets.QWidget(self)
        buttonWidget.setLayout(buttonLayout)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(headerWidget)
        mainLayout.addWidget(textWidget)
        mainLayout.addWidget(buttonWidget, 0, QtCore.Qt.AlignRight)

        self.setWindowTitle("Referenced Ontology")
        self.setModal(True)
        self.setLayout(mainLayout)
        self.setMinimumSize(1024, 480)

        connect(confirmation.clicked, self.accept)
        connect(exportBtn.clicked, self.doExport)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def doExport(self):
        """
        Export the generated OWL and schema.
        """
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        if dialog.exec_():
            directory = first(dialog.selectedFiles())
            owl = self.findChild(QtWidgets.QTextEdit, 'owl_text').toPlainText()
            fwrite(owl, os.path.join(directory, 'ontology.owl'))
            openPath(directory)



class TableInfoDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    This class implements the 'TableInfo' dialog.
    """

    # noinspection PyArgumentList
    def __init__(self, relationalTable, parent=None):
        """
        Initialize the TableInfo dialog.
        :type session: Session
        :type table: RelationalTable
        """
        super().__init__(parent)

        self.relationalTable = relationalTable

        columns = self.relationalTable.columns
        primaryKey = self.relationalTable.primaryKey
        uniques = self.relationalTable.uniques
        foreignKeys = self.relationalTable.foreignKeys
        assertions = self.relationalTable.assertions

        #############################################
        # COLUMNS TAB
        #################################

        table = QtWidgets.QTableWidget(len(self.relationalTable.columns), 6, self, objectName='columns_table')
        table.setHorizontalHeaderLabels(['Name', 'Data Type', 'Length', 'Precision', 'Not NULL?', 'Primary Key?'])
        table.setFont(Font('Roboto', 12))
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addWidget(table)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.Stretch)
        header.setSectionsClickable(False)
        header.setSectionsMovable(False)

        header = table.verticalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        for row, column in enumerate(columns):
            colName = column.columnName
            colType = column.columnType
            colNull = not column.isNullable
            if colName in primaryKey.columns:
                colPK = True
            else:
                colPK = False
            item = QtWidgets.QTableWidgetItem(colName)
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 0, item)
            item = QtWidgets.QTableWidgetItem(colType)
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 1, item)
            item = QtWidgets.QTableWidgetItem('-')
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 2, item)
            item = QtWidgets.QTableWidgetItem('-')
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 3, item)
            item = QtWidgets.QTableWidgetItem(str(colNull))
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 4, item)
            item = QtWidgets.QTableWidgetItem(str(colPK))
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 5, item)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.widget('columns_table'), 1)
        widget = QtWidgets.QWidget(objectName='columns_widget')
        widget.setLayout(layout)
        self.addWidget(widget)

        #############################################
        # PRIMARY KEY TAB
        #################################

        table = QtWidgets.QTableWidget(1, 2, self, objectName='pk_table')
        table.setHorizontalHeaderLabels(['Name', 'Columns'])
        table.setFont(Font('Roboto', 12))
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addWidget(table)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionsClickable(False)
        header.setSectionsMovable(False)
        header = table.verticalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        pkName = primaryKey.name
        item = QtWidgets.QTableWidgetItem(pkName)
        item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
        table.setItem(0, 0, item)
        pkColumnNames = primaryKey.columns
        item = QtWidgets.QTableWidgetItem(','.join(pkColumnNames))
        item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
        table.setItem(0, 1, item)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.widget('pk_table'), 1)
        widget = QtWidgets.QWidget(objectName='pk_widget')
        widget.setLayout(layout)
        self.addWidget(widget)

        #############################################
        # UNIQUE TAB
        #################################

        table = QtWidgets.QTableWidget(len(uniques), 2, self, objectName='uniques_table')
        table.setHorizontalHeaderLabels(['Name', 'Columns'])
        table.setFont(Font('Roboto', 12))
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addWidget(table)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionsClickable(False)
        header.setSectionsMovable(False)
        header = table.verticalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        for row, unique in enumerate(uniques):
            uniqueName = unique.name
            item = QtWidgets.QTableWidgetItem(uniqueName)
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 0, item)
            uniqueColumnNames = unique.columns
            item = QtWidgets.QTableWidgetItem(','.join(uniqueColumnNames))
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 1, item)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.widget('uniques_table'), 1)
        widget = QtWidgets.QWidget(objectName='uniques_widget')
        widget.setLayout(layout)
        self.addWidget(widget)

        #############################################
        # FOREIGN KEY TAB
        #################################

        table = QtWidgets.QTableWidget(len(foreignKeys), 3, self, objectName='fk_table')
        table.setHorizontalHeaderLabels(['Name', 'Referenced Table', 'Columns'])
        table.setFont(Font('Roboto', 12))
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addWidget(table)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Interactive)
        header.setSectionsClickable(False)
        header.setSectionsMovable(False)
        header = table.verticalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        for row, fk in enumerate(foreignKeys):
            fkName = fk.name
            item = QtWidgets.QTableWidgetItem(fkName)
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 0, item)
            tgtTableName = fk.tgtTable
            item = QtWidgets.QTableWidgetItem(tgtTableName)
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 1, item)
            srcColumnNames = ','.join(fk.srcColumns)
            tgtColumnNames = ','.join(fk.tgtColumns)
            columnsString = '({})-->({})'.format(srcColumnNames, tgtColumnNames)
            item = QtWidgets.QTableWidgetItem(columnsString)
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 2, item)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.widget('fk_table'), 1)
        widget = QtWidgets.QWidget(objectName='fk_widget')
        widget.setLayout(layout)
        self.addWidget(widget)

        #############################################
        # ASSERTIONS TAB
        #################################

        rowCount = 0
        if assertions:
            rowCount = len(assertions)
        table = QtWidgets.QTableWidget(rowCount, 1, self, objectName='assertions_table')
        table.setHorizontalHeaderLabels(['Intra table assertions'])
        table.setFont(Font('Roboto', 12))
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addWidget(table)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionsClickable(False)
        header.setSectionsMovable(False)
        header.hide()
        header = table.verticalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)


        if assertions:
            for row, assertion in enumerate(assertions):
                item = QtWidgets.QTableWidgetItem(assertion.getStringWithoutTableName())
                item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                table.setItem(row, 0, item)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.widget('assertions_table'), 1)
        widget = QtWidgets.QWidget(objectName='assertions_widget')
        widget.setLayout(layout)
        self.addWidget(widget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        confirmation.setFont(Font('Roboto', 12))
        self.addWidget(confirmation)

        #############################################
        # MAIN WIDGET
        #################################

        widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        widget.addTab(self.widget('columns_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'), 'Columns')
        widget.addTab(self.widget('pk_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'), 'Primary Key')
        widget.addTab(self.widget('uniques_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'), 'Uniques')
        widget.addTab(self.widget('fk_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'), 'Foreign Keys')
        widget.addTab(self.widget('assertions_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'), 'Assertions')
        self.addWidget(widget)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(740, 420)
        self.setWindowIcon(QtGui.QIcon(':/blackbird/icons/128/ic_blackbird'))
        self.setWindowTitle(self.relationalTable.name)

        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the main session (alias for PreferencesDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Executed when the dialog is accepted.
        """
        super().accept()


class SQLScriptDialog(QtWidgets.QDialog):
    """
    Subclass of QtWidgets.QDialog that shows the sql script to create current schema.
    """

    def __init__(self, sql, schemaName, parent=None, **kwargs):
        """
        Initialize the dialog.
        """
        super().__init__(parent, **kwargs)

        #############################################
        # TEXT AREA
        #################################

        self.schemaName = schemaName

        sqlLabel = QtWidgets.QLabel('SQL', self)

        headerLayout = QtWidgets.QHBoxLayout(self)
        headerLayout.addWidget(sqlLabel, 1, QtCore.Qt.AlignLeading)

        headerWidget = QtWidgets.QWidget(self)
        headerWidget.setLayout(headerLayout)

        sqlText = QtWidgets.QTextEdit(self)
        sqlText.setFont(Font('Roboto', 14))
        sqlText.setObjectName('sql_text')
        sqlText.setReadOnly(True)
        sqlText.setText(sql)

        innerLayout = QtWidgets.QHBoxLayout(self)
        innerLayout.setContentsMargins(8, 0, 8, 8)
        innerLayout.addWidget(sqlText)

        textWidget = QtWidgets.QWidget(self)
        textWidget.setLayout(innerLayout)

        #############################################
        # CONFIRMATION AREA
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        buttonLayout = QtWidgets.QHBoxLayout(self)
        buttonLayout.setContentsMargins(10, 0, 10, 10)
        buttonLayout.addWidget(confirmation)

        buttonWidget = QtWidgets.QWidget(self)
        buttonWidget.setLayout(buttonLayout)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(headerWidget)
        mainLayout.addWidget(textWidget)
        mainLayout.addWidget(buttonWidget, 0, QtCore.Qt.AlignRight)

        self.setWindowTitle("SQL Script")
        self.setModal(True)
        self.setLayout(mainLayout)
        self.setMinimumSize(1024, 480)

        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Executed when the dialog is accepted.
        """


        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, "Save SQL script", "",
                                                  "All Files (*);;", options=options)

        print(fileName)
        if fileName:
            file = QFile(fileName)
            if file.open(QIODevice.WriteOnly):
                stream = QTextStream(file)
                stream << self.findChild(QtWidgets.QTextEdit, 'sql_text').toPlainText()

        self.close()



