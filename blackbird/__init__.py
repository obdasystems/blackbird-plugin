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
from enum import unique

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView

from eddy import ORGANIZATION, APPNAME, WORKSPACE
from eddy.core.datatypes.common import IntEnum_
from eddy.core.datatypes.graphol import Item
from eddy.core.functions.misc import first
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect, disconnect
from eddy.core.plugin import AbstractPlugin

from eddy.core.output import getLogger

import requests
import json

LOGGER = getLogger()

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

    # noinspection PyArgumentList
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

    # noinspection PyArgumentList
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
        scene = QGraphicsScene()
        rect = QRectF(10, 10, 100, 100)
        pen = QPen(QtCore.Qt.red)
        brush = QBrush(QtCore.Qt.black)

        scene.addRect(rect, pen, brush)
        view = QGraphicsView(scene)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(view)
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Blackbird Plugin")
        dialog.setModal(False)
        dialog.setLayout(layout)
        dialog.show()

        getAllSchemasText = RestUtils.getAllSchemas()
        json_schema_data = json.loads(getAllSchemasText)

        getActionsText =  RestUtils.getActionsBySchema("BOOKS_DB_SCHEMA")
        json_action_data = json.loads(getActionsText)

        schema = RelationalSchemaParser.getSchema(json_schema_data,json_action_data)

        print(str(schema))


        # Executes dialog event loop synchronously with the rest of the ui (locks until the dialog is dismissed)
        # use the `raise_()` method if you want the dialog to run its own event thread.
        dialog.exec_()

class SchemaToDiagramElements(QtCore.QObject):

    def __init__(self, relational_schema, session=None, **kwargs):
        super().__init__(session, **kwargs)
        self._relationalSchema = relational_schema


    @property
    def session(self):
        return self.parent()



    def getType(self,value):
        type = EntityType.fromValue(value)
        if type==EntityType.Class:
            return 4

