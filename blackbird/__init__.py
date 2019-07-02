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

"""Blackbird: Ontology to relational schema translator plugin for Eddy."""


import json
import os
import tempfile
from textwrap import dedent

from PyQt5 import (
    QtCore,
    QtGui,
    QtNetwork,
    QtWidgets
)

from eddy import ORGANIZATION, APPNAME, WORKSPACE
from eddy.core.datatypes.owl import OWLAxiom, OWLSyntax
from eddy.core.datatypes.qt import Font
from eddy.core.diagram import Diagram
from eddy.core.exporters.owl2 import OWLOntologyExporterWorker
from eddy.core.functions.fsystem import fread, fexists
from eddy.core.functions.misc import first
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect, disconnect
from eddy.core.items.edges.common.base import AbstractEdge
from eddy.core.items.edges.inclusion import InclusionEdge
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.concept import ConceptNode
from eddy.core.output import getLogger
from eddy.core.plugin import AbstractPlugin
from eddy.ui.dialogs import DiagramSelectionDialog
from eddy.ui.dock import DockWidget
from eddy.ui.progress import BusyProgressDialog

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird import resources_rc
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.about import AboutDialog
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.dialogs import (
    BlackbirdLogDialog,
    BlackbirdOutputDialog
)
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.files import FileUtils
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.graphol import (
    ForeignKeyVisualElements,
    BlackbirdOntologyEntityManager
)
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.rest import NetworkManager
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import (
    RelationalSchemaParser,
    EntityType
)
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.translator import BlackbirdProcess

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalSchema
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.widgets.Info import BBInfoWidget
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.widgets.TableExplorer import TableExplorerWidget
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.widgets.ForeignKeyExplorer import ForeignKeyExplorerWidget
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalTableAction
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.widgets.ActionExplorer import BBActionWidget
from eddy.ui.view import DiagramView

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.diagram import BlackBirdDiagram
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.items.edges import ForeignKeyEdge
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.items.nodes import TableNode

LOGGER = getLogger()


