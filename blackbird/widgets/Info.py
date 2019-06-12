from abc import ABCMeta, abstractmethod

from PyQt5 import QtWidgets, QtCore
from eddy.core.datatypes.qt import Font
from eddy.core.functions.misc import clamp, first
from eddy.core.functions.signals import connect

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalSchema
from eddy.ui.fields import IntegerField, StringField, ComboBox

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

        #self.schemaInfo = SchemaInfo(self)
        self.schemaInfo = SchemaInfo(plugin.session,self)
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
        self.schemaInfo.updateData(len(tables),len(foreignKeys))


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
    def __init__(self,session,parent=None):
        super().__init__(session,parent)

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

        self.header = BBHeader('Schema properties')
        self.header.setFont(Font('Roboto',12))

        self.layout = QtWidgets.QFormLayout()
        self.layout.setSpacing(0)
        self.layout.addRow(self.tableCountKey,self.tableCountField)
        self.layout.addRow(self.fkCountKey,self.fkCountField)

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



#
# #class SchemaInfo(QtWidgets.QWidget):
#     def __init__(self, parent):
#         super().__init__(parent)
#         self.tableCountInfo = QtWidgets.QLabel(self)
#         self.fkCountInfo = QtWidgets.QLabel(self)
#         layout = QtWidgets.QVBoxLayout(self)
#         layout.addWidget(self.tableCountInfo)
#         layout.addWidget(self.fkCountInfo)
#         self.setLayout(layout)


    # def updateInfos(self, tableCount, fkCount):
    #     self.tableCountInfo.setText(str(tableCount))
    #     self.fkCountInfo.setText(str(fkCount))



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
        self.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
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
    def __init__(self,  *args):
        """
        Initialize the button.
        """
        super().__init__(*args)


class BBInteger(IntegerField):
    """
    This class implements the integer value of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)


class BBString(StringField):
    """
    This class implements the string value of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)


class BBSelect(ComboBox):
    """
    This class implements the selection box of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setScrollEnabled(False)