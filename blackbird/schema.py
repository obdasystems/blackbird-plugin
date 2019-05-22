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


from enum import unique

from eddy.core.datatypes.common import IntEnum_


@unique
class EntityType(IntEnum_):
    """
    Enumeration of all possible entity types that can correspond to a relational table.
    """
    Class = 0
    ObjectProperty = 1
    DataProperty = 2

    @classmethod
    def fromValue(cls, value):
        if value == 0:
            return cls.Class
        if value == 1:
            return cls.ObjectProperty
        if value == 2:
            return cls.DataProperty
        return None


class RelationalSchemaParser:
    # _instance = None
    #
    # def __new__(cls, *args, **kwargs):
    #    if not cls._instance:
    #           cls._instance = object.__new__(cls)
    #       return cls._instance

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
            action = RelationalTableAction(subjectName, actionType, objectsNames)
            actions.append(action)
        return RelationalSchema(schemaName, tables, actions)

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
        return RelationalTable(tableName, entity, columns, primaryKey, uniques, foreignKeys)

    @staticmethod
    def getColumn(jsonColumn):
        columnName = jsonColumn["columnName"]
        entityIRI = jsonColumn["entityIRI"]
        columnType = jsonColumn["columnType"]
        position = jsonColumn["position"]
        nullable = jsonColumn["nullable"]
        return RelationalColumn(columnName, entityIRI, columnType, position, nullable)

    @staticmethod
    def getOriginEntity(jsonEntity):
        fullIRI = jsonEntity["entityFullIRI"]
        shortIRI = jsonEntity["entityShortIRI"]
        entityType = jsonEntity["entityType"]
        return RelationalTableOriginEntity(fullIRI, shortIRI, entityType)

    @staticmethod
    def getPrimaryKey(jsonPK):
        pkName = jsonPK["pkName"]
        columnNames = jsonPK["columnNames"]
        return PrimaryKeyConstraint(pkName, columnNames)

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
        return ForeignKeyConstraint(fkName, srcTableName, srcColumnNames, tgtTableName, tgtColumnNames)


class RelationalSchema:
    def __init__(self, name, tables, actions):
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

    def getTableByName(self, tableName):
        for table in self.tables:
            if table.name == tableName:
                return table
        return None

    def __str__(self):
        tablesStr = "\n".join(map(str, self.tables))
        actionsStr = "\n".join(map(str, self.actions))
        return 'Name: {}\nTables: [{}]\nActions: [{}]'.format(self.name, tablesStr, actionsStr)


class RelationalTable:
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
        columnsStr = "\n".join(map(str, self.columns))
        uniquesStr = "\n".join(map(str, self.uniques))
        fkStr = "\n".join(map(str, self.foreignKeys))
        return 'Name: {}\nEntity: {}\nColumns: [{}]\n' \
               'PK: {}\nuniques: [{}]\nFKs: [{}]'.format(self.name, self.entity, columnsStr,
                                                         self.primaryKey, uniquesStr, fkStr)


class RelationalColumn:
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
        return 'Name: {}\nEntityIRI: {}\nColumnType: {}\n' \
               'Position: {}\nNullable: {}'.format(self.columnName, self.entityIRI, self.columnType,
                                                   self.position, self.isNullable)


class PrimaryKeyConstraint:
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
        columnsStr = ",".join(map(str, self.columns))
        return 'Name: {}\nColumns: [{}]'.format(self.name, columnsStr)


class UniqueConstraint:
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
        columnsStr = ",".join(map(str, self.columns))
        return 'Name: {}\nColumns: [{}]'.format(self.name, columnsStr)


class ForeignKeyConstraint:
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
        srcColumnsStr = ",".join(map(str, self.srcColumns))
        tgtColumnsStr = ",".join(map(str, self.tgtColumns))
        return 'Name: {}\nSourceTable: {}\nSourceColumns: [{}]\n' \
               'TargetTable: {} \nTargetColumns: [{}]'.format(self.name, self.srcTable, srcColumnsStr,
                                                              self.tgtTable, tgtColumnsStr)


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
        return 'FullIRI: {} \nShortIRI: {} \nType: {}'.format(self.fullIRI, self.shortIRI, self.entityTypeDescription)


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
        objectTablesStr = ",".join(map(str, self.objectTables))
        return 'SubjectTable: {} \nActionType: {} \n' \
               'ObjectTables: [{}]'.format(self.subjectTable, self.actionType, objectTablesStr)