class BlackbirdOntologyEntityManager(QtCore.QObject):
    """
    Initialize the manager.
    :type relational_schema: RelationalSchema
    :type parent: Project
    """
    def __init__(self, relational_schema, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._parent = parent
        self._ontologyDiagrams = parent.diagrams()
        self._relationalSchema = relational_schema
        self._tables = relational_schema.tables
        self._foreignKeys = relational_schema.foreignKeys

        self._diagramToTables = {}
        self._diagramToForeignKeys = {}

    def buildDictionaries(self):
        for ontDiagram in self._ontologyDiagrams:
            currDiagramToTableDict = {}
            for table in self._tables:
                currList = list()
                tableEntity = table.entity
                entityIRI = tableEntity.fullIRI
                entityShortIRI = tableEntity.shortIRI
                entityType = tableEntity.entityType
                nodes = ontDiagram.nodes
                if entityType == EntityType.Class:
                    for node in nodes:
                        if node.Type == Item.ConceptNode:
                            nodeShortIRI = node.text().replace("\n","")
                            if nodeShortIRI==entityShortIRI:
                                currList.append(node)
                elif entityType == EntityType.ObjectProperty:
                    for node in nodes:
                        if node.Type == Item.RoleNode:
                            nodeShortIRI = node.text().replace("\n","")
                            if nodeShortIRI==entityShortIRI:
                                currList.append(node)
                elif entityType == EntityType.DataProperty:
                    for node in nodes:
                        if node.Type == Item.AttributeNode:
                            nodeShortIRI = node.text().replace("\n","")
                            if nodeShortIRI==entityShortIRI:
                                currList.append(node)
                if len(currList)>0:
                    currDiagramToTableDict[table] = currList
            self._diagramToTables[ontDiagram] = currDiagramToTableDict

            currDiagramToForeignKeyDict = {}
            for fk in self._foreignKeys:
                currVisualEls = list()
                srcTableName = fk.srcTable
                srcTable = self._relationalSchema.getTableByName(srcTableName)
                srcEntity = srcTable.entity
                srcEntityShortIRI = srcEntity.shortIRI
                srcEntityType = srcEntity.entityType

                srcColumnNames = fk.srcColumns

                tgtTableName = fk.tgtTable
                tgtTable = self._relationalSchema.getTableByName(tgtTableName)
                tgtEntity = tgtTable.entity
                tgtEntityShortIRI = tgtEntity.shortIRI
                tgtEntityType = tgtEntity.entityType

                tgtColumnNames = fk.tgtColumns

                srcOccurrencesInDiagram = self._diagramToTables[ontDiagram][srcTable]
                tgtOccurrencesInDiagram = self._diagramToTables[ontDiagram][tgtTable]

                if srcOccurrencesInDiagram and tgtOccurrencesInDiagram:
                    if len(srcColumnNames)==1:
                        if srcEntityType==EntityType.Class:
                            if tgtEntityType==EntityType.Class:
                                currVisualEls.append(self.getEntityIsaEntityVEs(srcOccurrencesInDiagram,
                                                                                tgtOccurrencesInDiagram,
                                                                                ontDiagram))
                            elif tgtEntityType==EntityType.ObjectProperty:
                                tgtColumnName = first(tgtColumnNames)
                                relColumn = tgtTable.getColumnByName(tgtColumnName)
                                relcolPos = relColumn.position
                                if relcolPos==1:
                                    currVisualEls.append(self.getClassIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                                 tgtOccurrencesInDiagram,
                                                                                                 ontDiagram))
                                elif relcolPos==2:
                                    currVisualEls.append(self.getClassIsaExistRoleInvVEs(srcOccurrencesInDiagram,
                                                                                         tgtOccurrencesInDiagram,
                                                                                         ontDiagram))

                        elif tgtEntityType == EntityType.DataProperty:
                            tgtColumnName = first(tgtColumnNames)
                            relColumn = tgtTable.getColumnByName(tgtColumnName)
                            relcolPos = relColumn.position
                            if relcolPos == 1:
                                currVisualEls.append(self.getClassIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                             tgtOccurrencesInDiagram,
                                                                                             ontDiagram))
                        elif srcEntityType==EntityType.ObjectProperty:
                            srcColumnName = first(srcColumnNames)
                            srcRelColumn = srcTable.getColumnByName(srcColumnName)
                            srcRelcolPos = srcRelColumn.position
                            if tgtEntityType == EntityType.Class:
                                if srcRelcolPos==1:
                                    currVisualEls.append(self.getExistRoleOrAttributeIsaClassVEs(srcOccurrencesInDiagram,tgtOccurrencesInDiagram,ontDiagram))
                                elif srcRelcolPos==2:
                                    currVisualEls.append(self.getExistRoleInvIsaClassVEs(srcOccurrencesInDiagram,
                                                                                              tgtOccurrencesInDiagram,
                                                                                              ontDiagram))
                            elif tgtEntityType == EntityType.ObjectProperty:
                                tgtColumnName = first(tgtColumnNames)
                                tgtRelColumn = tgtTable.getColumnByName(tgtColumnName)
                                tgtRelcolPos = tgtRelColumn.position
                                if srcRelcolPos==1 and tgtRelcolPos==1:
                                    currVisualEls.append(self.getExistRoleOrAttributeIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                                            tgtOccurrencesInDiagram,
                                                                                                            ontDiagram))
                                elif srcRelcolPos==1 and tgtRelcolPos==2:
                                    currVisualEls.append(self.getExistRoleOrAttributeIsaExistRoleInvVEs(srcOccurrencesInDiagram,
                                                                                            tgtOccurrencesInDiagram,
                                                                                            ontDiagram))
                                elif srcRelcolPos==2 and tgtRelcolPos==1:
                                    currVisualEls.append(self.getExistRoleInvIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                            tgtOccurrencesInDiagram,
                                                                                            ontDiagram))
                                elif srcRelcolPos==2 and tgtRelcolPos==2:
                                    currVisualEls.append(self.getExistRoleInvIsaExistRoleInvVEs(srcOccurrencesInDiagram,
                                                                                            tgtOccurrencesInDiagram,
                                                                                            ontDiagram))
                            elif tgtEntityType == EntityType.DataProperty:
                                if srcRelcolPos==1:
                                    currVisualEls.append(self.getExistRoleOrAttributeIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                                                tgtOccurrencesInDiagram,
                                                                                                                ontDiagram))
                                elif srcRelcolPos==2:
                                    currVisualEls.append(self.getExistRoleInvIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                              tgtOccurrencesInDiagram,
                                                                                              ontDiagram))
                        elif srcEntityType==EntityType.DataProperty:
                            if tgtEntityType == EntityType.Class:
                                currVisualEls.append(self.getExistRoleOrAttributeIsaClassVEs(srcOccurrencesInDiagram,
                                                                                            tgtOccurrencesInDiagram,
                                                                                            ontDiagram))
                            elif tgtEntityType == EntityType.ObjectProperty:
                                tgtColumnName = first(tgtColumnNames)
                                tgtRelColumn = tgtTable.getColumnByName(tgtColumnName)
                                tgtRelcolPos = tgtRelColumn.position
                                if tgtRelcolPos==1:
                                    currVisualEls.append(self.getExistRoleOrAttributeIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                                                tgtOccurrencesInDiagram,
                                                                                                                ontDiagram))
                                elif tgtRelcolPos==2:
                                    currVisualEls.append(self.getExistRoleOrAttributeIsaExistRoleInvVEs(srcOccurrencesInDiagram,
                                                                                                       tgtOccurrencesInDiagram,
                                                                                                       ontDiagram))
                            elif tgtEntityType == EntityType.DataProperty:
                                currVisualEls.append(self.getExistRoleOrAttributeIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                                           tgtOccurrencesInDiagram,
                                                                                                           ontDiagram))
                    elif len(srcColumnNames)==2:
                        if srcEntityType == EntityType.ObjectProperty:
                            if tgtEntityType == EntityType.ObjectProperty:
                                currVisualEls.append(self.getEntityIsaEntityVEs(srcOccurrencesInDiagram,
                                                                                tgtOccurrencesInDiagram,
                                                                                ontDiagram))
                        elif srcEntityType == EntityType.DataProperty:
                            if tgtEntityType == EntityType.DataProperty:
                                currVisualEls.append(self.getEntityIsaEntityVEs(srcOccurrencesInDiagram,
                                                                                tgtOccurrencesInDiagram,
                                                                                ontDiagram))
                    if currVisualEls:
                        currDiagramToForeignKeyDict[fk]=currVisualEls
            self._diagramToForeignKeys[ontDiagram] = currDiagramToForeignKeyDict

    #A-->B, R-->P, U1-->U2
    def getEntityIsaEntityVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        result = list()
        edges = ontDiagram.edges
        for edge in edges:
            firstSrc = edge.source
            firstTgt = edge.target
            if edge.type==Item.InclusionEdge or edge.type==Item.EquivalenceEdge:
                if firstSrc in srcOccurrencesInDiagram and firstTgt in tgtOccurrencesInDiagram:
                    currVE = ForeignKeyVisualElements(firstSrc,firstTgt,[edge])
                    result.append(currVE)
            elif edge.type==Item.InputEdge:
                if firstSrc in srcOccurrencesInDiagram and (firstTgt.type()==Item.UnionNode or firstTgt.type()==Item.DisjointUnionNode):
                    for secondEdge in firstTgt.edges:
                        secondSrc = secondEdge.source
                        secondTgt = secondEdge.target
                        if secondSrc==firstTgt and secondTgt in tgtOccurrencesInDiagram:
                            currVE = ForeignKeyVisualElements(firstSrc, secondTgt, [edge,secondEdge],[firstTgt])

        return result

    #A-->exist(R) , A-->exist(U)
    def getClassIsaExistRoleOrAttributeVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        result = list()
        edges = ontDiagram.edges
        for edge in edges:
            if edge.type()==Item.InclusionEdge or edge.type()==Item.EquivalenceEdge:
                currSrc = edge.source
                currRestrTgt = edge.target
                if currSrc in srcOccurrencesInDiagram and currRestrTgt.type() is Item.DomainRestrictionNode:
                    for innerEdge in edges:
                        if innerEdge.type() == Item.InputEdge:
                            innerSrc = innerEdge.source
                            innerTgt = innerEdge.target
                            if innerSrc in tgtOccurrencesInDiagram and innerTgt==currRestrTgt:
                                currVE = ForeignKeyVisualElements(currSrc, innerSrc, [edge,innerEdge], [currRestrTgt])
                                result.append(currVE)
        return result

    # exist(R)-->A , exist(U)-->A
    def getExistRoleOrAttributeIsaClassVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        result = list()
        edges = ontDiagram.edges
        for edge in edges:
            if edge.type()==Item.InputEdge:
                currSrc = edge.source
                currRestrTgt = edge.target
                if currSrc in srcOccurrencesInDiagram and currRestrTgt.type() is Item.DomainRestrictionNode:
                    for innerEdge in edges:
                        if innerEdge.type()==Item.InclusionEdge or innerEdge.type()==Item.EquivalenceEdge:
                            innerSrc = innerEdge.source
                            innerTgt = innerEdge.target
                            if innerTgt in tgtOccurrencesInDiagram and innerSrc==currRestrTgt:
                                currVE = ForeignKeyVisualElements(currSrc, innerTgt, [edge,innerEdge], [currRestrTgt])
                                result.append(currVE)
        return result

    # exist(R)-->exist(P), exist(R)-->exist(U), exist(U)-->exist(R), exist(U1)-->exist(U2)
    def getExistRoleOrAttributeIsaExistRoleOrAttributeVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        result = list()
        edges = ontDiagram.edges
        for firstEdge in edges:
            if firstEdge.type()==Item.InputEdge:
                firstSrc = firstEdge.source
                firstTgt = firstEdge.target
                if firstSrc in srcOccurrencesInDiagram and firstTgt is Item.DomainRestrictionNode:
                    for secondEdge in edges:
                        if secondEdge.type()==Item.InclusionEdge or secondEdge.type()==Item.EquivalenceEdge:
                            secondSrc = secondEdge.source
                            secondTgt = secondEdge.target
                            if secondSrc==firstTgt and secondTgt is Item.DomainRestrictionNode:
                                for thirdEdge in edges:
                                    if thirdEdge.type()==Item.InputEdge:
                                        thirdSrc = thirdEdge.source
                                        thirdTgt = thirdEdge.target
                                        if thirdTgt==secondTgt and thirdSrc in tgtOccurrencesInDiagram:
                                            currVE = ForeignKeyVisualElements(firstSrc, thirdSrc, [firstEdge,secondEdge,thirdEdge],[firstTgt,secondTgt])
                                            result.append(currVE)
        return result

    # exist(inv(R))-->exist(P), exist(inv(R))-->exist(U)
    def getExistRoleInvIsaExistRoleOrAttributeVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        result = list()
        edges = ontDiagram.edges
        for firstEdge in edges:
            if firstEdge.type()==Item.InputEdge:
                firstSrc = firstEdge.source
                firstTgt = firstEdge.target
                if firstSrc in srcOccurrencesInDiagram and firstTgt is Item.RangeRestrictionNode:
                    for secondEdge in edges:
                        if secondEdge.type()==Item.InclusionEdge or secondEdge.type()==Item.EquivalenceEdge:
                            secondSrc = secondEdge.source
                            secondTgt = secondEdge.target
                            if secondSrc==firstTgt and secondTgt is Item.DomainRestrictionNode:
                                for thirdEdge in edges:
                                    if thirdEdge.type()==Item.InputEdge:
                                        thirdSrc = thirdEdge.source
                                        thirdTgt = thirdEdge.target
                                        if thirdTgt==secondTgt and thirdSrc in tgtOccurrencesInDiagram:
                                            currVE = ForeignKeyVisualElements(firstSrc, thirdSrc, [firstEdge,secondEdge,thirdEdge],[firstTgt,secondTgt])
                                            result.append(currVE)
        return result

    # exist(inv(R))-->exist(inv(P))
    def getExistRoleInvIsaExistRoleInvVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        result = list()
        edges = ontDiagram.edges
        for firstEdge in edges:
            if firstEdge.type()==Item.InputEdge:
                firstSrc = firstEdge.source
                firstTgt = firstEdge.target
                if firstSrc in srcOccurrencesInDiagram and firstTgt is Item.RangeRestrictionNode:
                    for secondEdge in edges:
                        if secondEdge.type()==Item.InclusionEdge or secondEdge.type()==Item.EquivalenceEdge:
                            secondSrc = secondEdge.source
                            secondTgt = secondEdge.target
                            if secondSrc==firstTgt and secondTgt is Item.RangeRestrictionNode:
                                for thirdEdge in edges:
                                    if thirdEdge.type()==Item.InputEdge:
                                        thirdSrc = thirdEdge.source
                                        thirdTgt = thirdEdge.target
                                        if thirdTgt==secondTgt and thirdSrc in tgtOccurrencesInDiagram:
                                            currVE = ForeignKeyVisualElements(firstSrc, thirdSrc, [firstEdge,secondEdge,thirdEdge],[firstTgt,secondTgt])
                                            result.append(currVE)
        return result

    # exist(R)-->exist(inv(P)), exist(U)-->exist(inv(P))
    def getExistRoleOrAttributeIsaExistRoleInvVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        result = list()
        edges = ontDiagram.edges
        for firstEdge in edges:
            if firstEdge.type()==Item.InputEdge:
                firstSrc = firstEdge.source
                firstTgt = firstEdge.target
                if firstSrc in srcOccurrencesInDiagram and firstTgt is Item.DomainRestrictionNode:
                    for secondEdge in edges:
                        if secondEdge.type()==Item.InclusionEdge or secondEdge.type()==Item.EquivalenceEdge:
                            secondSrc = secondEdge.source
                            secondTgt = secondEdge.target
                            if secondSrc==firstTgt and secondTgt is Item.RangeRestrictionNode:
                                for thirdEdge in edges:
                                    if thirdEdge.type()==Item.InputEdge:
                                        thirdSrc = thirdEdge.source
                                        thirdTgt = thirdEdge.target
                                        if thirdTgt==secondTgt and thirdSrc in tgtOccurrencesInDiagram:
                                            currVE = ForeignKeyVisualElements(firstSrc, thirdSrc, [firstEdge,secondEdge,thirdEdge],[firstTgt,secondTgt])
                                            result.append(currVE)

    # A-->exist(inv(R))
    def getClassIsaExistRoleInvVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        result = list()
        edges = ontDiagram.edges
        for edge in edges:
            if edge.type()==Item.InclusionEdge or edge.type()==Item.EquivalenceEdge:
                currSrc = edge.source
                currRestrTgt = edge.target
                if currSrc in srcOccurrencesInDiagram and currRestrTgt.type() is Item.RangeRestrictionNode:
                    for innerEdge in edges:
                        if innerEdge.type() == Item.InputEdge:
                            innerSrc = innerEdge.source
                            innerTgt = innerEdge.target
                            if innerSrc in tgtOccurrencesInDiagram and innerTgt==currRestrTgt:
                                currVE = ForeignKeyVisualElements(currSrc, innerSrc, [edge,innerEdge], [currRestrTgt])
                                result.append(currVE)
        return result

    # exist(inv(R))-->A
    def getExistRoleInvIsaClassVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        result = list()
        edges = ontDiagram.edges
        for edge in edges:
            if edge.type()==Item.InputEdge:
                currSrc = edge.source
                currRestrTgt = edge.target
                if currSrc in srcOccurrencesInDiagram and currRestrTgt.type() is Item.RangeRestrictionNode:
                    for innerEdge in edges:
                        if innerEdge.type()==Item.InclusionEdge or innerEdge.type()==Item.EquivalenceEdge:
                            innerSrc = innerEdge.source
                            innerTgt = innerEdge.target
                            if innerTgt in tgtOccurrencesInDiagram and innerSrc==currRestrTgt:
                                currVE = ForeignKeyVisualElements(currSrc, innerTgt, [edge,innerEdge], [currRestrTgt])
                                result.append(currVE)
        return result

