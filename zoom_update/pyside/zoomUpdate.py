# -*- coding: UTF-8 -*-
'''
pyside-uic zoomUpdate.ui -o zoomUpdate_ui.py

pyside-uic NE_Dialog.ui -o NE_Dialog_ui.py
'''
import sys
from PySide.QtGui import QMainWindow, QStandardItemModel , QStandardItem , QFileDialog, QApplication, QMessageBox, QAction, QDesktopWidget
from PySide.QtGui import QDialog
from PySide.QtCore import QObject , Qt  , QDir , QTranslator, SIGNAL, SLOT 

from PySide.QtGui import QAbstractItemDelegate, QStyleOptionProgressBar, QStyle, QStyledItemDelegate
from PySide.QtCore import QRegExp
from PySide.QtGui import QRegExpValidator

from ui.zoomUpdate_ui import Ui_MainWindow
from ui.NE_Dialog_ui import Ui_Dialog
from control.fileCheck import fileCheck, OPEN_FILE_OK, VERIFY_VERSION_OK
from control.config import *
from pyparsing import Word,Combine,Literal,nums

#错误码
ZOOM_UPDATE_CODE_BASE = 1000
ZOOM_OK =  ZOOM_UPDATE_CODE_BASE + 0
IP_ERR  =  ZOOM_UPDATE_CODE_BASE + 1

class editNEDialog(QDialog):
    def __init__(self,parent=None):
        super(editNEDialog,self).__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        #对IP输入框增加校验
        rx= QRegExp("((2[0-4]\d|25[0-5]|[01]?\d\d?)\.){3}(2[0-4]\d|25[0-5]|[01]?\d\d?)");
        validator =QRegExpValidator(rx,self)
        self.ui.lineEditIP.setValidator(validator)
        
        QObject.connect(self.ui.pushButtonOK, SIGNAL("clicked()"), self, SLOT("confirm()"))

                
    def ipCheck(self,IPtext):
        '''
                      校验IP地址是否正确
        '''
        IP_SECTION_1="IP1"
        IP_SECTION_4="IP4"
        IP=Combine(   Word(nums).setResultsName(IP_SECTION_1)+Literal(".") 
                    + Word(nums)+Literal(".")
                    + Word(nums)+Literal(".") 
                    + Word(nums).setResultsName(IP_SECTION_4)
                  )
        try:
            result = IP.searchString(IPtext)
            if int(result[0][IP_SECTION_1]) == 0:
                return IP_ERR

            if int(result[0][IP_SECTION_4]) == 0:
                return IP_ERR
        except:    
            return IP_ERR
        return ZOOM_OK
                    
                    
    def confirm(self):
        '''
                     确认按钮连接的slot,用来创建网元
        '''
        message=""
        neName         = self.ui.lineEditNE.text()
        neIp           = self.ui.lineEditIP.text()
        manageUserName = self.ui.lineEditManageUser.text()
        managePassword = self.ui.lineEditManagePassword.text()
        accessUserName = self.ui.lineEditAccessUser.text()
        accessPassword = self.ui.lineEditAccessPassword.text()
                
        if (neName         == "" or  
            neIp           == "" or
            accessUserName == "" or  
            accessPassword == "" or 
            manageUserName == "" or
            managePassword == ""):
            message=u"有输入框为空，请完成！"
            QMessageBox.information(self,u"警告",message)
            return
        
#         if neName=="":
#             message+=u"网元名称为空，请输入\n"
#         
#         if neIp=="":
#             message+=u"IP地址为空，请输入\n"
#                     
#         if accessUserName=="":
#             message+=u"管理平台用户为空，请输入\n"
# 
#         if accessPassword=="":
#             message+=u"管理平台密码为空，请输入\n"
# 
#         if manageUserName=="":
#             message+=u"接入平台密码为空，请输入\n"
# 
#         if managePassword=="":
#             message+=u"接入平台密码为空，请输入\n"
#         
#         if message!="":
#             QMessageBox.information(self,u"警告",message)
#             return
        
        if self.ipCheck(self.ui.lineEditIP.text()) != ZOOM_OK:
            message=u"IP地址格式不正确"
            QMessageBox.information(self,u"警告",message)
            
        
        
        
        ne =NE(neName,neIp,accessUserName,accessPassword,manageUserName,managePassword)
        
        self.accept()
        
#         print self.parent().NEs


