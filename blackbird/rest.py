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


import requests

from eddy.core.output import getLogger

LOGGER = getLogger()


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