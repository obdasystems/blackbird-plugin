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


import json

from eddy.core.output import getLogger

LOGGER = getLogger()


# TODO: Do we really need this class or can its single method be moved elsewhere?
class FileUtils:
    """
    This class contains a collection of utility methods to deal with JSON files.
    """

    # ADD LOGGING TO ALL METHODS, MOVE EXCEPTION HANDLING OUTSIDE

    @staticmethod
    def parseSchemaFile(filePath):
        """
        Return JSON object representing data in parsed file
        :type filePath: str
        :rtype: json
        """
        with open(filePath, 'r') as myfile:
            data = myfile.read()
        # parse file
        obj = json.loads(data)
        return obj
