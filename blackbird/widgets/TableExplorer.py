from PyQt5 import QtWidgets, QtGui, QtCore


from eddy.core.datatypes.annotation import Status
from eddy.core.datatypes.qt import Font
from eddy.core.functions.misc import first
from eddy.ui.dock import DockWidget
from eddy.ui.fields import StringField

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import EntityType
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalSchema


class BBTableExplorerWidget(QtWidgets.QScrollArea):
    """
    This class implements the explorer box widget.
    """
    def __init__(self, plugin):
        """
        Initialize the explorer box.
        """
        super().__init__(plugin.session)

        self.diagram = None
        self.plugin = plugin




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



    def setDiagram(self, diagram):
        """
        Sets the widget to inspect the given diagram.
        :type diagram: diagram
        """
        self.diagram = diagram



    @QtCore.pyqtSlot(RelationalSchema)
    def onSchemaChanged(self, schema):
        tables = schema.tables
        #foreignKeys = schema.foreignKeys
        #self.schemaInfo.updateData(len(tables),len(foreignKeys))


class TableExplorerWidget(QtWidgets.QWidget):
    """
    This class implements the schema explorer used to list schema tables.
    """

    def __init__(self, plugin):
        super().__init__(plugin.session)

        self.items = [
            EntityType.Class,
            EntityType.ObjectProperty,
            EntityType.DataProperty
        ]

        self.classIcon = QtGui.QIcon(':/icons/18/ic_treeview_concept')
        self.objPropIcon = QtGui.QIcon(':/icons/18/ic_treeview_role')
        self.dataPropIcon = QtGui.QIcon(':/icons/18/ic_treeview_attribute')

        self.searchShortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+f'), plugin.session)
        self.search = StringField(self)
        self.search.setAcceptDrops(False)
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText('Search...')
        self.search.setToolTip('Search ({})'.format(self.searchShortcut.key().toString(QtGui.QKeySequence.NativeText)))
        self.search.setFixedHeight(30)

        self.model = QtGui.QStandardItemModel(self)

        self.proxy = TableExplorerFilterProxyModel(self)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.proxy.setSourceModel(self.model)

        self.tableview = TableExplorerView(self)
        self.tableview.setModel(self.proxy)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.search)
        self.mainLayout.addWidget(self.tableview)

        self.setTabOrder(self.search, self.tableview)
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(216)

        self.setStyleSheet("""
            QLineEdit,
            QLineEdit:editable,
            QLineEdit:hover,
            QLineEdit:pressed,
            QLineEdit:focus {
              border: none;
              border-radius: 0;
              background: #FFFFFF;
              color: #000000;
              padding: 4px 4px 4px 4px;
            }
        """)

        header = self.tableview.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)


class TableExplorerView(QtWidgets.QTreeView):
    """
    This class implements the schema's tables explorer tree view.
    """
    def __init__(self,widget):
        """
        Initialize the ontology explorer view.
        :type widget: TableExplorerWidget
        """
        super().__init__(widget)
        self.startPos = None
        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.setFont(Font('Roboto', 12))
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setHeaderHidden(True)
        self.setHorizontalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setSelectionMode(QtWidgets.QTreeView.SingleSelection)
        self.setSortingEnabled(True)
        self.setWordWrap(True)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the Session holding the TableExplorer widget.
        :rtype: Session
        """
        return self.widget.session

    @property
    def widget(self):
        """
        Returns the reference to the TableExplorer widget.
        :rtype: TableExplorerWidget
        """
        return self.parent()

    #############################################
    #   EVENTS
    #################################

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the treeview.
        :type mouseEvent: QMouseEvent
        """
        self.clearSelection()

        if mouseEvent.buttons() & QtCore.Qt.LeftButton:
            self.startPos = mouseEvent.pos()

        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse if moved while a button is being pressed.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.buttons() & QtCore.Qt.LeftButton:
            #if Item.ConceptNode <= self.item < Item.InclusionEdge:
                distance = (mouseEvent.pos() - self.startPos).manhattanLength()
                if distance >= QtWidgets.QApplication.startDragDistance():

                    index = first(self.selectedIndexes())
                    if index:

                        model = self.model().sourceModel()
                        index = self.model().mapToSource(index)

                        item = model.itemFromIndex(index)
                        node = item.data()

                        if node:
                            pass
                        else:
                            if item.hasChildren():
                                node = item.child(0).data()

                        if node:
                            mimeData = QtCore.QMimeData()

                            mimeData.setText(str(node.Type.value))

                            node_iri = self.session.project.get_iri_of_node(node)
                            node_remaining_characters = node.remaining_characters

                            comma_seperated_text = str(node_iri + ',' + node_remaining_characters + ',' + node.text())

                            byte_array = QtCore.QByteArray()
                            byte_array.append(comma_seperated_text)

                            mimeData.setData(str(node.Type.value), byte_array)

                            drag = QtGui.QDrag(self)
                            drag.setMimeData(mimeData)
                            # drag.setPixmap(self.icon().pixmap(60, 40))
                            # drag.setHotSpot(self.startPos - self.rect().topLeft())
                            drag.exec_(QtCore.Qt.CopyAction)

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the tree view.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.button() == QtCore.Qt.RightButton:
            index = first(self.selectedIndexes())
            if index:
                model = self.model().sourceModel()
                index = self.model().mapToSource(index)
                item = model.itemFromIndex(index)
                node = item.data()
                if node:
                    self.widget.sgnItemRightClicked.emit(node)
                    menu = self.session.mf.create(node.diagram, [node])
                    menu.exec_(mouseEvent.screenPos().toPoint())

        super().mouseReleaseEvent(mouseEvent)

    #############################################
    #   INTERFACE
    #################################

    def sizeHintForColumn(self, column):
        """
        Returns the size hint for the given column.
        This will make the column of the treeview as wide as the widget that contains the view.
        :type column: int
        :rtype: int
        """
        return max(super().sizeHintForColumn(column), self.viewport().width())

class TableExplorerFilterProxyModel(QtCore.QSortFilterProxyModel):
    """
    Extends QSortFilterProxyModel adding filtering functionalities for the explorer widget
    """
    def __init__(self,parent=None):
        super().__init__(parent)
        self.items = {
            EntityType.Class,
            EntityType.ObjectProperty,
            EntityType.DataProperty
        }

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        return self.parent().project

    @property
    def session(self):
        return self.parent().session

    #############################################
    #   INTERFACE
    #################################

    def filterAcceptsRow(self, sourceRow, sourceIndex):
        """
        Overrides filterAcceptsRow to include extra filtering conditions
        :type sourceRow: int
        :type sourceIndex: QModelIndex
        :rtype: bool
        """
        index = self.sourceModel().index(sourceRow, 0, sourceIndex)
        item = self.sourceModel().itemFromIndex(index)
        # PARENT NODE
        if item.hasChildren():
            children = [item.child(c).data() for c in range(item.rowCount())]
            return super().filterAcceptsRow(sourceRow, sourceIndex) #\
                   #and \
                   #any([Status.valueOf(meta.get(K_DESCRIPTION_STATUS, '')) in self.status for meta in
                   #     [self.project.meta(node.type(), node.text()) for node in children
                   #      if node.type() in self.items]])
        # LEAF NODE
        return super().filterAcceptsRow(sourceRow, sourceIndex)
