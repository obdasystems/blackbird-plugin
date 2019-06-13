from PyQt5 import QtWidgets, QtGui, QtCore


from eddy.core.datatypes.qt import Font
from eddy.core.datatypes.system import File
from eddy.core.functions.misc import first, rstrip
from eddy.core.functions.signals import connect
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.ui.fields import StringField

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import EntityType
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalSchema
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalTable


# class BBTableExplorerWidget(QtWidgets.QScrollArea):
#     """
#     This class implements the explorer box widget.
#     """
#     def __init__(self, plugin):
#         """
#         Initialize the explorer box.
#         """
#         super().__init__(plugin.session)
#
#         self.diagram = None
#         self.plugin = plugin
#
#
#
#
#     #############################################
#     #   PROPERTIES
#     #################################
#
#     @property
#     def schema(self):
#         return self.plugin.schema
#
#     @property
#     def project(self):
#         """
#         Returns the reference to the active project.
#         :rtype: Session
#         """
#         return self.session.project
#
#     @property
#     def session(self):
#         """
#         Returns the reference to the active session.
#         :rtype: Session
#         """
#         return self.plugin.parent()
#
#     #############################################
#     #   EVENTS
#     #################################
#
#     def eventFilter(self, source, event):
#         """
#         Filter incoming events.
#         :type source: QObject
#         :type event: QtCore.QEvent
#         """
#         if source is self.verticalScrollBar():
#             if event.type() in {QtCore.QEvent.Show, QtCore.QEvent.Hide}:
#                 self.redraw()
#         return super().eventFilter(source, event)
#
#     #############################################
#     #   INTERFACE
#     #################################
#
#
#
#     def setDiagram(self, diagram):
#         """
#         Sets the widget to inspect the given diagram.
#         :type diagram: diagram
#         """
#         self.diagram = diagram
#
#
#
#     @QtCore.pyqtSlot(RelationalSchema)
#     def onSchemaChanged(self, schema):
#         tables = schema.tables
#         #foreignKeys = schema.foreignKeys
#         #self.schemaInfo.updateData(len(tables),len(foreignKeys))


