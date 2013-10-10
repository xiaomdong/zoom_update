# -*- coding: UTF-8 -*-
'''
pyside-uic zoomUpdate.ui -o zoomUpdate_ui.py

pyside-uic NE_Dialog.ui -o NE_Dialog_ui.py
'''
 
import sys,time,os,platform,datetime,filecmp 
 
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
from control.fileCheck import *
from control.config import *
from control.debug import *
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

#线程延时操作
SLEEP="sleep"

class NeThread(QThread):
    FUN_ERR ="thread_fun_err"
    FUN_OK  ="thread_fun_ok"
    FINISH_ALL_FUN="thread_all_ok"
    BEGIN_RUN_FUN="begine_run_fun"
    
    RUN_RUSULT="run_result"
    RUN_FUN   ="run_fun"
    RUN_RUSULT_DETIAL="run_result_detial"
    
    funStr    =Combine(CaselessLiteral(":")+Regex("<(.)*>").setResultsName(RUN_FUN))
    detialStr =Combine(CaselessLiteral("=")+Word(printables).setResultsName(RUN_RUSULT_DETIAL))
    emitPyparsingStr=oneOf(FUN_ERR+" "+FUN_OK+" "+FINISH_ALL_FUN+" "+BEGIN_RUN_FUN,caseless=False).setResultsName(RUN_RUSULT)+funStr+detialStr
    
         
    def __init__(self,parent = None):
        super(NeThread,self).__init__(parent)
        self.funs         = {}  #线程需要运行的函数
        self.funsArgs     = {}  #线程调用函数时需要用到的参数
        self.exceptResult = {}  #线程调用函数后的预期正确的返回结果
        self.realResult   = {}  #线程调用函数后的返回结果
        self.emit         = {}  #线程调用完毕后发送的信号
        self.signal = NESignal()
        
    def clearThreadfun(self):
        '''删除线程函数列表'''
        self.funs.clear()
        self.funsArgs.clear()
        self.exceptResult.clear()
        self.realResult.clear()
        self.emit.clear()
#         self.signal.disconnect()
        
    def setThreadfun(self,step,fun,exceptResult,emit=None,*args): 
        '''
        stp
                     设置进程计划运行的函数,excepResult函数预期的返回值，
        emit函数执行成功后发出的信号，如果emit为空，则不会有成功信号
                     当函数执行失败时会发出self.FUN_ERR信号
        '''
        self.funs[step]=fun
        self.funsArgs[step]= args
        self.exceptResult[step]= exceptResult
        self.realResult[step]= None
        self.emit[step] = emit
         
    def run(self):
        '''运行NE thread'''
        uiDebug("")
        uiDebug("")
        uiDebug("**** NeThread run stat ")
        print self.funs
        uiDebug("")
        uiDebug("")
        for key in self.funs.keys():
            fun =self.funs[key]
            #运行函数，将函数的运行结果保留到，self.realResult[fun]
            uiDebug("**** NeThread run fun: %s "%(str(fun)))
            
            self.signal.sig.emit(self.BEGIN_RUN_FUN+":"+str(fun)+"="+str(self.emit[key]))
            
            if len(self.funsArgs[key]) != 0:
                result=fun(*self.funsArgs[key])
            else:
                result=fun()
            
            #不对函数结果判断时，设置函数运行返回结果为None
            if self.exceptResult[key]==None:
                result = None
                
            #如果结果不符合预期，线程停止运行，发出thread_fun_err=附加码的信号,这里的附加码是预设值
            if result!=self.exceptResult[key]:
                self.signal.sig.emit(self.FUN_ERR+":"+str(fun)+"="+str(self.emit[key]))
                uiDebug("emit: "+self.FUN_ERR+":"+str(fun)+"="+str(self.emit[key]))
                uiDebug("**** NeThread run end 1")
                return
            else:
            #如果结果符合预期，线程停止运行，发出thread_fun_ok=附加码的信号,这里的附加码是预设值    
                if self.emit[key]!=None:
                    self.signal.sig.emit(self.FUN_OK+":"+str(fun)+"="+str(self.emit[key]))
                    uiDebug("emit: "+self.FUN_OK+":"+str(fun)+"="+str(self.emit[key]))
                
        #当所有函数运行完毕后，发出self.FINISH_ALL_FUN信号 ,
        #这里有一个小技巧，是发送最后一个函数的emit值   
        self.signal.sig.emit(self.FINISH_ALL_FUN+":"+str(fun)+"="+str(self.emit[key]))
        uiDebug("emit: "+self.FINISH_ALL_FUN+":"+str(fun)+"="+str(self.emit[key]))
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
                    #这里写的不好,直接修改了parent的成员变量
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
                 managePassword.encode("utf-8"),
                 self.parent().todaylogPath+self.parent().directorySeparator)
       
        #检查网元是否已经存在，如果存在，就不用再添加了
        if self.parent().checkNeExist(self.ne) != NE_NOT_EXIST:
            message=u"已有相同命名或者IP的网元存在，请修改"
            QMessageBox.information(self,u"警告",message)
            self.setEnabled(True)
            uiDebug("**** editNEDialog confirm end 3")
            return
        
        #这里使用线程运行，以防止界面假死
        self.thread.clearThreadfun()
        self.thread.setThreadfun(1,self.ne.telnetManagePlatformTest , NE_OK ,"None")
        self.thread.setThreadfun(2,self.ne.telnetAccessPlatformTest , NE_OK ,"None")
