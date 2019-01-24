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
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView

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
        self.mdiSubWindow = None

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
        self.showMessage("You have added a new diagram named: {}".format(diagram.name))

    @QtCore.pyqtSlot('QGraphicsScene')
    def onDiagramRemoved(self, diagram):
        """
        Executed whenever a diagram is removed from the active project.
        """
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

    @QtCore.pyqtSlot(QtWidgets.QMdiSubWindow)
    def onSubWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :type subwindow: MdiSubWindow
        """
        if subwindow and self.mdiSubWindow != subwindow:
            self.mdiSubWindow = subwindow
            self.showMessage("You have switched to the tab: {}".format(subwindow.windowTitle()))

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
        disconnect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)
        disconnect(self.menuAction.triggered)

    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Starting Blackbird plugin')

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        self.menuAction = QtWidgets.QAction('Blackbird', self)
        menu = self.session.menu('view')
        menu.addAction(self.menuAction)

        action = QtWidgets.QAction(
            'Start', self,
            objectName='start_blackbird',
            statusTip='Start Blackbird', triggered=lambda: self.showDialog("BLACKBIRD STARTED"))
        self.session.addAction(action)
        menu = QtWidgets.QMenu('&Blackbird', objectName='blackbird')
        menu.addAction(self.session.action('start_blackbird'))
        self.session.addMenu(menu)
        self.session.menuBar().addMenu(menu)

        # CONFIGURE SIGNAL/SLOTS
        self.debug('Connecting to active session')
        connect(self.session.sgnReady, self.onSessionReady)
        connect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)
        connect(self.menuAction.triggered, lambda: self.showMessage('Blackbird Plugin version: {}'.format(self.spec.get('plugin', 'version'))))

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

    def showDialog(self, message):
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