class TableExplorerWidget(QtWidgets.QWidget):
    """
    This class implements the schema explorer used to list schema tables.
    """
    # segnale emesso se clicco su NODO corrispondente a tabella in tree view-->aggiorna info widget con info tabella corrispondente, vai a nodo su diagramma
    sgnGraphicalNodeItemClicked = QtCore.pyqtSignal(QtWidgets.QGraphicsItem)
    # segnale emesso se clicco su NOME TABELLA in tree view-->aggiorna info widget con info tabella corrispondente
    sgnRelationalTableItemClicked = QtCore.pyqtSignal(RelationalTable)

    def __init__(self, plugin):
        super().__init__(plugin.session)

        self.plugin = plugin

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

        connect(plugin.sgnSchemaChanged, self.onSchemaChanged)
        connect(self.search.textChanged, self.doFilterItem)
        connect(self.tableview.pressed, self.onItemPressed)

    #############################################
    #   SLOTS
    #################################

    #A REGIME CI SARANNO METODI PER MODIFICA ENTRY DELL'ALBERO (i.e., funzione che modifica entry dopo cambio nome tabella)

    #QUESTO METODO DOVRA LAVORARE CON I NODI DEL DIAGRAMMA (Metodo doAddNode)
    # (COME CORRISPONDENTE FUNZIONE IN ontology_explorer.py), NON CON GLI ELEMENTI DELLO SCHEMA
    @QtCore.pyqtSlot(RelationalSchema)
    def onSchemaChanged(self, schema):
        """
        Add a node in the tree view.
        :type schema: RelationalSchema
        """
        tables = schema.tables
        for table in tables:
            parent =  self.parentFor(table)
            if not parent:
                parent = QtGui.QStandardItem(self.parentKey(table))
                parent.setIcon(self.iconFor(table))
                parent.setData(table)
                self.model.appendRow(parent)
            #child = QtGui.QStandardItem(self.childKey(diagram, node))
            #child.setData(node)
            # CHECK FOR DUPLICATE NODES
            #children = [parent.child(i) for i in range(parent.rowCount())]
            #if not any([child.text() == c.text() for c in children]):
            #    parent.appendRow(child)
            # APPLY FILTERS AND SORT
            if self.sender() != self.plugin:
                self.proxy.invalidateFilter()
                self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    # A REGIME diagram:BBDiagram, node:BBNode (SERVE SOLO DOPO CHE HO COMINCIATO A DISEGNARE)
    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def doAddNode(self, diagram, node):
        """
        Add a node in the tree view.
        :type diagram: QGraphicsScene
        :type node: AbstractItem
        """
        if node.type() in self.items:
            parent = self.parentFor(node)
            if not parent:
                parent = QtGui.QStandardItem(self.parentKey(node))
                parent.setIcon(self.iconFor(node))
                self.model.appendRow(parent)
            child = QtGui.QStandardItem(self.childKey(diagram, node))
            child.setData(node)
            # CHECK FOR DUPLICATE NODES
            children = [parent.child(i) for i in range(parent.rowCount())]
            if not any([child.text() == c.text() for c in children]):
                parent.appendRow(child)
            # APPLY FILTERS AND SORT
            if self.sender() != self.plugin:
                self.proxy.invalidateFilter()
                self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    # A REGIME diagram:BBDiagram, node:BBNode (SERVE SOLO DOPO CHE HO COMINCIATO A DISEGNARE)
    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def doRemoveNode(self, diagram, node):
        """
        Remove a node from the tree view.
        :type diagram: QGraphicsScene
        :type node: AbstractItem
        """
        if node.type() in self.items:
            parent = self.parentFor(node)
            if parent:
                child = self.childFor(parent, diagram, node)
                if child:
                    parent.removeRow(child.index().row())
                if not parent.rowCount():
                    self.model.removeRow(parent.index().row())

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
                if isinstance(item.data(),RelationalTable):
                    self.sgnRelationalTableItemClicked.emit(item.data())
                elif isinstance(item.data(),AbstractNode):
                    self.sgnGraphicalNodeItemClicked.emit(item.data())
    #############################################
    #   INTERFACE
    #################################

    def iconFor(self, table):
        """
        Returns the icon for the given node.
        :type table:RelationalTable
        """
        entity = table.entity
        entityType = entity.entityType
        if entityType is EntityType.Class:
            return self.classIcon
        if entityType is EntityType.ObjectProperty:
            return self.objPropIcon
        if entityType is EntityType.DataProperty:
            return self.dataPropIcon


    def parentFor(self, node):
        """
        Search the parent element of the given node.
        :type node: AbstractNode
        :rtype: QtGui.QStandardItem
        """
        for i in self.model.findItems(self.parentKey(node), QtCore.Qt.MatchExactly):
            n = i.child(0).data()
            if node.type() is n.type():
                return i
        return None

    def childFor(self, parent, diagram, node):
        """
        Search the item representing this node among parent children.
        :type parent: QtGui.QStandardItem
        :type diagram: Diagram
        :type node: AbstractNode
        """
        key = self.childKey(diagram, node)
        for i in range(parent.rowCount()):
            child = parent.child(i)
            if child.text() == key:
                return child
        return None

    @staticmethod
    def childKey(diagram, node):
        """
        Returns the child key (text) used to place the given node in the treeview.
        :type diagram: Diagram
        :type node: AbstractNode
        :rtype: str
        """
        #DA CAMBIARE CON DIAGRAMMI BLACKBIRD ED OPPORTUNA FORMATTAZIONE
        predicate = node.text().replace('\n', '')
        diagram = rstrip(diagram.name, File.Graphol.extension)
        return '{0} ({1} - {2})'.format(predicate, diagram, node.id)


    @staticmethod
    def parentKey(node):
        """
        Returns the parent key (text) used to place the given node in the treeview.
        :type node: AbstractNode
        :rtype: str
        """
        #ALLA FINE QUESTO METODO DOVRA RITORNARE IL NOME DELLA TABELLA CORRISPONDENTE AL NODO IN INPUT
        if isinstance(node, AbstractNode):
            return node.text().replace('\n', '')
        if isinstance(node, RelationalTable):
            return node.name

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QtCore.QSize
        """
        return QtCore.QSize(216, 266)



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
