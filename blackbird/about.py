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

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets
)

# noinspection PyUnresolvedReferences
from eddy.plugins.blackbird.translator import parseBlackbirdInfo


class AboutDialog(QtWidgets.QDialog):
    """
    Blackbird about dialog.
    """
    def __init__(self, plugin, parent=None):
        """
        Initialize the dialog.
        :type parent: QWidget
        """
        super().__init__(parent)
        pixmap = QtGui.QIcon(':/blackbird/images/im_blackbird_logo').pixmap(380 * self.devicePixelRatio())
        pixmap.setDevicePixelRatio(self.devicePixelRatio())
        heading = QtWidgets.QLabel(self)
        heading.setPixmap(pixmap)
        pluginGroup = QtWidgets.QGroupBox('Plugin', self)
        pluginAuthor = plugin.spec.get('plugin', 'author', fallback='-')
        pluginVersion = plugin.spec.get('plugin', 'version')
        authorLabel = QtWidgets.QLabel('Author: {}'.format(pluginAuthor), self)
        versionLabel = QtWidgets.QLabel('Version: {}'.format(pluginVersion), self)
        pluginLayout = QtWidgets.QVBoxLayout(self)
        pluginLayout.setContentsMargins(8, 8, 8, 8)
        pluginLayout.addWidget(authorLabel)
        pluginLayout.addWidget(versionLabel)
        pluginGroup.setLayout(pluginLayout)
        translatorGroup = QtWidgets.QGroupBox('Blackbird Engine', self)
        bbExecutable = os.path.join(plugin.path(), plugin.spec.get('blackbird', 'executable'))
        bbVersion = parseBlackbirdInfo(bbExecutable) or '-'
        bbVersionLabel = QtWidgets.QLabel('Version: {}'.format(bbVersion), self)
        translatorLayout = QtWidgets.QVBoxLayout(self)
        translatorLayout.addWidget(bbVersionLabel)
        translatorGroup.setLayout(translatorLayout)
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addWidget(heading)
        mainLayout.addWidget(pluginGroup)
        mainLayout.addWidget(translatorGroup)
        self.setLayout(mainLayout)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowFlags(QtCore.Qt.Popup | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.plugin = plugin

    #############################################
    #   EVENTS
    #################################

    def mouseReleaseEvent(self, event):
        """
        Close the dialog on mouse click.
        :type event: QMouseEvent
        """
        if event.button() == QtCore.Qt.LeftButton:
            self.hide()

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the Session associated with this dialog (alias for self.parent()).
        :rtype: Session
        """
        return self.plugin.session
