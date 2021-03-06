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
from PySide.QtNetwork import *

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
              #MASTER_SLAVE_STATE : 4  ,     
              NE_STATE           : 4  ,
              UPDATE_STATE       : 5  ,
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
#         self.breakFlag    = True
        self.signal = NESignal()
        
    def clearThreadfun(self):
        '''删除线程函数列表'''
        self.funs.clear()
        self.funsArgs.clear()
        self.exceptResult.clear()
        self.realResult.clear()
        self.emit.clear()
#         self.breakFlag    = True
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
        uiDebug("**** NeThread run stat ")
        for key in self.funs.keys():
            fun =self.funs[key]
            #运行函数，将函数的运行结果保留到，self.realResult[fun]
            
            self.signal.sig.emit(self.BEGIN_RUN_FUN+":"+str(fun)+"="+str(self.emit[key]))
            uiDebug("emit: "+self.BEGIN_RUN_FUN+":"+str(fun)+"="+str(self.emit[key]))
            
            if len(self.funsArgs[key]) != 0:
                result=fun(*self.funsArgs[key])
            else:
                result=fun()
            
            #将函数的运行结果保留到，self.realResult[fun]
            self.realResult[fun]=result
            
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
            #如果结果符合预期，线程继续运行，发出thread_fun_ok=附加码的信号,这里的附加码是预设值    
                if self.emit[key]!=None:
                    self.signal.sig.emit(self.FUN_OK+":"+str(fun)+"="+str(self.emit[key]))
                    uiDebug("emit: "+self.FUN_OK+":"+str(fun)+"="+str(self.emit[key]))
                
        #当所有函数运行完毕后，发出self.FINISH_ALL_FUN信号 ,
        #这里有一个小技巧，是发送最后一个函数的emit值   
        self.signal.sig.emit(self.FINISH_ALL_FUN+":"+str(fun)+"="+str(self.emit[key]))
        uiDebug("emit: "+self.FINISH_ALL_FUN+":"+str(fun)+"="+str(self.emit[key]))
        uiDebug("**** NeThread run end ")
        return 


def pyparsingEmit(Data):
    '''
           解析传递的信号，信号格式为 "执行结果:执行函数=结果细节
          解析后返回有两种情况：
          1.  返回EMIT_SIGNAL_ERR
          2.  列表[RUN_RUSULT，RUN_FUN，RUN_RUSULT_DETIAL]     
    '''
#     uiDebug("")
#     uiDebug("***pyparsingEmit start")
#     uiDebug("pyparsing data: %s"%(Data))
    resultValue=[]
    result=NeThread.emitPyparsingStr.searchString(Data)
#     uiDebug("pyparsing result: %s"%(str(result)))
    if len(result)==0:
#         uiDebug("return EMIT_SIGNAL_ERR")
#         uiDebug("***pyparsingEmit end")
#         uiDebug("")
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
#     uiDebug("")
    
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
            runFun = result[1]
            
            if runResult == NeThread.BEGIN_RUN_FUN:
                pass
            
            if runResult == NeThread.FINISH_ALL_FUN:
                    #这里写的不好,直接修改了parent的成员变量
                    self.parent().tempNe=self.ne
                    self.accept()
                    return
                
            if runResult == NeThread.FUN_ERR:
                
                telnetManagePlatformTestStr = str(NE.telnetManagePlatformTest).rstrip('>').lstrip("<").split()[2]
                if runFun.find(telnetManagePlatformTestStr) != -1:
                    message=u"无法telnet管理平台，请检查！"
                    QMessageBox.information(self,u"提示",message)
                    self.setEnabled(True)
                    return
                
                telnetAccessPlatformTestStr = str(NE.telnetAccessPlatformTest).rstrip('>').lstrip("<").split()[2]
                if runFun.find(telnetAccessPlatformTestStr) != -1:
                    message=u"无法telnet接入平台，请检查！"
                    QMessageBox.information(self,u"提示",message)
                    self.setEnabled(True)
                    return
                
                checkNeStr = str(NE.checkNe).rstrip('>').lstrip("<").split()[2]
                if runFun.find(checkNeStr) != -1:
                    message=u"检查网元失败，请检查！"
                    QMessageBox.information(self,u"提示",message)
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
            traceback.print_exc() 
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
        enablePassword = self.ui.lineEditEnablePassword.text()
                
        #确认各输入框是否为空，如果为空，需要重新输入        
        if (neName         == "" or  
            neIp           == "" or
            accessUserName == "" or  
            accessPassword == "" or 
            manageUserName == "" or
            managePassword == "" or
            enablePassword == "" ):
            message=u"有输入框为空，请完成！"
            QMessageBox.information(self,u"提示",message)
            self.setEnabled(True)
            uiDebug("**** editNEDialog confirm end 1")
            return
        
        if self.ipCheck(self.ui.lineEditIP.text()) != ZOOM_OK:
            message=u"IP地址格式不正确"
            QMessageBox.information(self,u"提示",message)
            self.setEnabled(True)
            uiDebug("**** editNEDialog confirm end 2")
            return
        
        #由于输入框的内容，QT保留为unicode编码，这里编码一下，让其他模块识别
        self.ne =NE(neName.encode("utf-8"),
                 neIp.encode("utf-8"),
                 accessUserName.encode("utf-8"),
                 accessPassword.encode("utf-8"),
                 enablePassword.encode("utf-8"),
                 manageUserName.encode("utf-8"),
                 managePassword.encode("utf-8"),
                 self.parent().todaylogPath+self.parent().directorySeparator)
               
        #检查网元是否已经存在，如果存在，就不用再添加了
        if self.parent().checkNeExist(self.ne) != NE_NOT_EXIST:
            message=u"已有相同命名或者IP的网元存在，请修改"
            QMessageBox.information(self,u"提示",message)
            self.setEnabled(True)
            uiDebug("**** editNEDialog confirm end 3")
            return
        
        #这里使用线程运行，以防止界面假死
        self.thread.clearThreadfun()
        self.thread.setThreadfun(1,self.ne.telnetManagePlatformTest , NE_OK ,"None")