class ForeignKeyVisualElements():
    def __init__(self, src, tgt, edges, inners=None):
        self._src = src
        self._tgt = tgt
        self._inners = inners
        self._edges = edges

    @property
    def src(self):
        return self._src

    @property
    def tgt(self):
        return self._tgt

    @property
    def inner(self):
        return self._inner

    @property
    def edges(self):
        return self._edges

class RelationalSchemaParser():
    """_instance = None
    def __new__(cls, *args, **kwargs):
       if not cls._instance:
              cls._instance = object.__new__(cls)
          return cls._instance"""

    @staticmethod
    def getSchema(schema_json_data, actions_json_data):
        schemaName = None
        tables = list()
        for item in schema_json_data:
            schemaName = item["schemaName"]
            jsonTables = item["tables"]
            for jsonTable in jsonTables:
                table = RelationalSchemaParser.getTable(jsonTable)
                tables.append(table)
        actions = list()
        for item in actions_json_data:
            subjectName = item["actionSubjectTableName"]
            actionType = item["actionType"]
            objectsNames = item["actionObjectsNames"]
            action = RelationalTableAction(subjectName,actionType,objectsNames)
            actions.append(action)
        return RelationalSchema(schemaName,tables,actions)

    @staticmethod
    def getTable(jsonTable):
        tableName = jsonTable["tableName"]
        entity = RelationalSchemaParser.getOriginEntity(jsonTable["entity"])
        columns = list()
        jsonColumns = jsonTable["columns"]
        if jsonColumns:
            for jsonColumn in jsonColumns:
                column = RelationalSchemaParser.getColumn(jsonColumn)
                columns.append(column)
        primaryKey = None
        jsonPK = jsonTable["primaryKeyConstraint"]
        if jsonPK:
            primaryKey = RelationalSchemaParser.getPrimaryKey(jsonPK)
        uniques = list()
        jsonUniques = jsonTable["uniqueConstraints"]
        if jsonUniques:
            for jsonUnique in jsonUniques:
                unique = RelationalSchemaParser.getUnique(jsonUnique)
                uniques.append(unique)
        foreignKeys = list()
        jsonFKs = jsonTable["foreingKeyConstraints"]
        if jsonFKs:
            for jsonFK in jsonFKs:
                fk = RelationalSchemaParser.getForeignKey(jsonFK)
                foreignKeys.append(fk)
        return RelationalTable(tableName,entity,columns,primaryKey,uniques,foreignKeys)

    @staticmethod
    def getColumn(jsonColumn):
        columnName = jsonColumn["columnName"]
        entityIRI = jsonColumn["entityIRI"]
        columnType = jsonColumn["columnType"]
        position = jsonColumn["position"]
        nullable = jsonColumn["nullable"]
        return RelationalColumn(columnName,entityIRI,columnType,position,nullable)

    @staticmethod
    def getOriginEntity(jsonEntity):
        fullIRI = jsonEntity["entityFullIRI"]
        shortIRI = jsonEntity["entityShortIRI"]
        entityType = jsonEntity["entityType"]
        return RelationalTableOriginEntity(fullIRI,shortIRI,entityType)

    @staticmethod
    def getPrimaryKey(jsonPK):
        pkName = jsonPK["pkName"]
        columnNames = jsonPK["columnNames"]
        return PrimaryKeyConstraint(pkName,columnNames)

    @staticmethod
    def getUnique(jsonUnique):
        name = jsonUnique["pkName"]
        columnNames = jsonUnique["columnNames"]
        return UniqueConstraint(name, columnNames)

    @staticmethod
    def getForeignKey(jsonFK):
        fkName = jsonFK["fkName"]
        srcTableName = jsonFK["sourceTableName"]
        srcColumnNames = jsonFK["sourceColumnsNames"]
        tgtTableName = jsonFK["targetTableName"]
        tgtColumnNames = jsonFK["targetColumnsNames"]
        return ForeignKeyConstraint(fkName,srcTableName,srcColumnNames,tgtTableName,tgtColumnNames)

