'''
Created on 6 de nov. de 2015

@author: martin
'''

from pyqode.qt import QtWidgets, QtCore

import serial
import threading
import pyte

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
        #self.setCursorWidth(0)
        self.setCursorWidth(QtWidgets.QFontMetrics(self.font()).width(' '))
        self.setStyleSheet("background-color : black; color : #cccccc;");
        self.onReceiveText.connect(self._appendText)
        self.serial = None
        self.thread = None
        self.stream = pyte.Stream()
        self.vt = pyte.Screen(80, 24)
        self.stream.attach(self.vt)
        
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
                self.onReceiveText.emit(text.decode(errors='ignore'))
        
    def paintEvent(self, event):
        super().paintEvent(event)
        p = QtWidgets.QPainter()
        p.begin(self.viewport())
        self.moveCursorTo(self.vt.cursor)
        p.fillRect(self.cursorRect(), QtWidgets.QBrush(QtCore.Qt.white))
        p.end()
        
    def virtualCursorRect(self):
        textSize = QtWidgets.QFontMetrics(self.font()).size(0, ' ')
        r = QtCore.QRect(QtCore.QPoint(), textSize)
        textCursor = self.vt.cursor()
        r.moveTopLeft(QtCore.QPoint(0,0) + 
                      QtCore.QPoint(textCursor[0]*r.width(),
                                    textCursor[1]*r.height()))
        return r
    
    def moveCursorTo(self, pos):
        line = pos.y
        col = pos.x
        c = self.textCursor()
        c.setPosition(0, c.MoveAnchor)
        c.movePosition(c.Down, c.MoveAnchor, line+1);
        c.movePosition(c.NextCharacter, c.MoveAnchor, col);
        self.setTextCursor(c)
        
    @QtCore.Slot(str)
    def _appendText(self, text):
        self.stream.feed(text)
        self.setPlainText('\n'.join(self.vt.display))
    
    def keyPressEvent(self, event):
        if self.serial and self.serial.isOpen():
            try:
                text = {
                    QtCore.Qt.Key_Tab: lambda x: b"\t",
                    QtCore.Qt.Key_Backspace: lambda x: b"\x7f",
                    QtCore.Qt.Key_Up: lambda x: b"\033[A",
                    QtCore.Qt.Key_Down: lambda x: b"\033[B",
                    QtCore.Qt.Key_Left: lambda x: b"\033[D",
                    QtCore.Qt.Key_Right: lambda x: b"\033[C",
                }[event.key()](event.key())
            except KeyError:
                text = bytes(event.text(), 'utf-8')
            if text:
                self.serial.write(text)
            event.accept()
