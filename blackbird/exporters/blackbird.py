import os

from PyQt5 import QtXml

from eddy.core.exporters.common import AbstractProjectExporter
from eddy.core.functions.misc import postfix
from eddy.core.functions.fsystem import fwrite, mkdir
from eddy.core.output import getLogger
from eddy.core.project import Project

from blackbird.datatypes.blackbird import Item
from blackbird.datatypes.system import File

LOGGER = getLogger()

class BlackBirdProjectExporter(AbstractProjectExporter):
    """
    Extends AbstractProjectExporter with facilities to export the structure of a BlackBird project.
    A BlackBird project is stored in a directory, whose structure is the following:
    -----------------------
    - projectname/
    -   blackbird/
    -       {VERSION}/
    -           projectname_{VERSION}.blackbird     # contains information on the schema
    -   ...
    """

    def __init__(self, project, session=None, schema=None, diagrams=None, version=None):
        """
        Initialize the project exporter.
        :type project: Project
        :type session: Session
        :type session: RelationalSchema
        :type diagrams: list
        :type version: str
        """
        super().__init__(project, session)

        if schema and diagrams:
            self.schema=schema
            self.diagrams = diagrams
        else:
            #TODO extract schema and diagrams from project
            LOGGER.debug("At least one between schema or diagram list is None")
            if not schema:
                LOGGER.debug("Input schema is None")
            if not diagrams:
                LOGGER.debug("Input list of diagrams is None")

        if version:
            self.version = version
        else:
            #TODO extract version (From schema? From input utente? Embedded counter based current project structure?)
            LOGGER.debug("Input version is None")
            self.version = 'Version String'

        self.document = None

    #############################################
    #   MAIN EXPORT
    #################################
    def createDomDocument(self):
        """
        Create the QDomDocument where to store project information.
        """
        self.document = QtXml.QDomDocument()
        instruction = self.document.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8"')
        self.document.appendChild(instruction)
        blackbird = self.document.createElement('blackbird')
        blackbird.setAttribute('version', '1')
        self.document.appendChild(blackbird)

        projectName = self.document.createElement('name')
        projectName.appendChild(self.document.createTextNode('PROJECT NAME'))#TODO Modifica
        projectVersion = self.document.createElement('version')
        projectVersion.appendChild(self.document.createTextNode(self.version))

        blackbird.appendChild(projectName)
        blackbird.appendChild(projectVersion)

    def createSchema(self):
        """
        Create the 'schema' element in the QDomDocument.
        """
        name = self.document.createElement('name')
        name.appendChild(self.document.createTextNode(self.schema.name))

        id = self.document.createElement('id')
        id.appendChild(self.document.createTextNode(self.schema.id))

        tables = self.document.createElement('tables')
        for relTable in self.schema.tables:
            table = self.document.createElement('table')

            tableName = self.document.createElement('name')
            tableName.appendChild(self.document.createTextNode(relTable.name))
            tableId = self.document.createElement('id')
            tableId.appendChild(self.document.createTextNode(relTable.id))

            tableEntity = self.document.createElement('entity')
            tableEntityFullIRI = self.document.createElement('fullIRI')
            tableEntityFullIRI.appendChild(self.document.createTextNode(relTable.entity.fullIRI))
            tableEntityShortIRI = self.document.createElement('shortIRI')
            tableEntityShortIRI.appendChild(self.document.createTextNode(relTable.entity.shortIRI))
            tableEntityType = self.document.createElement('type')
            tableEntityType.appendChild(self.document.createTextNode(relTable.entity.entityType))
            tableEntity.appendChild(tableEntityFullIRI)
            tableEntity.appendChild(tableEntityShortIRI)
            tableEntity.appendChild(tableEntityType)

            columns = self.document.createElement('columns')
            for relColumn in table.columns:
                column = self.document.createElement('column')
                colName = self.document.createElement('name')
                colName.appendChild(self.document.createTextNode(relColumn.columnName))
                colType = self.document.createElement('type')
                colType.appendChild(self.document.createTextNode(relColumn.columnType))

                colPosition = self.document.createElement('position')
                colPosition.appendChild(self.document.createTextNode(relColumn.position))
                colId = self.document.createElement('id')
                colId.appendChild(self.document.createTextNode(relColumn.id))
                colNullable = self.document.createElement('nullable')
                colNullable.appendChild(self.document.createTextNode(relColumn.isNullable))

                colEntity = self.document.createElement('entity')
                colEntityFullIRI = self.document.createElement('fullIRI')
                colEntityFullIRI.appendChild(self.document.createTextNode(relColumn.entityIRI.fullIRI))
                colEntityShortIRI = self.document.createElement('shortIRI')
                colEntityShortIRI.appendChild(self.document.createTextNode(relColumn.entityIRI.shortIRI))
                colEntityType = self.document.createElement('type')
                colEntityType.appendChild(self.document.createTextNode(relColumn.entityIRI.entityType))

                column.appendChild(colName)
                column.appendChild(colType)
                column.appendChild(colPosition)
                column.appendChild(colId)
                column.appendChild(colNullable)
                column.appendChild(colEntity)
                columns.appendChild(column)

            pk = self.document.createElement('primaryKey')
            if relTable.primaryKey:
                pkName = self.document.createElement('name')
                pkName.appendChild(self.document.createTextNode(relTable.primaryKey.name))
                pkColumns = self.document.createElement('columns')
                for pkCol in relTable.primaryKey.columns:
                    pkColumn = self.document.createElement('column')
                    pkColumn.appendChild(self.document.createTextNode(pkCol.columnName))
                    pkColumns.appendChild(pkColumn)
                pk.appendChild(pkName)
                pk.appendChild(pkColumns)

            uniques = self.document.createElement('uniques')
            for relUnique in relTable.uniques:
                unique = self.document.createElement('unique')
                uniqueName = self.document.createElement('name')
                uniqueName.appendChild(self.document.createTextNode(relUnique.name))
                uniqueColumns = self.document.createElement('columns')
                for uniqueCol in relUnique.columns:
                    uniqueColumn = self.document.createElement('column')
                    uniqueColumn.appendChild(self.document.createTextNode(uniqueCol.columnName))
                    uniqueColumns.appendChild(uniqueColumn)
                unique.appendChild(uniqueName)
                unique.appendChild(uniqueColumns)
                uniques.appendChild(unique)

            fks = self.document.createElement('foreignKeys')
            for relFK in relTable.foreignKeys:
                fk = self.document.createElement('foreignKey')
                fkName = self.document.createElement('name')
                fkName.appendChild(self.document.createTextNode(relFK.name))
                fkSrc = self.document.createElement('source')
                fkSrcTable = self.document.createElement('table')
                fkSrcTable.appendChild(self.document.createTextNode(relFK.srcTable))
                fkSrcColumns = self.document.createElement('columns')
                for relColumn in fk.srcColumns:
                    fkSrcColumn = self.document.createElement('column')
                    fkSrcColumn.appendChild(self.document.createTextNode(relColumn))
                    fkSrcColumns.appendChild(fkSrcColumn)
                fkSrc.appendChild(fkSrcTable)
                fkSrc.appendChild(fkSrcColumns)

                fkTgt = self.document.createElement('target')
                fkTgtTable = self.document.createElement('table')
                fkTgtTable.appendChild(self.document.createTextNode(relFK.tgtTable))
                fkTgtColumns = self.document.createElement('columns')
                for relColumn in fk.tgtColumns:
                    fkTgtColumn = self.document.createElement('column')
                    fkTgtColumn.appendChild(self.document.createTextNode(relColumn))
                    fkTgtColumns.appendChild(fkTgtColumn)
                fkTgt.appendChild(fkTgtTable)
                fkTgt.appendChild(fkTgtColumns)

                fkAxiomType = self.document.createElement('axiomType')
                fkAxiomType.appendChild(self.document.createTextNode(relFK.axiomType))

                fk.appendChild(fkName)
                fk.appendChild(fkSrc)
                fk.appendChild(fkTgt)
                fk.appendChild(fkAxiomType)
                fks.appendChild(fk)

            actions = self.document.createElement('actions')
            for relAction in relTable.actions:
                action = self.document.createElement('action')
                subjTable = self.document.createElement('subject')
                subjTable.appendChild(self.document.createTextNode(relAction.actionSubjectTableName))
                type = self.document.createElement('type')
                type.appendChild(self.document.createTextNode(relAction.actionType))
                objTables = self.document.createElement('objects')
                for relObjTable in relTable.actionObjectsNames:
                    objTable = self.document.createElement('object')
                    objTable.appendChild(self.document.createTextNode(relObjTable))
                    objTables.appendChild(objTable)
                action.appendChild(subjTable)
                action.appendChild(type)
                action.appendChild(objTables)
                actions.appendChild(action)

            table.appendChild(tableName)
            table.appendChild(tableId)
            table.appendChild(tableEntity)
            table.appendChild(columns)
            table.appendChild(pk)
            table.appendChild(uniques)
            table.appendChild(fks)
            table.appendChild(actions)
            tables.appendChild(table)

        section = self.document.createElement('schema')

        section.appendChild(name)
        section.appendChild(id)
        section.appendChild(tables)

        self.document.documentElement().appendChild(section)



    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :return: File
        """
        return File.Blackbird

    def run(self, *args, **kwargs):
        """
        Perform Project export to disk.
        """
        self.createDomDocument()
        self.createSchema()
        #self.createPredicatesMeta()
        #self.createDiagrams()
        #self.createProjectFile()