#         self.thread.setThreadfun(2,self.ne.telnetAccessPlatformTest , NE_OK ,"None")
        self.thread.setThreadfun(3,self.ne.checkNe , NE_OK)
        
        
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
        self.ui.pushButtonCancel.setDisabled(True)

        self.netModel = QStandardItemModel()
        self.ui.tableViewNe.setItemDelegate(updateProgress())
        
        for key in showColumn.keys():
            self.netModel.setHorizontalHeaderItem(showColumn[key], QStandardItem(key))
        
        #设置表格，以及表格的默认长度    
        self.ui.tableViewNe.setModel(self.netModel)
        self.ui.tableViewNe.setColumnWidth(showColumn[SOFTWARE_VERSION],150)
        self.ui.tableViewNe.setColumnWidth(showColumn[NE_STATE],150)
        self.ui.tableViewNe.setColumnWidth(showColumn[UPDATE_STATE],360)        
       
        QObject.connect(self.ui.pushButtonAddNe, SIGNAL("clicked()"), self, SLOT("addNe()"))
        QObject.connect(self.ui.pushButtonDelNe, SIGNAL("clicked()"), self, SLOT("delNe()"))
             
        QObject.connect(self.ui.pushButtonAddVersionFile, SIGNAL("clicked()"), self, SLOT("addVersionFile()"))
        QObject.connect(self.ui.actionImportConfig, SIGNAL("activated()"), self, SLOT("importConfig()"))
        QObject.connect(self.ui.actionSaveConfig, SIGNAL("activated()"), self, SLOT("saveConfig()"))
        QObject.connect(self.ui.actionSaveAs, SIGNAL("activated()"), self, SLOT("saveConfigAs()"))
        
        QObject.connect(self.ui.actionAbout, SIGNAL("activated()"), self, SLOT("about()"))
        
        
        QObject.connect(self.ui.pushButtonCheckNe, SIGNAL("clicked()"), self, SLOT("checkNe()"))
        QObject.connect(self.ui.pushButtonUpdateAll, SIGNAL("clicked()"), self, SLOT("updateAll()"))
        QObject.connect(self.ui.pushButtonCancel, SIGNAL("clicked()"), self, SLOT("cancelOperation()"))
        
        
        self.versionFile     = None   #目标升级版本文件名
        self.versionFilePath = None   #目标升级版本文件本地路径
        self.configFile = None        #升级软件配置  
        self.NEs = {}                 #升级网元字典 ,{row : NE },每个列表中的一行对应一个网元对象
        
        self.Dialog = None            #添加网元Dialog对象
        self.tempNe = None            #与添加网元Dialog对象交换数据介质
        
        self.NEthreads={}             #升级线程字典,{row : nethread }，每个列表中的一行对应一个网元升级线程

        self.updateMessage={}         #升级时界面显示的消息
        self.updateMessage[str(NE.checkNe).rstrip('>').lstrip("<").split()[2]]             = u"检查网元状态"
        self.updateMessage[str(NE.checkUpdateFile).rstrip('>').lstrip("<").split()[2]]     = u"检查升级文件"
        self.updateMessage[str(NE.saveNeConfig).rstrip('>').lstrip("<").split()[2]]        = u"保存网元配置"
        self.updateMessage[str(NE.saveNeConfigToLocal).rstrip('>').lstrip("<").split()[2]] = u"下载网元配置到本地"
        self.updateMessage[str(NE.updateVersionFile).rstrip('>').lstrip("<").split()[2]]   = u"上传版本文件到网元"
        self.updateMessage[str(NE.updateSoft).rstrip('>').lstrip("<").split()[2]]          = u"升级软件"
        self.updateMessage[str(NE.activeSoft).rstrip('>').lstrip("<").split()[2]]          = u"激活软件"
        self.updateMessage[str(NE.reboot).rstrip('>').lstrip("<").split()[2]]              = u"升级复位中"
        self.updateMessage[str(QThread.sleep).rstrip('>').lstrip("<").split()[2]]          = u"复位启动中"
        self.updateMessage[str(NE.afterRebootTest).rstrip('>').lstrip("<").split()[2]]     = u"升级复位后连接检测"
        self.updateMessage[str(NE.afterRebootCheck).rstrip('>').lstrip("<").split()[2]]    = u"升级复位后状态检测"
        self.updateMessage[str(NE.afterRebootConfigCheck).rstrip('>').lstrip("<").split()[2]]    = u"升级复位后配置检测"
        
        
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
        self.logging.info(u"开始运行升级软件")
         
        
        #创建contextMenu
        self.createNEContextMenu()
            
    def about(self):
        '''about'''
        aboutInfo = u'''<HTML>
         <p> AC升级工具：1.0rc </p>
         <p> 功能支持：AC软件自动升级功能，支持多台AC同时升级。</p>
         <p> 注意事项 ：</p>
         <p> 1.仅适用于mips平台AC。</p>
         <p> 2.此工具在一台pc上只能运行一个实例，无法打开多个。</p>
         <p> 3.此工具运行后，将在执行文件相同目录下建立名称为"log"的目录，</p>
         <p> 在log目录下，将依据软件运行的时间，以"年月日"为名称建立每天的日志目录。</p>
         <p> 在每天的日志目录下会建立"operation.log"日志，记录升级软件的操作过程，</p>
         <p> 同时还会以"网元名称_ip"为名称建立网元的升级日志目录。在网元的升级日志 </p>
         <p> 目录下会建立"log"日志文件，用于记录网元的操作信息，同时会按照升级过程中</p>
         <p> 保留配置的情况，以"config_年月日时分秒"为名称建立配置保留目录，升级过程</p>
         <p> 中保留的配置会保存在这些目录中。</p>
         <p> 4.升级开始后，可以通过点击取消按钮，取消选中网元的升级动作，但是取消动作</p>
         <p> 只在升级复位之前的阶段生效，即如果升级过程已经执行了升级复位动作，将无法</p>
         <p> 执行取消操作。</p>
         </HTML>'''
        QMessageBox.about(self, u"说明", aboutInfo)
 
            
    def createNEContextMenu(self):
        '''添加用户信息快捷菜单'''
        
