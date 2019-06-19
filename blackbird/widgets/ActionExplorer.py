from abc import ABCMeta, abstractmethod

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from eddy.core.datatypes.qt import Font
from eddy.core.functions.misc import clamp, first
from eddy.core.functions.signals import connect

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalSchema
from eddy.ui.fields import IntegerField, StringField, ComboBox
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalTable
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import ForeignKeyConstraint
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalTableAction
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.widgets.Info import BBAbstractInfo, BBHeader, BBKey, BBInteger, BBString

from blackbird.widgets.Info import BBButton


class BBActionWidget(QtWidgets.QScrollArea):
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

        self.actionInfo = ActionInfo(plugin.session,self.stacked)
        connect(plugin.sgnSchemaChanged,self.onSchemaChanged)

        self.stacked.addWidget(self.actionInfo)

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(QtCore.QSize(216, 112))
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setWidget(self.stacked)
        self.setWidgetResizable(True)

        self.setStyleSheet("""
        BBActionWidget {
          background: #FFFFFF;
        }
        BBActionWidget BBHeader {
          background: #5A5050;
          padding-left: 4px;
          color: #FFFFFF;
        }
        BBActionWidget BBKey {
          background: #BBDEFB;
          border-top: none;
          border-right: none;
          border-bottom: 1px solid #BBDEFB;
          border-left: none;
          padding: 0 0 0 4px;
        }
        BBActionWidget BBButton,
        BBActionWidget BBButton:focus,
        BBActionWidget BBButton:hover,
        BBActionWidget BBButton:hover:focus,
        BBActionWidget BBButton:pressed,
        BBActionWidget BBButton:pressed:focus,
        BBActionWidget BBInteger,
        BBActionWidget BBString,
        BBActionWidget BBSelect,
        BBActionWidget BBParent {
          background: #E3F2FD;
          border-top: none;
          border-right: none;
          border-bottom: 1px solid #BBDEFB !important;
          border-left: 1px solid #BBDEFB !important;
          padding: 0 0 0 4px;
          text-align:left;
        }
        BBActionWidget BBButton::menu-indicator {
          image: none;
        }
        BBActionWidget BBSelect:!editable,
        BBActionWidget BBSelect::drop-down:editable {
          background: #FFFFFF;
        }
        BBActionWidget BBSelect:!editable:on,
        BBActionWidget BBSelect::drop-down:editable:on {
          background: #FFFFFF;
        }
        BBActionWidget QCheckBox {
          background: #FFFFFF;
          spacing: 0;
          margin-left: 4px;
          margin-top: 2px;
        }
        BBActionWidget QCheckBox::indicator:disabled {
          background-color: #BABABA;
        }
        """)

        scrollbar = self.verticalScrollBar()
        scrollbar.installEventFilter(self)

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
            if isinstance(infoItem, list):
                if len(infoItem)>0:
                    if isinstance(infoItem[0], RelationalTableAction):
                        show = self.actionInfo
            if isinstance(infoItem, RelationalTable):
                show = self.actionInfo

            prev = self.stacked.currentWidget()
            self.stacked.setCurrentWidget(show)
            self.redraw()
            if prev is not show:
                scrollbar = self.verticalScrollBar()
                scrollbar.setValue(0)


    @QtCore.pyqtSlot(RelationalSchema)
    def onSchemaChanged(self, schema):
        actions = schema.actions
        self.actionInfo.updateData(actions)
        self.stack(actions)

    @QtCore.pyqtSlot(RelationalTable)
    def doSelectTable(self, table):
        actions = table.actions
        self.actionInfo.updateData(actions)
        self.stack(actions)

#############################################
#   INFO WIDGETS
#################################


class ActionInfo(BBAbstractInfo):
    def __init__(self,session,parent=None):
        super().__init__(session,parent)

        self.actions = []

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, actions):
        """
        Fetch new information and fill the widget with data.
        :type actions: list
        :
        """
        for index, action in enumerate(actions):
            subj = action.actionSubjectTableName
            type = action.actionType
            objs = action.actionObjectsNames

            header = BBHeader('Action {}'.format(index))
            header.setFont(Font('Roboto', 12))

            button = BBButton()
            button.setFont(Font('Roboto', 12))
            button.setText('Apply')
            button.setEnabled(True)

            headerLayout = QtWidgets.QFormLayout()
            headerLayout.setSpacing(0)
            headerLayout.addRow(header, button)

            subjKey = BBKey('Subject')
            subjKey.setFont(Font('Roboto', 12))
            subjField = BBString(self)
            subjField.setFont(Font('Roboto', 12))
            subjField.setReadOnly(True)
            subjField.setValue(subj)

            typeKey = BBKey('Type')
            typeKey.setFont(Font('Roboto', 12))
            typeField = BBString(self)
            typeField.setFont(Font('Roboto', 12))
            typeField.setReadOnly(True)
            typeField.setValue(type)

            objsKey = BBKey('Objects')
            objsKey.setFont(Font('Roboto', 12))
            objsField = BBString(self)
            objsField.setFont(Font('Roboto', 12))
            objsField.setReadOnly(True)
            objStr = ", ".join(map(str, objs))
            objsField.setValue(objStr)

            layout = QtWidgets.QFormLayout()
            layout.setSpacing(0)
            layout.addRow(subjKey, subjField)
            layout.addRow(typeKey, typeField)
            layout.addRow(objsKey, objsField)

            self.mainLayout.addWidget(header)
            self.mainLayout.addLayout(headerLayout)
            self.mainLayout.addLayout(layout)