class BlackbirdPlugin(AbstractPlugin):
    """
    This plugin provides integration with Blackbird, a tool for translating an ontology into a relational schema.
    """
    sgnStartTranslator = QtCore.pyqtSignal()
    sgnStopTranslator = QtCore.pyqtSignal()
    sgnSchemaChanged = QtCore.pyqtSignal(RelationalSchema)
    sgnActionCorrectlyApplied = QtCore.pyqtSignal()

    def __init__(self, spec, session):
        """
        Initialises a new instance of the Blackbird plugin.
        :type spec: PluginSpec
        :type session: Session
        """
        super().__init__(spec, session)
        self.nmanager = NetworkManager(self)
        self.translator = None
        self.bbOntologyEntityMgr = None

    # noinspection PyArgumentList
    def initActions(self):
        """
        Initialize plugin actions.
        """
        #############################################
        #   MenuBar Actions
        #################################
        self.addAction(QtWidgets.QAction('Open', self, objectName='open', triggered=self.doOpen))
        self.addAction(QtWidgets.QAction('Save', self, objectName='save', triggered=self.doSave))
        self.addAction(QtWidgets.QAction('Save as', self, objectName='save_as', triggered=self.doSaveAs))
        self.addAction(QtWidgets.QAction('Settings', self, objectName='settings', triggered=self.doOpenSettings))
        self.addAction(QtWidgets.QAction('Ontology Analysis', self, objectName='open_ontology_analysis',
                                         triggered=self.doOpenOntologyAnalysis))
        self.addAction(QtWidgets.QAction('Entity Filter', self, objectName='open_entity_filter',
                                         triggered=self.doOpenEntityFilter))
        self.addAction(QtWidgets.QAction('Recap Schema Selections', self, objectName='open_schema_selections',
                                         triggered=self.doOpenSchemaSelections))
        self.addAction(QtWidgets.QAction('Generate Preview Schema', self, objectName='generate_preview_schema',
                                         triggered=self.doGeneratePreviewSchema))
        self.addAction(QtWidgets.QAction('Export Mappings', self, objectName='export_mappings',
                                         triggered=self.doExportMappings))
        self.addAction(QtWidgets.QAction('Export SQL Script', self, objectName='export_sql',
                                         triggered=self.doExportSQLScript))
        self.addAction(QtWidgets.QAction('Export Schema Diagrams', self, objectName='export_schema_diagrams',
                                         triggered=self.doExportSchemaDiagrams))
        self.addAction(QtWidgets.QAction('Blackbird Log', self, objectName='blackbird_log',
                                         triggered=self.doShowTranslatorLog))
        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/blackbird/icons/128/ic_blackbird'), 'About Blackbird', self,
            objectName='about', triggered=self.doShowAboutDialog))

        #############################################
        #   ToolBar Actions
        #################################
        self.addAction(QtWidgets.QAction(
            QtGui.QIcon(':/blackbird/icons/128/ic_blackbird'), 'Generate Schema', self,
            objectName='generate_schema', toolTip='Generate database schema',
            triggered=self.doGenerateSchema))

    # noinspection PyArgumentList
    def initMenus(self):
        """
        Initialize plugin menu.
        """
        #############################################
        #   MenuBar QMenu
        #################################
        menu = QtWidgets.QMenu('&Blackbird', objectName='menubar_menu')
        menu.addAction(self.action('open'))
        menu.addAction(self.action('save'))
        menu.addAction(self.action('save_as'))
        menu.addSeparator()
        menu.addAction(self.action('settings'))
        menu.addSeparator()
        menu.addAction(self.action('open_ontology_analysis'))
        menu.addAction(self.action('open_entity_filter'))
        menu.addAction(self.action('open_schema_selections'))
        menu.addSeparator()
        menu.addAction(self.action('generate_preview_schema'))
        menu.addAction(self.action('export_mappings'))
        menu.addAction(self.action('export_sql'))
        menu.addAction(self.action('export_diagrams'))
        menu.addSeparator()
        menu.addAction(self.action('blackbird_log'))
        menu.addSeparator()
        menu.addAction(self.action('about'))
        self.addMenu(menu)
        # Add blackbird menu to session's menu bar
        self.session.menuBar().insertMenu(self.session.menu('window').menuAction(), self.menu('menubar_menu'))

    # noinspection PyArgumentList
    def initToolBars(self):
        """
        Initialize toolbar actions.
        """
        toolbar = QtWidgets.QToolBar(self.session, objectName='blackbird_toolbar')
        toolbar.addAction(self.action('generate_schema'))
        self.addWidget(toolbar)

        self.session.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('blackbird_toolbar'))
        self.session.insertToolBarBreak(self.widget('blackbird_toolbar'))

    def initSubprocess(self):
        """
        Initialize the Blackbird translator process.
        """
        path = os.path.normpath(os.path.join(__file__, os.pardir, os.pardir))
        bbpath = os.path.join(path, self.spec.get('blackbird', 'executable'))
        if not fexists(bbpath):
            raise IOError('Cannot find Blackbird executable!')
        self.translator = BlackbirdProcess(bbpath, self)
        connect(self.translator.started, self.onTranslatorReady)
        connect(self.translator.errorOccurred, self.onTranslatorErrorOccurred)
        connect(self.sgnStartTranslator, self.doStartTranslator)
        connect(self.sgnStopTranslator, self.doStopTranslator)

    # noinspection PyArgumentList
    def initWidgets(self):
        """
        Initialize plugin widgets.
        """
        progress = BusyProgressDialog('Generating Schema...', parent=self.session)
        progress.setObjectName('progress')
        self.addWidget(progress)

        actionProgress = BusyProgressDialog('Applying Action to Schema...', parent=self.session)
        actionProgress.setObjectName('action_progress')
        self.addWidget(actionProgress)

        undoProgress = BusyProgressDialog('Undoing Action to Schema...', parent=self.session)
        undoProgress.setObjectName('undo_progress')
        self.addWidget(undoProgress)

        #####################################
        #                                   #
        # INITIALIZE THE SCHEMA INFO WIDGET #
        #                                   #
        #####################################
        infoWidget = BBInfoWidget(self)
        infoWidget.setObjectName('blackbird_info')
        self.addWidget(infoWidget)
        # CREATE DOCKING AREA INFO WIDGET
        infoDockWidget = DockWidget('Schema Info', QtGui.QIcon(':/icons/18/ic_info_outline_black'), self.session)
        infoDockWidget.installEventFilter(self)
        infoDockWidget.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        infoDockWidget.setObjectName('blackbird_info_dock')
        infoDockWidget.setWidget(self.widget('blackbird_info'))
        self.addWidget(infoDockWidget)
        self.session.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget('blackbird_info_dock'))

        #####################################
        #                                   #
        # INITIALIZE THE ACTION INFO WIDGET #
        #                                   #
        #####################################
        actionWidget = BBActionWidget(self)
        actionWidget.setObjectName('blackbird_action_info')
        self.addWidget(actionWidget)
        # CREATE DOCKING AREA ACTION INFO WIDGET
        actionDockWidget = DockWidget('Action Explorer', QtGui.QIcon(':/icons/18/ic_explore_black'), self.session)
        actionDockWidget.installEventFilter(self)
        actionDockWidget.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        actionDockWidget.setObjectName('blackbird_action_info_dock')
        actionDockWidget.setWidget(self.widget('blackbird_action_info'))
        self.addWidget(actionDockWidget)
        self.session.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget('blackbird_action_info_dock'))

        menu = self.session.menu('view')
        menu.addAction(self.widget('blackbird_action_info_dock').toggleViewAction())

        ######################################
        #                                    #
        # INITIALIZE THE FK EXPLORER WIDGET #
        #                                    #
        ######################################
        fkExplorerWidget = ForeignKeyExplorerWidget(self)

        fkExplorerWidget.setObjectName('blackbird_fk_explorer')
        self.addWidget(fkExplorerWidget)
        # CREATE TOGGLE ACTIONS
        group = QtWidgets.QActionGroup(self, objectName='fk_explorer_item_toggle')
        group.setExclusive(False)
        # for item in fkExplorerWidget.items:
        #     action = QtWidgets.QAction(item.realName.title(), group, objectName=item.name, checkable=True)
        #     action.setChecked(True)
        #     action.setData(item)
        #     action.setFont(Font('Roboto', 11))
        #     connect(action.triggered, fkExplorerWidget.onMenuButtonClicked)
        #     group.addAction(action)
        self.addAction(group)

        group = QtWidgets.QActionGroup(self, objectName='fk_explorer_status_toggle')
        group.setExclusive(False)
        # for status in fkExplorerWidget.status:
        #     action = QtWidgets.QAction(status.value if status.value else 'Default', group, objectName=status.name, checkable=True)
        #     action.setChecked(True)
        #     action.setData(status)
        #     action.setFont(Font('Roboto', 11))
        #     connect(action.triggered, fkExplorerWidget.onMenuButtonClicked)
        #     group.addAction(action)
        self.addAction(group)

        # CREATE TOGGLE MENU
        menu = QtWidgets.QMenu(objectName='fk_explorer_toggle')
        menu.addSection('Items')
        menu.addActions(self.action('fk_explorer_item_toggle').actions())
        menu.addSection('Description')
        menu.addActions(self.action('fk_explorer_status_toggle').actions())
        self.addMenu(menu)

        # CREATE CONTROL WIDGET
        button = QtWidgets.QToolButton(objectName='fk_explorer_toggle')
        button.setIcon(QtGui.QIcon(':/icons/18/ic_settings_black'))
        button.setContentsMargins(0, 0, 0, 0)
        button.setFixedSize(18, 18)
        button.setFocusPolicy(QtCore.Qt.NoFocus)
        button.setMenu(self.menu('fk_explorer_toggle'))
        button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.addWidget(button)

        # CREATE DOCKING AREA WIDGET
        fkExplorerDockWidget = DockWidget('Foreign Keys Explorer', QtGui.QIcon(':icons/18/ic_explore_black'), self.session)

        fkExplorerDockWidget.addTitleBarButton(self.widget('fk_explorer_toggle'))
        fkExplorerDockWidget.installEventFilter(self)
        fkExplorerDockWidget.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        fkExplorerDockWidget.setObjectName('fk_explorer_dock')
        fkExplorerDockWidget.setWidget(self.widget('blackbird_fk_explorer'))
        self.addWidget(fkExplorerDockWidget)

        # CREATE SHORTCUTS
        action = fkExplorerDockWidget.toggleViewAction()
        action.setParent(self.session)
        action.setShortcut(QtGui.QKeySequence('Alt+4'))

        # CREATE ENTRY IN VIEW MENU
        menu = self.session.menu('view')
        menu.addAction(self.widget('fk_explorer_dock').toggleViewAction())

        ########################################
        #                                      #
        # INITIALIZE THE TABLE EXPLORER WIDGET #
        #                                      #
        ########################################
        tableExplorerWidget = TableExplorerWidget(self)

        tableExplorerWidget.setObjectName('blackbird_table_explorer')
        self.addWidget(tableExplorerWidget)
        # CREATE TOGGLE ACTIONS
        group = QtWidgets.QActionGroup(self, objectName='table_explorer_item_toggle')
        group.setExclusive(False)
        # for item in tableExplorerWidget.items:
        #     action = QtWidgets.QAction(item.realName.title(), group, objectName=item.name, checkable=True)
        #     action.setChecked(True)
        #     action.setData(item)
        #     action.setFont(Font('Roboto', 11))
        #     connect(action.triggered, tableExplorerWidget.onMenuButtonClicked)
        #     group.addAction(action)
        self.addAction(group)

        group = QtWidgets.QActionGroup(self, objectName='table_explorer_status_toggle')
        group.setExclusive(False)
        # for status in tableExplorerWidget.status:
        #     action = QtWidgets.QAction(status.value if status.value else 'Default', group, objectName=status.name, checkable=True)
        #     action.setChecked(True)
        #     action.setData(status)
        #     action.setFont(Font('Roboto', 11))
        #     connect(action.triggered, tableExplorerWidget.onMenuButtonClicked)
        #     group.addAction(action)
        self.addAction(group)

        # CREATE TOGGLE MENU
        menu = QtWidgets.QMenu(objectName='table_explorer_toggle')
        menu.addSection('Items')
        menu.addActions(self.action('table_explorer_item_toggle').actions())
        menu.addSection('Description')
        menu.addActions(self.action('table_explorer_status_toggle').actions())
        self.addMenu(menu)

        # CREATE CONTROL WIDGET
        button = QtWidgets.QToolButton(objectName='table_explorer_toggle')
        button.setIcon(QtGui.QIcon(':/icons/18/ic_settings_black'))
        button.setContentsMargins(0, 0, 0, 0)
        button.setFixedSize(18, 18)
        button.setFocusPolicy(QtCore.Qt.NoFocus)
        button.setMenu(self.menu('table_explorer_toggle'))
        button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.addWidget(button)

        # CREATE DOCKING AREA WIDGET
        tableExplorerDockWidget = DockWidget('Schema Tables Explorer', QtGui.QIcon(':icons/18/ic_explore_black'),
                                             self.session)
        tableExplorerDockWidget.addTitleBarButton(self.widget('table_explorer_toggle'))
        tableExplorerDockWidget.installEventFilter(self)
        tableExplorerDockWidget.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        tableExplorerDockWidget.setObjectName('table_explorer_dock')
        tableExplorerDockWidget.setWidget(self.widget('blackbird_table_explorer'))
        self.addWidget(tableExplorerDockWidget)

        # CREATE SHORTCUTS
        action = tableExplorerDockWidget.toggleViewAction()
        action.setParent(self.session)
        action.setShortcut(QtGui.QKeySequence('Alt+4'))

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('table_explorer_dock').toggleViewAction())

        #####################
        #                   #
        # CONFIGURE SIGNALS #
        #                   #
        #####################
        #connect(self.session.sgnReady, self.onSessionReady)
        connect(self.widget('blackbird_table_explorer').sgnRelationalTableItemClicked, self.widget('blackbird_info').doSelectTable)
        connect(self.widget('blackbird_fk_explorer').sgnForeignKeyItemClicked, self.widget('blackbird_info').doSelectForeignKey)
        connect(self.widget('blackbird_table_explorer').sgnRelationalTableItemClicked, self.widget('blackbird_action_info').doSelectTable)

        connect(self.widget('blackbird_action_info').sgnActionButtonClicked, self.onSchemaActionApplied)
        connect(self.widget('blackbird_action_info').sgnUndoButtonClicked, self.onSchemaActionUndo)

        #################
        #               #
        # DOCKING AREAS #
        #               #
        #################
        self.session.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget('table_explorer_dock'))
        self.session.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget('fk_explorer_dock'))

    def initDiagramDialog(self):
        self.tempDialog = QtWidgets.QDialog(self.session)

        eddyProject = self.session.project

        ontDiagramToShow = None
        ontDiagrams = eddyProject.diagrams()
        for ontDiagram in ontDiagrams:
            ontDiagramToShow = ontDiagram
            break
        if ontDiagramToShow:
            #bbDiagram = Diagram('{}_SCHEMA'.format(ontDiagramToShow.name),eddyProject)
            bbDiagram = BlackBirdDiagram('{}_SCHEMA'.format(ontDiagramToShow.name), eddyProject)

            ontNodeToBBNodeDict = {}

            # ADDING NODES
            diagramToTablesDict = self.bbOntologyEntityMgr.diagramToTables
            relTableToDiagramNodes = diagramToTablesDict[ontDiagramToShow]
            for table,ontNodeList in relTableToDiagramNodes.items():
                tableName = table.name
                for ontNode in ontNodeList:
                    #relNode = ConceptNode(ontNode.width(), ontNode.height(), remaining_characters=tableName, diagram=bbDiagram)
                    relNode = TableNode(ontNode.width(), ontNode.height(), remaining_characters=tableName,
                                          relational_table=table ,diagram=bbDiagram)
                    relNode.setPos(ontNode.pos())
                    relNode.setText(tableName)
                    bbDiagram.addItem(relNode)
                    ontNodeToBBNodeDict[ontNode] = relNode

            #ADDING EDGES
            diagramToForeignKeysDict = self.bbOntologyEntityMgr.diagramToForeignKeys
            fkToDiagramElements = diagramToForeignKeysDict[ontDiagramToShow]
            for fk,fkVisualElementList in fkToDiagramElements.items():
                fkName = fk.name
                for innerList in fkVisualElementList:
                    if len(innerList)==1:
                        fkVisualElement = innerList[0]
                        src = ontNodeToBBNodeDict[fkVisualElement.src]
                        tgt = ontNodeToBBNodeDict[fkVisualElement.tgt]
                        edges = fkVisualElement.edges
                        if len(edges)==1:
                            edge = edges[0]
                            fkBreakpoints = edge.breakpoints
                            #fkEdge = InclusionEdge(source=src, target=tgt, breakpoints=fkBreakpoints, diagram=bbDiagram)
                            fkEdge = ForeignKeyEdge(foreign_key=fk ,source=src, target=tgt, breakpoints=fkBreakpoints, diagram=bbDiagram)

                            canDraw = fkEdge.canDraw()
                            bbDiagram.addItem(fkEdge)

                            fkEdge.source.setAnchor(fkEdge, QtCore.QPointF(fkVisualElement.src.anchor(edge)))
                            fkEdge.target.setAnchor(fkEdge, QtCore.QPointF(fkVisualElement.tgt.anchor(edge)))

                            fkEdge.source.addEdge(fkEdge)
                            fkEdge.target.addEdge(fkEdge)

                            fkEdge.updateEdge(visible=True)
                        else:
                            srcAnchor = QtCore.QPointF(fkVisualElement.src.anchor(edges[0]))
                            tgtAnchor = QtCore.QPointF(fkVisualElement.tgt.anchor(edges[-1]))
                            fkBreakpoints = []

                            for item in fkVisualElement.orderedInnerItems:
                                if isinstance(item,AbstractNode):
                                    fkBreakpoints.append(item.mapToScene(item.center()))
                                elif isinstance(item,AbstractEdge):
                                    fkBreakpoints.extend(item.breakpoints)

                            #fkEdge = InclusionEdge(source=src, target=tgt, breakpoints=fkBreakpoints, diagram=bbDiagram)
                            fkEdge = ForeignKeyEdge(foreign_key=fk, source=src, target=tgt, breakpoints=fkBreakpoints,
                                                    diagram=bbDiagram)

                            bbDiagram.addItem(fkEdge)

                            fkEdge.source.setAnchor(fkEdge, srcAnchor)
                            fkEdge.target.setAnchor(fkEdge, tgtAnchor)

                            fkEdge.source.addEdge(fkEdge)
                            fkEdge.target.addEdge(fkEdge)


                            fkEdge.updateEdge(visible=True)
                    else:
                        for fkVisualElement in innerList:
                            length = len(innerList)

            diagramView = DiagramView(bbDiagram, self.session)

            tempDialogLayout = QtWidgets.QVBoxLayout()
            tempDialogLayout.addWidget(diagramView)
            self.tempDialog.setLayout(tempDialogLayout)
            self.tempDialog.show()



    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.
        :type source: QObject
        :type event: QtCore.QEvent
        :rtype: bool
        """
        if event.type() == QtCore.QEvent.Resize:
            widget = source.widget()
            if "redraw" in dir(widget):
                widget.redraw()
        return super().eventFilter(source, event)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot('QGraphicsScene')
    def onDiagramAdded(self, diagram):
        """
        Executed whenever a diagram is added to the active project.
        """
        pass

    @QtCore.pyqtSlot('QGraphicsScene')
    def onDiagramRemoved(self, diagram):
        """
        Executed whenever a diagram is removed from the active project.
        """
        pass

    @QtCore.pyqtSlot()
    def onDiagramSelectionChanged(self):
        """
        Executed whenever the selection of the active diagram changes.
        """
        pass

    @QtCore.pyqtSlot()
    def onDiagramUpdated(self):
        """
        Executed whenever the active diagram is updated.
        """
        pass

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def onProjectItemAdded(self, diagram, item):
        """
        Executed whenever a new element is added to the active project.
        """
        pass

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def onProjectItemRemoved(self, diagram, item):
        """
        Executed whenever a new element is removed from the active project.
        """
        pass

    @QtCore.pyqtSlot()
    def onProjectUpdated(self):
        """
        Executed whenever the current project is updated.
        """
        pass

    @QtCore.pyqtSlot()
    def onSessionReady(self):
        """
        Executed whenever the main session completes the startup sequence.
        """
        self.debug('Connecting to project: %s', self.project.name)
        connect(self.project.sgnUpdated, self.onProjectUpdated)
        connect(self.project.sgnDiagramAdded, self.onDiagramAdded)
        connect(self.project.sgnDiagramRemoved, self.onDiagramRemoved)
        connect(self.project.sgnItemAdded, self.onProjectItemAdded)
        connect(self.project.sgnItemRemoved, self.onProjectItemRemoved)

        # START BLACKBIRD PROCESS
        if not self.translator.state() == QtCore.QProcess.Running:
            self.sgnStartTranslator.emit()

        #TODO CANCELLA
        # INITIALIZE THE TEMPORARY DIALOG TO SHOW THE VIEW
        #self.initDiagramDialog()

    @QtCore.pyqtSlot()
    def onDiagramExportCompleted(self):
        """
        Executed when the diagram -> OWL export completes.
        """
        try:
            worker = self.session.worker('Blackbird OWL Export')
            owltext = fread(worker.tmpfile.name)
            os.unlink(worker.tmpfile.name)
            reply = self.nmanager.postSchema(owltext.encode('utf-8'))
            # We deal with network errors in the slot connected to the finished()
            # signal since it always follows the error() signal
            connect(reply.finished, self.onSchemaGenerationCompleted)
        except Exception as e:
            self.widget('progress').hide()
            self.session.addNotification(dedent("""\
                <b><font color="#7E0B17">ERROR</font></b>: Could not connect to Blackbird Engine.<br/>
                <p>{}</p>""".format(e)))
            LOGGER.exception(e)

    @QtCore.pyqtSlot(RelationalSchema,RelationalTableAction)
    def onSchemaActionApplied(self,schema, action):
        """
        Executed when an action has been applied over the current schema.
        """
        try:
            self.widget('action_progress').show()
            reply = self.nmanager.putActionToSchema(schema.name, action)
            # We deal with network errors in the slot connected to the finished()
            # signal since it always follows the error() signal
            connect(reply.finished, self.onSchemaActionCompleted)
        except Exception as e:
            self.widget('action_progress').hide()
            self.session.addNotification(dedent("""\
                <b><font color="#7E0B17">ERROR</font></b>: Could not connect to Blackbird Engine.<br/>
                <p>{}</p>""".format(e)))
            LOGGER.exception(e)

    @QtCore.pyqtSlot(RelationalSchema)
    def onSchemaActionUndo(self, schema):
        """
        Executed when an action has been undone over the current schema.
        """
        try:
            self.widget('undo_progress').show()
            reply = self.nmanager.putUndoToSchema(schema.name)
            # We deal with network errors in the slot connected to the finished()
            # signal since it always follows the error() signal
            connect(reply.finished, self.onSchemaUndoCompleted)
        except Exception as e:
            self.widget('undo_progress').hide()
            self.session.addNotification(dedent("""\
                    <b><font color="#7E0B17">ERROR</font></b>: Could not connect to Blackbird Engine.<br/>
                    <p>{}</p>""".format(e)))
            LOGGER.exception(e)

    @QtCore.pyqtSlot()
    def onDiagramExportFailure(self):
        """
        Executed when the diagram -> OWL export fails.
        """
        self.widget('progress').hide()
        self.session.addNotification(dedent("""\
                <b><font color="#7E0B17">ERROR</font></b>: Could not export diagram.<br/>
                <p>{}</p>"""))
        LOGGER.error('Could not export diagram')

    @QtCore.pyqtSlot()
    def onSchemaGenerationCompleted(self):
        """
        Executed when the schema generation completes.
        """
        try:
            reply = self.sender()
            reply.deleteLater()
            assert reply.isFinished()
            # noinspection PyArgumentList
            if reply.error() == QtNetwork.QNetworkReply.NoError:
                owltext = str(reply.request().attribute(NetworkManager.OWL), encoding='utf-8')
                schema = str(reply.readAll(), encoding='utf-8')
                #AGGANCIATI QUI CON IL PARSER
                jsonSchema = json.loads(schema)
                self.schema = RelationalSchemaParser.getSchema(jsonSchema)

                self.initializeOntologyEntityManager()
                self.initDiagramDialog()
                dialog = BlackbirdOutputDialog(owltext, json.dumps(json.loads(schema),indent=2),self.schema, self.session)
                dialog.show()
                dialog.raise_()
                LOGGER.debug(self.schema)
                self.sgnSchemaChanged.emit(self.schema)
            else:
                self.session.addNotification('Error generating schema: {}'.format(reply.errorString()))
                LOGGER.error('Error generating schema: {}'.format(reply.errorString()))
        finally:
            self.widget('progress').hide()

    @QtCore.pyqtSlot()
    def onSchemaActionCompleted(self):
        """
        Executed when an action over the current schema completes.
        """
        try:
            reply = self.sender()
            reply.deleteLater()
            assert reply.isFinished()
            # noinspection PyArgumentList
            if reply.error() == QtNetwork.QNetworkReply.NoError:
                schema = str(reply.readAll(), encoding='utf-8')
                dialog = BlackbirdOutputDialog('', json.dumps(json.loads(schema), indent=2), self.session)
                dialog.show()
                dialog.raise_()
                # AGGANCIATI QUI CON IL PARSER
                jsonSchema = json.loads(schema)
                self.schema = RelationalSchemaParser.getSchema(jsonSchema)
                self.sgnActionCorrectlyApplied.emit()
                self.sgnSchemaChanged.emit(self.schema)
            else:
                self.session.addNotification('Error applying action: {}'.format(reply.errorString()))
                LOGGER.error('Error applying action: {}'.format(reply.errorString()))
        finally:
            self.widget('action_progress').hide()

    @QtCore.pyqtSlot()
    def onSchemaUndoCompleted(self):
        """
        Executed when an undo-action over the current schema completes.
        """
        try:
            reply = self.sender()
            reply.deleteLater()
            assert reply.isFinished()
            # noinspection PyArgumentList
            if reply.error() == QtNetwork.QNetworkReply.NoError:
                schema = str(reply.readAll(), encoding='utf-8')
                dialog = BlackbirdOutputDialog('', json.dumps(json.loads(schema), indent=2), self.session)
                dialog.show()
                dialog.raise_()
                # AGGANCIATI QUI CON IL PARSER
                jsonSchema = json.loads(schema)
                self.schema = RelationalSchemaParser.getSchema(jsonSchema)
                self.sgnActionCorrectlyApplied.emit()
                self.sgnSchemaChanged.emit(self.schema)
            else:
                self.session.addNotification('Error undoing action: {}'.format(reply.errorString()))
                LOGGER.error('Error undoing action: {}'.format(reply.errorString()))
        finally:
            self.widget('undo_progress').hide()


    @QtCore.pyqtSlot(QtCore.QProcess.ProcessError)
    def onTranslatorErrorOccurred(self, error):
        """
        Executed when an error occurs during the Blackbird engine startup process.
        :type error: ProcessError
        """
        self.session.addNotification(dedent("""\
        <b><font color="#7E0B17">ERROR</font></b>: Could not start Blackbird Engine: {}
        """.format(error)))
        LOGGER.error('Could not start Blackbird Engine: {}'.format(error))

    @QtCore.pyqtSlot()
    def onTranslatorReady(self):
        """
        Executed when the Blackbird engine completes the startup process.
        """
        self.session.addNotification('Blackbird Engine Ready')
        LOGGER.info('Blackbird Engine Ready')

    @QtCore.pyqtSlot()
    def doOpen(self):
        """
        Open a project in the current session.
        """
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        workspace = settings.value('workspace/home', WORKSPACE, str)
        dialog = QtWidgets.QFileDialog(self.session)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setDirectory(expandPath(workspace))
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
            self.debug('Open file requested: {}'.format(expandPath(first(dialog.selectedFiles()))))

    @QtCore.pyqtSlot()
    def doSave(self):
        """
        Save the current project.
        """
        pass

    @QtCore.pyqtSlot()
    def doSaveAs(self):
        """
        Save a copy of the current project.
        """
        pass

    @QtCore.pyqtSlot()
    def doOpenSettings(self):
        """
        Open plugin settings dialog.
        """
        pass

    @QtCore.pyqtSlot()
    def doOpenOntologyAnalysis(self):
        """
        Open ontology analysis dialog.
        """
        pass

    @QtCore.pyqtSlot()
    def doOpenEntityFilter(self):
        """
        Open entity filter dialog.
        """
        pass

    @QtCore.pyqtSlot()
    def doOpenSchemaSelections(self):
        """
        Open schema selections dialog.
        """
        pass

    @QtCore.pyqtSlot()
    def doGeneratePreviewSchema(self):
        """
        Generate a preview schema for the current project.
        """
        self.showDialog()

    @QtCore.pyqtSlot()
    def doExportMappings(self):
        """
        Export mappings for the current project.
        """
        pass

    @QtCore.pyqtSlot()
    def doExportSQLScript(self):
        """
        Export the SQL script generated for the current project.
        """
        pass

    @QtCore.pyqtSlot()
    def doExportSchemaDiagrams(self):
        """
        Export schema diagrams from the current project.
        """
        pass

    @QtCore.pyqtSlot()
    def doGenerateSchema(self):
        """
        Generate the schema for the selected diagrams.
        """
        dialog = DiagramSelectionDialog(self.session)
        if not dialog.exec_():
            return
        diagrams = dialog.selectedDiagrams()
        if len(diagrams) and self.translator.state() == QtCore.QProcess.Running:
            self.widget('progress').show()
            # EXPORT DIAGRAM TO OWL
            tmpfile = tempfile.NamedTemporaryFile('wb', delete=False)
            worker = OWLOntologyExporterWorker(self.project, tmpfile.name,
                                               axioms={x for x in OWLAxiom},
                                               normalize=False,
                                               syntax=OWLSyntax.Functional,
                                               diagrams=diagrams)
            worker.tmpfile = tmpfile
            connect(worker.sgnCompleted, self.onDiagramExportCompleted)
            connect(worker.sgnErrored, self.onDiagramExportFailure)
            self.session.startThread('Blackbird OWL Export', worker)

    @QtCore.pyqtSlot()
    def doShowTranslatorLog(self):
        """
        Shows the output of the translator.
        """
        if self.translator:
            dialog = BlackbirdLogDialog(self.translator.buffer, self.session)
            dialog.exec_()

    @QtCore.pyqtSlot()
    def doStartTranslator(self):
        """
        Start the Blackbird translator process.
        """
        if self.translator and self.translator.state() == QtCore.QProcess.NotRunning:
            self.translator.start()
            attempt = 0
            while attempt < 30:
                self.translator.waitForStarted(100)
                QtWidgets.QApplication.processEvents()
                if self.translator.state() == QtCore.QProcess.Running:
                    break
                attempt += 1

    @QtCore.pyqtSlot()
    def doStopTranslator(self):
        """
        Stop the Blackbird translator process.
        """
        if self.translator and self.translator.state() != QtCore.QProcess.NotRunning:
            self.translator.terminate()
            attempt = 0
            while attempt < 30:
                self.translator.waitForFinished(100)
                QtWidgets.QApplication.processEvents()
                if self.translator.state() == QtCore.QProcess.NotRunning:
                    break
                attempt += 1
            if self.translator.state() != QtCore.QProcess.NotRunning:
                self.translator.kill()

    @QtCore.pyqtSlot()
    def doShowAboutDialog(self):
        """
        Show the Blackbird about dialog.
        """
        dialog = AboutDialog(self, self.session)
        dialog.show()
        dialog.raise_()

    @QtCore.pyqtSlot()
    def doUpdateState(self):
        """
        Executed when the plugin session updates its state.
        """
        isDiagramActive = self.session.mdi.activeDiagram() is not None
        self.action('generate_schema').setEnabled(isDiagramActive)

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
        # STOP BLACKBIRD PROCESS
        self.sgnStopTranslator.emit()

        # DISCONNECT FROM CURRENT PROJECT
        self.debug('Disconnecting from project: %s', self.project.name)
        disconnect(self.project.sgnUpdated, self.onProjectUpdated)
        disconnect(self.project.sgnDiagramAdded, self.onDiagramAdded)
        disconnect(self.project.sgnDiagramRemoved, self.onDiagramRemoved)
        disconnect(self.project.sgnItemAdded, self.onProjectItemAdded)
        disconnect(self.project.sgnItemRemoved, self.onProjectItemRemoved)

        # DISCONNECT FROM ACTIVE SESSION
        self.debug('Disconnecting from active session')
        disconnect(self.session.sgnReady, self.onSessionReady)
        disconnect(self.session.sgnUpdateState, self.doUpdateState)

    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Starting Blackbird plugin')

        # INITIALIZE ACTIONS AND MENUS
        self.initActions()
        self.initMenus()
        self.initToolBars()
        self.initWidgets()

        # INITIALIZE BLACKBIRD TRANSLATOR
        self.initSubprocess()

        # CONFIGURE SIGNAL/SLOTS
        self.debug('Connecting to active session')
        connect(self.session.sgnReady, self.onSessionReady)
        connect(self.session.sgnUpdateState, self.doUpdateState)

    #############################################
    #   UTILITIES
    #################################

    def showMessage(self, message):
        """
        Displays the given message in a new dialog.
        :type message: str
        """
        label = QtWidgets.QLabel(message)
        confirmation = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        confirmation.setContentsMargins(10, 0, 10, 10)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(confirmation)
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Blackbird Plugin")
        dialog.setModal(False)
        dialog.setLayout(layout)
        connect(confirmation.accepted, dialog.accept)
        dialog.show()
        dialog.exec_()

    def showDialog(self):
        """
        Displays the given message in a new dialog.
        """
        dialog = QtWidgets.QDialog(self.session)
        textSchema = QtWidgets.QTextEdit(self.session)
        textSchema.setFont(Font('Roboto', 14))

        textTables = QtWidgets.QTextEdit(self.session)
        textTables.setFont(Font('Roboto', 14))

        textFKs = QtWidgets.QTextEdit(self.session)
        textFKs.setFont(Font('Roboto', 14))

        confirmation = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close, self.session)
        confirmation.setContentsMargins(10, 0, 10, 10)
        confirmation.setFont(Font('Roboto', 12))
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(textSchema)
        layout.addWidget(textTables)
        layout.addWidget(textFKs)
        layout.addWidget(confirmation, 0, QtCore.Qt.AlignRight)
        dialog.setWindowTitle("Blackbird Plugin")
        dialog.setModal(False)
        dialog.setLayout(layout)
        dialog.setMinimumSize(640, 480)
        connect(confirmation.clicked, dialog.accept)

        with BusyProgressDialog('Generating Schema...', mtime=1, parent=self.session):
            # GET SCHEMA DEFINITION
            #getAllSchemasText = RestUtils.getAllSchemas()
            #json_schema_data = json.loads(getAllSchemasText)

            filePath = os.path.join(os.path.dirname(__file__), os.pardir, 'tests', 'test_export_schema_1', 'Diagram5.json')
            json_schema_data = FileUtils.parseSchemaFile(filePath)

            # GET TABLE ACTIONS
            getActionsText = '{}'  # Needs to be rewritten since we removed requests
            json_action_data = json.loads(getActionsText)

            # PARSE THE SCHEMA
            schema = RelationalSchemaParser.getSchema(json_schema_data, json_action_data)
            LOGGER.debug('Relational Schema Parsed: ')
            LOGGER.debug(str(schema))
            textSchema.setPlainText(str(schema))
            textSchema.setReadOnly(True)

            #MAP TO ONTOLOGY VISUAL ELEMENTS
            visualManager = BlackbirdOntologyEntityManager(schema,self.session.project)
            tableDict = visualManager.diagramToTables
            tableDictStr = visualManager.diagramToTablesString()

            LOGGER.debug('table dictionary created')
            LOGGER.debug(tableDictStr)
            textTables.setPlainText(tableDictStr)
            textTables.setReadOnly(True)

            fkDict = visualManager.diagramToForeignKeys
            fkDictStr = visualManager.diagramToForeignKeysString()
            LOGGER.debug('FKs dictionary created')
            LOGGER.debug(fkDictStr)
            textFKs.setPlainText(fkDictStr)
            textFKs.setReadOnly(True)

        # SHOW THE DIALOG
        dialog.exec_()


    #############################################
    #   INTERFACE
    #################################
    def initializeOntologyEntityManager(self):
        """
        Initialize the ontology visual elements manager.
        """
        self.bbOntologyEntityMgr = BlackbirdOntologyEntityManager(self.schema,self.session)
        LOGGER.debug('############# Initializing BlackbirdOntologyEntityManager')
        LOGGER.debug(self.bbOntologyEntityMgr.diagramToTablesString())
        LOGGER.debug(self.bbOntologyEntityMgr.diagramToForeignKeysString())