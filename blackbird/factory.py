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


from PyQt5 import (
    QtCore,
    QtWidgets
)

from eddy.core.functions.misc import first


class BBMenuFactory(QtCore.QObject):
    """
    This class can be used to produce diagram items contextual menus.
    """

    def __init__(self, plugin):
        self.plugin = plugin
        super().__init__(self.plugin.session)
        self.customAction = {}
        self.customMenu = {}

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the project loaded in the active session (alias for MenuFactory.session.project).
        :rtype: Project
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the reference to the currently active session (alias for MenuFactory.parent()).
        :return: Session
        """
        return self.parent()

    #############################################
    #   DIAGRAM
    #################################

    # TODO IMPLEMENTA OPPORTUNAMENTE
    def buildDiagramMenu(self, diagram):
        """
        Build and return a QMenu instance for the given diagram.
        :type diagram: Diagram
        :rtype: QMenu
        """
        menu = QtWidgets.QMenu()
        if not self.session.clipboard.empty():
            menu.addAction(self.session.action('paste'))
        menu.addAction(self.session.action('select_all'))
        menu.addSeparator()
        menu.addAction(self.session.action('diagram_properties'))
        self.session.action('diagram_properties').setData(diagram)
        return menu

    #############################################
    #   EDGES
    #################################

    def buildForeignKeyEdgeMenu(self, diagram, edge, pos):
        """
        Build and return a QMenu instance for a generic edge.
        :type diagram: BlackBirdDiagram
        :type edge: AbstractEdge
        :type pos: QPointF
        :rtype: QMenu
        """
        menu = QtWidgets.QMenu()
        breakpoint = edge.breakPointAt(pos)
        if breakpoint is not None:
            action = self.plugin.session.action('remove_breakpoint')
            action.setData((edge, breakpoint))
            menu.addAction(action)
        return menu

    #############################################
    #   NODES
    #################################

    def buildTableNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for a generic node.
        :type diagram: BlackBirdDiagram
        :type node: TableNode
        :rtype: QMenu
        """
        menu = QtWidgets.QMenu()
        tableName = node.relationalTable.name

        menu.addAction(self.plugin.tableNameToDescriptionQtAction[tableName])
        menu.addSeparator()
        if tableName in self.plugin.tableNameToSchemaQtActions:
            tableSchemaQtActions = self.plugin.tableNameToSchemaQtActions[tableName]
            for qtAction in tableSchemaQtActions:
                menu.addAction(qtAction)
        return menu

    #############################################
    #   FACTORY
    #################################

    def create(self, diagram, items, pos=None):
        """
        Build and return a QMenu instance according to the given parameters.
        :type diagram: BlackBirdDiagram
        :type items: T <= list|tuple
        :type pos: QPointF
        :rtype: QMenu
        """
        ## NO ITEM
        if not items:
            return self.buildDiagramMenu(diagram)

        item = first(items)

        ## NODES
        if item.isNode():
            return self.buildTableNodeMenu(diagram, item)

        ## EDGES
        if item.isEdge():
            return self.buildForeignKeyEdgeMenu(diagram, item, pos)

        raise RuntimeError('could not create menu for {0}'.format(item))