#         self.addNEAct = QAction(self)
#         self.addNEAct.setText(u"添加网元")
# 
#         self.delNEAct = QAction(self)
#         self.delNEAct.setText(u"删除网元")
        
        self.selectAllAct = QAction(self)
        self.selectAllAct.setText(u"全部选中")
        
        self.selectNoneAct = QAction(self)
        self.selectNoneAct.setText(u"全部不选")
        
#         self.ui.tableViewNe.addAction(self.addNEAct)
#         self.ui.tableViewNe.addAction(self.delNEAct)
        self.ui.tableViewNe.addAction(self.selectAllAct)
        self.ui.tableViewNe.addAction(self.selectNoneAct)
 
#         QObject.connect(self.addNEAct, SIGNAL("activated()"), self, SLOT("addNEaction()"))
#         QObject.connect(self.delNEAct, SIGNAL("activated()"), self, SLOT("delNEAction()"))              
        QObject.connect(self.selectAllAct, SIGNAL("activated()"), self, SLOT("selectAllNE()"))
        QObject.connect(self.selectNoneAct, SIGNAL("activated()"), self, SLOT("selectNoneNE()"))
        
        self.ui.tableViewNe.setContextMenuPolicy(Qt.ActionsContextMenu)
    
#     def addNEaction(self):
#         print self.ui.tableViewNe.actions()
#         print self.NEs
#         print self.NEthreads
#         self.cancelOperation()
#         index = self.ui.tableViewNe.selectionModel().currentIndex()
#         print "select "
#         print index
#         print index.row()
#         print index.parent
#         print self.ui.tableViewNe.selectionModel()
#         model=self.ui.tableViewNe.selectionModel()
#         print dir(self.ui.tableViewNe.selectionModel())
#         print model.Rows
#         print model.Select
#         print model.selectedRows()
#         print model.Current
# 
#                 
#         index = self.ui.tableViewNe.currentIndex()
#         print "current " 
#         print index
#         print index.parent
#         print self.netModel
#         model =self.netModel
        
        
#         row = model.rowCount(index.parent())
#         print row
    
    def delNEAction(self):
        self.clearConfig() 
     
    def selectAllNE(self):
        index = self.ui.tableViewNe.currentIndex()
        model =self.netModel
#         print type(model)
        rowCount = model.rowCount(index.parent())
        for row in range(0,rowCount):
            item=model.item(row, showColumn[NE_NAME])
            item.setCheckState(Qt.Checked)
#             print item.checkState()
    
    def selectNoneNE(self):
        index = self.ui.tableViewNe.currentIndex()
        model =self.netModel
        rowCount = model.rowCount(index.parent())
        for row in range(0,rowCount):
            item=model.item(row, showColumn[NE_NAME])
            item.setCheckState(Qt.Unchecked)
