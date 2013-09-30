# -*- coding: UTF-8 -*-
'''
pyside-uic zoomUpdate.ui -o zoomUpdate_ui.py

pyside-uic NE_Dialog.ui -o NE_Dialog_ui.py
'''
import sys,time
# from PySide.QtGui import QMainWindow, QStandardItemModel , QStandardItem , QFileDialog, QApplication, QMessageBox, QAction, QDesktopWidget
# from PySide.QtGui import QDialog
# from PySide.QtCore import QObject , Qt  , QDir , QTranslator, SIGNAL, SLOT 
# 
# from PySide.QtGui import QAbstractItemDelegate, QStyleOptionProgressBar, QStyle, QStyledItemDelegate
# from PySide.QtCore import QRegExp,QTimer,QThread
# from PySide.QtGui import QRegExpValidator

from PySide.QtCore import *
from PySide.QtGui import *

from ui.zoomUpdate_ui import Ui_MainWindow
from ui.NE_Dialog_ui import Ui_Dialog
from control.fileCheck import fileCheck, OPEN_FILE_OK, VERIFY_VERSION_OK
from control.config import *
from control.debug import uiDebug
from pyparsing import Word,Combine,Literal,nums

#错误码
ZOOM_UPDATE_CODE_BASE = 1000
ZOOM_OK   =  ZOOM_UPDATE_CODE_BASE + 0
IP_ERR    =  ZOOM_UPDATE_CODE_BASE + 1
NE_NOT_EXIST  =  ZOOM_UPDATE_CODE_BASE + 2
NE_NAME_EXIST =  ZOOM_UPDATE_CODE_BASE + 3
NE_IP_EXIST   =  ZOOM_UPDATE_CODE_BASE + 4
EMIT_SIGNAL_ERR =  ZOOM_UPDATE_CODE_BASE + 5
EMIT_SIGNAL_OK  =  ZOOM_UPDATE_CODE_BASE + 6

#界面显示表头
showColumn  = {NE_NAME           : 0  ,
              NE_IP              : 1  ,
              SOFTWARE_VERSION   : 2  ,    
              HARDWARE_VERSION   : 3  ,
              MASTER_SLAVE_STATE : 4  ,     
              NE_STATE           : 5  ,
              UPDATE_STATE       : 6  ,
             }

class NESignal(QObject):
    sig = Signal(str)


class NeThread(QThread):
    FUN_ERR ="thread_fun_err"
    FUN_OK  ="thread_fun_ok"
    FINISH_ALL_FUN="thread_all_ok"
    
    
    RUN_RUSULT="run_result"
    RUN_FUN   ="run_fun"
    RUN_RUSULT_DETIAL="run_result_detial"
    
    funStr    =Combine(CaselessLiteral(":")+Regex("<(.)*>").setResultsName(RUN_FUN))
    detialStr =Combine(CaselessLiteral("=")+Word(printables).setResultsName(RUN_RUSULT_DETIAL))
    emitPyparsingStr=oneOf(FUN_ERR+" "+FUN_OK+" "+FINISH_ALL_FUN,caseless=False).setResultsName(RUN_RUSULT)+funStr+detialStr
    
         
    def __init__(self,parent = None):
        super(NeThread,self).__init__(parent)
        self.funs         = []  #线程需要运行的函数
        self.funsArgs     = {}  #线程调用函数时需要用到的参数
        self.exceptResult = {}  #线程调用函数后的预期正确的返回结果
        self.realResult   = {}  #线程调用函数后的返回结果
        self.emit         = {}  #线程调用完毕后发送的信号
        self.signal = NESignal()
        
    def clearThreadfun(self):
        '''删除线程函数列表'''
        self.funs=[]
        self.funsArgs.clear()
        self.realResult.clear()
        self.emit.clear()
