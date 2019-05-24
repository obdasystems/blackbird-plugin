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


import re
import zipfile
from io import StringIO

from PyQt5 import QtCore
from eddy.core.functions.misc import first
from eddy.core.functions.path import expandPath

from eddy.core.functions.signals import connect
from eddy.core.output import getLogger

LOGGER = getLogger()


class BlackbirdProcess(QtCore.QProcess):
    """
    Subclass of QProcess that wraps the Blackbird translator executable.
    """
    sgnReady = QtCore.pyqtSignal()

    def __init__(self, path, parent=None):
        """
        Initialize the BlackbirdProcess instance.
        """
        super().__init__(parent)
        self.setProgram('java')
        self.setArguments(['-jar', path])
        self.buffer = StringIO()
        connect(self.readyReadStandardError, self.onStandardErrorReady)
        connect(self.readyReadStandardOutput, self.onStandardOutputReady)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onStandardErrorReady(self):
        """
        Executed when the process emits to standard error.
        """
        output = self.readAllStandardError()
        if output:
            decoded = str(output.data(), encoding='utf-8')
            self.buffer.write(decoded)

    @QtCore.pyqtSlot()
    def onStandardOutputReady(self):
        """
        Executed when the process emits to standard output.
        """
        output = self.readAllStandardOutput()
        if output:
            decoded = str(output.data(), encoding='utf-8')
            self.buffer.write(decoded)


#############################################
#   UTILITY FUNCTIONS
#################################

_RE_POM_FILE = re.compile(r'META-INF/maven/com.obdasystems/.*pom.xml', re.IGNORECASE)


def parseBlackbirdInfo(path):
    """
    Read version information from the Blackbird executable at 'path'.
    :type path: str
    """
    try:
        zf = zipfile.ZipFile(expandPath(path))
        for name in zf.namelist():
            if _RE_POM_FILE.match(name):
                with zf.open(name) as pom:
                    from xml.dom.minidom import parse
                    doc = parse(pom)
                    root = doc.documentElement
                    version = first(root.getElementsByTagName('version')).firstChild.nodeValue
                    return version
        return None
    except Exception as e:
        LOGGER.exception(e)
        return None