#         self.thread.setThreadfun(3,self.ne.checkNe , NE_OK)
        self.thread.start()
        
        uiDebug("**** editNEDialog confirm end")
        
    def closeEvent(self,event):
        self.thread.terminate()
        event.accept()        

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
        QObject.connect(self.ui.actionSaveConfig, SIGNAL("activated()"), self, SLOT("saveConfig()"))
        QObject.connect(self.ui.actionSaveAs, SIGNAL("activated()"), self, SLOT("saveConfigAs()"))
        
        
        QObject.connect(self.ui.pushButtonCheckNe, SIGNAL("clicked()"), self, SLOT("checkNe()"))
        QObject.connect(self.ui.pushButtonUpdateAll, SIGNAL("clicked()"), self, SLOT("updateAll()"))
        
        self.versionFile     = None   #目标升级版本文件名
        self.versionFilePath = None   #目标升级版本文件本地路径
        self.configFile = None            #升级软件配置  
        self.NEs = {}                 #升级网元字典 ,{ row : NE },每个列表中的一行对应一个网元对象
        
        self.Dialog = None            #添加网元Dialog对象
        self.tempNe = None            #与添加网元Dialog对象交换数据介质
        
        self.NEthreads={}             #升级线程字典,{ row : nethread }，每个列表中的一行对应一个网元升级线程

        self.updateMessage={}         #升级时界面显示的消息
        self.updateMessage[str(NE.checkNe).rstrip('>').lstrip("<").split()[2]]             = u"检查网元状态"
        self.updateMessage[str(NE.saveNeConfig).rstrip('>').lstrip("<").split()[2]]        = u"保存网元配置"
        self.updateMessage[str(NE.saveNeConfigToLocal).rstrip('>').lstrip("<").split()[2]] = u"下载网元配置到本地"
        self.updateMessage[str(NE.updateVersionFile).rstrip('>').lstrip("<").split()[2]]   = u"上传版本文件到网元"
        self.updateMessage[str(NE.updateSoft).rstrip('>').lstrip("<").split()[2]]          = u"升级软件"
        self.updateMessage[str(NE.activeSoft).rstrip('>').lstrip("<").split()[2]]          = u"激活软件"
        self.updateMessage[str(NE.reboot).rstrip('>').lstrip("<").split()[2]]              = u"升级复位中"
        self.updateMessage[str(QThread.sleep).rstrip('>').lstrip("<").split()[2]]          = u"复位启动中"
        self.updateMessage[str(NE.afterRebootTest).rstrip('>').lstrip("<").split()[2]]     = u"升级复位后连接检测"
        self.updateMessage[str(NE.afterRebootCheck).rstrip('>').lstrip("<").split()[2]]    = u"升级复位后状态检测"
        
        #目录分隔符
        self.directorySeparator="\\"
        if platform.system() == "Linux":
            self.directorySeparator="/" 
        elif platform.system() == "Windows":     
            self.directorySeparator="\\"
        
        #建立记录日志目录
        self.logPath="log" 
        if os.path.exists(self.logPath) == False:
            os.mkdir(self.logPath)
  
        #建立记录当天操作的目录                      
        self.todaylogPath = None     
        dataStr=str(datetime.date.today())
        self.todaylogPath= self.logPath + self.directorySeparator + dataStr    
        if os.path.exists(self.todaylogPath) == False:
            os.mkdir(self.todaylogPath)
        
        #建立记录当天软件操作的日志文件                
        self.todayOperationFile= self.todaylogPath + self.directorySeparator +"operation.log"
        
        #建立日志记录模块
        self.logging = logging.getLogger("update") 
        fd=logging.FileHandler(self.todayOperationFile)
        fm=logging.Formatter("%(asctime)s  %(levelname)s - %(message)s","%Y-%m-%d %H:%M:%S")
        fd.setFormatter(fm)
        self.logging.addHandler(fd)
        self.logging.setLevel(logging.INFO)
        self.logging.info("开始运行升级软件")
        
        
    def closeEvent(self,event):
        self.logging.info("结束运行升级软件\n")
        
        try:
            for thread in self.NEthreads.values():
                thread.terminate()
        except:
            pass      
          
        event.accept()
                        
    def checkNeExist(self,ne):
        '''检查网元名和网元IP是否已经存在'''
        self.logging.info("检查网元名和网元IP是否已经存在")
        for item in self.NEs.values():
            if item.neIp == ne.neIp: 
                self.logging.warning("网元IP%s已经存在"%(ne.neIp))
                return NE_IP_EXIST
            if item.neName == ne.neName:
                self.logging.warning("网元名%s已经存在"%(ne.neName))
                return NE_NAME_EXIST
        self.logging.info("检查网元结束，网元:IP%s,和网元名:%s,是唯一的"%(ne.neIp,ne.neName))    
        return NE_NOT_EXIST     
       
        
    def checkThreadRunning(self):
        '''检查网元线程是否运行'''
        if len(self.NEthreads)==0:
            return False
        
        for thread in self.NEthreads.values():
            if thread.isRunning()==False:
                return False
        return True    
            
    def checkNeSlot(self,message):
        '''接收检查线程反馈的消息，进行处理，根据结果在界面上反映'''
        uiDebug("")
        uiDebug("***updateWindow.checkNeSlot start")
        result = pyparsingEmit(message)
        
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
                self.messageShow(u"网元%s结束检查"%(self.NEs[row].neIp))
                self.NEthreads[row].signal.sig.disconnect(self.checkNeSlot)
                self.logging.info("收到网元%s,网元检查结束消息:%s"%(self.NEs[row].neIp,message))
            
            if runResult == NeThread.BEGIN_RUN_FUN:
                pass
                
            if runResult == NeThread.FUN_OK:
