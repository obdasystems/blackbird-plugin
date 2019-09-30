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


import urllib
from enum import unique
from json import JSONEncoder

from PyQt5 import (
    QtCore,
    QtNetwork
)

from eddy.core.datatypes.common import Enum_
from eddy.core.output import getLogger
from eddy import ORGANIZATION, APPNAME

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.schema import RelationalTableAction

LOGGER = getLogger()


@unique
class Resources(Enum_):
    Endpoint = 'http://localhost:8080/bbe'
    Schema = '{}/schema'.format(Endpoint)
    SchemaByName = '{}/{}'.format(Schema, '{}')
    SchemaHistoryByName = '{}/history'.format(SchemaByName)
    SchemaApplyActionByName = '{}/action'.format(SchemaByName)
    SchemaUndoByName = '{}/undo'.format(SchemaApplyActionByName)
    SchemaTables = '{}/tables'.format(SchemaByName, '{}')
    SchemaSingleTable = '{}/table/{}'.format(SchemaByName, '{}')
    SchemaSingleTableActions = '{}/actions'.format(SchemaSingleTable)


class NetworkManager(QtNetwork.QNetworkAccessManager):
    """
    Subclass of QNetworkAccessManager used for REST request to the Blackbird API.
    """
    OWL = QtNetwork.QNetworkRequest.Attribute(7001)
    SchemaName = QtNetwork.QNetworkRequest.Attribute(7002)

    def getAllSchemas(self):
        """
        Get the list of schemas from the Blackbird engine.
        :rtype: QNetworkReply
        """
        url = QtCore.QUrl(Resources.Schema.value)
        request = QtNetwork.QNetworkRequest(url)
        reply = self.get(request)
        return reply

    def postSchema(self, owl):
        """
        Post the specified OWL ontology to generate a database schema
        returning the corresponding reply.
        It is responsibility of the caller to delete the reply once
        the processing completes by calling its 'deleteLater()' method.
        :type owl: str
        :rtype: QNetworkReply
        """
        url = QtCore.QUrl(Resources.Schema.value)
        urlQuery = QtCore.QUrlQuery()

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)

        classMergePolicy = settings.value('blackbird/merge/policy/class/INT', "-1", str)
        classMergeDefault = settings.value('blackbird/merge/default/class/INT', "-1", str)
        objPropMergeDefault = settings.value('blackbird/merge/default/objProps/INT', "-1", str)
        dtPropMergeDefault = settings.value('blackbird/merge/default/dataProps/INT', "-1", str)

        urlQuery.addQueryItem("subClassMergeStrategy", classMergePolicy)
        urlQuery.addQueryItem("subClassMergeDefault", classMergeDefault)
        urlQuery.addQueryItem("dataPropertyMergeDefault", dtPropMergeDefault )
        urlQuery.addQueryItem("objectPropertyMergeDefault", objPropMergeDefault)
        url.setQuery(urlQuery)
        request = QtNetwork.QNetworkRequest(url)
        request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, 'text/plain;charset=utf-8')
        request.setAttribute(self.OWL, owl)
        reply = self.post(request, bytes(owl))
        return reply

    def getSchema(self, schemaName):
        """
        Get the schema identified by schemaName
        :type schemaName: str
        :rtype: QNetworkReply
        """
        if not schemaName:
            raise BlackbirdRequestError('Schema name must not be empty')
        url = QtCore.QUrl(Resources.Schema.value.format(schemaName))
        request = QtNetwork.QNetworkRequest(url)
        reply = self.get(request)
        return reply

    def getSchemaHistory(self, schemaName):
        """
        Get the transformation history of schema identified by schemaName
        :type schemaName: str
        :rtype: QNetworkReply
        """
        if not schemaName:
            raise BlackbirdRequestError('Schema name must not be empty')
        url = QtCore.QUrl(Resources.SchemaHistoryByName.value.format(schemaName))
        request = QtNetwork.QNetworkRequest(url)
        reply = self.get(request)
        return reply

    def deleteSchema(self, schemaName):
        """
        Delete the schema identified by schemaName
        :type schemaName: str
        :rtype: QNetworkReply
        """
        if not schemaName:
            raise BlackbirdRequestError('Schema name must not be empty')
        url = QtCore.QUrl(Resources.Schema.value.format(schemaName))
        request = QtNetwork.QNetworkRequest(url)
        reply = self.delete(request)
        return reply

    def putActionToSchema(self, schemaName, action):
        """
        Apply action over the schema identified by schemaName
        :type schemaName: str
        :type action: RelationalTableAction
        :rtype: QNetworkReply
        """
        if not schemaName:
            raise BlackbirdRequestError('Schema name must not be empty')
        if not action:
            raise BlackbirdRequestError('Action must not be empty')
        actionJsonStr = RelationalTableActionDecoder().encode(action)
        encodedSchemaName = self.encodeUrl(schemaName, '')
        url = QtCore.QUrl(Resources.SchemaApplyActionByName.value.format(encodedSchemaName))
        request = QtNetwork.QNetworkRequest(url)
        request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, 'application/json;charset=utf-8')
        byteContent = bytes(actionJsonStr, encoding='utf8')
        reply = self.put(request, byteContent)
        return reply

    def putUndoToSchema(self, schemaName):
        """
        Undo the last action applied over the schema identified by schemaName
        :type schemaName: str
        :rtype: QNetworkReply
        """
        if not schemaName:
            raise BlackbirdRequestError('Schema name must not be empty')
        emptyJsonStr = ''
        encodedSchemaName = self.encodeUrl(schemaName, '')
        url = QtCore.QUrl(Resources.SchemaUndoByName.value.format(encodedSchemaName))
        request = QtNetwork.QNetworkRequest(url)
        request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, 'application/json')
        reply = self.put(request, bytes(emptyJsonStr, encoding='utf8'))
        return reply

    def getTableNames(self, schemaName):
        """
        Get all the names of the tables in the schema identified by schemaName
        :type schemaName: str
        :rtype: QNetworkReply
        """
        if not schemaName:
            raise BlackbirdRequestError('Schema name must not be empty')
        url = QtCore.QUrl(Resources.SchemaTables.value.format(schemaName))
        request = QtNetwork.QNetworkRequest(url)
        reply = self.get(request)
        return reply

    def getTable(self, schemaName, tableName):
        """
        Get the table identified by tableName in the schema identified by schemaName
        :type schemaName: str
        :type tableName: str
        :rtype: QNetworkReply
        """
        if not schemaName:
            raise BlackbirdRequestError('Schema name must not be empty')
        if not tableName:
            raise BlackbirdRequestError('Table name must not be empty')
        url = QtCore.QUrl(Resources.SchemaSingleTable.value.format(schemaName, tableName))
        request = QtNetwork.QNetworkRequest(url)
        reply = self.get(request)
        return reply

    def getActions(self, schemaName, tableName):
        """
        Get the actions that can be applied over the table identified by tableName in the schema identified by schemaName
        :type schemaName: str
        :type tableName: str
        :rtype: QNetworkReply
        """
        if not schemaName:
            raise BlackbirdRequestError('Schema name must not be empty')
        if not tableName:
            raise BlackbirdRequestError('Table name must not be empty')
        url = QtCore.QUrl(Resources.SchemaSingleTableActions.value.format(schemaName, tableName))
        request = QtNetwork.QNetworkRequest(url)
        reply = self.get(request)
        return reply

    def encodeUrl(self, url, safe):
        return urllib.parse.quote(url, safe)


# A specialised JSONEncoder that encodes RelationalTableAction objects as JSON
class RelationalTableActionDecoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, RelationalTableAction):
            return o.__dict__
        else:
            return JSONEncoder.default(self, o)


class BlackbirdRequestError(Exception):
    """
    Raised when an error occurs during a network request.
    """
    pass