class RelationalSchema():
    def __init__(self,name, tables, actions):
        self._name = name
        self._tables = tables
        self._actions = actions
        self._foreignKeys = list()
        if self._tables:
            for table in self._tables:
                if table.foreignKeys:
                    self._foreignKeys.extend(table.foreignKeys)
    @property
    def name(self):
        return self._name

    @property
    def tables(self):
        return self._tables

    @property
    def actions(self):
        return self._actions

    @property
    def foreignKeys(self):
        return self._foreignKeys

    def getTableByName(self,tableName):
        for table in self.tables:
            if table.name == tableName:
                return table
        return None

    def __str__(self):
        tablesStr = "\n".join(map(str,self.tables))
        actionsStr = "\n".join(map(str,self.actions))
        return 'Name: {}\nTables: [{}]\nActions: [{}]'.format(self.name,tablesStr,actionsStr)

class RelationalTable():
    def __init__(self, name, entity, columns, primary_key, uniques, foreign_keys):
        self._name = name
        self._entity = entity
        self._columns = columns
        self._primaryKey = primary_key
        self._uniques = uniques
        self._foreignKeys = foreign_keys

    @property
    def name(self):
        return self._name

    @property
    def entity(self):
        return self._entity

    @property
    def columns(self):
        return self._columns

    @property
    def primaryKey(self):
        return self._primaryKey

    @property
    def uniques(self):
        return self._uniques

    @property
    def foreignKeys(self):
        return self._foreignKeys

    def getForeignKeyByName(self, fkName):
        if self._foreignKeys:
            for fk in self._foreignKeys:
                if fkName == fk.name:
                    return fk
        return None

    def getColumnByName(self, colName):
        if self._columns:
            for col in self._columns:
                if colName == col.name:
                    return col
        return None

    def __str__(self):
        columnsStr = "\n".join(map(str,self.columns))
        uniquesStr = "\n".join(map(str,self.uniques))
        fkStr = "\n".join(map(str,self.foreignKeys))
        return 'Name: {}\nEntity: {}\nColumns: [{}]\nPK: {}\nuniques: [{}]\nFKs: [{}]'.format(self.name,self.entity,columnsStr,self.primaryKey, uniquesStr, fkStr)

