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