#         self.signal.disconnect()
        
    def setThreadfun(self,fun,exceptResult,emit=None,*args): 
        '''
                     设置进程计划运行的函数,excepResult函数预期的返回值，
        emit函数执行成功后发出的信号，如果emit为空，则不会有成功信号
                     当函数执行失败时会发出self.FUN_ERR信号
        '''
        self.funs.append(fun)
        self.funsArgs[fun]= args
        self.exceptResult[fun]= exceptResult
        self.realResult[fun]= None
        self.emit[fun] = emit 
          
    def setEmit(self,fun,string):
        '''
                     一般通过self.realResult对函数运行记过进行判，
                     如果当信号有特殊要求时，可以设置信号来传递参数
        '''
        self.emit[fun] = string     
         
    def run(self):
        '''运行NE thread'''
        uiDebug("")
        uiDebug("")
        uiDebug("**** NeThread run stat ")
        print self.funs
        uiDebug("")
        uiDebug("")
        for fun in self.funs:
            
            #运行函数，将函数的运行结果保留到，self.realResult[fun]
            uiDebug("**** NeThread run fun: %s "%(str(fun)))
            if len(self.funsArgs[fun]) != 0:
                result=fun(*self.funsArgs[fun])
            else:
                result=fun()
            self.realResult[fun]=result

            
            #如果结果不符合预期，线程停止运行，发出thread_fun_err=附加码的信号,这里的附加码是预设值
            if result!=self.exceptResult[fun]:
                self.signal.sig.emit(self.FUN_ERR+":"+str(fun)+"="+str(self.emit[fun]))
                uiDebug(self.FUN_ERR+":"+str(fun)+"="+str(self.emit[fun]))
                uiDebug("**** NeThread run end 1")
                return
            else:
            #如果结果符合预期，线程停止运行，发出thread_fun_ok=附加码的信号,这里的附加码是预设值    
                if self.emit[fun]!=None:
                    self.signal.sig.emit(self.FUN_OK+":"+str(fun)+"="+str(self.emit[fun]))
                    uiDebug(self.FUN_OK+":"+str(fun)+"="+str(self.emit[fun]))
                
        #当所有函数运行完毕后，发出self.FINISH_ALL_FUN信号    
        self.signal.sig.emit(self.FINISH_ALL_FUN+":"+str(fun)+"="+str(self.emit[fun]))
        uiDebug(self.FINISH_ALL_FUN+":"+str(fun)+"="+str(self.emit[fun]))
        uiDebug("**** NeThread run end ")
        uiDebug("")
        uiDebug("")        
        return 


def pyparsingEmit(Data):
    '''
           解析传递的信号，信号格式为 "执行结果:执行函数=结果细节
          解析后返回有两种情况：
          1.  返回EMIT_SIGNAL_ERR
          2.  列表[RUN_RUSULT，RUN_FUN，RUN_RUSULT_DETIAL]     
    '''
    uiDebug("")
    uiDebug("***pyparsingEmit start")
    uiDebug("pyparsing data: %s"%(Data))
    resultValue=[]
    result=NeThread.emitPyparsingStr.searchString(Data)
    uiDebug("pyparsing result: %s"%(str(result)))
    if len(result)==0:
        uiDebug("return EMIT_SIGNAL_ERR")
        uiDebug("***pyparsingEmit end")
        uiDebug("")
        return EMIT_SIGNAL_ERR
    
    resultCode=result[0][NeThread.RUN_RUSULT]
    resultFun= result[0][NeThread.RUN_FUN]
    resultDetail= result[0][NeThread.RUN_RUSULT_DETIAL]
    
    resultValue.append(resultCode)
    resultValue.append(resultFun)
    resultValue.append(resultDetail)
    return resultValue
    uiDebug("return value %s"%(str(resultValue)))
    uiDebug("***pyparsingEmit end")
    uiDebug("")
    
