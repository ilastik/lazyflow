#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010, 2011 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#    
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#    
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#    
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

from PyQt4.QtGui import QDialog, QGridLayout, QGroupBox, QLabel, QVBoxLayout

#*******************************************************************************
# s h o r t c u t M a n a g e r                                                *
#*******************************************************************************

class shortcutManager():
    def __init__(self):
        self.shortcuts = dict()
        
    def register(self, shortcut, group, description):
        if not group in self.shortcuts:
            self.shortcuts[group] = dict()
        self.shortcuts[group][shortcut.key().toString()] = description
        
    def showDialog(self, parent=None):
        dlg = shortcutManagerDlg(self, parent)

#*******************************************************************************
# s h o r t c u t M a n a g e r D l g                                          *
#*******************************************************************************

class shortcutManagerDlg(QDialog):
    def __init__(self, s, parent=None):
        QDialog.__init__(self, parent)
        self.setModal(False)
        self.setWindowTitle("Shortcuts")
        self.setMinimumWidth(500)
        if len(s.shortcuts)>0:
            tempLayout = QVBoxLayout()
            
            for group in s.shortcuts.keys():
                grpBox = QGroupBox(group)
                l = QGridLayout(self)
                
                for i, sc in enumerate(s.shortcuts[group]):
                    desc = s.shortcuts[group][sc]
                    l.addWidget(QLabel(str(sc)), i,0)
                    l.addWidget(QLabel(desc), i,1)
                grpBox.setLayout(l)
                tempLayout.addWidget(grpBox)
            
            self.setLayout(tempLayout)
            self.show()
        else:
            l = QVBoxLayout()
            l.addWidget(QLabel("Load the data by pressing the \"New\" button in the project dialog"))
            self.setLayout(l)
            self.show()
            
shortcutManager = shortcutManager()