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
from eddy.core.functions.misc import rstrip
from eddy.core.regex import RE_CAMEL_SPACE


@unique
class Item(IntEnum_):
    """
    This class defines all the available elements for blackbird diagrams.
    """
    # TABLES
    TableNode = 75537

    # EDGES
    ForeignkeyEdge = 75554

    # EXTRA
    Undefined = 75561

    @property
    def realName(self):
        """
        Returns the item readable name, i.e: attribute node, concept node.
        :rtype: str
        """
        return RE_CAMEL_SPACE.sub(r'\g<1> \g<2>', self.name).lower()

    @property
    def shortName(self):
        """
        Returns the item short name, i.e: attribute, concept.
        :rtype: str
        """
        return rstrip(self.realName, ' node', ' edge')
