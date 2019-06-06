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


"""
Blackbird translator tests.
"""

import os
import json
import pytest

from PyQt5 import (
    QtCore,
    QtNetwork,
)

from eddy.core.functions.fsystem import fread

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.translator import BlackbirdProcess
# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.rest import NetworkManager


@pytest.fixture(scope='module')
def executable(spec):
    """
    Yields the path to the Blackbird executable.
    """
    basepath = os.path.join(os.path.dirname(__file__), os.pardir)
    yield os.path.join(basepath, spec.get('blackbird', 'executable'))


def test_process_start_stop(executable, qtbot):
    # GIVEN
    process = BlackbirdProcess(executable)
    try:
        # WHEN
        with qtbot.waitSignal(process.sgnReady, timeout=3000):
            process.start()
        # THEN
        assert process.state() == QtCore.QProcess.Running
        # WHEN
        with qtbot.waitSignal(process.sgnFinished, timeout=3000):
            process.terminate()
        # THEN
        assert process.state() == QtCore.QProcess.NotRunning
    finally:
        if process.state() != QtCore.QProcess.NotRunning:
            process.kill()


@pytest.mark.parametrize('owlfilename,ntables', [
    ('Diagram1.owl', 3),
    ('Diagram2.owl', 3),
    ('Diagram3.owl', 3),
    ('Diagram4.owl', 3),
    ('Diagram5.owl', 4),
    ('Diagram6.owl', 4),
])
def test_process_translate_owl(executable, qtbot, owlfilename, ntables):
    # GIVEN
    process = BlackbirdProcess(executable)
    nmanager = NetworkManager()
    basepath = os.path.join(os.path.dirname(__file__), os.pardir)
    owlfile = os.path.join(basepath, 'tests', 'test_export_owl_1', owlfilename)
    try:
        # WHEN
        with qtbot.waitSignal(process.sgnReady, timeout=3000):
            process.start()
        # THEN
        assert process.state() == QtCore.QProcess.Running
        # WHEN
        reply = nmanager.postSchema(fread(owlfile).encode('utf-8'))
        with qtbot.waitSignal(reply.finished, timeout=3000):
            pass
        # THEN
        assert reply.error() == QtNetwork.QNetworkReply.NoError
        # AND
        schema = json.loads(str(reply.readAll(), encoding='utf-8'))
        assert 'id' in schema
        assert 'schemaName' in schema
        assert 'tables' in schema
        assert ntables == len(schema['tables'])
        # WHEN
        with qtbot.waitSignal(process.sgnFinished, timeout=3000):
            process.terminate()
        # THEN
        assert process.state() == QtCore.QProcess.NotRunning
    finally:
        if process.state() != QtCore.QProcess.NotRunning:
            process.kill()
