# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <danielepantaleone@me.com>      #
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
#  #####################                          #####################  #
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from enum import unique

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets
)

from eddy import ORGANIZATION, APPNAME
from eddy.core.common import HasWidgetSystem
from eddy.core.datatypes.common import IntEnum_, Enum_
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect
from eddy.ui.fields import ComboBox



@unique
class ClassMergeWithClassDefaultLabels(Enum_):
    """
    This class list the labels associated to all the available options when merging tables representing classes whith a table representing a class.
    """

    # NO MERGE AT ALL
    NO_MERGE = 'No merge'

    # MERGE BY ADDING FLAG COLUMNS TO TARGET TABLE
    MERGE_SUB_CLASSES = 'Merge Subclass Hierarchies'

    @staticmethod
    def getIntValue(label):
        if label==ClassMergeWithClassDefaultLabels.NO_MERGE.value:
            return 0
        elif label==ClassMergeWithClassDefaultLabels.MERGE_SUB_CLASSES.value:
            return 1
        return -1

@unique
class ClassMergeWithClassPolicyLabels(Enum_):
    """
    This class list the labels associated to all the available options when merging tables representing classes whith a table representing a class.
    """

    # MERGE BY ADDING FLAG COLUMNS TO TARGET TABLE
    MERGE_FLAGS = 'Merge By Flags'

    # MERGE BY ADDING TYPOLOGICAL TABLES TO CONSIDERED SCHEMA
    MERGE_TYPOLOGICAL = 'Merge By Typological'

    @staticmethod
    def getIntValue(label):
        if label==ClassMergeWithClassPolicyLabels.MERGE_FLAGS.value:
            return 0
        elif label==ClassMergeWithClassPolicyLabels.MERGE_TYPOLOGICAL.value:
            return 1
        return -1


@unique
class ObjectPropertyMergeWithClassDefaultLabels(Enum_):
    """
    This class list the labels associated to all the available options when merging tables representing object properties whith a table representing a class.
    """

    # NO MERGE AT ALL
    NO_MERGE = 'No merge'

    # MERGE THE OBJECT PROPERTIES WITH THE CLASS THEY ARE DEFINED ON
    MERGE_DEFINED = 'Merge Defined'

    @staticmethod
    def getIntValue(label):
        if label==ObjectPropertyMergeWithClassDefaultLabels.NO_MERGE.value:
            return 0
        elif label==ObjectPropertyMergeWithClassDefaultLabels.MERGE_DEFINED.value:
            return 1
        return -1



@unique
class DataPropertyMergeWithClassDefaultLabels(Enum_):
    """
    This class list the labels associated to all the available options when merging tables representing data properties whith a table representing a class.
    """

    # NO MERGE AT ALL
    NO_MERGE = 'No merge'

    # MERGE THE DATA PROPERTIES WITH THE CLASS THEY ARE DEFINED BY
    MERGE_DEFINED = 'Merge Defined'

    # MERGE THE DATA PROPERTIES WITH THE CLASS THEY ARE TYPED ON
    MERGE_TYPED = 'Merge Typed'

    @staticmethod
    def getIntValue(label):
        if label == DataPropertyMergeWithClassDefaultLabels.NO_MERGE.value:
            return 0
        elif label == DataPropertyMergeWithClassDefaultLabels.MERGE_TYPED.value:
            return 1
        elif label == DataPropertyMergeWithClassDefaultLabels.MERGE_DEFINED.value:
            return 2
        return -1

@unique
class TakeIntoAccountDisjointnessAxiomsDefaultLabels(Enum_):

    YES = 'Yes (Schema generation and loading may require a long processing time)'

    NO = 'No'


    @staticmethod
    def getIntValue(label):
        if label == TakeIntoAccountDisjointnessAxiomsDefaultLabels.NO.value:
            return 0
        elif label == TakeIntoAccountDisjointnessAxiomsDefaultLabels.YES.value:
            return 1
        return -1


class BlackbirdPreferencesDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    This class implements the 'Preferences' dialog.
    """

    # noinspection PyArgumentList
    def __init__(self, session):
        """
        Initialize the Preferences dialog.
        :type session: Session
        """
        super().__init__(session)

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)

        #############################################
        # GENERAL TAB
        #################################

        ## TABLE MERGE POLICY GROUP
        # CLASSES
        prefix = QtWidgets.QLabel(self, objectName='class_merge_policy_prefix')
        prefix.setFont(Font('Roboto', 12))
        prefix.setText('Class Merge Policy')
        self.addWidget(prefix)

        combobox = ComboBox(objectName='class_merge_policy_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.addItems([x.value for x in ClassMergeWithClassPolicyLabels])
        combobox.setCurrentText(
            settings.value('blackbird/merge/policy/class', ClassMergeWithClassPolicyLabels.MERGE_FLAGS.value, str))
        self.addWidget(combobox)

        prefix = QtWidgets.QLabel(self, objectName='class_merge_default_prefix')
        prefix.setFont(Font('Roboto', 12))
        prefix.setText('Class Merge Default')
        self.addWidget(prefix)

        combobox = ComboBox(objectName='class_merge_default_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.addItems([x.value for x in ClassMergeWithClassDefaultLabels])
        combobox.setCurrentText(
            settings.value('blackbird/merge/default/class', ClassMergeWithClassDefaultLabels.NO_MERGE.value, str))
        self.addWidget(combobox)



        # OBJECT PROPERTIES
        prefix = QtWidgets.QLabel(self, objectName='object_properties_merge_policy_prefix')
        prefix.setFont(Font('Roboto', 12))
        prefix.setText('Object Properties Merge Default')
        self.addWidget(prefix)

        combobox = ComboBox(objectName='object_properties_merge_policy_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.addItems([x.value for x in ObjectPropertyMergeWithClassDefaultLabels])
        combobox.setCurrentText(
            settings.value('blackbird/merge/default/objProps', ObjectPropertyMergeWithClassDefaultLabels.NO_MERGE.value,
                           str))
        self.addWidget(combobox)

        # DATA PROPERTIES
        prefix = QtWidgets.QLabel(self, objectName='data_properties_merge_policy_prefix')
        prefix.setFont(Font('Roboto', 12))
        prefix.setText('Data Properties Merge Default')
        self.addWidget(prefix)

        combobox = ComboBox(objectName='data_properties_merge_policy_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.addItems([x.value for x in DataPropertyMergeWithClassDefaultLabels])
        combobox.setCurrentText(
            settings.value('blackbird/merge/default/dataProps', DataPropertyMergeWithClassDefaultLabels.NO_MERGE.value,
                           str))
        self.addWidget(combobox)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('class_merge_policy_prefix'), self.widget('class_merge_policy_switch'))

        formlayout.addRow(self.widget('class_merge_default_prefix'), self.widget('class_merge_default_switch'))

        formlayout.addRow(self.widget('object_properties_merge_policy_prefix'),
                          self.widget('object_properties_merge_policy_switch'))
        formlayout.addRow(self.widget('data_properties_merge_policy_prefix'),
                          self.widget('data_properties_merge_policy_switch'))
        groupbox = QtWidgets.QGroupBox('Table Merge Policy', self, objectName='merge_policy_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ## AXIOMS GROUP
        #DISJOINTNESS
        prefix = QtWidgets.QLabel(self, objectName='consider_disjointness_prefix')
        prefix.setFont(Font('Roboto', 12))
        prefix.setText('Take into account disjointness axioms')
        self.addWidget(prefix)

        combobox = ComboBox(objectName='consider_disjointness_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.addItems([x.value for x in TakeIntoAccountDisjointnessAxiomsDefaultLabels])
        combobox.setCurrentText(
            settings.value('blackbird/axioms/disjointness', TakeIntoAccountDisjointnessAxiomsDefaultLabels.NO.value, str))
        self.addWidget(combobox)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('consider_disjointness_prefix'), self.widget('consider_disjointness_switch'))

        groupbox = QtWidgets.QGroupBox('Ontology Axioms', self, objectName='ontology_axioms_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ## GENERAL TAB LAYOUT CONFIGURATION

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('merge_policy_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('ontology_axioms_widget'), 0, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('general_widget')
        self.addWidget(widget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        confirmation.setFont(Font('Roboto', 12))
        self.addWidget(confirmation)

        #############################################
        # MAIN WIDGET
        #################################

        widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        widget.addTab(self.widget('general_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'),
                      'Schema Configuration')
        self.addWidget(widget)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(740, 420)
        self.setWindowIcon(QtGui.QIcon(':/blackbird/icons/128/ic_blackbird'))
        self.setWindowTitle('Preferences')

        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the main session (alias for PreferencesDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Executed when the dialog is accepted.
        """
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)

        #############################################
        # GENERAL TAB
        #################################

        class_merge_policy = self.widget('class_merge_policy_switch').currentText()
        class_merge_policy_INT = ClassMergeWithClassPolicyLabels.getIntValue(class_merge_policy)

        class_merge_default = self.widget('class_merge_default_switch').currentText()
        class_merge_default_INT = ClassMergeWithClassDefaultLabels.getIntValue(class_merge_default)

        object_properties_merge_default = self.widget('object_properties_merge_policy_switch').currentText()
        object_properties_merge_default_INT = ObjectPropertyMergeWithClassDefaultLabels.getIntValue(object_properties_merge_default)

        data_properties_merge_default = self.widget('data_properties_merge_policy_switch').currentText()
        data_properties_merge_default_INT = DataPropertyMergeWithClassDefaultLabels.getIntValue(data_properties_merge_default)

        consider_disjointness_default = self.widget('consider_disjointness_switch').currentText()
        consider_disjointness_default_INT = TakeIntoAccountDisjointnessAxiomsDefaultLabels.getIntValue(consider_disjointness_default)

        settings.setValue('blackbird/merge/policy/class', class_merge_policy)
        settings.setValue('blackbird/merge/default/class', class_merge_default)
        settings.setValue('blackbird/merge/default/objProps', object_properties_merge_default)
        settings.setValue('blackbird/merge/default/dataProps', data_properties_merge_default)
        settings.setValue('blackbird/axioms/disjointness', consider_disjointness_default)

        settings.setValue('blackbird/merge/policy/class/INT', class_merge_policy_INT)
        settings.setValue('blackbird/merge/default/class/INT', class_merge_default_INT)
        settings.setValue('blackbird/merge/default/objProps/INT', object_properties_merge_default_INT)
        settings.setValue('blackbird/merge/default/dataProps/INT', data_properties_merge_default_INT)
        settings.setValue('blackbird/axioms/disjointness/INT', consider_disjointness_default_INT)

        #############################################
        # SAVE & EXIT
        #################################

        settings.sync()

        super().accept()