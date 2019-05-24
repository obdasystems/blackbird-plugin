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


from PyQt5 import QtCore

from eddy.core.datatypes.graphol import Item
from eddy.core.functions.misc import first
from eddy.core.output import getLogger

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import EntityType

LOGGER = getLogger()

class SchemaToDiagramElements(QtCore.QObject):

    # noinspection PyArgumentList
    def __init__(self, relational_schema, session=None, **kwargs):
        super().__init__(session, **kwargs)
        self._relationalSchema = relational_schema

    @property
    def session(self):
        return self.parent()

    def getType(self, value):
        type = EntityType.fromValue(value)
        if type == EntityType.Class:
            return 4


class ForeignKeyVisualElements:
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
    def inners(self):
        return self._inners

    @property
    def edges(self):
        return self._edges

    def __repr__(self):
        edgesStr = '['
        for edge in self.edges:
            edgesStr += ' ({}) '.format(str(edge))
        edgesStr += ']'
        innersStr = 'EMPTY'
        if self.inners:
            innersStr = '['
            for inner in self.inners:
                innersStr += ' ({}) '.format(str(inner))
            innersStr += ']'
        return 'VE(src:({}); edges:{}; inners:{}; tgt:({}))'.format(str(self.src), edgesStr, innersStr, str(self.tgt))

    def __str__(self):
        edgesStr = '['
        for edge in self.edges:
            edgesStr += ' ' + edge.id
        edgesStr += ']'
        innersStr = 'EMPTY'
        if self.inners:
            innersStr = '['
            for inner in self.inners:
                innersStr += ' ' + inner.id
            innersStr += ']'
        return 'VE(src:{}; edges:{}; inners:{}; tgt:{})'.format(self.src.id, edgesStr, innersStr, self.tgt.id)