#             print item.checkState()
            
    def closeEvent(self,event):
        self.logging.info(u"结束运行升级软件\n")
        try:
            for thread in self.NEthreads.values():
                thread.terminate()
            logging.shutdown() 
        except:
            traceback.print_exc()
        event.accept()
                        
    def checkNeExist(self,ne):
        '''检查网元名和网元IP是否已经存在'''
        self.logging.info(u"检查网元名和网元IP是否已经存在")
        for _ne in self.NEs.values():
            if _ne.neIp == ne.neIp: 
                self.logging.warning(u"网元IP%s已经存在"%(ne.neIp))
                return NE_IP_EXIST
            if _ne.neName == ne.neName:
                self.logging.warning(u"网元名%s已经存在"%(unicode(ne.neName,"utf-8")))
                return NE_NAME_EXIST
        self.logging.info(u"检查网元结束，网元:IP%s,和网元名:%s,是唯一的"%(ne.neIp,unicode(ne.neName,"utf-8")))    
        return NE_NOT_EXIST     
        
    def checkThreadRunning(self):
        '''检查网元线程是否运行'''
        if len(self.NEthreads)==0:
            return False
        
        for thread in self.NEthreads.values():
            if thread.isRunning()==False:
                return False
        return True    
        
    def setUIstatusDisable(self):
        self.ui.pushButtonCancel.setDisabled(False)
        
        self.ui.actionImportConfig.setDisabled(True)
        self.ui.actionSaveAs.setDisabled(True)
        self.ui.actionSaveConfig.setDisabled(True)
        self.ui.pushButtonAddNe.setDisabled(True)
        self.ui.pushButtonDelNe.setDisabled(True)
        self.ui.pushButtonCheckNe.setDisabled(True)
        self.ui.pushButtonUpdateAll.setDisabled(True)
        self.ui.pushButtonAddVersionFile.setDisabled(True)
        for action in self.ui.tableViewNe.actions():
            action.setDisabled(True)
        
        self.ui.groupBoxCheckOption.setDisabled(True)
            
    def setUIstatusEnable(self):
        self.ui.pushButtonCancel.setDisabled(True)
        
        self.ui.actionImportConfig.setDisabled(False)
        self.ui.actionSaveAs.setDisabled(False)
        self.ui.actionSaveConfig.setDisabled(False)
        self.ui.pushButtonAddNe.setDisabled(False)
        self.ui.pushButtonDelNe.setDisabled(False)
        self.ui.pushButtonCheckNe.setDisabled(False)
        self.ui.pushButtonUpdateAll.setDisabled(False)
        self.ui.pushButtonAddVersionFile.setDisabled(False)
        for action in self.ui.tableViewNe.actions():
            action.setDisabled(False)
        self.ui.groupBoxCheckOption.setDisabled(False)
                
    def checkNeSlot(self,message):
        '''接收检查线程反馈的消息，进行处理，根据结果在界面上反映'''
        uiDebug("")
        uiDebug("***updateWindow.checkNeSlot start")
        result = pyparsingEmit(message)
        
        if  result !=EMIT_SIGNAL_ERR:
            runResult = result[0]
#             runFun  = result[1]
            row  = int(result[2])
            
            if runResult == NeThread.FINISH_ALL_FUN:
                model = self.netModel
                
                model.setData(model.index(row, showColumn[NE_IP])               ,self.NEs[row].neIp)
                model.setData(model.index(row, showColumn[SOFTWARE_VERSION])    ,self.NEs[row].softwareVersion)
                model.setData(model.index(row, showColumn[HARDWARE_VERSION])    ,self.NEs[row].hardwareVersion)
                model.setData(model.index(row, showColumn[NE_STATE])            ,self.NEs[row].neState)
                
                self.NEs[row].processState=0
                model.setData(model.index(row, showColumn[UPDATE_STATE])        ,self.NEs[row].processState)
                
                self.messageShow(u"网元%s结束检查"%(self.NEs[row].neIp))
                self.NEthreads[row].signal.sig.disconnect(self.checkNeSlot)
                self.logging.info(u"收到网元%s,网元检查结束消息:%s"%(self.NEs[row].neIp,message))
                self.setUIstatusEnable()
                
            if runResult == NeThread.BEGIN_RUN_FUN:
                pass
                
            if runResult == NeThread.FUN_OK:
                self.logging.info(u"收到网元%s,函数执行成功消息:%s"%(self.NEs[row].neIp,message))
                
            if runResult == NeThread.FUN_ERR:
                self.messageShow(u"网元%s，检查失败"%(self.NEs[row].neIp))
                self.logging.error(u"收到网元%s,函数执行失败消息:%s"%(self.NEs[row].neIp,message))
                self.setUIstatusEnable()
        else:
            uiDebug("receive without control message: %s"%(message))
            self.logging.warning(u"检查网元信息处理模块收到未定义的消息%s"%(message))
            
        uiDebug("***updateWindow.checkNeSlot end")
        uiDebug("")
        
    def checkNe(self):
        '''检查网元slot'''
        self.logging.info(u"开始检查网元操作:")
        self.messageShow(u"开始检查网元")
        
        self.setUIstatusDisable()
        
        _flag = 0
        for row in self.NEs.keys():
            item=self.netModel.item(row, showColumn[NE_NAME])
            if item.checkState() == Qt.Checked:
                _flag = 1
                break

        if _flag ==0:   
            Info = u"没有选择任何网元,检查网元无法继续"
            QMessageBox.information(self,u"提示",Info)
            self.logging.warning(u"没有选择任何网元")
            self.logging.info(u"终止检查网元\n")
            self.messageShow(u"终止检查网元")
            self.setUIstatusEnable()
            return

        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            self.logging.warning(u"上一个操作还未结束")
            self.logging.info(u"终止检查网元操作\n")
            self.setUIstatusEnable()
            self.messageShow(u"终止检查网元")
            return 
         
         
        _flag = 0 
        for row in self.NEs.keys():
            item=self.netModel.item(row, showColumn[NE_NAME])
            if item.checkState() != Qt.Checked:
                continue
            _flag=1
            self.NEthreads[row].clearThreadfun()
            self.NEthreads[row].setThreadfun(1,self.NEs[row].checkNe , NE_OK , row)
            self.NEthreads[row].signal.sig.connect(self.checkNeSlot)
            self.NEthreads[row].run()
            self.logging.info(u"执行NE:%s,检测线程"%(self.NEs[row].neIp))
        
        if _flag==0:
            self.setUIstatusEnable()
            
        self.logging.info(u"完成检查网元操作:相关检查操作在子线程中执行\n")
    
    def updataAllSlot(self,message):
        '''升级操作slot'''
        result = pyparsingEmit(message)
        if  result !=EMIT_SIGNAL_ERR:
            runResult = result[0]
            runFun    = result[1]
            runFunStr= self.updateMessage[runFun.rstrip('>').lstrip("<").split()[2]]
            value =int(result[2].encode("utf-8"))
            row = value / 1000
            processState = value %1000
            model = self.netModel
            
            if runResult == NeThread.FINISH_ALL_FUN:
                
                #升级完毕，将新的信息显示到节面
                processState=100
                
                model.setData(model.index(row, showColumn[NE_IP])               ,self.NEs[row].neIp)
                model.setData(model.index(row, showColumn[SOFTWARE_VERSION])    ,self.NEs[row].softwareVersion)
                model.setData(model.index(row, showColumn[HARDWARE_VERSION])    ,self.NEs[row].hardwareVersion)

                model.setData(model.index(row, showColumn[NE_STATE])  ,u"升级成功")
                self.messageShow(u"网元%s结束升级"%(self.NEs[row].neIp))
                self.logging.info(u"收到网元%s结束升级消息%s"%(self.NEs[row].neIp,message))
                self.NEthreads[row].signal.sig.disconnect(self.updataAllSlot)
                self.setUIstatusEnable()
                 
                 
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
#                     runFunStr= self.updateMessage[runFun.rstrip('>').lstrip("<").split()[2]]
                    self.messageShow(u"网元%s升级操作,执行函数%s成功"%(self.NEs[row].neIp,runFunStr))

                self.logging.info(u"收到网元%s升级操作,执行函数%s成功消息:%s"%(self.NEs[row].neIp,runFun,message))
                    
            if runResult == NeThread.FUN_ERR:
                for item in self.updateMessage.keys():
                    if runFun.find(item) == -1:
                        pass
                    else:
                        model.setData(model.index(row, showColumn[NE_STATE])  ,self.updateMessage[item]+u":失败")
                
                #版本冲突时需要特殊显示        
                checkUpdateFileStr = str(NE.checkUpdateFile).rstrip('>').lstrip("<").split()[2]
                if runFun.find(checkUpdateFileStr) != -1:
                    model.setData(model.index(row, showColumn[NE_STATE])  ,u"升级版本与运行版本存在冲突")
                

                    
                self.messageShow(u"网元%s升级操作,执行函数%s失败"%(self.NEs[row].neIp,runFunStr))
                self.logging.error(u"收到网元%s升级操作,执行函数%s失败消息:%s"%(self.NEs[row].neIp,runFun,message))
                self.setUIstatusEnable()
                
            #在界面上显示进度条    
            model.setData(model.index(row, showColumn[UPDATE_STATE]),processState)
            
            #更新网元升级状态
            self.NEs[row].processState=processState
            
    def updateAll(self):
        '''开始升级'''
        self.logging.info(u"开始升级网元操作:")
        self.setUIstatusDisable()
        self.messageShow(u"开始升级网元")
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            self.logging.warning(u"上一个操作还未结束")
            self.logging.info(u"终止升级网元操作\n")
            self.setUIstatusEnable()
            self.messageShow(u"终止升级网元操作")
            return         
        
        if self.versionFile == None:
            Info = u"版本文件不可用，请配置好相关文件后再升级"
            QMessageBox.information(self,u"提示",Info)
            self.logging.warning(u"未设置升级版本文件")
            self.logging.info(u"终止升级网元操作\n")
            self.setUIstatusEnable()
            self.messageShow(u"终止升级网元操作")
            return
        
        _flag = 0
        for row in self.NEs.keys():
            item=self.netModel.item(row, showColumn[NE_NAME])
            if item.checkState() == Qt.Checked:
                _flag += 1
