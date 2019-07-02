from enum import unique

from eddy.core.datatypes.common import IntEnum_


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
