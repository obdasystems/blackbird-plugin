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

import requests

from PyQt5 import (
    QtCore,
    QtNetwork
)

from eddy.core.datatypes.common import Enum_
from eddy.core.output import getLogger

LOGGER = getLogger()


@unique
class Resources(Enum_):
    Endpoint = 'http://localhost:8080/bbe'
    Schema = '{}/schema'.format(Endpoint)
    SchemaActions = '{}/{}/table/actions'.format(Schema, '{}')


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

    def getSchemaActions(self, schema):
        """
        Get the list of actions for the specified schema.
        :type schema: str
        :rtype: QNetworkReply
        """
        if not schema:
            raise BlackbirdRequestError('Schema name must not be empty')
        url = QtCore.QUrl(Resources.SchemaActions.value.format(schema))
        request = QtNetwork.QNetworkRequest(url)
        request.setAttribute(self.SchemaName, schema)
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
        request = QtNetwork.QNetworkRequest(url)
        request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, 'text/plain;charset=utf-8')
        request.setAttribute(self.OWL, owl)
        reply = self.post(request, bytes(owl))
        return reply


class RestUtils:
    """
    Utility class to deal with REST requests.
    """
    baseUrl = "https://obdatest.dis.uniroma1.it:8080/BlackbirdEndpoint/rest/bbe/{}"
    schemaListResource = "schema"
    actionsBySchemaResource = "schema/{}/table/actions"

    # ADD LOGGING TO ALL METHODS, MOVE EXCEPTION HANDLING OUTSIDE

    @staticmethod
    def getAllSchemas(verifySSL=False):
        """
        Return string representation of service response
        :type verifySSL: bool
        :rtype: str
        """
        try:
            resourceUrl = RestUtils.baseUrl.format(RestUtils.schemaListResource)
            response = requests.get(resourceUrl, verify=verifySSL)
            return response.text
        except requests.exceptions.Timeout as e:
            # Maybe set up for a retry, or continue in a retry loop
            LOGGER.exception(e)
        except requests.exceptions.TooManyRedirects as e:
            # Tell the user their URL was bad and try a different one
            LOGGER.exception(e)
        except requests.exceptions.RequestException as e:
            # catastrophic error. bail.
            LOGGER.exception(e)

    @staticmethod
    def getActionsBySchema(schemaName="", verifySSL=False):
        """
        Return string representation of service response
        :type schemaName: str
        :type verifySSL: bool
        :rtype: str
        """
        try:
            resource = RestUtils.actionsBySchemaResource.format(schemaName)
            resourceUrl = RestUtils.baseUrl.format(resource)
            response = requests.get(resourceUrl, verify=verifySSL)
            return response.text
        except requests.exceptions.Timeout as e:
            # Maybe set up for a retry, or continue in a retry loop
            LOGGER.exception(e)
        except requests.exceptions.TooManyRedirects as e:
            # Tell the user their URL was bad and try a different one
            LOGGER.exception(e)
        except requests.exceptions.RequestException as e:
            # catastrophic error. bail.
            LOGGER.exception(e)


class BlackbirdRequestError(Exception):
    """
    Raised when an error occurs during a network request.
    """
    pass