class RelationalColumn():
    def __init__(self, column_name, entity_IRI, column_type, position, is_nullable=True):
        self._columnName = column_name
        self._entityIRI = entity_IRI
        self._columnType = column_type
        self._position = position
        self._isNullable = is_nullable

    @property
    def columnName(self):
        return self._columnName

    @property
    def entityIRI(self):
        return self._entityIRI

    @property
    def columnType(self):
        return self._columnType

    @property
    def position(self):
        return self._position

    @property
    def isNullable(self):
        return self._isNullable

    def __str__(self):
        return 'Name: {}\nEntityIRI: {}\nColumnType: {}\nPosition: {}\nNullable: {}'.format(self.columnName,self.entityIRI,self.columnType,self.position, self.isNullable)

class PrimaryKeyConstraint():
    def __init__(self, name, columns):
        self._name = name
        self._columns = columns

    @property
    def name(self):
        return self._name

    @property
    def columns(self):
        return self._columns

    def __str__(self):
        columnsStr = ",".join(map(str,self.columns))
        return 'Name: {}\nColumns: [{}]'.format(self.name,columnsStr)

class UniqueConstraint():
    def __init__(self, name, columns):
        self._name = name
        self._columns = columns

    @property
    def name(self):
        return self._name

    @property
    def columns(self):
        return self._columns

    def __str__(self):
        columnsStr = ",".join(map(str,self.columns))
        return 'Name: {}\nColumns: [{}]'.format(self.name,columnsStr)