class editNEDialog(QDialog):
    '''网元信息编辑框'''
    def __init__(self,parent=None):
        super(editNEDialog,self).__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        #对IP输入框增加校验
        rx= QRegExp("((2[0-4]\d|25[0-5]|[01]?\d\d?)\.){3}(2[0-4]\d|25[0-5]|[01]?\d\d?)");
        validator =QRegExpValidator(rx,self)
        self.ui.lineEditIP.setValidator(validator)
        
        QObject.connect(self.ui.pushButtonOK, SIGNAL("clicked()"), self, SLOT("confirm()"))
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.thread=NeThread()
        self.thread.signal.sig.connect(self.finish)
        self.ne = None     
        self.status= None    
                
    def finish(self,Data):
        '''thread运行确认slot，用于判断线程运行结果'''
        result = pyparsingEmit(Data)
        
        if  result !=EMIT_SIGNAL_ERR:
            runResult = result[0]

            if runResult == NeThread.FINISH_ALL_FUN:
                    self.parent().tempNe=self.ne
                    self.accept()
                    return
                
            if runResult == NeThread.FUN_ERR:
                if self.thread.realResult[self.ne.telnetManagePlatformTest] != NE_OK:
                    message=u"无法telnet管理平台，请检查！"
                    QMessageBox.information(self,u"警告",message)
                    self.setEnabled(True)
                    return
                
                if self.thread.realResult[self.ne.telnetAccessPlatformTest] != NE_OK:   
                    message=u"无法telnet接入平台，请检查！"
                    QMessageBox.information(self,u"警告",message)
                    self.setEnabled(True)
                    return
        else:
            uiDebug("receive without control message: %s"%(Data))
            
                                
    def ipCheck(self,IPtext):
        '''校验IP地址是否正确'''
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
        '''确认按钮连接的slot,用来创建网元'''
        uiDebug("**** editNEDialog confirm start")
        self.setDisabled(True)
        
        neName         = self.ui.lineEditNE.text()
        neIp           = self.ui.lineEditIP.text()
        manageUserName = self.ui.lineEditManageUser.text()
        managePassword = self.ui.lineEditManagePassword.text()
        accessUserName = self.ui.lineEditAccessUser.text()
        accessPassword = self.ui.lineEditAccessPassword.text()
                
        #确认各输入框是否为空，如果为空，需要重新输入        
        if (neName         == "" or  
            neIp           == "" or
            accessUserName == "" or  
            accessPassword == "" or 
            manageUserName == "" or
            managePassword == ""):
            message=u"有输入框为空，请完成！"
            QMessageBox.information(self,u"警告",message)
            self.setEnabled(True)
            uiDebug("**** editNEDialog confirm end 1")
            return
        
        if self.ipCheck(self.ui.lineEditIP.text()) != ZOOM_OK:
            message=u"IP地址格式不正确"
            QMessageBox.information(self,u"警告",message)
            self.setEnabled(True)
            uiDebug("**** editNEDialog confirm end 2")
            return
        
        #由于输入框的内容，QT保留为unicode编码，这里编码一下，让其他模块识别
        self.ne =NE(neName.encode("utf-8"),
                 neIp.encode("utf-8"),
                 accessUserName.encode("utf-8"),
                 accessPassword.encode("utf-8"),
                 manageUserName.encode("utf-8"),
                 managePassword.encode("utf-8"))
       
        #检查网元是否已经存在，如果存在，就不用再添加了
        if self.parent().checkNeExist(self.ne) != NE_NOT_EXIST:
            message=u"已有相同命名或者IP的网元存在，请修改"
            QMessageBox.information(self,u"警告",message)
            self.setEnabled(True)
            uiDebug("**** editNEDialog confirm end 3")
            return
        
        #这里使用线程运行，以防止界面假死
        self.thread.clearThreadfun()
        self.thread.setThreadfun(self.ne.telnetManagePlatformTest , NE_OK ,"None")
        self.thread.setThreadfun(self.ne.telnetAccessPlatformTest , NE_OK ,"None")
#         self.thread.setThreadfun(self.ne.checkNe , NE_OK)
        self.thread.start()
        
        uiDebug("**** editNEDialog confirm end")
        

class updateProgress(QStyledItemDelegate):
    '''进度条打印类'''
    def paint(self, painter, option, index):
        if index.column() == showColumn[UPDATE_STATE]:
            progress = int(index.data());
            progressBarOption = QStyleOptionProgressBar();  
            progressBarOption.rect = option.rect;  
            progressBarOption.minimum = 0;  
            progressBarOption.maximum = 100;  
            progressBarOption.progress = progress;  
         
            progressBarOption.text = str(progress) + "%";  
            progressBarOption.textVisible = True;  
             
            QApplication.style().drawControl(QStyle.CE_ProgressBar, progressBarOption, painter); 
        else:
            QStyledItemDelegate.paint(self, painter, option, index)    
            
        
    
class updateWindow(QMainWindow):
    '''升级主窗口'''
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
        
        
        QObject.connect(self.ui.pushButtonCheckNe, SIGNAL("clicked()"), self, SLOT("checkNe()"))
        QObject.connect(self.ui.pushButtonUpdateAll, SIGNAL("clicked()"), self, SLOT("updateAll()"))
        
        self.versionFile     = None
        self.versionFilePath = None
        self.config = None
        self.NEs={}
        self.Dialog = None
        
        self.timer=QTimer(self)
        QObject.connect(self.timer,SIGNAL("timeout()"),self,SLOT("timerDone()"))
        self.NEthreads={}