#                 break

        if _flag ==0:   
            Info = u"没有选择任何网元，升级无法继续"
            QMessageBox.information(self,u"提示",Info)
            self.logging.warning(u"没有选择任何网元")
            self.logging.info(u"终止升级网元操作\n")
            self.setUIstatusEnable()
            self.messageShow(u"终止升级网元操作")
            return

        #暂时只运行同时升级8个AP
        if _flag >= 8: 
            Info = u"同时升级网元数目不能超过8个，请修改"
            QMessageBox.information(self,u"提示",Info)
            self.logging.warning(u"同时升级网元数目不能超过8个")
            self.logging.info(u"终止升级网元操作\n")
            self.setUIstatusEnable()
            self.messageShow(u"终止升级网元操作")
            return
        
            
        #清除网元保留的配置文件路径
        for row in self.NEs.keys():
            item=self.netModel.item(row, showColumn[NE_NAME])
            if item.checkState() != Qt.Checked:
                continue

            ne =self.NEs[row]
            self.NEthreads[row]=NeThread()
            self.NEthreads[row].clearThreadfun()
            
            _step=0
            
            #升级前检测
            _step=_step+1
            #self.ui.checkBoxCheckNe 
            self.NEthreads[row].setThreadfun(_step,ne.checkNe, NE_OK, row*1000+2)
                       
            #检测升级版本是否与当前运行版本存在冲突            
            _step=_step+1
            #self.ui.checkBoxCheckUpdateFile
            self.NEthreads[row].setThreadfun(_step,ne.checkUpdateFile, NE_OK, row*1000+2,self.versionFile)

            #保留当前网元配置
            _step=_step+1
            if self.ui.checkBoxSaveNeConfig.checkState() == Qt.Checked:
                self.NEthreads[row].setThreadfun(_step,ne.saveNeConfig, NE_OK, row*1000+5)
            
            #下载网元配置到本地
            _step=_step+1
            #self.ui.checkBoxSaveNeConfigToLocal
            self.NEthreads[row].setThreadfun(_step,ne.saveNeConfigToLocal, NE_OK, row*1000+5)
           
            #上传版本文件到网元
            _step=_step+1
            if self.ui.checkBoxUpdateVersionFile.checkState() == Qt.Checked:
                self.NEthreads[row].setThreadfun(_step,ne.updateVersionFile, NE_OK, row*1000+20,self.versionFile, self.versionFilePath)
            
            #升级版本文件
            _step=_step+1
            if self.ui.checkBoxUpgradeSoft.checkState() == Qt.Checked:
                self.NEthreads[row].setThreadfun(_step,ne.updateSoft,NE_OK, row*1000+25, self.versionFile, ne.willUpdateSoftPartition)
           
            #激活版本文件
            _step=_step+1
            if self.ui.checkBoxActiveSoft.checkState() == Qt.Checked:
                self.NEthreads[row].setThreadfun(_step,ne.activeSoft,NE_OK, row*1000+30, ne.willUpdateSoftPartition)
            
            
            #复位网元,进度是35%
            _step=_step+1
            if self.ui.checkBoxReboot.checkState() == Qt.Checked: 
                self.NEthreads[row].setThreadfun(_step,ne.reboot,NE_OK, row*1000+35)
               
            #复位等待  
            if self.ui.checkBoxReboot.checkState() == Qt.Checked:
                for _step in range(_step+1,45):
                    self.NEthreads[row].setThreadfun(_step,QThread.sleep,None, row*1000+40+_step,10)
            else:
                _step=44
                 
            #复位后连接测试      
            _step=_step+1
            if self.ui.checkBoxAfterRebootConnectTest.checkState() == Qt.Checked: 
                self.NEthreads[row].setThreadfun(_step,ne.afterRebootTest,NE_OK, row*1000+90)
             
            #复位网元正常后，网元检测 
            _step=_step+1
            if self.ui.checkBoxAfterRebootTest.checkState() == Qt.Checked:
                self.NEthreads[row].setThreadfun(_step,ne.afterRebootCheck, NE_OK, row*1000+95,self.ui.lineEditVersion.text())


            #复位网元正常后，网元检测 
            _step=_step+1
            if self.ui.checkBoxfterRebootConfigCheck.checkState() == Qt.Checked:
                self.NEthreads[row].setThreadfun(_step,ne.afterRebootConfigCheck, NE_OK, row*1000+99)

                
            self.NEthreads[row].signal.sig.connect(self.updataAllSlot)
            
            self.NEthreads[row].start()
            self.logging.info(u"执行NE:%s,升级线程"%(ne.neIp))

    def messageShow(self,text):
        self.ui.textEditInformation.append(text)

    def cancelOperation(self):
        '''取消操作'''
        
        _flag = 0
        for row in self.NEs.keys():
            item=self.netModel.item(row, showColumn[NE_NAME])
            if item.checkState() == Qt.Checked:
                _flag = 1
                break

        if _flag ==0:   
            Info = u"没有选择任何网元，取消操作无法继续"
            QMessageBox.information(self,u"提示",Info)
            self.logging.warning(u"没有选择任何网元")
            self.logging.info(u"无法开展取消操作\n")
            self.setUIstatusEnable()
            self.messageShow(Info)
            return
        
        cantCancelNE=[]
        cancelNE=[]
        model = self.netModel    
        if self.checkThreadRunning()==True:
            for row in self.NEthreads.keys():
                ne=self.NEs[row]
                thread= self.NEthreads[row] 
                item=self.netModel.item(row, showColumn[NE_NAME])
                if item.checkState() == Qt.Checked:
                    if ne.processState >= 35:
                        #当processState >=35时 说明网元已经开始复位操作，这个时候不允许cancel网元
                        self.messageShow(u"网元%s已经执行完复位操作，后续步骤不允许取消"%(self.NEs[row].neIp))
                        cantCancelNE.append(ne)
                        continue
                    
                    thread.terminate()
                    thread.wait(2)
                    model.setData(model.index(row, showColumn[NE_STATE])  ,u"取消动作成功")
                    
                    cancelNE.append(ne)
                    self.messageShow(u"网元%s操作人为终止"%(self.NEs[row].neIp))
            
            if len(cancelNE) == len(self.NEs):
                #如果所有网元都被终止，需要改变界面按钮的使能情况
                self.setUIstatusEnable()

            if cantCancelNE !=[]:
                _message = ""
                for _ne in cantCancelNE:
                    _message +=_ne.neIp+"," 
                    
                QMessageBox.information(self,u"提示",u"网元:%s已经执行完复位操作，后续步骤不允许取消"%_message)
                        
    def clearConfig(self):
        #导入配置前，清除上一次配置
        
        #删除界面上所有网元
        index = self.ui.tableViewNe.currentIndex()
        model = self.netModel
        rowCount = model.rowCount(index.parent())
        while rowCount!=0:
            model.removeRow(0,index.parent())
            rowCount -= 1
            
        self.NEs.clear()
        self.NEthreads.clear()
        self.versionFile     = None   #目标升级版本文件名
        self.versionFilePath = None   #目标升级版本文件本地路径
        self.configFile = None        #升级软件配置  
                    
    def __activeConfig(self,config):
        '''将导入的配置显示到界面上'''
        if config != None:
            for ne in config.getNeLists().values():
                
                
                self.__addNe(ne)
                
    def importConfig(self):
        '''从配置文件中导入配置'''
        
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            self.logging.warning(u"上一个操作还未结束")
            self.logging.info(u"终止检查网元操作\n")
            return 
        
        configFile = QFileDialog.getOpenFileName(self, u"Load configFile File", QDir.currentPath(), filter="*.conf")
        if configFile != None:
            #导入配置时，需要保留之前的配置到当前目录下的lastNoSaveConfig文件
            backConfig = updateConfig()
            backConfig.configFile = self.todaylogPath + self.directorySeparator + "lastNoSaveConfig" 
            for ne in self.NEs.values():
                backConfig.addNe(ne)
            backConfig.saveConfig()
            
            #导入配置文件
            config = updateConfig()
            #这里写的有点丑陋
            result = config.readConfig(configFile[0],self.todaylogPath+self.directorySeparator)
            if result == READ_CONFIG_OK:
                #读取配置文件成功
                
                #清空当前配置
                self.clearConfig()
                
                #激活配置
                self.__activeConfig(config)
                
                #激活配置后要检查