class ForeignKeyConstraint():
    def __init__(self, name, src_table, src_columns, tgt_table, tgt_columns):
        self._name = name
        self._srcTable = src_table
        self._srcColumns = src_columns
        self._tgtTable = tgt_table
        self._tgtColumns = tgt_columns

    @property
    def name(self):
        return self._name

    @property
    def srcTable(self):
        return self._srcTable

    @property
    def srcColumns(self):
        return self._srcColumns

    @property
    def tgtTable(self):
        return self._tgtTable

    @property
    def tgtColumns(self):
        return self._tgtColumns

    def __str__(self):
        srcColumnsStr = ",".join(map(str,self.srcColumns))
        tgtColumnsStr = ",".join(map(str,self.tgtColumns))
        return 'Name: {}\nSourceTable: {}\nSourceColumns: [{}]\nTargetTable: {} \nTargetColumns: [{}]'.format(self.name,self.srcTable,srcColumnsStr,self.tgtTable,tgtColumnsStr)

class RelationalTableOriginEntity:
    def __init__(self, full_IRI, short_IRI, entity_type):
        self._fullIRI = full_IRI
        self._shortIRI = short_IRI
        self._entityType = entity_type
        self._entityTypeDescr = EntityType.fromValue(entity_type)

    @property
    def fullIRI(self):
        return self._fullIRI

    @property
    def shortIRI(self):
        return self._shortIRI

    @property
    def entityType(self):
        return self._entityType

    @property
    def entityTypeDescription(self):
        return self._entityTypeDescr

    def __str__(self):
        return 'FullIRI: {} \nShortIRI: {} \nType: {}'.format(self.fullIRI,self.shortIRI,self.entityTypeDescription)

