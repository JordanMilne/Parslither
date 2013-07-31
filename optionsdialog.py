#!/usr/bin/env python

from PyQt4 import Qt, QtCore, QtGui # pylint: disable-msg=W0611
                                    # Qt NEEDS to be imported to appease pylint
from PyQt4.QtGui import QColor, QFont, QPalette, QColorDialog, QFontDialog

from Ui_optionsdialog import Ui_OptionsDialog

class OptionsDialog(QtGui.QDialog):
    accepted = QtCore.pyqtSignal()

    def __init__(self):
        super(OptionsDialog, self).__init__()
        self.ui = Ui_OptionsDialog()
        self.ui.setupUi(self)
        
        self.readSettings()
        #make sure to write the settings, in case we used any defaults
        self.writeSettings()
        
    def readSettings(self):
        """Read user-changeable settings and add them to the UI"""
        settings = QtCore.QSettings()
        
        self.ui.cbAddressArea.setChecked(
            settings.value("AddressArea", True).toBool())
        self.ui.cbAsciiArea.setChecked(
            settings.value("AsciiArea", True).toBool())
        self.ui.cbHighlighting.setChecked(
            settings.value("Highlighting", True).toBool())
        self.ui.cbOverwriteMode.setChecked(
            settings.value("OverwriteMode", True).toBool())
        self.ui.cbReadOnly.setChecked(settings.value("ReadOnly", False).toBool())
        
        set_label_bg_color(self.ui.lbHighlightingColor,
                      QColor(settings.value("HighlightingColor", QColor(0xff, 0xff, 0x99, 0xff))))
        set_label_bg_color(self.ui.lbAddressAreaColor,
                      QColor(settings.value("AddressAreaColor", QColor(0xd4, 0xd4, 0xd4, 0xff))))
        set_label_bg_color(self.ui.lbSelectionColor,
                      QColor(settings.value("SelectionColor", QColor(0x6d, 0x9e, 0xff, 0xff))))
        self.ui.leWidgetFont.setFont(
            QFont(settings.value("WidgetFont", QFont("Courier New", 10))))
        
        self.ui.sbAddressAreaWidth.setValue(
            settings.value("AddressAreaWidth", 4).toInt()[0])
        
    def writeSettings(self):
        """Save the values of the option controls to the setting store"""
        settings = QtCore.QSettings()
        settings.setValue("AddressArea", self.ui.cbAddressArea.isChecked())
        settings.setValue("AsciiArea", self.ui.cbAsciiArea.isChecked())
        settings.setValue("Highlighting", self.ui.cbHighlighting.isChecked())
        settings.setValue("OverwriteMode", self.ui.cbOverwriteMode.isChecked())
        settings.setValue("ReadOnly", self.ui.cbReadOnly.isChecked())

        settings.setValue("HighlightingColor",
                          get_label_bg_color(self.ui.lbHighlightingColor))
        settings.setValue("AddressAreaColor",
                          get_label_bg_color(self.ui.lbAddressAreaColor))
        settings.setValue("SelectionColor",
                          get_label_bg_color(self.ui.lbSelectionColor))
        settings.setValue("WidgetFont", self.ui.leWidgetFont.font())
        
        settings.setValue("AddressAreaWidth",
                          self.ui.sbAddressAreaWidth.value())


    def accept(self):
        """(PyQT slot) User clicked the OK button on the dialog"""
        self.writeSettings()
        self.accepted.emit()
        super(OptionsDialog, self).hide()

    def reject(self):
        """(PyQT slot) user clicked the Cancel button on the dialog"""
        #axe any changes we made
        self.readSettings()
        super(OptionsDialog, self).hide()

    def on_pbHighlightingColor_pressed(self):
        self.selectLabelColor(self.ui.lbHighlightingColor)
        
    def on_pbAddressAreaColor_pressed(self):
        self.selectLabelColor(self.ui.lbAddressAreaColor)
        
    def on_pbSelectionColor_pressed(self):
        self.selectLabelColor(self.ui.lbSelectionColor)
        
    def on_pbWidgetFont_pressed(self):
        font, ok = QFontDialog().getFont(self.ui.leWidgetFont.font(), self)
        if ok:
            self.ui.leWidgetFont.setFont(font)

    def selectLabelColor(self, label):
        """Display a color picker allowing the user to change the color of a
        QLabel, initialized with the current color of the label.

        If the color picked was valid and the user clicked ok, the color will
        change
        """
        color = QColorDialog.getColor(get_label_bg_color(label), self)
        if color.isValid():
            set_label_bg_color(label, color)

def get_label_bg_color(label):
    """Get the background color of a QLabel"""
    return label.palette().color(QPalette.Background)

def set_label_bg_color(label, color):
    """Set the background color of a QLabel"""
    palette = label.palette()
    palette.setColor(QPalette.Background, color)
    label.setPalette(palette)
    label.setAutoFillBackground(True)