#                 self.checkNe()
                self.configFile=configFile[0]
                self.logging.info(u"配置文件%s读取成功"%(configFile[0]))
            else:
                #读取配置文件失败
                self.logging.error(u"配置文件%s读取失败"%(configFile[0]))
                
    def saveConfig(self):
        '''保存当前升级配置，主要是网元信息'''
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            self.logging.warning(u"上一个操作还未结束")
            self.logging.info(u"终止检查网元操作\n")
            return 
        
        if self.configFile!=None:
            #如果当前网元是从配置文件中导入的，则存入这个导入的配置文件中
            config = updateConfig()
            config.configFile = self.configFile 
            for ne in self.NEs.values():
                config.addNe(ne)
            result = config.saveConfig()
            if result == SAVE_CONFIG_OK:
                self.logging.info(u"配置文件%s保留成功"%(self.configFile))
            else:
                self.logging.error(u"配置文件%s保留失败"%(self.configFile))
        else:
            #如果当前网元不是从配置文件中导入的，则进行另存为的操作
            self.saveConfigAs()
           
    def saveConfigAs(self):
        '''保存当前升级配置，主要是网元信息'''
        configFile = QFileDialog.getSaveFileName(self, u"save configFile File", QDir.currentPath(), filter="*.conf")
        if configFile != None:
            self.configFile=configFile[0]
            self.saveConfig()
        else:
            self.logging.warning(u"没有选择任何文件保留配置")
            
    def __addNe(self, tempNe ,active=True):
        if tempNe!=None:
            index = self.ui.tableViewNe.selectionModel().currentIndex()
            model = self.netModel
            row = model.rowCount(index.parent())
        
            
            name = QStandardItem(unicode(tempNe.neName,"utf-8"))
            name.setCheckable(True)
            name.setEditable(False)
            name.setEnabled(active)
            model.setItem(row, showColumn[NE_NAME], name)
            
            neIp = QStandardItem(tempNe.neIp)
            neIp.setEditable(False)
            neIp.setEnabled(active)
            model.setItem(row, showColumn[NE_IP]               , neIp)
            
            softwareVersion = QStandardItem(tempNe.softwareVersion)
            softwareVersion.setEditable(False)
            softwareVersion.setEnabled(active)
            model.setItem(row, showColumn[SOFTWARE_VERSION]    , softwareVersion)
            
            hardwareVersion = QStandardItem(tempNe.hardwareVersion)
            hardwareVersion.setEditable(False)
            hardwareVersion.setEnabled(active)
            model.setItem(row, showColumn[HARDWARE_VERSION]    , hardwareVersion)
            
            neState = QStandardItem(tempNe.neState)
            neState.setEditable(False)
            neState.setEnabled(active)
            model.setItem(row, showColumn[NE_STATE]            , neState)
            
            processState = QStandardItem(tempNe.processState)
            processState.setEditable(False)
            processState.setEnabled(active)
            model.setItem(row, showColumn[UPDATE_STATE]        , processState)
                    
            index=model.index(row, showColumn[UPDATE_STATE])
            model.setData(index,tempNe.processState)
            
            self.NEs[row]=tempNe
            self.NEthreads[row]=NeThread()

            for key in showColumn.keys():
                model.item(row, showColumn[key]).setTextAlignment(Qt.AlignCenter);
             
            self.logging.info(u"添加网元%s\n"%(tempNe.neIp))
        else:    
            self.logging.warning(u"没有添加任何网元\n")    
            
    def addNe(self):
        '''添加网元操作'''
        self.logging.info(u"开始添加网元操作:")
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            self.logging.warning(u"上一个操作还未结束")
            self.logging.info(u"终止添加网元操作\n")
            return 
        
        
        #使用模态Dialog进行输入
        self.tempNe=None
        testDialog= editNEDialog(self)
        res=testDialog.exec_()
        
        self.__addNe(self.tempNe)
    
    def delNe(self):
        '''删除网元操作'''
        self.logging.info(u"开始删除网元")
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            self.logging.warning(u"上一个操作还未结束")
            self.logging.info(u"终止删除网元操作\n")
            return 
        
        index = self.ui.tableViewNe.currentIndex()
        model =self.netModel
        rowCount = model.rowCount(index.parent())

        #记录那些row被删除
        delRows=[]
        delRowChanges={}
        for row in range(0,rowCount):
            item=model.item(row, showColumn[NE_NAME])
