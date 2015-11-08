'''
Created on 6 de nov. de 2015

@author: martin
'''

from pyqode.qt import QtWidgets, QtCore

import serial
import threading
import vt102

class Terminal(QtWidgets.QTextEdit):
    '''
    classdocs
    '''
    
    onReceiveText = QtCore.Signal(str)
     
    def __init__(self, parent):
        '''
        Constructor
        '''
        super(self.__class__, self).__init__(parent)
        self.setFont(QtWidgets.QFont('Monospace', 10))
        self.setCursorWidth(QtWidgets.QFontMetrics(self.font()).width(' '))
        self.setStyleSheet("QTextEdit { background-color : black; color : #cccccc; }");
        self.onReceiveText.connect(self._appendText)
        self.serial = None
        self.thread = None
        self.stream = vt102.stream()
        self.vt = vt102.screen((24, 80))
        self.vt.attach(self.stream)
        
    def open(self, port, speed):
        if self.serial is serial.Serial:
            self.serial.close()
        try:
            self.serial = serial.Serial(port, speed, timeout=0)
            self._startThread()
        except serial.SerialException as e:
            print(e)
    
    def _startThread(self):
        if self.thread and self.thread.isAlive():
            self.thread.join()
            self.thread = None
        self.thread = threading.Thread(target=self._readThread)
        self.thread.setDaemon(1)
        self.thread.start()
        
    def _readThread(self):
        while self.serial.isOpen():
            text = self.serial.read(1)
            if text:
                n = self.serial.inWaiting()
                if n:
                    text = text + self.serial.read(n)
                self.onReceiveText.emit(text.decode('utf-8'))
        
    def paintEvent(self, event):
        self.setPlainText('\n'.join(self.vt.display))
        super().paintEvent(event)
        p = QtWidgets.QPainter()
        p.begin(self.viewport())
        self.moveCursorTo(self.vt.cursor())
        p.fillRect(self.cursorRect(), QtWidgets.QBrush(QtCore.Qt.white))
        p.end()
        
    def moveCursorTo(self, pos):
        line = pos[1]
        col = pos[0]
        c = self.textCursor()
        c.setPosition(0, c.MoveAnchor)
        c.movePosition(c.Down, c.MoveAnchor, line+1);
        c.movePosition(c.NextCharacter, c.MoveAnchor, col);
        self.setTextCursor(c)
        
    @QtCore.Slot(str)
    def _appendText(self, text):
        self.stream.process(text)
    
    def keyPressEvent(self, event):
        if self.serial and self.serial.isOpen():
            try:
                text = {
                    QtCore.Qt.Key_Tab: lambda x: b"\t",
                    QtCore.Qt.Key_Backspace: lambda x: b"\x7f"
                }[event.key()](event.key())
                print(text)
            except KeyError:
                text = bytes(event.text(), 'utf-8')
            if text:
                self.serial.write(text)
            event.accept()