class RelationalTableAction:
    def __init__(self, subject_table, action_type, object_tables):
        self._subjectTable = subject_table
        self._actionType = action_type
        self._objectTables = object_tables

    @property
    def subjectTable(self):
        return self._subjectTable

    @property
    def actionType(self):
        return self._actionType

    @property
    def objectTables(self):
        return self._objectTables

    def __str__(self):
        objectTablesStr = ",".join(map(str,self.objectTables))
        return 'SubjectTable: {} \nActionType: {} \nObjectTables: [{}]'.format(self.subjectTable,self.actionType,objectTablesStr)

@unique
class EntityType(IntEnum_):

    Class=0
    ObjectProperty=1
    DataProperty=2

    @classmethod
    def fromValue(cls, value):
        if value == 0:
            return cls.Class
        if value == 1:
            return cls.ObjectProperty
        if value == 2:
            return cls.DataProperty
        return None

class RestUtils():

    baseUrl = "https://obdatest.dis.uniroma1.it:8080/BlackbirdEndpoint/rest/bbe/{}"
    schemaListResource = "schema"
    actionsBySchemaResource = "schema/{}/table/actions"

    """
    ADD LOGGING TO ALL METHODS, MOVE EXCEPTION HANDLING OUTSIDE
    """

    @staticmethod
    def getAllSchemas(verifySSL=False):
        """
        Return string representation of service response
        :param verifySSL: bool
        :rtype: str
        """
        try:
            resourceUrl = RestUtils.baseUrl.format(RestUtils.schemaListResource)
            response = requests.get(resourceUrl, verify=verifySSL)
            return response.text;
        except requests.exceptions.Timeout as e:
            # Maybe set up for a retry, or continue in a retry loop
            print(e)
        except requests.exceptions.TooManyRedirects as e:
            # Tell the user their URL was bad and try a different one
            print(e)
        except requests.exceptions.RequestException as e:
            # catastrophic error. bail.
            print(e)

    @staticmethod
    def getActionsBySchema(schemaName="", verifySSL=False):
        """
        Return string representation of service response
        :param schemaName: str
        :param verifySSL: bool
        :rtype: str
        """
        try:
            resource = RestUtils.actionsBySchemaResource.format(schemaName)
            resourceUrl = RestUtils.baseUrl.format(resource)
            response = requests.get(resourceUrl, verify=verifySSL)
            return response.text;
        except requests.exceptions.Timeout as e:
            # Maybe set up for a retry, or continue in a retry loop
            print(e)
        except requests.exceptions.TooManyRedirects as e:
            # Tell the user their URL was bad and try a different one
            print(e)
        except requests.exceptions.RequestException as e:
            # catastrophic error. bail.
            print(e)