#             print row
#             print item
#             print item.checkState()
#             print item.checkState() ==Qt.Checked 
            
            if item.checkState() == Qt.Checked:
                delRows.append(row)
                for _row in range(row,rowCount):
                    delRowChanges[_row]=_row+1
                    
        
            
        if delRows != []:
            ret = QMessageBox.warning(self, u"警告",
                               u"被选中的网元将被删除，请确认是否继续",
                               QMessageBox.Ok|QMessageBox.Cancel,
                               QMessageBox.Ok)
                  
            if ret == QMessageBox.Cancel:
                #选择不删除网元
                return
     
            #从高到低删除row
            delRows.reverse()
            for row in delRows:
                model.removeRow(row,index.parent())
                self.logging.info(u"删除网元%s\n"%(self.NEs[row].neIp))
                self.NEs.pop(row)
                self.NEthreads.pop(row)
           
           
            #重组self.NES和self.NEthreads
            NEs = self.NEs.values()
            NEthreads = self.NEthreads.values()
            self.NEs.clear()
            self.NEthreads.clear()
            for row in range(0,model.rowCount(index.parent())):
                self.NEs[row]=NEs[row]
                self.NEthreads[row]=NEthreads[row]
        
        else:
            Info = u"没有选中网元！请选中后，再操作。"
            QMessageBox.information(self,u"提示",Info)
            self.logging.warning(u"没有删除任何网元\n")
            
    def addVersionFile(self):
        '''添加版本文件'''
        self.logging.info(u"开始添加版本文件操作")
        if self.checkThreadRunning()==True:
            self.messageShow(u"上一个操作还未结束，请稍后再尝试")
            self.logging.warning(u"上一个操作还未结束")
            self.logging.info(u"终止添加版本文件操作\n")
            return 
                
        self.ui.lineEditVersion.setText("")
        openFile = QFileDialog.getOpenFileName(self, "Find Files", QDir.currentPath())
        
        if openFile[0] != u"" :
            self.ui.lineEditVersionFile.setText(openFile[0])
            versionFile = fileCheck(openFile[0])
            if versionFile.getVersion() != OPEN_FILE_OK :
                self.versionFile=None
                self.ui.lineEditVersion.setText(u"没有打开任何版本文件")
                self.logging.warning(u"没有打开任何版本文件")
                return
            else:
                if versionFile.verifyVersion() != VERIFY_VERSION_OK:
                    self.versionFile=None
                    self.ui.lineEditVersion.setText(u"版本文件无法校验")
                    self.logging.warning(u"版本文件%s无法校验"%(openFile))
                    return
        else:
            return        
        self.ui.lineEditVersion.setText(versionFile.version["version"])
        self.versionFilePath = openFile[0][0:len(openFile[0])- len(versionFile.version["version"])]   
        self.versionFile = versionFile.version["version"]    
        self.logging.info(u"添加版本文件%s成功\n"%(openFile[0]))
          

