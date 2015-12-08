#!/usr/bin/env python3
import os
import re
import sys
import base64
import glob

import pyqode.python.backend.server as server
import pyqode.python.widgets as widgets
import pyqode.qt.QtCore as QtCore
import pyqode.qt.QtWidgets as QtWidgets
import pyqode_i18n
import termWidget
import xml.etree.ElementTree as ElementTree

import resources

__version__ = '1.0'


def i18n(s):
    return pyqode_i18n.tr(s)


def icon(name):
    return QtWidgets.QIcon(":/images/{}.svg".format(name))


def rccfile(path):
    f = QtCore.QFile(path)
    if not f.open(QtCore.QFile.ReadOnly):
        return None
    s = f.readAll()
    f.close()
    return s


class WidgetSpacer(QtWidgets.QWidget):
    def __init__(self, parent, wmax=None):
        super(WidgetSpacer, self).__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        if wmax:
            self.setMaximumWidth(wmax)


class PortSelector(QtWidgets.QComboBox):
    def __init__(self, parent):
        super(self.__class__, self).__init__(parent)
        self.widget = parent
        self.addItems(termWidget.serial_ports())
        self.currentIndexChanged.connect(self.onChange)
        self.setCurrentIndex(0)
        self.onChange(0)

    @QtCore.Slot(int)
    def onChange(self, n):
        if self.currentText():
            self.widget.setPort(self.currentText())


