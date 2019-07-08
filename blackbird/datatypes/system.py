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