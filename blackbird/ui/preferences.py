from enum import unique

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy import ORGANIZATION, APPNAME
from eddy.core.common import HasWidgetSystem
from eddy.core.datatypes.common import IntEnum_, Enum_
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect
from eddy.ui.fields import ComboBox



@unique
class ClassMergeWithClassPolicy(IntEnum_):
    """
    This class list all the available options when merging tables representing classes whith a table representing a class.
    """

    #NO MERGE AT ALL
    NO_MERGE = 10001

    #MERGE BY ADDING FLAG COLUMNS TO TARGET TABLE
    MERGE_FLAGS = 10002

    # MERGE BY ADDING TYPOLOGICAL TABLES TO CONSIDERED SCHEMA
    MERGE_TYPOLOGICAL = 10003

@unique
class ClassMergeWithClassPolicyLabels(Enum_):
    """
    This class list the labels associated to all the available options when merging tables representing classes whith a table representing a class.
    """

    #NO MERGE AT ALL
    NO_MERGE = 'No merge'

    #MERGE BY ADDING FLAG COLUMNS TO TARGET TABLE
    MERGE_FLAGS = 'Merge By Flags'

    # MERGE BY ADDING TYPOLOGICAL TABLES TO CONSIDERED SCHEMA
    MERGE_TYPOLOGICAL = 'Merge By Typological'


@unique
class ObjectPropertyMergeWithClassPolicy(IntEnum_):
    """
    This class list all the available options when merging tables representing object properties whith a table representing a class.
    """

    #NO MERGE AT ALL
    NO_MERGE = 20001

    #MERGE THE OBJECT PROPERTIES WITH THE CLASS THEY ARE DEFINED ON
    MERGE_DEFINED = 20002

@unique
class ObjectPropertyMergeWithClassPolicyLabels(Enum_):
    """
    This class list the labels associated to all the available options when merging tables representing object properties whith a table representing a class.
    """

    #NO MERGE AT ALL
    NO_MERGE = 'No merge'

    #MERGE THE OBJECT PROPERTIES WITH THE CLASS THEY ARE DEFINED ON
    MERGE_DEFINED = 'Merge Defined'


@unique
class DataPropertyMergeWithClassPolicy(IntEnum_):
    """
    This class list all the available options when merging tables representing data properties whith a table representing a class.
    """

    #NO MERGE AT ALL
    NO_MERGE = 30001

    # MERGE THE DATA PROPERTIES WITH THE CLASS THEY ARE DEFINED BY
    MERGE_DEFINED = 30002

    # MERGE THE DATA PROPERTIES WITH THE CLASS THEY ARE TYPED ON
    MERGE_TYPED = 30003

@unique
class DataPropertyMergeWithClassPolicyLabels(Enum_):
    """
    This class list the labels associated to all the available options when merging tables representing data properties whith a table representing a class.
    """

    #NO MERGE AT ALL
    NO_MERGE = 'No merge'

    # MERGE THE DATA PROPERTIES WITH THE CLASS THEY ARE DEFINED BY
    MERGE_DEFINED = 'Merge Defined'

    # MERGE THE DATA PROPERTIES WITH THE CLASS THEY ARE TYPED ON
    MERGE_TYPED = 'Merge Typed'


class BlackbirdPreferencesDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    This class implements the 'Preferences' dialog.
    """

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
        #CLASSES
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
        combobox.setCurrentText(settings.value('blackbird/merge/policy/class', ClassMergeWithClassPolicyLabels.NO_MERGE.value, str))
        self.addWidget(combobox)

        # OBJECT PROPERTIES
        prefix = QtWidgets.QLabel(self, objectName='object_properties_merge_policy_prefix')
        prefix.setFont(Font('Roboto', 12))
        prefix.setText('Object Properties Merge Policy')
        self.addWidget(prefix)

        combobox = ComboBox(objectName='object_properties_merge_policy_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.addItems([x.value for x in ObjectPropertyMergeWithClassPolicyLabels])
        combobox.setCurrentText(
            settings.value('blackbird/merge/policy/objProps', ObjectPropertyMergeWithClassPolicyLabels.NO_MERGE.value, str))
        self.addWidget(combobox)

        # DATA PROPERTIES
        prefix = QtWidgets.QLabel(self, objectName='data_properties_merge_policy_prefix')
        prefix.setFont(Font('Roboto', 12))
        prefix.setText('Data Properties Merge Policy')
        self.addWidget(prefix)

        combobox = ComboBox(objectName='data_properties_merge_policy_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.addItems([x.value for x in DataPropertyMergeWithClassPolicyLabels])
        combobox.setCurrentText(
            settings.value('blackbird/merge/policy/dataProps', DataPropertyMergeWithClassPolicyLabels.NO_MERGE.value,
                           str))
        self.addWidget(combobox)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('class_merge_policy_prefix'), self.widget('class_merge_policy_switch'))
        formlayout.addRow(self.widget('object_properties_merge_policy_prefix'), self.widget('object_properties_merge_policy_switch'))
        formlayout.addRow(self.widget('data_properties_merge_policy_prefix'), self.widget('data_properties_merge_policy_switch'))
        groupbox = QtWidgets.QGroupBox('Table Merge Policy', self, objectName='merge_policy_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ## GENERAL TAB LAYOUT CONFIGURATION

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('merge_policy_widget'), 0, QtCore.Qt.AlignTop)
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
        widget.addTab(self.widget('general_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'), 'Schema Configuration')
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

        settings.setValue('blackbird/merge/policy/class', self.widget('class_merge_policy_switch').currentText())
        settings.setValue('blackbird/merge/policy/objProps', self.widget('object_properties_merge_policy_switch').currentText())
        settings.setValue('blackbird/merge/policy/dataProps', self.widget('data_properties_merge_policy_switch').currentText())

        #############################################
        # SAVE & EXIT
        #################################

        settings.sync()

        super().accept()