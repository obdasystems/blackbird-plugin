# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <danielepantaleone@me.com>      #
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
#  #####################                          #####################  #
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################

"""Blackbird: Ontology to relational schema translator plugin."""

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView

from eddy import ORGANIZATION, APPNAME, WORKSPACE
from eddy.core.functions.misc import first
from eddy.core.functions.path import expandPath
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.diagram import Diagram
from eddy.core.functions.signals import connect, disconnect
from eddy.core.items.edges.inclusion import InclusionEdge
from eddy.core.items.nodes.concept import ConceptNode
from eddy.core.plugin import AbstractPlugin
from eddy.core.project import Project


class BlackbirdPlugin(AbstractPlugin):
    """
    This plugin provides integration with Blackbird, a tool for translating an ontology into a relational schema.
    """

    def __init__(self, spec, session):
        """
        Initialises a new instance of the Blackbird plugin.
        :type spec: PluginSpec
        :type session: Session
        """
        super().__init__(spec, session)

    def initActions(self):
        #############################################
        #   MenuBar Actions
        #################################
        self.addAction(QtWidgets.QAction('Open', objectName='open', triggered=self.doOpen))
        self.addAction(QtWidgets.QAction('Save', objectName='save', triggered=self.doSave))
        self.addAction(QtWidgets.QAction('Save as', objectName='save_as', triggered=self.doSaveAs))
        self.addAction(QtWidgets.QAction('Settings', objectName='settings', triggered=self.doOpenSettings))
        self.addAction(QtWidgets.QAction('Ontology Analysis', objectName='open_ontology_analysis',
                                         triggered=self.doOpenOntologyAnalysis))
        self.addAction(QtWidgets.QAction('Entity Filter', objectName='open_entity_filter',
                                         triggered=self.doOpenEntityFilter))
        self.addAction(QtWidgets.QAction('Recap Schema Selections', objectName='open_schema_selections',
                                         triggered=self.doOpenSchemaSelections))
        self.addAction(QtWidgets.QAction('Generate Preview Schema', objectName='generate_preview_schema',
                                         triggered=self.doGeneratePreviewSchema))
        self.addAction(QtWidgets.QAction('Export Mappings', objectName='export_mappings',
                                         triggered=self.doExportMappings))
        self.addAction(QtWidgets.QAction('Export SQL Script', objectName='export_sql',
                                         triggered=self.doExportSQLScript))
        self.addAction(QtWidgets.QAction('Export Schema Diagrams', objectName='export_schema_diagrams',
                                         triggered=self.doExportSchemaDiagrams))

    def initMenus(self):
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
        self.addMenu(menu)
        # Add blackbird menu to session's menu bar
        self.session.menuBar().insertMenu(self.session.menu('tools').menuAction(), self.menu('menubar_menu'))

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
        connect(diagram.sgnMenuCreated, self.onMenuCreated)
        self.showMessage("You have added a new diagram named: {}".format(diagram.name))

    @QtCore.pyqtSlot('QGraphicsScene')
    def onDiagramRemoved(self, diagram):
        """
        Executed whenever a diagram is removed from the active project.
        """
        disconnect(diagram.sgnMenuCreated, self.onMenuCreated)
        self.showMessage("You have deleted the diagram named: {}".format(diagram.name))

    @QtCore.pyqtSlot()
    def onDiagramSelectionChanged(self):
        """
        Executed whenever the selection of the active diagram changes.
        """
        self.showMessage("Selection changed on diagram {}".format(self.mdiSubWindow.diagram.name))

    @QtCore.pyqtSlot()
    def onDiagramUpdated(self):
        """
        Executed whenever the active diagram is updated.
        """
        self.showMessage("Diagram {} has changed".format(self.mdiSubWindow.diagram.name))

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def onProjectItemAdded(self, diagram, item):
        """
        Executed whenever a new element is added to the active project.
        """
        self.showMessage("Added item {} to diagram {}".format(item, diagram.name))

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def onProjectItemRemoved(self, diagram, item):
        """
        Executed whenever a new element is removed from the active project.
        """
        self.showMessage("Removed item {} from diagram {}".format(item, diagram.name))

    @QtCore.pyqtSlot()
    def onProjectUpdated(self):
        """
        Executed whenever the current project is updated.
        """
        self.showMessage("Project {} has been updated".format(self.session.project.name))

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

        self.showMessage("Blackbird plugin initialized!")

    @QtCore.pyqtSlot('QMenu', list, 'QPointF')
    def onMenuCreated(self, menu, items, pos=None):
        self.showMessage("Constructed menu {}".format(menu))

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

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
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

    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Starting Blackbird plugin')

        # INITIALIZE ACTIONS AND MENUS
        self.initActions()
        self.initMenus()

        # CONFIGURE SIGNAL/SLOTS
        self.debug('Connecting to active session')
        connect(self.session.sgnReady, self.onSessionReady)

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
        connect(confirmation.accepted, lambda: dialog.accept())
        dialog.show()
        # Executes dialog event loop synchronously with the rest of the ui (locks until the dialog is dismissed)
        # use the `raise_()` method if you want the dialog to run its own event thread.
        dialog.exec_()

    def showDialog(self):
        """
        Displays the given message in a new dialog.
        :type message: str
        """
        #scene = QGraphicsScene()


        rect = QRectF(10, 10, 100, 100)
        pen = QPen(QtCore.Qt.red)
        brush = QBrush(QtCore.Qt.black)

        #scene.addRect(rect, pen, brush)


        scene = Diagram("POllo", parent=self.session.project)
        conc = ConceptNode(diagram=scene, id="pollo")
        scene.mode = DiagramMode.Idle
        scene.addItem(conc)

        conc1 = ConceptNode(diagram=scene, id="pollo1")
        conc1.setPos(QtCore.QPointF(0, 150))

        scene.addItem(conc1)

        edge = InclusionEdge(source=conc,target=conc1, diagram=scene)
        print("Can draw edge ",edge.canDraw())

        scene.addItem(edge)

        view = QGraphicsView(scene)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(view)
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Blackbird Plugin")
        dialog.setModal(False)
        dialog.setLayout(layout)
        dialog.show()

        # Executes dialog event loop synchronously with the rest of the ui (locks until the dialog is dismissed)
        # use the `raise_()` method if you want the dialog to run its own event thread.
        dialog.exec_()

