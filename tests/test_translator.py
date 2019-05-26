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
import sys
import json
import requests

from PyQt5 import (
    QtCore,
    QtTest,
)
from eddy.core.functions.fsystem import fread

from tests import PluginTest, PluginTestFinder

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.translator import BlackbirdProcess


class TranslatorTest(PluginTest):
    """
    Blackbird translator test case.
    """
    def setUp(self):
        super().setUp()
        self.executable = os.path.join(self.basepath, self.spec.get('blackbird', 'executable'))

    def test_process_start_stop(self):
        # GIVEN
        process = BlackbirdProcess(self.executable)
        readySpy = QtTest.QSignalSpy(process.sgnReady)
        stopSpy = QtTest.QSignalSpy(process.sgnFinished)
        try:
            # WHEN
            process.start()
            # THEN
            self.assertTrue(readySpy.wait())
            self.assertEqual(1, len(readySpy))
            # WHEN
            process.terminate()
            # THEN
            self.assertTrue(stopSpy.wait())
            self.assertEqual(1, len(stopSpy))
        finally:
            if process.state() != QtCore.QProcess.NotRunning:
                process.kill()

    def test_process_translate_owl(self):
        # GIVEN
        process = BlackbirdProcess(self.executable)
        readySpy = QtTest.QSignalSpy(process.sgnReady)
        stopSpy = QtTest.QSignalSpy(process.sgnFinished)
        try:
            # WHEN
            process.start()
            # THEN
            self.assertTrue(readySpy.wait())
            self.assertEqual(1, len(readySpy))
            # WHEN
            owlfile = os.path.join(self.basepath, 'tests', 'test_export_owl_1', 'Diagram2.owl')
            response = requests.post('http://localhost:8080/bbe/schema',
                                     headers={'Content-Type': 'text/plain'},
                                     data=fread(owlfile).encode('utf-8'))
            # THEN
            self.assertEqual(200, response.status_code)
            # AND
            schema = json.loads(response.text, encoding='utf-8')
            self.assertIn('id', schema)
            self.assertIn('schemaName', schema)
            self.assertIn('tables', schema)
            self.assertEqual(3, len(schema['tables']))
            # WHEN
            process.terminate()
            # THEN
            self.assertTrue(stopSpy.wait())
            self.assertEqual(1, len(stopSpy))
        finally:
            if process.state() != QtCore.QProcess.NotRunning:
                process.kill()