class QtSingleApplication(QApplication):
    #网上拷贝的一个程序，使得程序只能运行一个
    #http://stackoverflow.com/questions/12712360/qtsingleapplication-for-pyside-or-pyqt
    messageReceived = Signal(unicode)

    def __init__(self, id, *argv):

        super(QtSingleApplication, self).__init__(*argv)
        self._id = id
        self._activationWindow = None
        self._activateOnMessage = False

        # Is there another instance running?
        self._outSocket = QLocalSocket()
        self._outSocket.connectToServer(self._id)
        self._isRunning = self._outSocket.waitForConnected()

        if self._isRunning:
            # Yes, there is.
            self._outStream = QTextStream(self._outSocket)
            self._outStream.setCodec('UTF-8')
        else:
            # No, there isn't.
            self._outSocket = None
            self._outStream = None
            self._inSocket = None
            self._inStream = None
            self._server = QLocalServer()
            self._server.listen(self._id)
            self._server.newConnection.connect(self._onNewConnection)

    def isRunning(self):
        return self._isRunning

    def id(self):
        return self._id

    def activationWindow(self):
        return self._activationWindow

    def setActivationWindow(self, activationWindow, activateOnMessage = True):
        self._activationWindow = activationWindow
        self._activateOnMessage = activateOnMessage

    def activateWindow(self):
        if not self._activationWindow:
            return
        self._activationWindow.setWindowState(
            self._activationWindow.windowState() & ~Qt.WindowMinimized)
        self._activationWindow.raise_()
        self._activationWindow.activateWindow()

    def sendMessage(self, msg):
        if not self._outStream:
            return False
        self._outStream << msg << '\n'
        self._outStream.flush()
        return self._outSocket.waitForBytesWritten()

    def _onNewConnection(self):
        if self._inSocket:
            self._inSocket.readyRead.disconnect(self._onReadyRead)
        self._inSocket = self._server.nextPendingConnection()
        if not self._inSocket:
            return
        self._inStream = QTextStream(self._inSocket)
        self._inStream.setCodec('UTF-8')
        self._inSocket.readyRead.connect(self._onReadyRead)
        if self._activateOnMessage:
            self.activateWindow()

    def _onReadyRead(self):
        while True:
            msg = self._inStream.readLine()
            if not msg: break
            self.messageReceived.emit(msg)
                      
def main():
    app = QApplication(sys.argv)
    app.setStyle("cleanlooks")
#    app.setStyle("arthurStyle")
    d = updateWindow(app)
    d.show()
    sys.exit(app.exec_())
    

def singleMain():
    appGuid = 'F3FF80BA-BA05-4277-8063-82A6DB9245A2'
    app = QtSingleApplication(appGuid, sys.argv)
    app.setStyle("cleanlooks")
    if app.isRunning():
        sys.exit(0)

    d = updateWindow(app)
    d.show()
    sys.exit(app.exec_())
    
            
if __name__ == '__main__':
#     main()  
    singleMain()  
