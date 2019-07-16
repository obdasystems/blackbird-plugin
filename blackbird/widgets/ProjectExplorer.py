import natsort

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.datatypes.qt import Font
from eddy.core.functions.misc import first
from eddy.core.functions.signals import connect, disconnect


class BlackbirdProjectExplorerWidget(QtWidgets.QWidget):
    """
    This class implements the project explorer used to display the project structure.
    """
    sgnFakeDiagramAdded = QtCore.pyqtSignal('QGraphicsScene')
    sgnItemActivated = QtCore.pyqtSignal('QGraphicsScene')
    sgnItemClicked = QtCore.pyqtSignal('QGraphicsScene')
    sgnItemDoubleClicked = QtCore.pyqtSignal('QGraphicsScene')

    def __init__(self, plugin):
        """
        Initialize the project explorer.
        :type plugin: ProjectExplorer
        """
        super().__init__(plugin.session)

        self.plugin = plugin
        self.project = None

        self.iconRoot = QtGui.QIcon(':/icons/18/ic_folder_open_black')
        self.iconBlank = QtGui.QIcon(':/icons/18/ic_document_blank')
        self.iconGraphol = QtGui.QIcon(':/icons/18/ic_document_graphol')
        self.iconOwl = QtGui.QIcon(':/icons/18/ic_document_owl')

        self.root = QtGui.QStandardItem()
        self.root.setFlags(self.root.flags() & ~QtCore.Qt.ItemIsEditable)
        self.root.setFont(Font('Roboto', 12, bold=True))
        self.root.setIcon(self.iconRoot)

        self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Shift+d'), self.session)
        self.model = QtGui.QStandardItemModel(self)
        self.proxy = ProjectExplorerSortedProxyModel(self)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.proxy.setSourceModel(self.model)
        self.projectview = ProjectExplorerView(self)
        self.projectview.setModel(self.proxy)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.projectview)

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(216)

        header = self.projectview.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        connect(self.projectview.activated, self.onItemActivated)
        connect(self.projectview.doubleClicked, self.onItemDoubleClicked)
        connect(self.projectview.pressed, self.onItemPressed)
        connect(self.shortcut.activated, self.doFocusProjectView)
        connect(self.sgnItemActivated, self.plugin.doFocusDiagram)
        connect(self.sgnItemDoubleClicked, self.plugin.doFocusDiagram)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the active session.
        :rtype: Session
        """
        return self.plugin.parent()

    #############################################
    #   WIDGET INTERNAL SLOTS
    #################################

    @QtCore.pyqtSlot('QGraphicsScene')
    def doAddDiagram(self, diagram):
        """
        Add a diagram in the treeview.
        :type diagram: BlackBirdDiagram
        """
        if not self.findItem(diagram.name):
            item = QtGui.QStandardItem(diagram.name)
            item.setData(diagram)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            item.setFont(Font('Roboto', 12))
            item.setIcon(self.iconGraphol)
            self.root.appendRow(item)
            self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    @QtCore.pyqtSlot('QGraphicsScene')
    def doRemoveDiagram(self, diagram):
        """
        Remove a diagram from the treeview.
        :type diagram: BlackBirdDiagram
        """
        item = self.findItem(diagram.name)
        if item:
            self.root.removeRow(item.index().row())

    @QtCore.pyqtSlot()
    def doFocusProjectView(self):
        """
        Focus the project view.
        """
        # RAISE THE ENTIRE WIDGET TREE IF IT IS NOT VISIBLE
        if not self.isVisible():
            widget = self
            while widget != self.session:
                widget.show()
                widget.raise_()
                widget = widget.parent()
        self.projectview.setFocus()

    @QtCore.pyqtSlot('QModelIndex')
    def onItemActivated(self, index):
        """
        Executed when an item in the tree view is activated (e.g. by pressing Return or Enter key).
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() == QtCore.Qt.NoButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data():
                self.sgnItemActivated.emit(item.data())
                # KEEP FOCUS ON THE TREE VIEW UNLESS SHIFT IS PRESSED
                if QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.SHIFT:
                    return
                self.projectview.setFocus()
            elif item:
                # EXPAND/COLLAPSE PARENT ITEM
                if self.projectview.isExpanded(index):
                    self.projectview.collapse(index)
                else:
                    self.projectview.expand(index)

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
                self.sgnItemDoubleClicked.emit(item.data())

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
                self.sgnItemClicked.emit(item.data())

    #############################################
    #   EVENTS
    #################################

    def paintEvent(self, paintEvent):
        """
        This is needed for the widget to pick the stylesheet.
        :type paintEvent: QPaintEvent
        """
        option = QtWidgets.QStyleOption()
        option.initFrom(self)
        painter = QtGui.QPainter(self)
        style = self.style()
        style.drawPrimitive(QtWidgets.QStyle.PE_Widget, option, painter, self)

    #############################################
    #   INTERFACE
    #################################

    def findItem(self, name):
        """
        Find the item with the given name inside the root element.
        :type name: str
        """
        for i in range(self.root.rowCount()):
            item = self.root.child(i)
            if item.text() == name:
                return item
        return None

    def setProject(self, project):
        """
        Set the project explorer to browse the given project.
        :type project: Project
        """
        self.model.clear()

        self.root = QtGui.QStandardItem()
        self.root.setFlags(self.root.flags() & ~QtCore.Qt.ItemIsEditable)
        self.root.setFont(Font('Roboto', 12, bold=True))
        self.root.setIcon(self.iconRoot)

        self.model.appendRow(self.root)
        self.root.setText(project.name)
        #TODO SCOMMENTA SOTTO DOPO OPPORTUNE MODIFICHE
        # connect(self.sgnFakeDiagramAdded, self.doAddDiagram)
        # for diagram in project.diagrams():
        #     self.sgnFakeDiagramAdded.emit(diagram)
        # disconnect(self.sgnFakeDiagramAdded)
        sindex = self.root.index()
        pindex = self.proxy.mapFromSource(sindex)
        self.projectview.expand(pindex)

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QtCore.QSize
        """
        return QtCore.QSize(216, 266)


class ProjectExplorerView(QtWidgets.QTreeView):
    """
    This class implements the project explorer tree view.
    """
    def __init__(self, widget):
        """
        Initialize the project explorer view.
        :type widget: ProjectExplorerWidget
        """
        super().__init__(widget)
        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
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
        Returns the reference to the Session holding the ProjectExplorer widget.
        :rtype: Session
        """
        return self.widget.session

    @property
    def widget(self):
        """
        Returns the reference to the ProjectExplorer widget.
        :rtype: ProjectExplorer
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
        super().mousePressEvent(mouseEvent)

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
                diagram = item.data()
                if diagram:
                    menu = QtWidgets.QMenu()
                    menu.addAction(self.session.action('new_diagram'))
                    menu.addSeparator()
                    menu.addAction(self.session.action('rename_diagram'))
                    menu.addAction(self.session.action('remove_diagram'))
                    menu.addSeparator()
                    menu.addAction(self.session.action('diagram_properties'))
                    self.session.action('rename_diagram').setData(diagram)
                    self.session.action('remove_diagram').setData(diagram)
                    self.session.action('diagram_properties').setData(diagram)
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


class ProjectExplorerSortedProxyModel(QtCore.QSortFilterProxyModel):
    """
    This class implements the proxy model used to sort elements in the Project Explorer widget.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the model.
        """
        super().__init__(*args, **kwargs)

    def lessThan(self, index1, index2):
        """
        Implements < operator.
        :type index1: QModelIndex
        :type index2: QModelIndex
        :rtype: bool
        """
        data1 = self.sourceModel().data(index1)
        data2 = self.sourceModel().data(index2)
        items = natsort.natsorted([data1, data2])
        try:
            return items.index(data1) < items.index(data2)
        except IndexError:
            return data1 < data2