class updateProgress(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.column() == showColumn[UPDATE_STATE]:
#             progress = index.data().toInt();
#             print "index data =" + index.data()
            progressBarOption = QStyleOptionProgressBar();  
            progressBarOption.rect = option.rect;  
            progressBarOption.minimum = 0;  
            progressBarOption.maximum = 100;  
            progressBarOption.progress = 50;  
         
            progressBarOption.text = str(50) + "%";  
            progressBarOption.textVisible = True;  
             
            QApplication.style().drawControl(QStyle.CE_ProgressBar, progressBarOption, painter); 
        else:
            QStyledItemDelegate.paint(self, painter, option, index)    
            
    
class updateWindow(QMainWindow):
    def __init__(self, _app, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.netModel = QStandardItemModel()
        self.ui.tableViewNet.setItemDelegate(updateProgress())
        
        for key in showColumn.keys():
            self.netModel.setHorizontalHeaderItem(showColumn[key], QStandardItem(key))
        self.ui.tableViewNet.setModel(self.netModel)
       
        QObject.connect(self.ui.pushButtonAddNe, SIGNAL("clicked()"), self, SLOT("addNe()"))
        QObject.connect(self.ui.pushButtonDelNe, SIGNAL("clicked()"), self, SLOT("delNe()"))
             
        QObject.connect(self.ui.pushButtonAddVersionFile, SIGNAL("clicked()"), self, SLOT("addVersionFile()"))
        QObject.connect(self.ui.actionImportConfig, SIGNAL("activated()"), self, SLOT("importConfig()"))
        QObject.connect(self.ui.actionSavetConfig, SIGNAL("activated()"), self, SLOT("saveConfig()"))
        
        
#         QObject.connect(self.ui.pushButtonCheckNe, SIGNAL("clicked()"), self, SLOT("checkNe()"))
        QObject.connect(self.ui.pushButtonUpdateAll, SIGNAL("clicked()"), self, SLOT("updateAll()"))
        
        QObject.connect(self.ui.pushButtonCheckNe, SIGNAL("clicked()"), self, SLOT("test()"))
        
        self.versionFile     = None
        self.versionFilePath = None
        self.config = None
        self.NEs={}
        self.Dialog = None
        
        
    def checkNe(self):
        '''
                     检查网元
        '''
        self.ui.textEditInformation.setText(u"开始检查网元")
        for row in self.NEs.keys():
            result = self.NEs[row].checkNe()
            if result != NE_OK:
                pass
            else:
                model = self.ui.tableViewNet.model()
                
#                 name = QStandardItem(NE.neName)
#                 name.setCheckable(True)
#                 model.setItem(row, showColumn[NE_NAME], name)
                
                model.setItem(row, showColumn[NE_IP]               , QStandardItem(self.NEs[row].neIp))
#                 model.setItem(row, showColumn[ACCESS_USER]         , QStandardItem(self.NEs[row].accessUserName))
#                 model.setItem(row, showColumn[ACCESS_PASSWORD]     , QStandardItem(self.NEs[row].accessPassword))
#                 model.setItem(row, showColumn[MANAGE_USER]         , QStandardItem(self.NEs[row].manageUserName))
#                 model.setItem(row, showColumn[MANAGE_PASSWORD]     , QStandardItem(self.NEs[row].managePassword))
#                 print self.NEs[row].softwareVersion
                model.setItem(row, showColumn[SOFTWARE_VERSION]    , QStandardItem(self.NEs[row].softwareVersion))
                model.setItem(row, showColumn[HARDWARE_VERSION]    , QStandardItem(self.NEs[row].hardwareVersion))
                model.setItem(row, showColumn[MASTER_SLAVE_STATE]  , QStandardItem(self.NEs[row].masterSlaveState))
                model.setItem(row, showColumn[NE_STATE]            , QStandardItem(self.NEs[row].neState))
                model.setItem(row, showColumn[UPDATE_STATE]        , QStandardItem(self.NEs[row].processState))

   
        self.ui.textEditInformation.setText(u"检查网元结束")
        pass
    
    
    def updateAll(self):
        '''
                     开始升级
        '''
        if self.versionFile == None:
            Info = u"版本文件不可用，请配置好相关文件后再升级"
            QMessageBox.information(self,u"警告",Info)
        
        for ne in self.NEs.keys():
            result = ne.checkNe()
            if result != NE_OK:
                pass
            else:
                model = self.ui.tableViewNet.model()
                row = self.NEs[ne]
                ne.saveNeConfigToLocal("test")
                ne.updateVersionFile(self.versionFile,self.versionFilePath)
                ne.updateSoft(self.versionFile,ne.willUpdateSoftPartition)
                
                
        self.ui.textEditInformation.setText(u"开始升级网元")
        
        
    def showConfig(self):
        '''
                      将导入的配置显示到界面上
        '''
        if self.config != None:
            print self.config.getNeLists()
            for ne in self.config.getNeLists().values():
                print ne
                self.addNe(ne)
            
            
    def importConfig(self):
        '''
                      从配置文件中导入配置
        '''
        configFile = QFileDialog.getOpenFileName(self, u"Load config File", QDir.currentPath(), filter="*.conf")
        if configFile != None:
            config = updateConfig()
            config.readConfig(configFile)
            if self.config != None:
                del self.config
            self.config = config    
            self.showConfig()
        
        
    
    def saveConfig(self):
        '''
                     保存当前升级配置，主要是网元信息
        '''
        configFile = QFileDialog.getOpenFileName(self, u"Load config File", QDir.currentPath(), filter="*.conf")
        if configFile != None:
            pass
        
    def test(self):
        print self.Dialog
        print self.Dialog.destroyed        
        print self.Dialog.finished
        
    def addNe(self, ne=NE()):
        '''
                      添加网元操作
        '''
#         if self.Dialog != None:
#             self.Dialog. 
            
        testDialog= editNEDialog(self)
        res=testDialog.exec_()
        print res
        self.Dialog = testDialog
        
        
#         print ne
#         index = self.ui.tableViewNet.selectionModel().currentIndex()
#         model = self.ui.tableViewNet.model()
#        
#         row = model.rowCount(index.parent())
#         
#         name = QStandardItem(ne.neName)
#         name.setCheckable(True)
#         model.setItem(row, showColumn[NE_NAME], name)
# 
#         model.setItem(row, showColumn[NE_IP]               , QStandardItem(ne.neIp))
#         model.setItem(row, showColumn[ACCESS_USER]         , QStandardItem(ne.accessUserName))
#         model.setItem(row, showColumn[ACCESS_PASSWORD]     , QStandardItem(ne.accessPassword))
#         model.setItem(row, showColumn[MANAGE_USER]         , QStandardItem(ne.manageUserName))
#         model.setItem(row, showColumn[MANAGE_PASSWORD]     , QStandardItem(ne.managePassword))
#         model.setItem(row, showColumn[SOFTWARE_VERSION]    , QStandardItem(ne.softwareVersion))
#         model.setItem(row, showColumn[HARDWARE_VERSION]    , QStandardItem(ne.hardwareVersion))
#         model.setItem(row, showColumn[MASTER_SLAVE_STATE]  , QStandardItem(ne.masterSlaveState))
#         model.setItem(row, showColumn[NE_STATE]            , QStandardItem(ne.neState))
#         model.setItem(row, showColumn[UPDATE_STATE]        , QStandardItem(ne.processState))
#         
# 
#         for key in showColumn.keys():
#             model.item(row, showColumn[key]).setTextAlignment(Qt.AlignCenter);
# 
#         self.NEs[row]=ne
#         print "add Net end"		


    
    def delNe(self):
        '''
                     删除网元操作
        '''
        if self.ui.tableViewNet.selectionModel().hasSelection():
            currentIndex=self.ui.tableViewNet.selectionModel().currentIndex()
            model = self.ui.tableViewNet.model()
            model.removeRow(currentIndex.row(),currentIndex.parent())
            print self.NEs
            print currentIndex.row()
#             del self.NEs[currentIndex.row()]
#             print self.NEs
            self.NEs.pop(currentIndex.row())
            print self.NEs
            print self.NEs[currentIndex.row()] 
        else:
            
            Info = u"没有选中网元！请选中后，再操作。"
            QMessageBox.information(self,u"警告",Info)
            print "no NE select"
        
        print "del NE end"     
            

    def addVersionFile(self):
        '''
                     添加版本文件
        '''
        self.ui.lineEditVersion.setText("")
        openFile = QFileDialog.getOpenFileName(self, "Find Files", QDir.currentPath())
        
        if openFile != None :
            self.ui.lineEditVersionFile.setText(openFile[0])
            versionFile = fileCheck(openFile[0])
            if versionFile.getVersion() != OPEN_FILE_OK :
                self.versionFile=None
                self.ui.lineEditVersion.setText(u"版本文件无法打开")
                return
            else:
                if versionFile.verifyVersion() != VERIFY_VERSION_OK:
                    self.versionFile=None
                    self.ui.lineEditVersion.setText(u"版本文件无法校验")
                    return
                        
        self.ui.lineEditVersion.setText(versionFile.version["version"])
        self.versionFilePath = openFile[0][0:len(openFile[0])- len(versionFile.version["version"])]   
        self.versionFile = versionFile.version["version"]    
        
        print self.versionFilePath
        print self.versionFile
          
def main():
    app = QApplication(sys.argv)
    app.setStyle("cleanlooks")
#    app.setStyle("arthurStyle")
    d = updateWindow(app)
    d.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()    