class BlackbirdOntologyEntityManager(QtCore.QObject):
    """
    Initialize the manager.

    :type relational_schema: RelationalSchema
    :type parent: Project
    """

    # noinspection PyArgumentList
    def __init__(self, relational_schema, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._parent = parent
        self._ontologyDiagrams = parent.diagrams()
        self._relationalSchema = relational_schema
        self._tables = relational_schema.tables
        self._foreignKeys = relational_schema.foreignKeys

        self._diagramToTables = {}
        self._diagramToForeignKeys = {}
        self.buildDictionaries()

    @property
    def diagramToTables(self):
        return self._diagramToTables

    @property
    def diagramToForeignKeys(self):
        return self._diagramToForeignKeys

    def buildDictionaries(self):
        LOGGER.info('########## Starting mapping schema objects to diagrams\' visual elements ##########')
        for ontDiagram in self._ontologyDiagrams:
            LOGGER.debug('\n##### DIAGRAM {} #####'.format(ontDiagram.name))
            currDiagramToTableDict = {}
            LOGGER.info('### TABLES ###'.format(ontDiagram.name))
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
                            nodeShortIRI = node.text().replace("\n", "")
                            if nodeShortIRI == entityShortIRI:
                                currList.append(node)
                elif entityType == EntityType.ObjectProperty:
                    for node in nodes:
                        if node.Type == Item.RoleNode:
                            nodeShortIRI = node.text().replace("\n", "")
                            if nodeShortIRI == entityShortIRI:
                                currList.append(node)
                elif entityType == EntityType.DataProperty:
                    for node in nodes:
                        if node.Type == Item.AttributeNode:
                            nodeShortIRI = node.text().replace("\n", "")
                            if nodeShortIRI == entityShortIRI:
                                currList.append(node)
                if len(currList) > 0:
                    currDiagramToTableDict[table] = currList
                    tablesStr = ",".join(map(str, currList))
                    LOGGER.info('{} --> [{}]'.format(table.name,tablesStr))
            self._diagramToTables[ontDiagram] = currDiagramToTableDict

            LOGGER.info('### FOREIGN KEYS ###'.format(ontDiagram.name))
            currDiagramToForeignKeyDict = {}
            for fk in self._foreignKeys:
                LOGGER.debug('## Mapping fk {}'.format(fk.name))
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
                    if len(srcColumnNames) == 1:
                        if srcEntityType == EntityType.Class:
                            if tgtEntityType == EntityType.Class:
                                currVisualEls.append(self.getEntityIsaEntityVEs(srcOccurrencesInDiagram,
                                                                                tgtOccurrencesInDiagram,
                                                                                ontDiagram))
                            elif tgtEntityType == EntityType.ObjectProperty:
                                tgtColumnName = first(tgtColumnNames)
                                relColumn = tgtTable.getColumnByName(tgtColumnName)
                                relcolPos = relColumn.position
                                if relcolPos == 1:
                                    currVisualEls.append(
                                        self.getClassIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                tgtOccurrencesInDiagram,
                                                                                ontDiagram))
                                elif relcolPos == 2:
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
                        elif srcEntityType == EntityType.ObjectProperty:
                            srcColumnName = first(srcColumnNames)
                            srcRelColumn = srcTable.getColumnByName(srcColumnName)
                            srcRelcolPos = srcRelColumn.position
                            if tgtEntityType == EntityType.Class:
                                if srcRelcolPos == 1:
                                    currVisualEls.append(
                                        self.getExistRoleOrAttributeIsaClassVEs(srcOccurrencesInDiagram,
                                                                                tgtOccurrencesInDiagram, ontDiagram))
                                elif srcRelcolPos == 2:
                                    currVisualEls.append(self.getExistRoleInvIsaClassVEs(srcOccurrencesInDiagram,
                                                                                         tgtOccurrencesInDiagram,
                                                                                         ontDiagram))
                            elif tgtEntityType == EntityType.ObjectProperty:
                                tgtColumnName = first(tgtColumnNames)
                                tgtRelColumn = tgtTable.getColumnByName(tgtColumnName)
                                tgtRelcolPos = tgtRelColumn.position
                                if srcRelcolPos == 1 and tgtRelcolPos == 1:
                                    currVisualEls.append(
                                        self.getExistRoleOrAttributeIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                               tgtOccurrencesInDiagram,
                                                                                               ontDiagram))
                                elif srcRelcolPos == 1 and tgtRelcolPos == 2:
                                    currVisualEls.append(
                                        self.getExistRoleOrAttributeIsaExistRoleInvVEs(srcOccurrencesInDiagram,
                                                                                       tgtOccurrencesInDiagram,
                                                                                       ontDiagram))
                                elif srcRelcolPos == 2 and tgtRelcolPos == 1:
                                    currVisualEls.append(
                                        self.getExistRoleInvIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                       tgtOccurrencesInDiagram,
                                                                                       ontDiagram))
                                elif srcRelcolPos == 2 and tgtRelcolPos == 2:
                                    currVisualEls.append(self.getExistRoleInvIsaExistRoleInvVEs(srcOccurrencesInDiagram,
                                                                                                tgtOccurrencesInDiagram,
                                                                                                ontDiagram))
                            elif tgtEntityType == EntityType.DataProperty:
                                if srcRelcolPos == 1:
                                    currVisualEls.append(
                                        self.getExistRoleOrAttributeIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                               tgtOccurrencesInDiagram,
                                                                                               ontDiagram))
                                elif srcRelcolPos == 2:
                                    currVisualEls.append(
                                        self.getExistRoleInvIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                       tgtOccurrencesInDiagram,
                                                                                       ontDiagram))
                        elif srcEntityType == EntityType.DataProperty:
                            if tgtEntityType == EntityType.Class:
                                currVisualEls.append(self.getExistRoleOrAttributeIsaClassVEs(srcOccurrencesInDiagram,
                                                                                             tgtOccurrencesInDiagram,
                                                                                             ontDiagram))
                            elif tgtEntityType == EntityType.ObjectProperty:
                                tgtColumnName = first(tgtColumnNames)
                                tgtRelColumn = tgtTable.getColumnByName(tgtColumnName)
                                tgtRelcolPos = tgtRelColumn.position
                                if tgtRelcolPos == 1:
                                    currVisualEls.append(
                                        self.getExistRoleOrAttributeIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                               tgtOccurrencesInDiagram,
                                                                                               ontDiagram))
                                elif tgtRelcolPos == 2:
                                    currVisualEls.append(
                                        self.getExistRoleOrAttributeIsaExistRoleInvVEs(srcOccurrencesInDiagram,
                                                                                       tgtOccurrencesInDiagram,
                                                                                       ontDiagram))
                            elif tgtEntityType == EntityType.DataProperty:
                                currVisualEls.append(
                                    self.getExistRoleOrAttributeIsaExistRoleOrAttributeVEs(srcOccurrencesInDiagram,
                                                                                           tgtOccurrencesInDiagram,
                                                                                           ontDiagram))
                    elif len(srcColumnNames) == 2:
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
                        currDiagramToForeignKeyDict[fk] = currVisualEls
                        fksStr = ",".join(map(str, currVisualEls))
                        LOGGER.info('{} --> [{}]'.format(fk.name, fksStr))
            self._diagramToForeignKeys[ontDiagram] = currDiagramToForeignKeyDict

    # A-->B, R-->P, U1-->U2
    def getEntityIsaEntityVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        LOGGER.debug('Call to getEntityIsaEntityVEs')
        result = list()
        edges = ontDiagram.edges
        for edge in edges:
            firstSrc = edge.source
            firstTgt = edge.target
            if edge.type == Item.InclusionEdge or edge.type == Item.EquivalenceEdge:
                if firstSrc in srcOccurrencesInDiagram and firstTgt in tgtOccurrencesInDiagram:
                    currVE = ForeignKeyVisualElements(firstSrc, firstTgt, [edge])
                    result.append(currVE)
            elif edge.type == Item.InputEdge:
                if firstSrc in srcOccurrencesInDiagram and (
                        firstTgt.type() == Item.UnionNode or firstTgt.type() == Item.DisjointUnionNode):
                    for secondEdge in firstTgt.edges:
                        secondSrc = secondEdge.source
                        secondTgt = secondEdge.target
                        if secondSrc == firstTgt and secondTgt in tgtOccurrencesInDiagram:
                            currVE = ForeignKeyVisualElements(firstSrc, secondTgt, [edge, secondEdge], [firstTgt])
                            result.append(currVE)
        return result

    # A-->exist(R) , A-->exist(U)
    def getClassIsaExistRoleOrAttributeVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        LOGGER.debug('Call to getClassIsaExistRoleOrAttributeVEs')
        result = list()
        edges = ontDiagram.edges
        for edge in edges:
            if edge.type() == Item.InclusionEdge or edge.type() == Item.EquivalenceEdge:
                currSrc = edge.source
                currRestrTgt = edge.target
                if currSrc in srcOccurrencesInDiagram and currRestrTgt.type() is Item.DomainRestrictionNode:
                    for innerEdge in edges:
                        if innerEdge.type() == Item.InputEdge:
                            innerSrc = innerEdge.source
                            innerTgt = innerEdge.target
                            if innerSrc in tgtOccurrencesInDiagram and innerTgt == currRestrTgt:
                                currVE = ForeignKeyVisualElements(currSrc, innerSrc, [edge, innerEdge], [currRestrTgt])
                                result.append(currVE)
        return result

    # exist(R)-->A , exist(U)-->A
    def getExistRoleOrAttributeIsaClassVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        LOGGER.debug('Call to getExistRoleOrAttributeIsaClassVEs')
        result = list()
        edges = ontDiagram.edges
        for edge in edges:
            if edge.type() == Item.InputEdge:
                currSrc = edge.source
                currRestrTgt = edge.target
                if currSrc in srcOccurrencesInDiagram and currRestrTgt.type() is Item.DomainRestrictionNode:
                    for innerEdge in edges:
                        if innerEdge.type() == Item.InclusionEdge or innerEdge.type() == Item.EquivalenceEdge:
                            innerSrc = innerEdge.source
                            innerTgt = innerEdge.target
                            if innerTgt in tgtOccurrencesInDiagram and innerSrc == currRestrTgt:
                                currVE = ForeignKeyVisualElements(currSrc, innerTgt, [edge, innerEdge], [currRestrTgt])
                                result.append(currVE)
        return result

    # exist(R)-->exist(P), exist(R)-->exist(U), exist(U)-->exist(R), exist(U1)-->exist(U2)
    def getExistRoleOrAttributeIsaExistRoleOrAttributeVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram,
                                                          ontDiagram):
        LOGGER.debug('Call to getExistRoleOrAttributeIsaExistRoleOrAttributeVEs')
        result = list()
        edges = ontDiagram.edges
        for firstEdge in edges:
            if firstEdge.type() == Item.InputEdge:
                firstSrc = firstEdge.source
                firstTgt = firstEdge.target
                if firstSrc in srcOccurrencesInDiagram and firstTgt is Item.DomainRestrictionNode:
                    for secondEdge in edges:
                        if secondEdge.type() == Item.InclusionEdge or secondEdge.type() == Item.EquivalenceEdge:
                            secondSrc = secondEdge.source
                            secondTgt = secondEdge.target
                            if secondSrc == firstTgt and secondTgt is Item.DomainRestrictionNode:
                                for thirdEdge in edges:
                                    if thirdEdge.type() == Item.InputEdge:
                                        thirdSrc = thirdEdge.source
                                        thirdTgt = thirdEdge.target
                                        if thirdTgt == secondTgt and thirdSrc in tgtOccurrencesInDiagram:
                                            currVE = ForeignKeyVisualElements(firstSrc, thirdSrc,
                                                                              [firstEdge, secondEdge, thirdEdge],
                                                                              [firstTgt, secondTgt])
                                            result.append(currVE)
        return result

    # exist(inv(R))-->exist(P), exist(inv(R))-->exist(U)
    def getExistRoleInvIsaExistRoleOrAttributeVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        LOGGER.debug('Call to getExistRoleInvIsaExistRoleOrAttributeVEs')
        result = list()
        edges = ontDiagram.edges
        for firstEdge in edges:
            if firstEdge.type() == Item.InputEdge:
                firstSrc = firstEdge.source
                firstTgt = firstEdge.target
                if firstSrc in srcOccurrencesInDiagram and firstTgt is Item.RangeRestrictionNode:
                    for secondEdge in edges:
                        if secondEdge.type() == Item.InclusionEdge or secondEdge.type() == Item.EquivalenceEdge:
                            secondSrc = secondEdge.source
                            secondTgt = secondEdge.target
                            if secondSrc == firstTgt and secondTgt is Item.DomainRestrictionNode:
                                for thirdEdge in edges:
                                    if thirdEdge.type() == Item.InputEdge:
                                        thirdSrc = thirdEdge.source
                                        thirdTgt = thirdEdge.target
                                        if thirdTgt == secondTgt and thirdSrc in tgtOccurrencesInDiagram:
                                            currVE = ForeignKeyVisualElements(firstSrc, thirdSrc,
                                                                              [firstEdge, secondEdge, thirdEdge],
                                                                              [firstTgt, secondTgt])
                                            result.append(currVE)
        return result

    # exist(inv(R))-->exist(inv(P))
    def getExistRoleInvIsaExistRoleInvVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        LOGGER.debug('Call to getExistRoleInvIsaExistRoleInvVEs')
        result = list()
        edges = ontDiagram.edges
        for firstEdge in edges:
            if firstEdge.type() == Item.InputEdge:
                firstSrc = firstEdge.source
                firstTgt = firstEdge.target
                if firstSrc in srcOccurrencesInDiagram and firstTgt is Item.RangeRestrictionNode:
                    for secondEdge in edges:
                        if secondEdge.type() == Item.InclusionEdge or secondEdge.type() == Item.EquivalenceEdge:
                            secondSrc = secondEdge.source
                            secondTgt = secondEdge.target
                            if secondSrc == firstTgt and secondTgt is Item.RangeRestrictionNode:
                                for thirdEdge in edges:
                                    if thirdEdge.type() == Item.InputEdge:
                                        thirdSrc = thirdEdge.source
                                        thirdTgt = thirdEdge.target
                                        if thirdTgt == secondTgt and thirdSrc in tgtOccurrencesInDiagram:
                                            currVE = ForeignKeyVisualElements(firstSrc, thirdSrc,
                                                                              [firstEdge, secondEdge, thirdEdge],
                                                                              [firstTgt, secondTgt])
                                            result.append(currVE)
        return result

    # exist(R)-->exist(inv(P)), exist(U)-->exist(inv(P))
    def getExistRoleOrAttributeIsaExistRoleInvVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        LOGGER.debug('Call to getExistRoleOrAttributeIsaExistRoleInvVEs')
        result = list()
        edges = ontDiagram.edges
        for firstEdge in edges:
            if firstEdge.type() == Item.InputEdge:
                firstSrc = firstEdge.source
                firstTgt = firstEdge.target
                if firstSrc in srcOccurrencesInDiagram and firstTgt is Item.DomainRestrictionNode:
                    for secondEdge in edges:
                        if secondEdge.type() == Item.InclusionEdge or secondEdge.type() == Item.EquivalenceEdge:
                            secondSrc = secondEdge.source
                            secondTgt = secondEdge.target
                            if secondSrc == firstTgt and secondTgt is Item.RangeRestrictionNode:
                                for thirdEdge in edges:
                                    if thirdEdge.type() == Item.InputEdge:
                                        thirdSrc = thirdEdge.source
                                        thirdTgt = thirdEdge.target
                                        if thirdTgt == secondTgt and thirdSrc in tgtOccurrencesInDiagram:
                                            currVE = ForeignKeyVisualElements(firstSrc, thirdSrc,
                                                                              [firstEdge, secondEdge, thirdEdge],
                                                                              [firstTgt, secondTgt])
                                            result.append(currVE)

    # A-->exist(inv(R))
    def getClassIsaExistRoleInvVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        LOGGER.debug('Call to getClassIsaExistRoleInvVEs')
        result = list()
        edges = ontDiagram.edges
        for edge in edges:
            if edge.type() == Item.InclusionEdge or edge.type() == Item.EquivalenceEdge:
                currSrc = edge.source
                currRestrTgt = edge.target
                if currSrc in srcOccurrencesInDiagram and currRestrTgt.type() is Item.RangeRestrictionNode:
                    for innerEdge in edges:
                        if innerEdge.type() == Item.InputEdge:
                            innerSrc = innerEdge.source
                            innerTgt = innerEdge.target
                            if innerSrc in tgtOccurrencesInDiagram and innerTgt == currRestrTgt:
                                currVE = ForeignKeyVisualElements(currSrc, innerSrc, [edge, innerEdge], [currRestrTgt])
                                result.append(currVE)
        return result

    # exist(inv(R))-->A
    def getExistRoleInvIsaClassVEs(self, srcOccurrencesInDiagram, tgtOccurrencesInDiagram, ontDiagram):
        LOGGER.debug('Call to getExistRoleInvIsaClassVEs')
        result = list()
        edges = ontDiagram.edges
        for edge in edges:
            if edge.type() == Item.InputEdge:
                currSrc = edge.source
                currRestrTgt = edge.target
                if currSrc in srcOccurrencesInDiagram and currRestrTgt.type() is Item.RangeRestrictionNode:
                    for innerEdge in edges:
                        if innerEdge.type() == Item.InclusionEdge or innerEdge.type() == Item.EquivalenceEdge:
                            innerSrc = innerEdge.source
                            innerTgt = innerEdge.target
                            if innerTgt in tgtOccurrencesInDiagram and innerSrc == currRestrTgt:
                                currVE = ForeignKeyVisualElements(currSrc, innerTgt, [edge, innerEdge], [currRestrTgt])
                                result.append(currVE)
        return result