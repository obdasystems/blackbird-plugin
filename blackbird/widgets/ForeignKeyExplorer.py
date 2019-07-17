from PyQt5 import QtWidgets, QtGui, QtCore


from eddy.core.datatypes.qt import Font
from eddy.core.datatypes.system import File
from eddy.core.functions.misc import first, rstrip
from eddy.core.functions.signals import connect
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.output import getLogger
from eddy.ui.fields import StringField

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import EntityType
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalSchema
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalTable
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import ForeignKeyConstraint
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.diagram import BlackBirdDiagram
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.items.edges import ForeignKeyEdge

LOGGER = getLogger()

class ForeignKeyExplorerWidget(QtWidgets.QWidget):
    """
    This class implements the schema explorer used to list schema foreign keys.
    """
    sgnGraphicalEdgeItemClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnGraphicalEdgeItemActivated = QtCore.pyqtSignal('QGraphicsItem')
    sgnGraphicalEdgeItemDoubleClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnGraphicalEdgeItemRightClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnForeignKeyItemClicked = QtCore.pyqtSignal(ForeignKeyConstraint)
    sgnForeignKeyItemActivated = QtCore.pyqtSignal(ForeignKeyConstraint)
    sgnForeignKeyItemDoubleClicked = QtCore.pyqtSignal(ForeignKeyConstraint)
    sgnForeignKeyItemRightClicked = QtCore.pyqtSignal(ForeignKeyConstraint)

    def __init__(self, plugin):
        super().__init__(plugin.session)

        self.plugin = plugin
        self.fkIcon = QtGui.QIcon(':blackbird/icons/24/ic_blackbird_fk')
        self.searchShortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+f'), plugin.session)
        self.search = StringField(self)
        self.search.setAcceptDrops(False)
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText('Search...')
        self.search.setToolTip('Search ({})'.format(self.searchShortcut.key().toString(QtGui.QKeySequence.NativeText)))
        self.search.setFixedHeight(30)
        self.model = QtGui.QStandardItemModel(self)
        self.proxy = ForeignKeyExplorerFilterProxyModel(self)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.proxy.setSourceModel(self.model)
        self.tableview = ForeignKeyExplorerView(self)
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

        connect(plugin.sgnSchemaChanged, self.onSchemaChanged)
        connect(plugin.sgnEdgeAdded, self.doAddNode)
        connect(self.tableview.pressed, self.onItemPressed)
        connect(self.tableview.doubleClicked, self.onItemDoubleClicked)
        connect(self.search.textChanged, self.doFilterItem)
        connect(self.search.returnPressed, self.onReturnPressed)
        connect(self.searchShortcut.activated, self.doFocusSearch)
        connect(self.sgnGraphicalEdgeItemActivated, self.plugin.doFocusItem)
        connect(self.sgnGraphicalEdgeItemClicked, self.plugin.doFocusItem)
        connect(self.sgnGraphicalEdgeItemDoubleClicked, self.plugin.doFocusItem)
        connect(self.sgnGraphicalEdgeItemRightClicked, self.plugin.doFocusItem)
        connect(self.sgnForeignKeyItemActivated, self.plugin.doFocusForeignKey)
        connect(self.sgnForeignKeyItemClicked, self.plugin.doFocusForeignKey)
        connect(self.sgnForeignKeyItemDoubleClicked, self.plugin.doFocusForeignKey)
        connect(self.sgnForeignKeyItemRightClicked, self.plugin.doFocusForeignKey)



    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(RelationalSchema)
    def onSchemaChanged(self, schema):
        """
        Add a node in the tree view.
        :type schema: RelationalSchema
        """
        self.model.clear()

    @QtCore.pyqtSlot(BlackBirdDiagram, ForeignKeyEdge)
    def doAddNode(self, diagram, edge):
        """
        Add a node in the tree view.
        :type diagram: QGraphicsScene
        :type edge: ForeignKeyEdge
        """
        parent = self.parentFor(edge)
        if not parent:
            parent = QtGui.QStandardItem(self.parentKey(edge))
            parent.setIcon(self.iconFor(edge.foreignKey))
            parent.setData(edge.foreignKey)
            self.model.appendRow(parent)
        child = QtGui.QStandardItem(self.childKey(diagram, edge))
        child.setData(edge)
        parent.appendRow(child)
        # APPLY FILTERS AND SORT
        if self.sender() != self.plugin:
            self.proxy.invalidateFilter()
            self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    @QtCore.pyqtSlot(str)
    def doFilterItem(self, key):
        """
        Executed when the search box is filled with data.
        :type key: str
        """
        self.proxy.setFilterFixedString(key)
        self.proxy.sort(QtCore.Qt.AscendingOrder)

    @QtCore.pyqtSlot()
    def doFocusSearch(self):
        """
        Focus the search bar.
        """
        # RAISE THE ENTIRE WIDGET TREE IF IT IS NOT VISIBLE
        if not self.isVisible():
            widget = self
            while widget != self.session:
                widget.show()
                widget.raise_()
                widget = widget.parent()
        self.search.setFocus()
        self.search.selectAll()

    @QtCore.pyqtSlot()
    def onReturnPressed(self):
        """
        Executed when the Return or Enter key is pressed in the search field.
        """
        self.focusNextChild()

    @QtCore.pyqtSlot('QModelIndex')
    def onItemActivated(self, index):
        """
        Executed when an item in the treeview is activated (e.g. by pressing Return or Enter key).
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() == QtCore.Qt.NoButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data():
                if isinstance(item.data(), ForeignKeyConstraint):
                    self.sgnForeignKeyItemActivated.emit(item.data())
                elif isinstance(item.data(), ForeignKeyEdge):
                    self.sgnGraphicalEdgeItemActivated.emit(item.data())
                    self.sgnForeignKeyItemActivated.emit(item.data().relationalTable)
                # KEEP FOCUS ON THE TREE VIEW UNLESS SHIFT IS PRESSED
                if QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.SHIFT:
                    return
                self.tableview.setFocus()
            elif item:
                # EXPAND/COLLAPSE PARENT ITEM
                if self.tableview.isExpanded(index):
                    self.tableview.collapse(index)
                else:
                    self.tableview.expand(index)

    @QtCore.pyqtSlot('QModelIndex')
    def onItemDoubleClicked(self, index):
        """
        Executed when an item in the treeview is double clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data():
                if isinstance(item.data(), ForeignKeyConstraint):
                    self.sgnForeignKeyItemDoubleClicked.emit(item.data())
                elif isinstance(item.data(), ForeignKeyEdge):
                    self.sgnGraphicalEdgeItemDoubleClicked.emit(item.data())
                    self.sgnForeignKeyItemDoubleClicked.emit(item.data().foreignKey)


    @QtCore.pyqtSlot('QModelIndex')
    def onItemPressed(self, index):
        """
        Executed when an item in the treeview is clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data():
                if isinstance(item.data(),ForeignKeyConstraint):
                    self.sgnForeignKeyItemClicked.emit(item.data())
                elif isinstance(item.data(),ForeignKeyEdge):
                    self.sgnGraphicalEdgeItemClicked.emit(item.data())
                    self.sgnForeignKeyItemClicked.emit(item.data().foreignKey)

    #############################################
    #   INTERFACE
    #################################

    def iconFor(self, fk):
        """
        Returns the icon for the given node.
        :type fk: ForeignKeyConstraint
        """
        return self.fkIcon


    def parentFor(self, node):
        """
        Search the parent element of the given node.
        :type node: ForeignKeyEdge
        :rtype: QtGui.QStandardItem
        """
        for i in self.model.findItems(self.parentKey(node), QtCore.Qt.MatchExactly):
            if i.child(0):
                n = i.child(0).data()
                if node.type() is n.type():
                    return i
        return None

    # def childFor(self, parent, diagram, node):
    #     """
    #     Search the item representing this node among parent children.
    #     :type parent: QtGui.QStandardItem
    #     :type diagram: Diagram
    #     :type node: AbstractNode
    #     """
    #     key = self.childKey(diagram, node)
    #     for i in range(parent.rowCount()):
    #         child = parent.child(i)
    #         if child.text() == key:
    #             return child
    #     return None

    @staticmethod
    def childKey(diagram, edge):
        """
        Returns the child key (text) used to place the given node in the treeview.
        :type diagram: Diagram
        :type edge: ForeignKeyEdge
        :rtype: str
        """
        diagram = rstrip(diagram.name, File.Graphol.extension)
        return '[{0} - {1}] ({2})'.format(diagram, edge.id, edge.foreignKey.name)


    @staticmethod
    def parentKey(node):
        """
        Returns the parent key (text) used to place the given node in the treeview.
        :type node: Union[ForeignKeyEdge,ForeignKeyConstraint]
        :rtype: str
        """
        if isinstance(node, ForeignKeyConstraint):
            return node.name
        if isinstance(node, ForeignKeyEdge):
            return node.foreignKey.name

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QtCore.QSize
        """
        return QtCore.QSize(216, 266)



class ForeignKeyExplorerView(QtWidgets.QTreeView):
    """
    This class implements the schema's FKs explorer tree view.
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

    #TODO CAUSA CRASH
    # def mouseReleaseEvent(self, mouseEvent):
    #     """
    #     Executed when the mouse is released from the tree view.
    #     :type mouseEvent: QMouseEvent
    #     """
    #     if mouseEvent.button() == QtCore.Qt.RightButton:
    #         index = first(self.selectedIndexes())
    #         if index:
    #             model = self.model().sourceModel()
    #             index = self.model().mapToSource(index)
    #             item = model.itemFromIndex(index)
    #             node = item.data()
    #             if node:
    #                 if isinstance(node,ForeignKeyConstraint):
    #                     self.widget.sgnForeignKeyConstraintItemRightClicked.emit(node)
    #                 elif isinstance(node,ForeignKeyEdge):
    #                     self.widget.sgnGraphicalEdgeItemRightClicked.emit(node)
    #                     self.widget.sgnForeignKeyConstraintItemRightClicked.emit(node.foreignKey)
    #                 menu = self.session.mf.create(node.diagram, [node])
    #                 menu.exec_(mouseEvent.screenPos().toPoint())
    #
    #     super().mouseReleaseEvent(mouseEvent)

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

class ForeignKeyExplorerFilterProxyModel(QtCore.QSortFilterProxyModel):
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


