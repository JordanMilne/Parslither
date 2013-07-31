#!/usr/bin/env python
# Copyright 2011 Jordan Milne

from PyQt4 import Qt, QtCore, QtGui
from qhexedit import QHexEdit

from PyQt4.QtGui import QTreeWidget, QTreeWidgetItem, QDockWidget, \
    QFont, QColor, QKeySequence, QAction

from optionsdialog import OptionsDialog
import qhexedit_rc # pylint: disable-msg=W0611

import magic

from yapsy.PluginManager import PluginManager
from format_dissector import FormatDissector

import construct


class MainWindow(QtGui.QMainWindow):
    """A configurable hex editor that supports binary templates and
    scripting through use of the construct library
    """
    def __init__(self, file_name=None):
        """Initializer"""
        super(MainWindow, self).__init__()

        #Flag set to ignore the next data change event
        self._treeChangedData = False

        self._isUntitled = True
        self._curFile = ''
        self._setCurrentFile('')

        self.__mimeTypes = magic.Magic(mime=True)
        
        # UI attribute definitions (populated in __initUI and the various
        # __create* methods)

        #ToolBar
        self._fileToolBar = self.addToolBar("File")

        #StatusBar
        self._lbAddress = QtGui.QLabel()
        self._lbAddressName = QtGui.QLabel()
        self._lbSize = QtGui.QLabel()
        self._lbSizeName = QtGui.QLabel()
        self._lbOverwriteMode = QtGui.QLabel()
        self._lbOverwriteModeName = QtGui.QLabel()

        #Menus
        self._fileMenu = self.menuBar().addMenu("&File")
        self._editMenu = self.menuBar().addMenu("&Edit")
        self._helpMenu = self.menuBar().addMenu("&Help")

        #Action definitions
        self._openAct = None
        self._saveAct = None
        self._saveAsAct = None
        self._saveReadableAct = None
        self._saveSelReadableAct = None
        self._exitAct = None
        self._undoAct = None
        self._redoAct = None
        self._aboutAct = None
        self._optionsAct = None

        #Other
        self._hexEdit = QHexEdit()
        self._treeDissected = QTreeWidget()
        self._optionsDialog = OptionsDialog()

        self.__initUI()

        self.readSettings()

        # Create plugin manager

        # Which plugin types to load and which categories to put them in
        category_mapping = {"FormatDissectors": FormatDissector}

        self._manager = PluginManager(categories_filter=category_mapping)
        self._manager.setPluginPlaces(["plugins"])

        #Dissectors
        self._dissector = None
        self._availDissectors = {}

        #load in the plugins
        self.__reloadPlugins()


        if file_name:
            self.loadFile(file_name)



    #############
    # GUI SETUP #
    #############

    def about(self):
        """Display an 'About' dialog box describing the application"""
        QtGui.QMessageBox.about(self, "About ParSlither",
            "Parslither v0.1 (WIP)")

    def closeEvent(self, event): # pylint: disable-msg=W0613
        """(PyQT event handler) the application is due to close"""
        self.writeSettings()
        del self._optionsDialog
        self.close()

    def __createActions(self):
        """Create actions for the menus and toolbars in the UI"""
        self._openAct = QAction(QtGui.QIcon(':/images/open.png'),
                "&Open...", self, shortcut=QKeySequence.Open,
                statusTip="Open an existing file", triggered=self.dlgOpen)

        self._saveAct = QAction(QtGui.QIcon(':/images/save.png'),
                "&Save", self, shortcut=QKeySequence.Save,
                statusTip="Save the document to disk", triggered=self.save)

        self._saveAsAct = QAction("Save &As...", self,
                shortcut=QKeySequence.SaveAs,
                statusTip="Save the document under a new name",
                triggered=self.dlgSaveAs)
        
        self._saveReadableAct = QAction("Save as &Readable...", self,
                statusTip="Save in a readable format",
                triggered=self.dlgSaveToReadableFile)

        self._saveSelReadableAct = QAction("Save Selection Readable...", self,
                statusTip="Save selection in a readable format",
                triggered=self.dlgSaveSelectionToReadableFile)

        self._exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit the application", triggered=self.close)
        
        self._undoAct = QAction("&Undo", self, shortcut=QKeySequence.Undo,
                triggered=self._hexEdit.undo)
                
        self._redoAct = QAction("&Redo", self, shortcut=QKeySequence.Redo,
                triggered=self._hexEdit.redo)
        
        self._aboutAct = QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)
                
        self._optionsAct = QAction("&Options", self,
                statusTip="Show the options dialog",
                triggered=self.showOptionsDialog)

    def __initMenus(self):
        """Initialize menus for the UI"""
        self._fileMenu.addAction(self._openAct)
        self._fileMenu.addAction(self._saveAct)
        self._fileMenu.addAction(self._saveAsAct)
        self._fileMenu.addAction(self._saveReadableAct)
        self._fileMenu.addSeparator()
        self._fileMenu.addAction(self._exitAct)

        self._editMenu.addAction(self._undoAct)
        self._editMenu.addAction(self._redoAct)
        self._editMenu.addAction(self._saveSelReadableAct)
        self._editMenu.addSeparator()
        self._editMenu.addAction(self._optionsAct)

        self._helpMenu.addAction(self._aboutAct)
        
    def __initStatusBar(self):
        """Initialize status bar for the UI"""
        # Address Label
        self._lbAddressName.setText("Address:")
        self.statusBar().addPermanentWidget(self._lbAddressName)
        self._lbAddress.setFrameShape(QtGui.QFrame.Panel)
        self._lbAddress.setFrameShadow(QtGui.QFrame.Sunken)
        self._lbAddress.setMinimumWidth(70)
        self.statusBar().addPermanentWidget(self._lbAddress)
        self._hexEdit.currentAddressChanged.connect(self.__setAddress)
        
        # Address Size
        self._lbSizeName.setText("Size:")
        self.statusBar().addPermanentWidget(self._lbSizeName)
        self._lbSize.setFrameShape(QtGui.QFrame.Panel)
        self._lbSize.setFrameShadow(QtGui.QFrame.Sunken)
        self._lbSize.setMinimumWidth(70)
        self.statusBar().addPermanentWidget(self._lbSize)
        self._hexEdit.currentSizeChanged.connect(self.__setSize)
        
        # Overwrite Mode label
        self._lbOverwriteModeName.setText("Mode:")
        self.statusBar().addPermanentWidget(self._lbOverwriteModeName)
        self._lbOverwriteMode.setFrameShape(QtGui.QFrame.Panel)
        self._lbOverwriteMode.setFrameShadow(QtGui.QFrame.Sunken)
        self._lbOverwriteMode.setMinimumWidth(70)
        self.statusBar().addPermanentWidget(self._lbOverwriteMode)
        self.setOverwriteMode(self._hexEdit.overwriteMode())

        self.statusBar().showMessage("Ready")
        
    def __initToolBars(self):
        """Initialize ToolBars for the UI"""
        self._fileToolBar.addAction(self._openAct)
        self._fileToolBar.addAction(self._saveAct)

    def __initDockWindows(self):
        """Initialize Docked Windows for the UI"""
        dock = QtGui.QDockWidget("Dissected",  self)
        dock.setFeatures(
            QDockWidget.DockWidgetFeatures(QDockWidget.NoDockWidgetFeatures))
        dock.setAllowedAreas(Qt.Qt.BottomDockWidgetArea)
        dock.setWidget(self._treeDissected)
        self.addDockWidget(Qt.Qt.BottomDockWidgetArea, dock)

    def __initUI(self):
        """Initialize everything for the UI"""
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self._optionsDialog.accepted.connect(self.__optionsAccepted)

        self._hexEdit.overwriteModeChanged.connect(self.setOverwriteMode)
        self._hexEdit.dataChanged.connect(self.__hexDataChanged)
        self.setCentralWidget(self._hexEdit)

        #we don't want to be able to sort by rows (keep serialized order)
        self._treeDissected.setSortingEnabled(False)

        tree_header = QTreeWidgetItem(["Name",  "Value"])
        self._treeDissected.setHeaderItem(tree_header)

        self.__createActions()
        self.__initMenus()
        self.__initToolBars()
        self.__initStatusBar()
        self.__initDockWindows()



    ###########
    # PLUGINS #
    ###########

    def __reloadPlugins(self):
        """ Load plugins """
        self._manager.locatePlugins()
        self._manager.loadPlugins()

        self.__refreshDissectors()

    def __refreshDissectors(self):
        """Refresh dissectors from the plugin manager"""
        self._availDissectors = {}
        for plugin in self._manager.getPluginsOfCategory("FormatDissectors"):
            # plugin.plugin_object is an instance of the plugin
            plug_obj = plugin.plugin_object
            self._availDissectors[plug_obj.name] = plug_obj

        # if we have a dissector loaded, reload it from the dict of
        # available dissectors
        if self._dissector and self._dissector.name in self._availDissectors:
            self._dissector = self._availDissectors[self._dissector.name]
        else:
            self._dissector = None



    ############
    # SETTINGS #
    ############

    def readSettings(self):
        """Reload all settings for this application from storage"""
        settings = QtCore.QSettings()
        pos = settings.value('pos', QtCore.QPoint(200, 200)).toPoint()
        size = settings.value('size', QtCore.QSize(610, 460)).toSize()
        self.move(pos)
        self.resize(size)

        editor = self._hexEdit

        editor.setAddressArea(settings.value("AddressArea").toBool())
        editor.setAsciiArea(settings.value("AsciiArea").toBool())
        editor.setHighlighting(settings.value("Highlighting").toBool())
        editor.setOverwriteMode(settings.value("OverwriteMode").toBool())
        editor.setReadOnly(settings.value("ReadOnly").toBool())

        editor.setHighlightingColor(QColor(settings.value("HighlightingColor")))
        editor.setAddressAreaColor(QColor(settings.value("AddressAreaColor")))
        editor.setSelectionColor(QColor(settings.value("SelectionColor")))

        default_font = QFont("Courier New", 10)
        editor.setFont(QFont(settings.value("WidgetFont", default_font)))

        editor.setAddressWidth(settings.value("AddressAreaWidth").toInt()[0])

    def writeSettings(self):
        """Write all non-session settings to storage"""
        settings = QtCore.QSettings()
        settings.setValue('pos', self.pos())
        settings.setValue('size', self.size())

    def showOptionsDialog(self):
        """Show the options dialog"""
        self._optionsDialog.show()

    def __optionsAccepted(self):
        """(Callback) The user is ok with the changes to the settings"""
        self.writeSettings()
        self.readSettings()



    #########################
    # FILE LOADING / SAVING #
    #########################

    def save(self):
        """Save the entire hex editor buffer to a file as-is

        If a file was already open, it will be saved to that file, otherwise a
        file chooser will be presented and the user will be asked to choose a
        file
        """
        def write_whole(handle):
            handle.write(self._hexEdit.data())

        if self._isUntitled:
            return self.dlgSaveAs()
        else:
            return self.writeFile(write_whole, self._curFile, as_is=True)

    def dlgSaveAs(self):
        """Save the entire hex editor buffer to a file as-is"""
        def write_whole(handle):
            handle.write(self._hexEdit.data())

        return self.writeFile(write_whole, as_is=True, op_name="Save As")
    
    def dlgSaveToReadableFile(self):
        """Save the entire hex editor buffer to a file in a readable format"""
        def write_readable(handle):
            handle.write(self._hexEdit.toReadableString())

        return self.writeFile(write_readable, op_name="Save To Readable File")

    def dlgSaveSelectionToReadableFile(self):
        """Save the selected section to a file in a readable format"""
        def write_sel_readable(handle):
            handle.write(self._hexEdit.toReadableString())
        
        return self.writeFile(write_sel_readable,
                              op_name="Save To Readable File")

    def writeFile(self, write_func, file_name=None, as_is=False, op_name=""):
        """Try to save content to the specified file using the specified
        write_func

        Arguments:
        write_func(handle) -- Function to save the desired content to the file

        Keyword Arguments:
        file_name -- Filename to save to instead of displaying a
                     file picker (Defaults to None)
        as_is -- whether the hex editor is being saved without modification
                (Defaults to False)
        op_name -- (Defaults to "")
        """
        if not file_name:
            file_name = QtGui.QFileDialog.getSaveFileName(self,
                                                          op_name,
                                                          self._curFile)
            if not file_name:
                return False

        file_handle = QtCore.QFile(file_name)

        if not file_handle.open(QtCore.QFile.WriteOnly):
            error_msg = "Cannot write file %s:\n%s." % \
                        (file_name, file_handle.errorString())

            QtGui.QMessageBox.warning(self, "HexEdit", error_msg)
            return False

        # call the function to actually write to the file
        write_func(file_handle)

        # only set the current file to the saved filename if we're
        # saving the whole file as-is
        if as_is:
            self._setCurrentFile(file_name)
        self.statusBar().showMessage("File saved", 2000)
        return True

    def dlgOpen(self):
        """Display a file picker and ask the user to choose a file to open in
        the hex editor"""
        file_name = QtGui.QFileDialog.getOpenFileName(self)
        if file_name:
            self.loadFile(file_name)

    def loadFile(self, file_name):
        """Load the specified file into the hex editor"""
        file_handle = QtCore.QFile(file_name)
        if not file_handle.open( QtCore.QFile.ReadOnly):
            warning_msg = "Cannot read file %s:\n%s." % \
                          file_name, file_handle.errorString()
            QtGui.QMessageBox.warning(self, "QHexEdit", warning_msg)
            return

        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self._hexEdit.setData(file_handle.readAll())
        QtGui.QApplication.restoreOverrideCursor()

        self._setCurrentFile(file_name)
        self.statusBar().showMessage("File loaded", 2000)

        self.__autoLoadDissector(file_name)
        self.__refreshDissectionTree()

    def _setCurrentFile(self, file_name):
        """Set the current filename"""
        self._curFile = file_name
        self._isUntitled = (file_name == "")
        self.setWindowModified(False)
        window_title = "%s[*] - QHexEdit" % \
                       QtCore.QFileInfo(self._curFile).fileName()
        self.setWindowTitle(window_title)
        
    def __setAddress(self, address):
        """Set the address at the caret"""
        self._lbAddress.setText('%x' % address)
        
    def setOverwriteMode(self, mode):
        """Overwrite the nibble following the caret instead of inserting?"""
        if mode:
            self._lbOverwriteMode.setText("Overwrite")
        else:
            self._lbOverwriteMode.setText("Insert")
            
    def __setSize(self, size):
        """Set the total size of the file in the hex editor"""
        self._lbSize.setText('%d' % size)




    def __hexDataChanged(self):
        """The data in the hex editor control changed"""

        # don't refresh the dissection tree if the hex editor data was
        # based on the data in there anyways
        if not self._treeChangedData:
            self.__refreshDissectionTree()
        
        self._treeChangedData = False

    def __autoLoadDissector(self, file_name):
        """Try to auto-assign an available dissector based on filename
        and mimetype
        """
        
        #don't use a dissector if we can't auto-assign one
        self._dissector = None

        #first try and assign a dissector by extension
        for dissector in self._availDissectors.values():
            for extension in dissector.file_exts:
                if file_name.endsWith(extension):
                    self._dissector = dissector
                    return

        #now try to assign a dissector by mimetype
        file_mimetype = self.__mimeTypes.from_file(file_name)

        if not file_mimetype:
            return

        for dissector in self._availDissectors.values():
            for supp_mimetype in dissector.file_mimetypes:
                if file_name == supp_mimetype:
                    self._dissector = dissector
                    return

    def __refreshDissectionTree(self):
        """Refresh the tree of dissected data with data from the hex editor"""
        self._treeDissected.clear()

        #only refresh if we have data and a dissector
        if self._dissector and self._hexEdit.data():
            self.__addToDissectionTree(
                self._dissector.dissect(self._hexEdit.data().data()))
            
    
    def __addToDissectionTree(self, attr_container, parent=None):
        """Recursively add a Construct container and its children to the
        dissected data tree widget
        
        Arguments:
        attr_container -- Construct container whose attributes to recursively
                          add to the tree

        Keyword Arguments:
        parent -- Reference to the tree item that represents the current
                  container (default None)
        """

        def add_item_to_tree(child):
            """ Add a tree item to the tree, with its parent item as the
            parent if it has one """
            if not parent:
                self._treeDissected.addTopLevelItem(child)
            else:
                parent.addChild(child)
        
        def add_container_to_tree(name, source_container):
            """ Add a container to the dissection tree as a tree item and
            handle its children """
            container_item = QTreeWidgetItem([name, ""])
            add_item_to_tree(container_item)
            self.__addToDissectionTree(source_container, container_item)

        #look through the container's attributes and add them to the tree
        #as necessary
        for attr_k in attr_container:
            #skip private attributes if we were given any
            if not attr_k.startswith("_"):
                #get the value of this attribute
                attr_v = attr_container[attr_k]
                
                #value is a container
                if isinstance(attr_v,  construct.Container):
                    add_container_to_tree(attr_k, attr_v)
                #value is list-like
                elif isinstance(attr_v, (list, tuple)):
                    elem_idx = 0
                    for elem in attr_v:
                        elem_name = "%s[%d]" % (attr_k, elem_idx)

                        #list element is a container
                        if isinstance(elem, construct.Container):
                            add_container_to_tree(elem_name, elem)
                        #list element is a primitive or non-construct object
                        else:
                            new_item = QTreeWidgetItem([elem_name, str(elem)])
                            add_item_to_tree(new_item)
                            
                        elem_idx += 1
                #value is a primitive or a non-construct object
                else:
                    add_item_to_tree(QTreeWidgetItem([attr_k, str(attr_v)]))



if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv) # pylint: disable-msg=C0103
    app.setApplicationName("ParSlither")
    app.setOrganizationName("ParSlither")
    mainWin = MainWindow() # pylint: disable-msg=C0103
    mainWin.show()
    sys.exit(app.exec_())

