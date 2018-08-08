# MDQC GUI (OSX)
# Version 0.1, 2013-10-28
# Copyright (c) 2013 AudioVisual Preservation Solutions
# All rights reserved.
# Released under the Apache license, v. 2.0

from PySide.QtCore import *
from PySide.QtGui import *
import os
from os import path, walk, getcwd, sep
from GUI import AboutMDQCGUI, Configuration
import logging
import datetime
import qcdict
import sys
import re
import subprocess
import csv

# lists to hold data between classes
# regexes: tuples of the form (int, value, regex object)
# tags: QLineEdits containing tag names
# ops: QComboBoxes indicating comparators
# vals: QLineEdits containing values
# adds: QPushButtons set to duplicate rows
global reportdir
regexes, tags, ops, vals, adds = [], [], [], [], []

reportdir = sys.executable[:sys.executable.rfind('/')] + "/../../.."
isReportDir = ""
print reportdir



# Main window for MDQC, primarily for navigation between functions
class MainWin(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.configuration = Configuration.Configuration()
        menubar = self.menuBar()

        #check if output dir available
        testLogpath = reportdir +str(sep) + "mdqc.log"
        try:
            open(path.abspath(testLogpath), 'w')

            print "Dirs created at passed -> " + testLogpath
        except Exception as e:
            print(e)
            print "Dirs created at failed -> " + testLogpath
            global isReportDir
            isReportDir = "reports" +str(sep)
            global reportdir
            reportdir = path.expanduser('~') +str(sep) + "Desktop"+str(sep) +"MDQC-0.4"+str(sep) ;


            if not os.path.exists(reportdir):
                os.makedirs(reportdir)
            if not os.path.exists(reportdir + "reports"):
                os.makedirs(reportdir + "reports")

            print "Dirs created at -> " + reportdir


        file = menubar.addMenu('&File')
        save = QAction('&Save Template', self)
        load = QAction('&Load Template', self)
        rdir = QAction('&Report Directory', self)
        quit = QAction('&Quit', self)
        tool = menubar.addMenu('&Tools')
        self.exif = QAction('&ExifTool', self)
        self.mnfo = QAction('&MediaInfo', self)
        self.about_mdqc_menu = QAction('&About MDQC', self)
        self.about_mdqc_menu.setShortcut('CTRL+,')

        self.tgroup = QActionGroup(self)
        self.exif.setActionGroup(self.tgroup)
        self.mnfo.setActionGroup(self.tgroup)
        self.tgroup.triggered.connect(self.onToolChange)
        self.exif.setCheckable(True)
        self.exif.setChecked(True)
        self.mnfo.setCheckable(True)
        file.addAction(self.about_mdqc_menu)
        file.addAction(save)
        file.addAction(load)
        file.addAction(rdir)
        file.addAction(quit)
        tool.addAction(self.exif)
        tool.addAction(self.mnfo)

        save.triggered.connect(self.saveTemplate)
        load.triggered.connect(self.loadTemplate)
        rdir.triggered.connect(self.reportDir)
        self.about_mdqc_menu.triggered.connect(self.aboutMDQC)

        quit.triggered.connect(qApp.quit)

        self.fbox = QLineEdit(self)
        self.dbox = QLineEdit(self)
        self.rbut = QPushButton("Metadata Rules")
        self.dbut = QPushButton("Scan Rules")
        self.scan = QPushButton("Begin Test")
        self.rd = QPushButton("...")
        self.dd = QPushButton("...")
        self.rd.setFixedSize(QSize(30, 20))
        self.dd.setFixedSize(QSize(30, 20))
        self.widget = QWidget(self)
        # self.setWindowTitle("Metadata Quality Control")
        self.layout = QGridLayout(self.widget)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # visible incase of mediainfo
        self.whichMediaFile = QLabel("File Type:")
        self.layout.addWidget(self.whichMediaFile, 0, 0)
        self.mediaFileType = QComboBox(self)
        self.mediaFileType.addItem("Original File")
        self.mediaFileType.addItem("MediaInfo File")
        self.layout.addWidget(self.mediaFileType, 0, 1)
        self.toggleMediaInfo(0)

        self.layout.addWidget(QLabel("Reference File:"), 1, 0)
        self.layout.addWidget(self.fbox, 1, 1)
        self.layout.addWidget(self.rd, 1, 2)
        self.layout.addWidget(self.rbut, 1, 3)

        self.layout.addWidget(QLabel("Directory to Scan:"), 2, 0)
        self.layout.addWidget(self.dbox, 2, 1)
        self.layout.addWidget(self.dd, 2, 2)
        self.layout.addWidget(self.dbut, 2, 3)

        #Start GUI for base file
        self.csvSelectInput = QLineEdit(self)
        self.layout.addWidget(QLabel("Base filenames:"), 3, 0);
        self.layout.addWidget(self.csvSelectInput, 3, 1)
        self.csvFileSelector = QPushButton("...")
        self.csvFileSelector.setFixedSize(QSize(30, 20))
        self.layout.addWidget(self.csvFileSelector, 3, 2)
        self.layout.addWidget(QLabel("Load CSV file"), 3, 3);
        self.csvFileSelector.clicked.connect(self.setCsvFile)
        #End GUI for base filenames

        self.layout.addWidget(self.scan, 4, 2, 1, 2)

        self.rbut.clicked.connect(self.validate)
        self.dbut.clicked.connect(self.dirrules)
        self.rd.clicked.connect(self.setr)
        self.dd.clicked.connect(self.setd)
        self.scan.clicked.connect(self.scanner)

        self.setCentralWidget(self.widget)
        self.about_mdqc_gui = AboutMDQCGUI.AboutMDQCGUI(self)
        try:
            self.setWindowIcon(QIcon(path.join(getcwd() + str(sep), 'assets'+str(sep)+'avpreserve-2.png')))
        except:
            try:
                self.setWindowIcon(QIcon(path.join(sys._MEIPASS, 'assets' + (str(sep)) + 'avpreserve-2.png')))
            except:
                pass
            pass


        self.setWindowTitle(self.configuration.getApplicationName() +' '+ self.configuration.getApplicationVersion())


    def toggleMediaInfo(self, status):
        if status == 1:
            self.whichMediaFile.show()
            self.mediaFileType.show()
        else:
            self.whichMediaFile.hide()
            self.mediaFileType.hide()

    def onToolChange(self):
        if self.mnfo.isChecked():
            self.toggleMediaInfo(1)
        else:
            self.toggleMediaInfo(0)


    # Checking for exif Tool and media Info tool if any single of these tool don't exists it will exit the Application
    def checkForTool(self):
        
        exif_tool_found = True
        exif_not_found_msg = "ExifTool not found. Please download the .dmg from the following url and install: <a href='http://www.sno.phy.queensu.ca/~phil/exiftool/'>http://www.sno.phy.queensu.ca/~phil/exiftool/</a>"
        mediainfo_not_found_msg = "MediaInfo not found. Please download the CLI version from the following url and install: <a href='http://mediaarea.net/en-us/MediaInfo/Download/Mac_OS'>http://mediaarea.net/en-us/MediaInfo/Download/Mac_OS</a>"
        try:
            subprocess.Popen(['/usr/bin/exiftool'])
            exifVersion = subprocess.check_output(['/usr/bin/exiftool', '-ver'])
            print exifVersion
        except OSError:
            try:
                subprocess.Popen(['/usr/local/bin/exiftool'])
                exifVersion = subprocess.check_output(['/usr/local/bin/exiftool','-ver'])
                print ">> + >> "
                print exifVersion
                print "<< + <<"
            except OSError as e:
                print e
                exif_tool_found = False
                print "exif_tool_found = false"
                pass



        media_info_found = True
        try:
            subprocess.Popen(['/usr/bin/mediainfo'])
        except OSError:
            try:
                subprocess.Popen(['/usr/local/bin/mediainfo'])
            except OSError:
                media_info_found = False
                pass


        if exif_tool_found is False and media_info_found is False:
            QMessageBox.critical(self,
                                 None,
                                str(exif_not_found_msg) + ' <br/> <br/>' + str(mediainfo_not_found_msg) )
            return False

        if exifVersion.strip() < 10.70:
            QMessageBox.critical(self,
                                 None,
                                 str("MDQC supports ExifTool version >= 10.70")  )
            return False

        elif exif_tool_found is False:
            QMessageBox.critical(self,
                                 None,
                                 exif_not_found_msg
                                 )
            return False


        elif media_info_found is False:
            QMessageBox.critical(self,
                                 None,
                                 mediainfo_not_found_msg )
            return False


        return True

    def validate(self):
        global isExif
        isExif = self.exif.isChecked()
        if self.fbox.text() != '' or len(tags) != 0:
            refMediaInfo = False
            if "MediaInfo File" == self.mediaFileType.currentText():
                refMediaInfo = True
            self.frule = TagRuleWin(self.fbox.text(), refMediaInfo)
        else:
            QMessageBox.warning(self, "Metadata Quality Control",
                                "No reference file selected!")

    # prompts user for filename/location of rules template to write out
    # rules templates use the following format:
    #
    # tagname	op int	value
    # [...]
    # ===   directory to scan
    # regex op value	value to match	regex
    def saveTemplate(self):
        dest = QFileDialog.getSaveFileName(dir=reportdir,
                    filter='MDQC Template (*.tpl)')[0]

        if self.mnfo.isChecked():
            toolUsed = 'tool===mi'
        else:
            toolUsed = 'tool===ef'

        f = open(dest, 'w+')
        for n in xrange(len(tags)):
            t = tags[n].text()
            i = ops[n].currentIndex()
            v = vals[n].text()
            o = t + "\t" + str(i) + "\t" + v + "\n"
            f.write(o.encode("utf-8"))
        f.write("===")
        f.write(self.dbox.text() + "\n")
        for n in xrange(len(regexes)):
            a = str(regexes[n][0]) + "\t" + regexes[n][1] + "\t" + \
                        regexes[n][2].pattern + "\n"
            f.write(a.encode("utf-8"))
        f.write(toolUsed)
        f.close()

    # reads template data from specified file, populating MDQC's settings
    def loadTemplate(self):
        del tags[:]
        del ops[:]
        del vals[:]
        del regexes[:]
        src = QFileDialog.getOpenFileName(dir=reportdir, filter='MDQC Template (*.tpl)')[0]
        f = open(src, 'r')
        rgx = False
        lines = f.readlines()
        f.close()
        for line in lines:

            if line.find('tool===') != -1:
                toolUsed = line.replace('tool===', '')
                if toolUsed == 'mi':
                    self.mnfo.setChecked(1)
                else:
                    self.exif.setChecked(1)

            elif len(line) > 2 and line[:3] == "===":
                self.dbox.setText(line[3:].rstrip())
                rgx = True
            elif not rgx:
                data = line.split('\t')
                try:
                    tags.append(QLineEdit(data[0]))
                except:
                    pass

                try:
                    vals.append(QLineEdit(data[2].decode("utf-8")))
                except:
                    pass

                o = QComboBox()
                o.addItems(['[Ignore Tag]', 'Exists', 'Does Not Exist',
                            'Is', 'Is Not', 'Contains', 'Does Not Contain',
                            'Is Greater Than', 'Is At Least', 'Is Less Than',
                            'Is At Most'])
                o.setCurrentIndex(int(data[1]))
                ops.append(o)
            elif rgx:
                data = line.split('\t')
                print "data: " + line
                regexes.append((data[0],data[1],re.compile(data[2].rstrip())))

    def reportDir(self):
        global reportdir
        reportdir = QFileDialog.getExistingDirectory(dir=reportdir)

    def aboutMDQC(self):
        self.about_mdqc_gui.Cancel()
        self.about_mdqc_gui = AboutMDQCGUI.AboutMDQCGUI(self)
        self.about_mdqc_gui.LaunchDialog()

    # invokes window to set directory rules
    def dirrules(self):
        self.dirs = DirRuleWin()

    # sets reference file from user option
    def setr(self):
        self.fbox.setText(QFileDialog.getOpenFileName(
                            dir=path.expanduser('~') + "/Desktop/")[0])
    # sets root directory from user option
    def setd(self):
        self.dbox.setText(QFileDialog.getExistingDirectory(
                            dir=path.expanduser('~') + "/Desktop/"))

    # begins test
    def scanner(self):
        useMediaInfoFile = False
        if self.mnfo.isChecked():
            toolUsed = 'mi'
            if "MediaInfo File" == self.mediaFileType.currentText():
                useMediaInfoFile  = True
        else:
            toolUsed = 'ef'
            #and (len(regexes) > 0 or self.csvSelectInput.text())
        if len(tags) != 0 and str(self.dbox.text()) != "":
            endsWith = ""
            try:
                print regexes
                for n in xrange(len(regexes)):
                    print regexes[n]
                    if regexes[n][0]  == 6:
                        endsWith = regexes[n][1]
            except:
                print "exc"

            filesList = {}
            k = 0
            # and endsWith != ""
            if endsWith == "":
                print "Empty EndsWith: " + endsWith
            if self.csvSelectInput.text() and self.csvSelectInput.text() != "" :
                with open(str(self.csvSelectInput.text()), 'r') as f:
                    print f
                    for row in csv.reader(f.read().splitlines()):
                        filesList[k] = row[0]
                        k = k + 1

            else:
                print "CSV file failed to parse."
            self.v = Scanner(str(self.dbox.text()).rstrip(), toolUsed, filesList, useMediaInfoFile)
        else:
            if len(tags) == 0:
                QMessageBox.warning(self, "Metadata Quality Control", "Cannot test - Metadata Rules must be set.")
            elif str(self.dbox.text()) == "":
                QMessageBox.warning(self, "Metadata Quality Control", "Cannot test - Scan Directory must be selected.")
            elif len(regexes) == 0 and self.csvSelectInput.text() == "":
                QMessageBox.warning(self, "Metadata Quality Control",
                                    "Cannot test - Please select Base file or set Scan Rules.")
            else:
                QMessageBox.warning(self, "Metadata Quality Control", "Cannot test - Please fill in all fields and try again.")





# sets csv file from user option
    def setCsvFile(self):
        self.csvSelectInput.setText(QFileDialog.getOpenFileName(
                            dir=path.expanduser('~') + "/Desktop/")[0])
        # self.clearer()

    # Window providing metadata rules settings
    # if no existing metadata is set, populate it from the reference file
    # otherwise, only provide metadata rules as set
class TagRuleWin(QWidget):
    def __init__(self, file, isMediaInfo):
        QWidget.__init__(self)
        self.scroll = QScrollArea()
        self.setWindowTitle("Rule Generation")
        self.layout = QVBoxLayout(self)
        self.slayout = QVBoxLayout(self)
        self.slayout.setContentsMargins(0, 0, 0, 0)
        self.slayout.setSpacing(0)
        self.val = QPushButton("Set Rules", self)
        self.val.clicked.connect(self.close)
        self.layout.addWidget(self.val)
        self.swidget = QWidget(self)
        self.swidget.setLayout(self.slayout)

        # if nothing was set, populate
        if tags == []:
            if isExif:
                dict = qcdict.exifMeta(file)
            else:
                if isMediaInfo:
                    dict = dict = qcdict.mnfoMeta(file, True) #self.parseMediaInfo(file)
                else:
                    dict = qcdict.mnfoMeta(file, False)

            sdict = sorted(dict)
            n = 0
            for d in sdict:
                self.addRow(d, 0, dict[d], n)
                n += 1

        # otherwise, use what's there
        else:
            xtags = tags[:]
            xops = ops[:]
            xvals = vals[:]
            del tags[0:len(tags)]
            del ops[0:len(ops)]
            del vals[0:len(vals)]
            for n in xrange(len(xtags)):
                self.addRow(xtags[n].text(), xops[n].currentIndex(),
                                xvals[n].text(), n)

        self.layout.addWidget(self.scroll)
        self.setLayout(self.layout)
        self.scroll.setWidget(self.swidget)
        self.scroll.setWidgetResizable(True)
        self.show()

        #Scan txt file for rules (metadata) instead of file
    def parseMediaInfo(self, fileName):
        import io
        print "Scanning : " + fileName
        f = io.open(fileName, mode="r", encoding="utf-8")
        from collections import defaultdict
        meta = defaultdict(list)
        for line in f:
            data = line.split(":", 1)
            if len(data) == 2 and not meta[data[0].strip()]:
                meta[data[0].strip()] = data[1].strip()
        f.close()
        print "Scannning compelete: "+fileName
        return meta

    # two functions to copy a row under itself
    def dupeRow(self):
        num = adds.index(self.sender())
        self.addRow(tags[num].text(), 0, vals[num].text(), num)

    def addRow(self, tag, oper, val, r):
        op = QComboBox()
        op.addItems([
                    '[Ignore Tag]', 'Exists', 'Does Not Exist', 'Is', 'Is Not',
                    'Contains', 'Does Not Contain', 'Is Greater Than',
                    'Is At Least', 'Is Less Than', 'Is At Most'])
        op.setCurrentIndex(oper)
        tline = QLineEdit()
        vline = QLineEdit()
        add = QPushButton("+")
        add.setFixedSize(QSize(30, 20))
        add.clicked.connect(self.dupeRow)
        tline.setText(tag)
        vline.setText(val)
        tline.setCursorPosition(0)
        vline.setCursorPosition(0)

        tags.insert(r, tline)
        ops.insert(r, op)
        vals.insert(r, vline)
        adds.insert(r, add)

        row = QHBoxLayout()
        row.addWidget(tags[r])
        row.addWidget(ops[r])
        row.addWidget(vals[r])
        row.addWidget(adds[r])

        self.slayout.insertLayout(r+1, row)

    # purges empty (no comparator set) rows from global arrays
    def closeEvent(self, event):
        for n in reversed(ops):
            if n.currentIndex() == 0:
                q = ops.index(n)
                del tags[q]
                del ops[q]
                del vals[q]
                del adds[q]
        event.accept()
        self.scroll.close()

# window to set file matching rules
class DirRuleWin(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.field, self.op, self.val, self.add = [], [], [], []

        self.setWindowTitle("File Matching Rules")
        self.scroll = QScrollArea()
        self.layout = QVBoxLayout(self)
        self.dlayout = QVBoxLayout()
        self.dlayout.setContentsMargins(0, 0, 0, 0)
        self.dlayout.setSpacing(0)

        self.dwidget = QWidget(self)
        self.dwidget.setLayout(self.dlayout)
        self.validator = QPushButton("Set Rules", self)
        self.validator.clicked.connect(self.sendOut)
        self.layout.addWidget(self.validator)

        # if rules are already set, display them
        # otherwise, create two rows to get the user started
        if regexes != []:
            for n in xrange(len(regexes)):
                self.addRow(regexes[n][0], regexes[n][1], n)
        else:
            self.addRow(2, '', 0)
            self.addRow(5, '', 1)
        self.layout.addWidget(self.scroll)
        self.scroll.setWidget(self.dwidget)
        self.scroll.setWidgetResizable(True)
        self.show()

    def dupeRow(self):
        num = self.add.index(self.sender())
        self.addRow(self.op[num].currentIndex(), self.val[num].text(), num+1)

    def addRow(self, oper, value, r):
        op = QComboBox()
        op.addItems(['[Ignore]', 'Directory Begins With', 'Directory Contains',
                    'Directory Ends With', 'Filename Begins With',
                    'Filename Contains', 'Filename Ends With'])
        op.setCurrentIndex(int(oper))
        vline = QLineEdit()
        add = QPushButton("+")
        add.setFixedSize(QSize(30, 20))
        add.clicked.connect(self.dupeRow)
        vline.setText(value)
        vline.setCursorPosition(0)

        self.op.insert(r, op)
        self.val.insert(r, vline)
        self.add.insert(r, add)

        row = QHBoxLayout()
        row.addWidget(self.op[r])
        row.addWidget(self.val[r])
        row.addWidget(self.add[r])

        self.dlayout.insertLayout(r+1, row)

    def sendOut(self):
        del regexes[0:len(regexes)]
        for n in xrange(len(self.op)):
            if self.val[n].text() != "":
                v = str(self.val[n].text())
                if self.op[n].currentIndex() == 1:
                    regexes.append((1, v, re.compile("/" + v)))
                if self.op[n].currentIndex() == 2:
                    regexes.append((2, v, re.compile("/.*" + v + ".*/")))
                if self.op[n].currentIndex() == 3:
                    regexes.append((3, v, re.compile(v + "/")))
                if self.op[n].currentIndex() == 4:
                    regexes.append((4, v, re.compile("/" + v + "[^/]*$")))
                if self.op[n].currentIndex() == 5:
                    regexes.append((5, v, re.compile("/.*" + v + "[^/]*$")))
                if self.op[n].currentIndex() == 6:
                    regexes.append((6, v, re.compile(v + "$")))
        self.close()
		
# window to display test results
class Scanner(QWidget):

    def __init__(self, dir, toolUsed='ef', csvFile = '', useMediaInfoFile = False):

        QWidget.__init__(self)
        self.useMediaInfoFile = useMediaInfoFile
        self.d = dir.rstrip()
        self.toolUsed = toolUsed
        self.db = self.makeList()
        self.csvFile = csvFile

        self.setWindowTitle('Metadata Quality Control')
        self.lay = QVBoxLayout(self)
        xit = QPushButton("Exit", self)
        xit.setEnabled(False)
        xit.clicked.connect(self.closeScanner)
        self.te = QTextEdit(self)
        self.te.setReadOnly(True)
        self.lay.addWidget(self.te)
        self.lay.addWidget(xit)
        self.setLayout(self.lay)
        self.resize(800, 300)
        self.show()

        self.test(self.useMediaInfoFile)
        xit.setEnabled(True)



    def closeScanner(self):
        self.close()

    def makeList(self):
        rules = []
        for n in xrange(len(tags)):
            t = str(tags[n].text())
            i = ops[n].currentIndex()
            v = vals[n].text()
            rules.append((t, i, v))
        return rules

    def test(self, useMediaInfoFile = False):
        documentPath = os.path.expanduser('~/Documents/') +'MDQC Reports'+str(sep)

        if not os.path.exists(documentPath):
            try:
                os.makedirs(documentPath)
            except Exception as e:
                print(e)
                print "errors creating Directory: " + documentPath
                self.te.append("documentPath: " + documentPath)
                self.te.append("Some error occured while opening the file. " + "\n")

        file_name_of_report =  str(datetime.datetime.now()).replace(' ', '').replace(':', ''). \
                replace('-', '').rpartition('.')[0] + ".tsv"
        rpath = documentPath  + "report_" + file_name_of_report

        try:
            report = open( rpath, "w")
        except Exception as e:
            print(e)
            print "errors creating file: " + rpath
            self.te.append("rpath: " + rpath)
            self.te.append("Some error occured while opening the file. " + "\n")


        report.write("METADATA QUALITY CONTROL REPORT\n" + \
                        str(datetime.datetime.now()).rpartition('.')[0] + \
                        "\n\nMETADATA RULES USED\n")
        for n in xrange(len(tags)):
            q = tags[n].text() + "\t" + ops[n].currentText() + \
                    "\t"

            try:
                report.write(q)
            except Exception as e:
                print(e)
                try:
                    report.write(q.decode("utf-8"))
                except:
                    try:
                        report.write(q.encode("utf-8"))
                    except:
                        pass
                    pass

            try:
                report.write(vals[n].text().encode('latin1'))
            except:
                try:
                    report.write(vals[n].text())
                except:
                    pass
                pass

            report.write("\n")

        report.write("\nSCANNING RULES USED\n")
        for n in xrange(len(regexes)):
            r = regexes[n][1]
            if regexes[n][0] == 1:
                report.write(u"Directory begins with " + \
                                r.encode("utf-8") + u"\n")
            if regexes[n][0] == 2:
                report.write(u"Directory contains " + \
                                r.encode("utf-8") + u"\n")
            if regexes[n][0] == 3:
                report.write(u"Directory ends with " + \
                                r.encode("utf-8") + u"\n")
            if regexes[n][0] == 4:
                report.write(u"Filename begins with " + \
                                r.encode("utf-8") + u"\n")
            if regexes[n][0] == 5:
                report.write("Filename contains " + \
                                r.encode("utf-8") + u"\n")
            if regexes[n][0] == 6:
                report.write("Filename ends with " + \
                                r.encode("utf-8") + u"\n")
        if len(regexes) == 0:
            report.write("Match all files\n")
        fls = []
        report.write("\nVALIDATION\n")
        # if self.csvFile:
        #     for f in self.csvFile:
        #         print self.csvFile[f]
        #         fls.append( path.join(self.d, self.csvFile[f]) )
        # else:
        r = {}
        for root, subFolders, files in walk(self.d):
            for file in files:
                if len(regexes) <= 0 and len(self.csvFile) <= 0:
                    fls.append(path.join(root, file))
                elif len(regexes) <= 0 and len(self.csvFile) > 0:
                    for f in self.csvFile:
                        if self.csvFile[f] in path.join(root, file):
                            fls.append(path.join(root, file))
                elif len(regexes) > 0 and len(self.csvFile) > 0:
                    add_file = 0
                    for r in regexes:
                        if all(r[2].search(path.join(root, file)) for r in regexes):
                            add_file = 1
                        else:
                            add_file = 0
                            break

                    if add_file == 1:
                        if len(self.csvFile) > 0:
                            for f in self.csvFile:
                                if self.csvFile[f] in path.join(root, file):
                                    fls.append(path.join(root, file))
                        else:
                            fls.append(path.join(root, file))
                elif len(regexes) > 0 and len(self.csvFile) <= 0:
                    if all(r[2].search(path.join(root, file)) for r in regexes):
                        fls.append(path.join(root, file))


        if self.toolUsed == 'ef':
            self.te.append("\nTool:: ExifTool \n")
        else:
            self.te.append("\nTool:: MediaInfo \n")

        self.te.append("Found " + str(len(fls)) + " matching files to validate")

        report.write("Files found\t\t" + str(len(fls)) + "\n")
        QCoreApplication.processEvents()
        QCoreApplication.processEvents()
        out = ""
        fails = 0

        logging.basicConfig(filename=reportdir+"mdqc.log", level=logging.INFO)
        # logging.basicConfig(filename="mdqc.log", level=logging.INFO)

        for rf in fls:
            logging.info("Validating " + rf)

            try:

                if self.toolUsed == 'ef':
                    l = qcdict.validate(rf, self.db, isExif)
                else:
                    l = qcdict.validate(rf, self.db, False, useMediaInfoFile)


            except Exception, e:
                logging.exception(e)
                continue

            if not ": PASSED" in l[0].decode('utf8'):
                fails += 1

            logging.info("Appending to output..")
            self.te.append(l[0].rstrip())
            logging.info("Encoding to UTF8 and appending...")
            ul = l[1].decode('utf8')
            out += ul
            logging.info("Processing events...")
            QCoreApplication.processEvents()

        report.write("Files failed\t\t" + str(fails))

        try:
            report.write("\n\n" + out)
        except:
            try:
                report.write("\n\n" + out.decode('utf-8'))
            except:

                report.write("\n\n" + out.encode('utf-8'))

                pass
            pass

        self.te.append("Wrote report to " + path.abspath(rpath))
        report.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWin()
    response = w.checkForTool()
    if response:
        w.show()
        sys.exit(app.exec_())