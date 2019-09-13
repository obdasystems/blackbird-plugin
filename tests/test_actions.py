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
Tests for Blackbird plugin actions.
"""

import os
import pytest

from PyQt5 import (
    QtCore
)

from eddy.core.datatypes.graphol import Item
from eddy.core.functions.misc import first
from eddy.core.functions.path import expandPath
from eddy.core.plugin import PluginManager
from eddy.ui.session import Session

basepath = expandPath(os.path.join(os.path.dirname(__file__), os.pardir))


@pytest.fixture
def session(qapp, qtbot, logging_disabled):
    """
    Provide an initialized Session instance.
    """
    with logging_disabled:
        # SCAN FOR PLUGIN
        PluginManager.scan(os.path.abspath(os.path.normpath(os.path.join(os.curdir, os.pardir))))
        # CREATE EDDY SESSION
        session = Session(qapp, expandPath(os.path.join(basepath, 'tests', 'test_books')))
        session.show()
    qtbot.addWidget(session)
    qtbot.waitExposed(session, timeout=3000)
    with qtbot.waitSignal(session.sgnDiagramFocused):
        session.sgnFocusDiagram.emit(session.project.diagram('books'))
    yield session


@pytest.fixture
def plugin(spec, session, qtbot):
    """
    Provide an initialized BlackbirdPlugin instance.
    """
    yield session.plugin(spec.get('plugin', 'id'))


@pytest.fixture(autouse=True)
def auto_diagram_selection(monkeypatch, session):
    """
    Automatically patch DiagramSelectionDialog to make them always return
    the full list of project diagrams without raising the widget.
    """
    from eddy.ui.dialogs import DiagramSelectionDialog
    monkeypatch.setattr(DiagramSelectionDialog, 'exec_', lambda _: True)
    monkeypatch.setattr(DiagramSelectionDialog, 'selectedDiagrams', lambda _: session.project.diagrams())


#############################################
#   SCHEMA GENERATION
#################################

def test_generate_schema_all_diagrams(session, plugin, qtbot):
    # GIVEN
    project = session.project
    view = session.mdi.activeView()
    diagram = session.mdi.activeDiagram()
    node = first(project.predicates(Item.ConceptNode, ':Book', diagram))
    action = plugin.action('generate_schema')
    # WHEN
    try:
        while not plugin.translator.state() == QtCore.QProcess.Running:
            qtbot.wait(100)
        qtbot.wait(2000)
        with qtbot.waitSignal(plugin.sgnSchemaChanged, timeout=5000):
            action.trigger()
        # THEN
        # TODO: complete test assertions
        assert True
    finally:
        if not plugin.translator.state() == QtCore.QProcess.NotRunning:
            plugin.doStopTranslator()
            qtbot.wait(1000)
