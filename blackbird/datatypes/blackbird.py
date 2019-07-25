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


@unique
class ClassMergeWithClassPolicy(IntEnum_):
    """
    This class list all the available options when merging tables representing classes whith a table representing a class.
    """

    #NO MERGE AT ALL
    NO_MERGE = 10001

    #MERGE BY ADDING FLAG COLUMNS TO TARGET TABLE
    MERGE_FLAGS = 10002

    # MERGE BY ADDING TYPOLOGICAL TABLES TO CONSIDERED SCHEMA
    MERGE_TYPOLOGICAL = 10003

@unique
class ClassMergeWithClassPolicyLabels(IntEnum_):
    """
    This class list the labels associated to all the available options when merging tables representing classes whith a table representing a class.
    """

    #NO MERGE AT ALL
    NO_MERGE = 'No merge'

    #MERGE BY ADDING FLAG COLUMNS TO TARGET TABLE
    MERGE_FLAGS = 'Merge By Flags'

    # MERGE BY ADDING TYPOLOGICAL TABLES TO CONSIDERED SCHEMA
    MERGE_TYPOLOGICAL = 'Merge By Typological'


@unique
class ObjectPropertyMergeWithClassPolicy(IntEnum_):
    """
    This class list all the available options when merging tables representing object properties whith a table representing a class.
    """

    #NO MERGE AT ALL
    NO_MERGE = 20001

    #MERGE THE OBJECT PROPERTIES WITH THE CLASS THEY ARE DEFINED ON
    MERGE_DEFINED = 20002

@unique
class ObjectPropertyMergeWithClassPolicyLabels(IntEnum_):
    """
    This class list the labels associated to all the available options when merging tables representing object properties whith a table representing a class.
    """

    #NO MERGE AT ALL
    NO_MERGE = 'No merge'

    #MERGE THE OBJECT PROPERTIES WITH THE CLASS THEY ARE DEFINED ON
    MERGE_DEFINED = 'Merge Defined'


@unique
class DataPropertyMergeWithClassPolicy(IntEnum_):
    """
    This class list all the available options when merging tables representing data properties whith a table representing a class.
    """

    #NO MERGE AT ALL
    NO_MERGE = 30001

    # MERGE THE DATA PROPERTIES WITH THE CLASS THEY ARE DEFINED BY
    MERGE_DEFINED = 30002

    # MERGE THE DATA PROPERTIES WITH THE CLASS THEY ARE TYPED ON
    MERGE_TYPED = 30003

@unique
class DataPropertyMergeWithClassPolicyLabels(IntEnum_):
    """
    This class list the labels associated to all the available options when merging tables representing data properties whith a table representing a class.
    """

    #NO MERGE AT ALL
    NO_MERGE = 'No merge'

    # MERGE THE DATA PROPERTIES WITH THE CLASS THEY ARE DEFINED BY
    MERGE_DEFINED = 'Merge Defined'

    # MERGE THE DATA PROPERTIES WITH THE CLASS THEY ARE TYPED ON
    MERGE_TYPED = 'Merge Typed'