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


import os
import re
import signal
import sys
import zipfile
from io import StringIO

from PyQt5 import QtCore
from eddy.core.functions.fsystem import fexists, isdir, fread, fwrite, fremove

from eddy.core.functions.misc import first
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect
from eddy.core.jvm import findJavaHome
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
        javaHome = findJavaHome() or ''
        # Will resort to look for the java executable in PATH
        self.javaExe = 'java' if not sys.platform.startswith('win32') else 'java.exe'
        # If we hava JAVA_HOME set then try to use the bundled java executable
        if isdir(javaHome):
            # For Java <= 1.8 we use the JDK's private jre path,
            # this was done for compatibility with pyjnius that uses
            # that fixes the path to libjvm at compile time.
            if fexists(os.path.join(javaHome, 'jre', 'bin', self.javaExe)):
                self.javaExe = os.path.join(javaHome, 'jre', 'bin', self.javaExe)
            # For java > 1.8 there is no private JRE, so we use the standard path
            elif fexists(os.path.join(javaHome, 'bin', self.javaExe)):
                self.javaExe = os.path.join(javaHome, 'bin', self.javaExe)
            # No java executable under JAVA_HOME so we log an error.
            # We still try to look for java in PATH though
            else:
                LOGGER.error('Unable to locate java executable in JAVA_HOME: {}'.format(javaHome))
        self.setProgram(self.javaExe)
        self.setArguments(['-jar', path])
        self.buffer = StringIO()
        self.runtimeDir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.RuntimeLocation)
        # CHECK FOR PRE-EXISTING FILES TO DEAL WITH ORPHANED PROCESSES
        if isdir(self.runtimeDir) and fexists(os.path.join(self.runtimeDir, 'blackbird.pid')):
            try:
                pid = int(fread(os.path.join(self.runtimeDir, 'blackbird.pid')))
                LOGGER.warning('Found pre-existing Blackbird process running (PID: {})'.format(pid))
                # ATTEMPT TO KILL THE PROCESS
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                # PROCESS WAS ALREADY STOPPED
                pass
            except Exception as e:
                LOGGER.exception(e)
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
        # WRITE PROCESS ID TO FILE
        if isdir(self.runtimeDir):
            try:
                fwrite('{:d}'.format(self.processId()), os.path.join(self.runtimeDir, 'blackbird.pid'))
            except Exception as e:
                LOGGER.error('Failed to write PID to file')
                LOGGER.exception(e)

    @QtCore.pyqtSlot(int, QtCore.QProcess.ExitStatus)
    def onFinished(self, exitCode, exitStatus):
        """
        Executed when the process finishes execution.
        :type exitCode: int
        :type exitStatus: ExitStatus
        """
        if exitStatus != QtCore.QProcess.NormalExit:
            LOGGER.warning('Blackbird Engine terminated abnormally (code: {:d})'.format(exitCode))
        # DELETE PID FILE
        if isdir(self.runtimeDir):
            try:
                fremove(os.path.join(self.runtimeDir, 'blackbird.pid'))
            except Exception:
                pass
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
