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


from PyQt5 import (
    QtCore,
    QtGui
)

from eddy.core.items.nodes.common.label import NodeLabel


class TableNodeLabel(NodeLabel):
    """
    This class implements the label to be attached to the table nodes.
    """

    def __init__(self, template='', pos=None, movable=True, editable=True, parent=None):
        """
        Initialize the label.
        :type template: str
        :type pos: callable
        :type movable: bool
        :type editable: bool
        :type parent: QObject
        """
        super().__init__(template, pos, movable, editable, parent=parent)

    #############################################
    #   INTERFACE
    #################################

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the diagram.
        :type painter: QPainter
        :type option: QStyleOptionGraphicsItem
        :type widget: QWidget
        """
        # painter = QPainter(self)

        # super().paint(painter, option, widget)

        metrics = QtGui.QFontMetrics(self.font())
        # TODO CONTROLLA PERCHE' non viene settato parent correttamente (parent()=None sempre)
        if self.parent():
            elided = metrics.elidedText(self.text(), QtCore.Qt.ElideRight, self.parent().width())
        elif self._parent:
            elided = metrics.elidedText(self.text(), QtCore.Qt.ElideRight, self._parent.width())
        else:
            elided = metrics.elidedText(self.text(), QtCore.Qt.ElideRight, self.width())
        painter.drawText(self.boundingRect(), self.alignment(), elided)

    def isEdge(self):
        return False

    def isLabel(self):
        return True

    def isNode(self):
        return False
