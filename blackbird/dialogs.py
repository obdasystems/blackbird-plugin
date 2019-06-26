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


