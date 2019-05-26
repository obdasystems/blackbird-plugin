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
RE_STARTED = re.compile(r'.*-\sStarted\s@(\d+)ms')


class BlackbirdProcess(QtCore.QProcess):
    """
    Subclass of QProcess that wraps the Blackbird translator executable.
    """
    sgnReady = QtCore.pyqtSignal()
    sgnFinished = QtCore.pyqtSignal()
    sgnErrorOccurred = QtCore.pyqtSignal()

    # noinspection PyArgumentList
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
        connect(self.started, self.onStarted)
        connect(self.finished, self.onFinished)
        connect(self.errorOccurred, self.onErrorOccurred)

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
            for line in decoded.splitlines(False):
                match = RE_STARTED.match(line)
                if match:
                    LOGGER.info('Blackbird Engine startup completed in {} ms'.format(match.group(1)))
                    self.sgnReady.emit()
            self.buffer.write(decoded)

    @QtCore.pyqtSlot()
    def onStandardOutputReady(self):
        """
        Executed when the process emits to standard output.
        """
        output = self.readAllStandardOutput()
        if output:
            decoded = str(output.data(), encoding='utf-8')
            for line in decoded.splitlines(False):
                match = RE_STARTED.match(line)
                if match:
                    LOGGER.info('Blackbird Engine startup completed in {} ms'.format(match.group(1)))
                    self.sgnReady.emit()
            self.buffer.write(decoded)

    @QtCore.pyqtSlot()
    def onStarted(self):
        """
        Executed when the process is started.
        """
        LOGGER.info('Blackbird process starting (PID: {})'.format(self.processId()))

    @QtCore.pyqtSlot(int, QtCore.QProcess.ExitStatus)
    def onFinished(self, exitCode, exitStatus):
        """
        Executed when the process finishes execution.
        :type exitCode: int
        :type exitStatus: ExitStatus
        """
        if exitStatus != QtCore.QProcess.NormalExit:
            LOGGER.warning('Blackbird Engine terminated abnormally')
        self.sgnFinished.emit()

    @QtCore.pyqtSlot(QtCore.QProcess.ProcessError)
    def onErrorOccurred(self, error):
        """
        Executed when an error occurs.
        :type error: ProcessError
        """
        LOGGER.error('Error starting Blackbird engine: {}'.format(error))
        if self.state() != QtCore.QProcess.NotRunning:
            self.kill()
        self.sgnErrorOccurred.emit()


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
