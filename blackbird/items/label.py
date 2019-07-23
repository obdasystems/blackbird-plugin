from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from eddy.core.items.nodes.common.label import NodeLabel


class TableNodeLabel(NodeLabel):
    """
    This class implements the label to be attached to the table nodes.
    """
    """
        This class implements the label to be attached to the graphol nodes.
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

        #super().paint(painter, option, widget)

        metrics = QFontMetrics(self.font())
        #TODO CONTROLLA PERCHE' non viene settato parent correttamente (parent()=None sempre)
        if self.parent():
            elided = metrics.elidedText(self.text(), Qt.ElideRight, self.parent().width())
        elif self._parent:
            elided = metrics.elidedText(self.text(), Qt.ElideRight, self._parent.width())
        else:
            elided = metrics.elidedText(self.text(), Qt.ElideRight, self.width())
        painter.drawText(self.boundingRect(), self.alignment(), elided)