class SnipplerWidget(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super(SnipplerWidget, self).__init__(i18n('Snipplets'), parent)
        self.setWindowTitle(i18n("Snipplets"))
        self.snippletView = QtWidgets.QListWidget(self)
        self.setWidget(self.snippletView)
        self.loadSnipplets()
        self.snippletView.itemDoubleClicked.connect(self._insertToParent)

    def _insertToParent(self, item):
        self.parent().editor.insertPlainText(item.toolTip())

    def addSnipplet(self, description, contents):
        item = QtWidgets.QListWidgetItem(self.snippletView)
        item.setText(description)
        item.setToolTip(contents)

    def loadSnippletFrom(self, inp):
        xml = ElementTree.fromstring(inp) if type(inp) is str else  \
            ElementTree.parse(inp).getroot()
        for child in xml:
            self.addSnipplet(child.attrib["name"], child.text)

    def loadCodeSnipplet(self, source):
        with open(source) as f:
            s = f.read()
            r = re.compile(r'^# Description: (.*)[\r\n]*')
            description = ''.join(re.findall(r, s))
            contents = re.sub(r, '', s)
            if description and contents:
                self.addSnipplet(description, contents)

    @QtCore.Slot()
    def loadSnipplets(self):
        self.snippletView.setStyleSheet('''QToolTip {
            font-family: "monospace";
        }''')
        self.loadSnippletFrom(rccfile(':snipplets.xml').data().decode())
        snipplet_glob = os.path.join(os.path.dirname(__file__), '..', 'share',
                                     'snipplet', '*.py')
        for source in glob.glob(snipplet_glob):
            self.loadCodeSnipplet(source)


class MainWindow(QtWidgets.QMainWindow):
    onListDir = QtCore.Signal(str)

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.cwd = QtCore.QDir.homePath()
        self.setWindowTitle(i18n("Edu CIAA MicroPython"))
        self.editor = widgets.PyCodeEdit(server_script=server.__file__)
        self.term = termWidget.Terminal(self)
        self.outline = widgets.PyOutlineTreeWidget()
        self.outline.set_editor(self.editor)
        self.dock_outline = QtWidgets.QDockWidget(i18n('Outline'))
        self.dock_outline.setWidget(self.outline)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_outline)
        self.snippler = SnipplerWidget(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.snippler)
        self.stack = QtWidgets.QStackedWidget(self)
        self.stack.addWidget(self.editor)
        self.stack.addWidget(self.term)
        self.setCentralWidget(self.stack)
        self.makeAppToolBar()
        self.i18n()
        self.resize(800, 600)
        self.onListDir.connect(lambda l: self._showDir(l))

    def __enter__(self):
        self.show()

    def __exit__(self, t, v, bt):
        self.terminate()

    def i18n(self, actions=None):
        if not actions:
            actions = self.editor.actions()
        for action in actions:
            if not action.isSeparator():
                action.setText(pyqode_i18n.tr(action.text()))
            if action.menu():
                self.i18n(action.menu().actions())

    def terminate(self):
        self.term.close()
        self.editor.backend.stop()

    def makeAppToolBar(self):
        bar = QtWidgets.QToolBar(self)
        bar.setIconSize(QtCore.QSize(48, 48))
        bar.addAction(icon("document-new"), i18n("New"), self.fileNew)
        bar.addAction(icon("document-open"), i18n("Open"), self.fileOpen)
        bar.addAction(icon("document-save"), i18n("Save"), self.fileSave)
        bar.addWidget(WidgetSpacer(self))
        bar.addWidget(QtWidgets.QLabel(i18n("Serial Port:")))
        bar.addWidget(WidgetSpacer(self, 12))
        bar.addWidget(PortSelector(self))
        bar.addAction(icon("run"), i18n("Run"), self.progRun)
        bar.addAction(icon("download"), i18n("Download"), self.progDownload)
        self.termAction = bar.addAction(icon("terminal"), i18n("Terminal"),
                                        self.openTerm)
        self.termAction.setCheckable(True)
        # self.termAction.setMenu(self.terminalMenu())
        self.addToolBar(bar)

    def terminalMenu(self):
        m = QtWidgets.QMenu(self)
        g = QtWidgets.QActionGroup(m)
        g.triggered.connect(lambda a: self.setPort(a.text()))
        for s in termWidget.serial_ports():
            a = m.addAction(s)
            g.addAction(a)
            a.setCheckable(True)
        if g.actions():
            g.actions()[0].setChecked(True)
            self.setPort(g.actions()[0].text())
        return m

    def setPort(self, port):
        self.term.open(port, 115200)

    def closeEvent(self, event):
        event.accept()
        if self.editor.dirty:
            x = self.dirtySaveDischartCancel()
            if x == QtWidgets.QMessageBox.Save:
                if not self.fileSave():
                    event.ignore()
            elif x == QtWidgets.QMessageBox.Cancel:
                event.ignore()

    def fileNew(self):
        if self.editor.dirty:
            x = self.dirtySaveDischartCancel()
            if x == QtWidgets.QMessageBox.Save:
                if not self.fileSave():
                    return
            elif x == QtWidgets.QMessageBox.Cancel:
                return
        self.editor.file.close()

    def dirtySaveDischartCancel(self):
        d = QtWidgets.QMessageBox()
        d.setWindowTitle(i18n("Question"))
        d.setText(i18n("Document was modify"))
        d.setInformativeText(i18n("Save changes?"))
        d.setIcon(QtWidgets.QMessageBox.Question)
        d.setStandardButtons(QtWidgets.QMessageBox.Save |
                             QtWidgets.QMessageBox.Discard |
                             QtWidgets.QMessageBox.Cancel)
        return d.exec_()

    def dirtySaveCancel(self):
        d = QtWidgets.QMessageBox()
        d.setWindowTitle(i18n("Question"))
        d.setText(i18n("Document was modify"))
        d.setInformativeText(i18n("Save changes?"))
        d.setIcon(QtWidgets.QMessageBox.Question)
        d.setStandardButtons(QtWidgets.QMessageBox.Save |
                             QtWidgets.QMessageBox.Cancel)
        return d.exec_()

    def fileOpen(self):
        if self.editor.dirty:
            x = self.dirtySaveDischartCancel()
            if x == QtWidgets.QMessageBox.Save:
                if not self.fileSave():
                    return
            elif x == QtWidgets.QMessageBox.Cancel:
                return
        name, dummy = QtWidgets.QFileDialog.getOpenFileName(
            self, i18n("Open File"), self.cwd,
            i18n("Python files (*.py);;All files (*)"))
        if name:
            self.editor.file.open(name)
            self.cwd = os.path.dirname(name)

    def fileSave(self):
        if not self.editor.file.path:
            path, dummy = QtWidgets.QFileDialog.getSaveFileName(
                self, i18n("Save File"), self.cwd,
                i18n("Python files (*.py);;All files (*)"))
        else:
            path = self.editor.file.path
        if not path:
            return False
        self.editor.file.save(path)
        return True

    def openTerm(self):
        if self.termAction.isChecked():
            self.stack.setCurrentIndex(1)
            self.term.setFocus()
            # self.term.remoteExec(b'\x04')
        else:
            self.stack.setCurrentIndex(0)

    def progRun(self):
        self._targetExec(self.editor.toPlainText())
        self.termAction.setChecked(True)
        self.openTerm()

    def _targetExec(self, script, continuation=None):
        def progrun2(text):
            # print("{} {}".format(4, progrun2.text))
            progrun2.text += text
            if progrun2.text.endswith(b'\x04>'):
                # print("{} {}".format(5, progrun2.text))
                if callable(continuation):
                    continuation(progrun2.text)
                return True
            return False

        def progrun1(text):
            progrun1.text += text
            # print("{} {}".format(2, progrun1.text))
            if progrun1.text.endswith(b'to exit\r\n>'):
                progrun2.text = b''
                # print("{} {}".format(3, progrun1.text))
                cmd = 'print("\033c")\r{}\r\x04\x02'.format(script)
                # print("{} {}".format(3.5, cmd))
                self.term.remoteExec(bytes(cmd, 'utf-8'), progrun2)
                return True
            return False
        progrun1.text = b''
        # print(1)
        self.term.remoteExec(b'\r\x03\x03\r\x01', progrun1)

    def showDir(self):
        def finished(raw):
            text = ''.join(re.findall(r"(\[.*?\])", raw.decode()))
            print(raw, text)
            self.onListDir.emit(text)
        self._targetExec('print(os.listdir())', finished)

    def _showDir(self, text):
        items = eval(text)
        d = QtWidgets.QDialog(self)
        l = QtWidgets.QVBoxLayout(d)
        h = QtWidgets.QListWidget(d)
        l.addWidget(h)
        h.addItems(items)
        h.itemClicked.connect(d.accept)
        d.exec_()

    def _writeRemoteFile(self, local_name):
        def finished(raw):
            print('_writeRemoteFile terminated: ', raw)
        remote_name = '/flash/{}'.format(os.path.basename(local_name))
        with open(local_name, 'rb') as f:
            data = base64.b16encode(f.read())
        cmd = "import ubinascii\r" \
              "with open('{}', 'wb') as f:\r" \
              "    f.write(ubinascii.unhexlify({}))".format(remote_name, data)
        print("Writing remote to ", remote_name, data)
        print("--------------\n", cmd, "\n--------------")
        self._targetExec(cmd, finished)

    def progDownload(self):
        if not self.editor.file.path:
            if self.dirtySaveCancel() == QtWidgets.QMessageBox.Cancel:
                return
            if not self.fileSave():
                return
        self._writeRemoteFile(self.editor.file.path)


def main():
    app = QtWidgets.QApplication(sys.argv)
    with MainWindow():
        app.exec_()

if __name__ == "__main__":
    resources.__file__
    main()
