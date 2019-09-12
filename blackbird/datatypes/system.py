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

from eddy.core.datatypes.common import Enum_
from eddy.core.regex import RE_FILE_EXTENSION


@unique
class File(Enum_):
    """
    Enum implementation to deal with file types.
    """
    Blackbird = 'Blackbird (*.blackbird)'

    @classmethod
    def forPath(cls, path):
        """
        Returns the File matching the given path.
        :type path: str
        :rtype: File
        """
        for x in cls:
            if path.endswith(x.extension):
                return x
        return None

    @classmethod
    def forValue(cls, value):
        """
        Returns the File matching the given value.
        :type value: str
        :rtype: File
        """
        for x in cls:
            if x.value == value:
                return x
        return None

    @property
    def extension(self):
        """
        The extension associated with the Enum member.
        :rtype: str
        """
        match = RE_FILE_EXTENSION.match(self.value)
        if match:
            return match.group('extension')
        return None

    def __lt__(self, other):
        """
        Returns True if the current File is "lower" than the given other one.
        :type other: File
        :rtype: bool
        """
        return self.value < other.value

    def __gt__(self, other):
        """
        Returns True if the current File is "greater" than the given other one.
        :type other: File
        :rtype: bool
        """
        return self.value > other.value
