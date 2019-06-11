from PyQt5 import QtWidgets, QtCore
from eddy.core.functions.misc import clamp, first
from eddy.core.functions.signals import connect

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalSchema


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

        self.schemaInfo = SchemaInfo(self)
        connect(plugin.sgnSchemaChanged,self.onSchemaChanged)

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(QtCore.QSize(216, 120))
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setWidget(self.stacked)
        self.setWidgetResizable(True)

        self.setStyleSheet("""
        BBInfoWidget {
          background: #FFFFFF;
        }
        BBInfoWidget Header {
          background: #5A5050;
          padding-left: 4px;
          color: #FFFFFF;
        }
        BBInfoWidget Key {
          background: #BBDEFB;
          border-top: none;
          border-right: none;
          border-bottom: 1px solid #BBDEFB;
          border-left: none;
          padding: 0 0 0 4px;
        }
        BBInfoWidget Button,
        BBInfoWidget Button:focus,
        BBInfoWidget Button:hover,
        BBInfoWidget Button:hover:focus,
        BBInfoWidget Button:pressed,
        BBInfoWidget Button:pressed:focus,
        BBInfoWidget Integer,
        BBInfoWidget String,
        BBInfoWidget Select,
        BBInfoWidget Parent {
          background: #E3F2FD;
          border-top: none;
          border-right: none;
          border-bottom: 1px solid #BBDEFB !important;
          border-left: 1px solid #BBDEFB !important;
          padding: 0 0 0 4px;
          text-align:left;
        }
        BBInfoWidget Button::menu-indicator {
          image: none;
        }
        BBInfoWidget Select:!editable,
        BBInfoWidget Select::drop-down:editable {
          background: #FFFFFF;
        }
        BBInfoWidget Select:!editable:on,
        BBInfoWidget Select::drop-down:editable:on {
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

    def stack(self):
        """
        Set the current stacked widget.
        """
        if self.schema:
            self.stacked.setCurrentWidget(self.schemaInfo)

    @QtCore.pyqtSlot(RelationalSchema)
    def onSchemaChanged(self, schema):
        tables = schema.tables
        foreignKeys = schema.foreignKeys
        self.schemaInfo.updateInfos(len(tables),len(foreignKeys))

class SchemaInfo(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.tableCountInfo = QtWidgets.QLabel(self)
        self.fkCountInfo = QtWidgets.QLabel(self)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.tableCountInfo)
        layout.addWidget(self.fkCountInfo)
        self.setLayout(layout)

    def updateInfos(self, tableCount, fkCount):
        self.tableCountInfo.setText(str(tableCount))
        self.fkCountInfo.setText(str(fkCount))