#     def timerDone(self):
#         model = self.ui.tableViewNet.model()
#         for row in self.NEs.keys():
#             ne =self.NEs[row]
#             result = NE_OK
#             if result != NE_OK:
#                 pass
#             else:
#                 item=model.index(row, showColumn[UPDATE_STATE])
#                 model.setData(item,"40")

    
    def checkNeExist(self,ne):
        '''检查网元是否已经存在了'''
        for item in self.NEs.values():
            if item.neIp == ne.neIp: 
                return NE_IP_EXIST
            if item.neName == ne.neName:
                return NE_NAME_EXIST
        return NE_NOT_EXIST        
        
    def checkThreadRunning(self):
        '''检查网元线程是否运行'''
        
        if len(self.NEthreads)==0:
            return False
        
        for thread in self.NEthreads.values():
            if thread.isRunning()==False:
                return False
        return True    
            
    def checkNeSlot(self,Data):
        '''接收检查线程反馈的消息，进行处理，根据结果在界面上反映'''
        uiDebug("")
        uiDebug("***updateWindow.checkNeSlot start")
        result = pyparsingEmit(Data)
        
        if  result !=EMIT_SIGNAL_ERR:
            runResult = result[0]
            runFun  = result[1]
            row  = int(result[2])
            
            if runResult == NeThread.FINISH_ALL_FUN:
                model = self.ui.tableViewNet.model()
                model.setData(model.index(row, showColumn[NE_IP])               ,self.NEs[row].neIp)
                model.setData(model.index(row, showColumn[SOFTWARE_VERSION])    ,self.NEs[row].softwareVersion)
                model.setData(model.index(row, showColumn[HARDWARE_VERSION])    ,self.NEs[row].hardwareVersion)
                model.setData(model.index(row, showColumn[MASTER_SLAVE_STATE])  ,self.NEs[row].masterSlaveState)
                model.setData(model.index(row, showColumn[NE_STATE])            ,self.NEs[row].neState)
                model.setData(model.index(row, showColumn[UPDATE_STATE])        ,self.NEs[row].processState)
                self.messageShow(u"检查%s网元成功"%(self.NEs[row].neName))
                self.NEthreads[row].signal.sig.disconnect(self.checkNeSlot)
                
            if runResult == NeThread.FUN_OK:
                uiDebug(u"%d网元，函数%s执行成功"%(row,runFun))
            
            if runResult == NeThread.FUN_ERR:
                self.messageShow(u"检查%s网元失败"%(self.NEs[row].neName))
                uiDebug(u"%d网元，函数%s执行失败"%(row,runFun))
                uiDebug(u"检查网元意外终止，请检查")
                uiDebug("***updateWindow.checkNeSlot end")
                uiDebug("")
                return
        else:
            uiDebug("receive without control message: %s"%(Data))
            
        uiDebug("***updateWindow.checkNeSlot end")
        uiDebug("")
        
    def checkNe(self):
        '''检查网元slot'''
        self.ui.textEditInformation.setText(u"开始检查网元")
        if self.checkThreadRunning()==True:
            self.ui.textEditInformation.setText(u"上一个操作还未结束，请稍后再尝试")
            return 
        
        for row in self.NEs.keys():
            self.NEthreads[row].clearThreadfun()
            self.NEthreads[row].setThreadfun(self.NEs[row].checkNe , NE_OK , row)
            self.NEthreads[row].signal.sig.connect(self.checkNeSlot)
            self.NEthreads[row].run()
    
    
    def updataAllSlot(self,Data):
        result = pyparsingEmit(Data)
        if  result !=EMIT_SIGNAL_ERR:
            runResult = result[0]
            runFun    = result[1]
            value =int(result[2].encode("utf-8"))
            row = value / 100
            process = value %1000
            
            if runResult == NeThread.FINISH_ALL_FUN:
                process = 100
                self.messageShow(u"结束升级网元")
                self.NEthreads[row].signal.sig.disconnect(self.updataAllSlot)
                 
            model = self.ui.tableViewNet.model()
            item=model.index(row, showColumn[UPDATE_STATE])
            model.setData(item,process)
        
            if runResult == NeThread.FUN_OK:
                self.messageShow(u"执行函数%s成功"%(runFun))
                
            if runResult == NeThread.FUN_ERR:
                self.messageShow(u"执行函数%s失败"%(runFun))
                
    
    def messageShow(self,text):
        self.ui.textEditInformation.append(text)
        
    def updateAll(self):
        '''开始升级'''
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            return         
        if self.versionFile == None:
            Info = u"版本文件不可用，请配置好相关文件后再升级"
            QMessageBox.information(self,u"警告",Info)

        for row in self.NEs.keys():
            ne =self.NEs[row]
            self.NEthreads[row].clearThreadfun()
            self.NEthreads[row].setThreadfun(ne.saveNeConfigToLocal, NE_OK, row*1000+5,"test")
            self.NEthreads[row].setThreadfun(ne.updateVersionFile, NE_OK, row*1000+20,self.versionFile, self.versionFilePath)
            self.NEthreads[row].setThreadfun(ne.updateSoft,NE_OK, row*1000+25,self.versionFile, ne.willUpdateSoftPartition)
            self.NEthreads[row].signal.sig.connect(self.updataAllSlot)
            self.NEthreads[row].start()

        self.messageShow(u"开始升级网元")
        
        
        
    def showConfig(self):
        '''将导入的配置显示到界面上'''
        if self.config != None:
            print self.config.getNeLists()
            for ne in self.config.getNeLists().values():
                print ne
                self.addNe(ne)
            
            
    def importConfig(self):
        '''从配置文件中导入配置'''
        configFile = QFileDialog.getOpenFileName(self, u"Load config File", QDir.currentPath(), filter="*.conf")
        if configFile != None:
            config = updateConfig()
            config.readConfig(configFile)
            if self.config != None:
                del self.config
            self.config = config    
            self.showConfig()
        
        
    
    def saveConfig(self):
        '''保存当前升级配置，主要是网元信息'''
        configFile = QFileDialog.getOpenFileName(self, u"Load config File", QDir.currentPath(), filter="*.conf")
        if configFile != None:
            pass
        
    def test(self):
        print self.Dialog
        print self.Dialog.destroyed        
        print self.Dialog.finished
        
            
    def addNe(self):
        '''添加网元操作'''
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            return 
        self.tempNe=None
        
        #使用模态Dialog进行输入
        testDialog= editNEDialog(self)
        res=testDialog.exec_()
        
        if self.tempNe!=None:
            index = self.ui.tableViewNet.selectionModel().currentIndex()
            model = self.ui.tableViewNet.model()
            row = model.rowCount(index.parent())
        
            name = QStandardItem(self.tempNe.neName)
            name.setCheckable(True)
            model.setItem(row, showColumn[NE_NAME], name)
     
            model.setItem(row, showColumn[NE_IP]               , QStandardItem(self.tempNe.neIp))
            model.setItem(row, showColumn[SOFTWARE_VERSION]    , QStandardItem(self.tempNe.softwareVersion))
            model.setItem(row, showColumn[HARDWARE_VERSION]    , QStandardItem(self.tempNe.hardwareVersion))
            model.setItem(row, showColumn[MASTER_SLAVE_STATE]  , QStandardItem(self.tempNe.masterSlaveState))
            model.setItem(row, showColumn[NE_STATE]            , QStandardItem(self.tempNe.neState))
            model.setItem(row, showColumn[UPDATE_STATE]        , QStandardItem(self.tempNe.processState))
                    
            item=model.index(row, showColumn[UPDATE_STATE])
            model.setData(item,self.tempNe.processState)
     
            for key in showColumn.keys():
                model.item(row, showColumn[key]).setTextAlignment(Qt.AlignCenter);
     
            self.NEs[row]=self.tempNe
            self.NEthreads[row]=NeThread()

    
    def delNe(self):
        '''删除网元操作'''
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            return 
                
        if self.ui.tableViewNet.selectionModel().hasSelection():
            currentIndex=self.ui.tableViewNet.selectionModel().currentIndex()
            model = self.ui.tableViewNet.model()
            model.removeRow(currentIndex.row(),currentIndex.parent())
            self.NEs.pop(currentIndex.row())
            self.NEthreads.pop(currentIndex.row())
        else:
            
            Info = u"没有选中网元！请选中后，再操作。"
            QMessageBox.information(self,u"警告",Info)
            uiDebug("no NE select")
        uiDebug("del NE end")     


    def addVersionFile(self):
        '''添加版本文件'''
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            return 
                
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
        
          
def main():
    app = QApplication(sys.argv)
    app.setStyle("cleanlooks")
#    app.setStyle("arthurStyle")
    d = updateWindow(app)
    d.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()    