#                 self.messageShow(u"网元%s，检查成功"%(self.NEs[row].neName))
                self.logging.info("收到网元%s,函数执行成功消息:%s"%(self.NEs[row].neIp,message))
                
            if runResult == NeThread.FUN_ERR:
                self.messageShow(u"网元%s，检查失败"%(self.NEs[row].neIp))
                self.logging.error("收到网元%s,函数执行失败消息:%s"%(self.NEs[row].neIp,message))
                return
        else:
            uiDebug("receive without control message: %s"%(message))
            self.logging.warning("检查网元信息处理模块收到未定义的消息%s"%(message))
            
        uiDebug("***updateWindow.checkNeSlot end")
        uiDebug("")
        
        
    def checkNe(self):
        '''检查网元slot'''
        self.logging.info("开始检查网元操作:")
        self.messageShow(u"开始检查网元")
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            self.logging.warning("上一个操作还未结束")
            self.logging.info("终止检查网元操作\n")
            return 
        
        for row in self.NEs.keys():
            self.NEthreads[row].clearThreadfun()
            self.NEthreads[row].setThreadfun(1,self.NEs[row].checkNe , NE_OK , row)
            self.NEthreads[row].signal.sig.connect(self.checkNeSlot)
            self.NEthreads[row].run()
            self.logging.info("执行NE:%s,检测线程"%(self.NEs[row].neIp))
            
        self.logging.info("完成检查网元操作:相关检查操作在子线程中执行\n")
    
    
    def updataAllSlot(self,message):
        '''升级操作slot'''
        result = pyparsingEmit(message)
        if  result !=EMIT_SIGNAL_ERR:
            runResult = result[0]
            runFun    = result[1]
            value =int(result[2].encode("utf-8"))
            row = value / 100
            process = value %1000
            model = self.ui.tableViewNet.model()
            
            if runResult == NeThread.FINISH_ALL_FUN:
                
                #升级完毕，将新的信息显示到节面
                process=100
                
                model.setData(model.index(row, showColumn[NE_IP])               ,self.NEs[row].neIp)
                model.setData(model.index(row, showColumn[SOFTWARE_VERSION])    ,self.NEs[row].softwareVersion)
                model.setData(model.index(row, showColumn[HARDWARE_VERSION])    ,self.NEs[row].hardwareVersion)
                model.setData(model.index(row, showColumn[MASTER_SLAVE_STATE])  ,self.NEs[row].masterSlaveState)
                model.setData(model.index(row, showColumn[NE_STATE])  ,u"升级成功")
                self.messageShow(u"网元%s结束升级"%(self.NEs[row].neIp))
                self.logging.info("收到网元%s结束升级消息%s"%(self.NEs[row].neIp,message))
                self.NEthreads[row].signal.sig.disconnect(self.updataAllSlot)
                 
            #用于界面显示     
            if runResult == NeThread.BEGIN_RUN_FUN:
                for item in self.updateMessage.keys():
                    if runFun.find(item) == -1:
                        pass
                    else:
                        model.setData(model.index(row, showColumn[NE_STATE])  ,self.updateMessage[item])

            if runResult == NeThread.FUN_OK:
                #对于主动休眠操作，不在界面上显示，只记录日志
                sleepStr=str(QThread.sleep).rstrip('>').lstrip("<").split()[2]
                if runFun.find(sleepStr) == -1:
                    self.messageShow(u"网元%s升级操作,执行函数%s成功"%(self.NEs[row].neIp,runFun))
                
                self.logging.info("收到网元%s升级操作,执行函数%s成功消息:%s"%(self.NEs[row].neIp,runFun,message))
                    
            if runResult == NeThread.FUN_ERR:
                self.messageShow(u"网元%s升级操作,执行函数%s失败"%(self.NEs[row].neIp,runFun))
                self.logging.error("收到网元%s升级操作,执行函数%s失败消息:%s"%(self.NEs[row].neIp,runFun,message))

            #在界面上显示进度条    
            model.setData(model.index(row, showColumn[UPDATE_STATE]),process)
                
    def messageShow(self,text):
        self.ui.textEditInformation.append(text)
        
        
    def updateAll(self):
        '''开始升级'''
        self.logging.info("开始升级网元操作:")
        self.messageShow(u"开始升级网元")
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            self.logging.warning("上一个操作还未结束")
            self.logging.info("终止升级网元操作\n")
            return         
        
        if self.versionFile == None:
            Info = u"版本文件不可用，请配置好相关文件后再升级"
            QMessageBox.information(self,u"警告",Info)
            self.logging.warning("未设置升级版本文件")
            self.logging.info("终止升级网元操作\n")
            return
        
        #清除网元保留的配置文件路径
        for row in self.NEs.keys():
            ne =self.NEs[row]
            self.NEthreads[row]=NeThread()
            self.NEthreads[row].clearThreadfun()
            step=0
            
            step=step+1
            self.NEthreads[row].setThreadfun(step,ne.saveNeConfig, NE_OK, row*1000+5)
            
            step=step+1
            self.NEthreads[row].setThreadfun(step,ne.saveNeConfigToLocal, NE_OK, row*1000+5)
          
            step=step+1
            self.NEthreads[row].setThreadfun(step,ne.updateVersionFile, NE_OK, row*1000+20,self.versionFile, self.versionFilePath)
           
            step=step+1
            self.NEthreads[row].setThreadfun(step,ne.updateSoft,NE_OK, row*1000+25, self.versionFile, ne.willUpdateSoftPartition)
          
            step=step+1
            self.NEthreads[row].setThreadfun(step,ne.activeSoft,NE_OK, row*1000+30, ne.willUpdateSoftPartition)
           
            step=step+1
            self.NEthreads[row].setThreadfun(step,ne.reboot,NE_OK, row*1000+35)
              
            for step in range(step+1,34):
                self.NEthreads[row].setThreadfun(step,QThread.sleep,None, row*1000+40+step,10)
                  
            step=step+1
            self.NEthreads[row].setThreadfun(step,ne.afterRebootTest,NE_OK, row*1000+90)
             
            step=step+1
            self.NEthreads[row].setThreadfun(step,ne.afterRebootCheck, NE_OK, row*1000+99,self.ui.lineEditVersion.text())
                
            self.NEthreads[row].signal.sig.connect(self.updataAllSlot)
            
            self.NEthreads[row].start()
            self.logging.info("执行NE:%s,升级线程"%(ne.neIp))
            
        
    def __activeConfig(self,config):
        '''将导入的配置显示到界面上'''
        if config != None:
            for ne in config.getNeLists().values():
                self.__addNe(ne)

                
    def importConfig(self):
        '''从配置文件中导入配置'''
        configFile = QFileDialog.getOpenFileName(self, u"Load configFile File", QDir.currentPath(), filter="*.conf")
        print configFile 
        print str(configFile)
        if configFile != None:
            config = updateConfig()
            config.readConfig(configFile[0])
            self.__activeConfig(config)
            #激活配置后要检查配置
            self.checkNe()
            self.configFile=configFile[0]
    
    def saveConfig(self):
        '''保存当前升级配置，主要是网元信息'''
        print "self.configFile : "
        print self.configFile 
        if self.configFile!=None:
            config = updateConfig()
            config.configFile = self.configFile 
            for ne in self.NEs.values():
                print ne
                config.addNe(ne)
            print config.neLists    
            config.saveConfig()
        else:
            self.saveConfigAs()
            
    def saveConfigAs(self):
        '''保存当前升级配置，主要是网元信息'''
        configFile = QFileDialog.getSaveFileName(self, u"save configFile File", QDir.currentPath(), filter="*.conf")
        print configFile
        print str(configFile)
        if configFile != None:
            self.configFile=configFile[0]
            self.saveConfig()
            
            
    def __addNe(self,tempNe):
        if tempNe!=None:
            index = self.ui.tableViewNet.selectionModel().currentIndex()
            model = self.ui.tableViewNet.model()
            row = model.rowCount(index.parent())
        
            name = QStandardItem(tempNe.neName)
            name.setCheckable(True)
            model.setItem(row, showColumn[NE_NAME], name)
     
            model.setItem(row, showColumn[NE_IP]               , QStandardItem(tempNe.neIp))
            model.setItem(row, showColumn[SOFTWARE_VERSION]    , QStandardItem(tempNe.softwareVersion))
            model.setItem(row, showColumn[HARDWARE_VERSION]    , QStandardItem(tempNe.hardwareVersion))
            model.setItem(row, showColumn[MASTER_SLAVE_STATE]  , QStandardItem(tempNe.masterSlaveState))
            model.setItem(row, showColumn[NE_STATE]            , QStandardItem(tempNe.neState))
            model.setItem(row, showColumn[UPDATE_STATE]        , QStandardItem(tempNe.processState))
                    
            item=model.index(row, showColumn[UPDATE_STATE])
            model.setData(item,tempNe.processState)
     
            for key in showColumn.keys():
                model.item(row, showColumn[key]).setTextAlignment(Qt.AlignCenter);
     
            self.NEs[row]=tempNe
            self.NEthreads[row]=NeThread()
            self.logging.info("添加网元%s\n"%(tempNe.neIp))
        else:    
            self.logging.warning("没有添加任何网元\n")    
            
    def addNe(self):
        '''添加网元操作'''
        self.logging.info("开始添加网元操作:")
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            self.logging.warning("上一个操作还未结束")
            self.logging.info("终止添加网元操作\n")
            return 
        
        
        #使用模态Dialog进行输入
        self.tempNe=None
        testDialog= editNEDialog(self)
        res=testDialog.exec_()
        
        self.__addNe(self.tempNe)
        
        
    
    def delNe(self):
        '''删除网元操作'''
        self.logging.info("开始删除网元")
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            self.logging.warning("上一个操作还未结束")
            self.logging.info("终止删除网元操作\n")
            return 
                
        if self.ui.tableViewNet.selectionModel().hasSelection():
            currentIndex=self.ui.tableViewNet.selectionModel().currentIndex()
            model = self.ui.tableViewNet.model()
            model.removeRow(currentIndex.row(),currentIndex.parent())
            self.logging.info("删除网元%s\n"%(self.NEs[currentIndex.row()].neIp))
            self.NEs.pop(currentIndex.row())
            self.NEthreads.pop(currentIndex.row())
        else:
            Info = u"没有选中网元！请选中后，再操作。"
            QMessageBox.information(self,u"警告",Info)
            self.logging.warning("没有删除任何网元\n")


    def addVersionFile(self):
        '''添加版本文件'''
        self.logging.info("开始添加版本文件操作")
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            self.logging.warning("上一个操作还未结束")
            self.logging.info("终止添加版本文件操作\n")
            return 
                
        self.ui.lineEditVersion.setText("")
        openFile = QFileDialog.getOpenFileName(self, "Find Files", QDir.currentPath())
        
        if openFile != None :
            self.ui.lineEditVersionFile.setText(openFile[0])
            versionFile = fileCheck(openFile[0])
            if versionFile.getVersion() != OPEN_FILE_OK :
                self.versionFile=None
                self.ui.lineEditVersion.setText(u"没有打开任何版本文件")
                self.logging.warning("没有打开任何版本文件")
                return
            else:
                if versionFile.verifyVersion() != VERIFY_VERSION_OK:
                    self.versionFile=None
                    self.ui.lineEditVersion.setText(u"版本文件无法校验")
                    self.logging.warning("版本文件%s无法校验"%(openFile))
                    return
                
        self.ui.lineEditVersion.setText(versionFile.version["version"])
        self.versionFilePath = openFile[0][0:len(openFile[0])- len(versionFile.version["version"])]   
        self.versionFile = versionFile.version["version"]    
        self.logging.info("添加版本文件%s成功\n"%(openFile[0]))
          
def main():
    app = QApplication(sys.argv)
    app.setStyle("cleanlooks")
#    app.setStyle("arthurStyle")
    d = updateWindow(app)
    d.show()
    sys.exit(app.exec_())
    
    
if __name__ == '__main__':
    main()    
