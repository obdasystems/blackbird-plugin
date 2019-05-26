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

from eddy import VERSION, APPNAME
from eddy.core.application import main
from eddy.core.output import getLogger
from eddy.core.plugin import PluginManager

LOGGER = getLogger()

if __name__ == '__main__':
    try:
        # SCAN FOR PLUGIN
        PluginManager.scan(os.path.abspath(os.path.normpath(os.path.join(os.curdir, os.pardir))))
        # START EDDY
        LOGGER.info('Starting {} {}'.format(APPNAME, VERSION))
        main()
    except Exception as e:
        LOGGER.exception(e)
