# -*- coding: UTF-8 -*-
'''
Created on 2010-9-19

@author: x00163361
'''
import logging,os,datetime,time,filecmp
import subprocess
import platform
from pyparsing import *
from debug import *
import ConfigParser
from telnet import telnetAC ,TELNET_OK
from fileCheck import fileCheck,RMIOS_STR,VXWORKS_STR,LINUX_STR,VERSION_STR,BOOTLOADER_STR
from ftp import ftpAC ,FTP_OK
import traceback

#错误码
CONFIG_CODE_BASE                     = 300 
READ_CONFIG_OK                       = CONFIG_CODE_BASE + 0 
READ_CONFIG_ERR                      = CONFIG_CODE_BASE + 1
SAVE_CONFIG_OK                       = CONFIG_CODE_BASE + 2
SAVE_CONFIG_ERR                      = CONFIG_CODE_BASE + 3
OPEN_CONFIG_FILE_ERR                 = CONFIG_CODE_BASE + 4
DEL_NE_OK                            = CONFIG_CODE_BASE + 5
DEL_NE_ERR                           = CONFIG_CODE_BASE + 6
PYPARSING_SOFTWARE_VERSION_ERR       = CONFIG_CODE_BASE + 7
CONNECT_OK                           = CONFIG_CODE_BASE + 8
PYPARSING_HARDWARE_VERSION_ERR       = CONFIG_CODE_BASE + 9
PYPARSING_CURRENT_SOFT_PARTITION_ERR = CONFIG_CODE_BASE + 10
GET_UPDATE_FILE_ERR                  = CONFIG_CODE_BASE + 11
PYPARSING_UPDATE_FILE_ERR            = CONFIG_CODE_BASE + 12
SOFT_PARTITION_PARA_ERR              = CONFIG_CODE_BASE + 13
NE_OK                                = CONFIG_CODE_BASE + 14
NE_ALIVE                             = CONFIG_CODE_BASE + 15
NE_DOWN                              = CONFIG_CODE_BASE + 16
RUN_COMMAND_ERR                      = CONFIG_CODE_BASE + 17
TELNET_MANAGE_PLATFORM_ERR           = CONFIG_CODE_BASE + 18
GET_SOFT_VERSION_ERR                 = CONFIG_CODE_BASE + 19
TELNET_ACCESS_PLATFORM_ERR           = CONFIG_CODE_BASE + 20
GET_HOTSTANDBY_STATUS_ERR            = CONFIG_CODE_BASE + 21
RUN_REBOOT_COMMAND_ERR               = CONFIG_CODE_BASE + 22
RUN_REBOOT_CONFIRM_COMMAND_ERR       = CONFIG_CODE_BASE + 23
RUN_UPGRADE_COMMAND_ERR              = CONFIG_CODE_BASE + 24
RUN_UPGRADE_CONFIRM_COMMAND_ERR      = CONFIG_CODE_BASE + 25
RUN_ACTIVE_COMMAND_ERR               = CONFIG_CODE_BASE + 26
RUN_LS_COMMAND_ERR                   = CONFIG_CODE_BASE + 27

FTP_LOGIN_MANAGE_PLATFORM_ERR        = CONFIG_CODE_BASE + 28
FTP_LOGOUT_MANAGE_PLATFORM_ERR       = CONFIG_CODE_BASE + 29
FTP_PUT_SOFT_MANAGE_PLATFORM_ERR     = CONFIG_CODE_BASE + 30
SOME_CONFIG_FILE_NOT_SAVED           = CONFIG_CODE_BASE + 31

FILE_IS_NOT_EXIST                    = CONFIG_CODE_BASE + 32
FILE_IS_EXIST                        = CONFIG_CODE_BASE + 33
PYPARSING_FILE_ERR                   = CONFIG_CODE_BASE + 34

SUPER_MODE_ERR                       = CONFIG_CODE_BASE + 35

UPDATE_VERSION_ERR                   = CONFIG_CODE_BASE + 36
CONFIG_FILE_DIFF                     = CONFIG_CODE_BASE + 37
CONFIG_FILE_CONTEXT_DIFF             = CONFIG_CODE_BASE + 38
UPDATE_PARTITION_ERR                 = CONFIG_CODE_BASE + 39
TARGET_VERSION_SAME                  = CONFIG_CODE_BASE + 40

#关键字
NE_NAME            = u"网元名" 
NE_IP              = u"网元IP"  
ACCESS_USER        = u"接入平台用户" 
ACCESS_PASSWORD    = u"接入平台密码"
MANAGE_USER        = u"管理平台用户" 
MANAGE_PASSWORD    = u"管理平台密码"
SOFTWARE_VERSION   = u"软件版本" 
HARDWARE_VERSION   = u"硬件版本"
MASTER_SLAVE_STATE = u"主备状态" 
NE_STATE           = u"网元状态" 
UPDATE_STATE       = u"进度"




# TELNET_ACCESS_PORT = 23
# TELNET_MANAGE_PORT = 87


#管理平台telnet命令列表
GET_VERSION   = "getVerrsion"
REBOOT        = "reboot"
UPGRADE       = "upgrade"
ACTIVE        = "active"
UPGRADE_YES   = "active_yes"
LS            = "ls"
PWD           = "pwd"
REBOOT        = "reboot"
REBOOT_YES    = "reboot_yes"

#软件分区升级定义，
#当前分区为version0时，需要升级version1分区
#当前分区为version0时，需要升级version0分区
SOFT_PARTITION={"version0":"0","version1":"1"}
GET_WILL_UPDATE_SOFT_PARTITION={"version0":"version1","version1":"version0"}

#接入平台telnet命令列表
ENABLE_MODE = "enable"
ENABLE_PASSWORD ="super"
# DEBUG_MODE     = "debug develop"
# DEBUG_PASSWORD = "Il0vethisT1m."
SHOW_HOTSTANDBY_GROUP_INFO_ALL="hotstandbyall"
SHOW_HOTSTANDBY_GROUP_INFO="hotstandby"
COPY_CONFIG="copy configFile"

#内部使用字符串定义
HARDWARE_CODE ="hardwareCode" 
CURRENT_SOFT_PARTITION="currentSoftPartition"
SOFT_FILE="softFile" 
 
#硬件版本表
hardwareDict={
 10 : "Bgate1030-AW6000" , #6000整机
 11 : "BMCR408"          , #6004整机
 12 : "BMCR416"          , #6006整机
 #13 : "ZA3212"           ,
 #14 : "ZA3212"           ,
 20 : "NPU_SN"           , #业务版
 22 : "NMC_SN"           , #网板
 #23 : ""                , #12GE扩展板
 24 : "AMCR732"          , #732前插板
 25 : "AMCR732-RTM"      , #732后插板
 27 : "AMCR732"          , #732前插板,不带连接器 
 28 : "MCS2828"          , #MCS2828网板
 80 : "ISA8327"          , #Bgate-GT10-I（ISA8327）业务板
 }

LOG_DIR="updatelog"
LOG_OPERATION="operation.txt"


class NELog():
    def __init__(self):
        pass

    
class NE:
    
    #接入平台telnet配置
    telnet_accesss_port = 23
    telnet_accesss_user_except_string = "Login:"
    telnet_accesss_password_except_string = "Password:"
    telnet_accesss_welcome_string=""
#     telnet_accesss_prompt="BNOS>"
    telnet_accesss_prompt=">"
    
    #接入平台命令列表
    telnet_access_comandDict={SHOW_HOTSTANDBY_GROUP_INFO_ALL:"show hotstandby group-info all",
                              SHOW_HOTSTANDBY_GROUP_INFO:"show hotstandby group-info",
                              ENABLE_MODE:"enable",
                              ENABLE_PASSWORD:"super",
                              COPY_CONFIG:"copy running-configFile startup-configFile"
                              }

#     telnet_access_commandPromtDict={telnet_access_comandDict[SHOW_HOTSTANDBY_GROUP_INFO_ALL]:"BNOS",
#                                     telnet_access_comandDict[SHOW_HOTSTANDBY_GROUP_INFO]:"BNOS",
#                                     telnet_access_comandDict[ENABLE_MODE]:"Password:",
#                                     telnet_access_comandDict[ENABLE_PASSWORD]:"BNOS",
#                                     telnet_access_comandDict[COPY_CONFIG]:"BNOS",                                                                        
#                                }
    #对提示符的判断存在问题
    telnet_access_commandPromtDict={telnet_access_comandDict[SHOW_HOTSTANDBY_GROUP_INFO_ALL]:">",
                                    telnet_access_comandDict[SHOW_HOTSTANDBY_GROUP_INFO]:">",
                                    telnet_access_comandDict[ENABLE_MODE]:"Password:",
                                    telnet_access_comandDict[ENABLE_PASSWORD]:"#",
                                    telnet_access_comandDict[COPY_CONFIG]:"#",                                                                        
                               }    
         
    #管理平台配置    
    telnet_manage_port  = 87
    telnet_manage_user_except_string = "cwcos login:"
    telnet_manage_password_except_string = "Password:"
    telnet_manage_welcome_string="Welcome to Centralize wireless Controller Operating System"
    telnet_manage_prompt="cwcos#"
    softPath    = '/root/'  #存放软件的路径
    
    
    #管理平台命令列表    
    telnet_manage_command_dict={GET_VERSION:"cat /proc/rmi/mips-version",
                               REBOOT:"",
                               UPGRADE:"version upgrade",
                               UPGRADE_YES:"y",
                               ACTIVE:"version active",
                               LS:"ls ",
                               PWD:"pwd",
                               REBOOT:"reboot",    
                               REBOOT_YES:"y",
                              }
    telnet_manage_commandPromt_dict={telnet_manage_command_dict[GET_VERSION]:"cwcos#",
                               telnet_manage_command_dict[UPGRADE]:"to exit:",
                               telnet_manage_command_dict[UPGRADE_YES]:"Version upgrade success!",
                               telnet_manage_command_dict[ACTIVE]:"Version active success!",
                               telnet_manage_command_dict[LS]:"cwcos#",
                               telnet_manage_command_dict[PWD]:"cwcos#",
                               telnet_manage_command_dict[REBOOT]:"Are you sure to reboot",
                               telnet_manage_command_dict[REBOOT_YES]:"cwcos#",
                               }
    

    
#     hardwareCodePyparsingStr=MatchFirst("the board id is:") + Word(printables).setResultsName(HARDWARE_CODE) +Literal('''<NULL>''')
    hardwareCodePyparsingStr=MatchFirst("the board id is:") + Word(printables).setResultsName(HARDWARE_CODE)
    currentVersionPyparsingStr = MatchFirst("current-running-version:") + Word(printables).setResultsName(CURRENT_SOFT_PARTITION)
    
    #网元配置路径
    ne_config_file_dict={
                          "access.conf"           : "/icac/conf/",
                          "forward.conf"          : "/icac/conf/",
                          "nproxy.conf"           : "/icac/conf/",
                          "web.conf"              : "/icac/conf/",
                          "license.conf"          : "/icac/conf/",
                          "zoom_ac_config.conf"   : "/icac/conf/",
                          "hostname"              : "/etc/",
                          "health-monitor-configFile" : "/etc/",
                          "lsave.conf"            : "/etc/",
                          "syslog.conf"           : "/etc/",
                          "ntp.conf"              : "/etc/",
                          "network.conf"          : "/etc/",
                          "nsswitch.conf"         : "/etc/",
                          "bcm_running_config"    : "/etc/",
                          "vxworks_conf"          : "/nvram/",
                          }
    
    
    def __init__(self,neName = "AC",
                      neIp   = "10.1.1.2",
                      accessUserName = "bnas",
                      accessPassword = "bnas",
                      manageUserName = "root",
                      managePassword = "fitap^_^",
                      logpath="."
                      ):
        self.neName = neName
        self.neIp   = neIp
        self.accessUserName = accessUserName
        self.accessPassword = accessPassword
        self.manageUserName = manageUserName
        self.managePassword = managePassword
        self.softwareVersion  = None
        self.hardwareVersion  = None
        self.currentSoftPartition   = None
        self.willUpdateSoftPartition =None
        self.masterSlaveState = None
        self.neState          = None
        self.processState     = 0
        self.updateFile       = None
        
        self.telnetManagePlatform = telnetAC(self.neIp, 
                                   self.telnet_manage_port, 
                                   self.telnet_manage_user_except_string, 
                                   self.telnet_manage_password_except_string, 
                                   self.telnet_manage_welcome_string, 
                                   self.telnet_manage_prompt)
        
        self.telnetAccessPlatform = telnetAC(self.neIp,
                                     self.telnet_accesss_port,
                                     self.telnet_accesss_user_except_string,
                                     self.telnet_accesss_password_except_string,
                                     self.telnet_accesss_welcome_string,
                                     self.telnet_accesss_prompt)
        
        self.ftpManagePlatform = ftpAC(self.neIp)
    
        self.noSavedConfigFile = []   
        self.savedConfigFile   = []   
        
        #目录分隔符
        self.directorySeparator="\\"
        if platform.system() == "Linux":
            self.directorySeparator="/" 
        elif platform.system() == "Windows":     
            self.directorySeparator="\\"
            
        #建立日志记录模块,在logpath目录下，以网元名加IP地址建立网元日志目录
        if logpath==".":
            self.logPath=unicode(self.neName+"_"+self.neIp,"utf-8")
        else:
            self.logPath=unicode(logpath+self.neName+"_"+self.neIp,"utf-8")

        if os.path.exists(self.logPath) == False:
            os.mkdir(self.logPath)     
        
        #记录网元操作的日志文件，处于日志目录下，名称为log
        self.logFile = self.logPath + self.directorySeparator +"log"  
        
        #记录最近一次保留的配置文件路径 
        self.saveConfigPath= None
                    
        self.logging = logging.getLogger(self.neName) 
        fd=logging.FileHandler(self.logFile)
        fm=logging.Formatter("%(asctime)s  %(levelname)s - %(message)s","%Y-%m-%d %H:%M:%S")
        fd.setFormatter(fm)
        self.logging.addHandler(fd)
        self.logging.setLevel(logging.INFO)
        
    def checkUpdateFile(self,fileVersion):
        if fileVersion == self.softwareVersion:
            return TARGET_VERSION_SAME
        return NE_OK
    
    def checkNe(self):
        '''检查网元，获取网元信息，软件版本，硬件版本，主备状态'''
        
        self.logging.info(u"开始检查网元信息") 
        
        #管理平台登录操作
        self.logging.info(u"**telnet管理平台")
        result = self.telnetManagePlatform.login(self.manageUserName, self.managePassword) 
        if result != TELNET_OK:
            controlDebug("can't login ac manage platform: %s\n"%(self.neIp))
            self.logging.error(u"**telnet管理平台失败: 错误码为:%d"%(result))
            self.logging.info(u"由于意外，终止检查网元信息")
            return TELNET_MANAGE_PLATFORM_ERR
         
        self.telnetManagePlatform.setCommand(self.telnet_manage_commandPromt_dict)
        
        #下发版本查看命令 
        self.logging.info(u"**下发获取版本命令:%s"%(self.telnet_manage_command_dict[GET_VERSION]))
        result=self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[GET_VERSION])
        if result != TELNET_OK:
            controlDebug(u"run command %s err\n"%(self.telnet_manage_commandPromt_dict[GET_VERSION]))
            self.logging.error(u"**执行获取版本命令日志失败: 错误码为:%d"%(result))
            self.telnetManagePlatform.logout()
            self.logging.info(u"**断开管理平台telnet连接")
            self.logging.info(u"由于意外，终止检查网元信息")
            return GET_SOFT_VERSION_ERR
         
        self.logging.info(u"**获取版本信息为:")
        self.logging.info(self.telnetManagePlatform.commandResult)   
            
        #获取软件版本
        try:
            tempstr= fileCheck.pyparsingstr[RMIOS_STR] +\
                     fileCheck.pyparsingstr[VXWORKS_STR] +\
                     fileCheck.pyparsingstr[LINUX_STR] +\
                     fileCheck.pyparsingstr[VERSION_STR]
            result=tempstr.searchString(self.telnetManagePlatform.commandResult,True)
            self.softwareVersion=result[0][VERSION_STR]
        except:
            self.telnetManagePlatform.logout()
            self.logging.error(u"**解析软件版本信息出错")
            self.logging.info(u"**断开管理平台telnet连接")
            self.logging.info(u"由于意外，终止检查网元信息")
            traceback.print_exc()
            return PYPARSING_SOFTWARE_VERSION_ERR   
 
        self.logging.info(u"**获取软件版本信息为:%s"%(self.softwareVersion))
        
        #获取硬件版本
        try:
#             controlDebug(self.telnetManagePlatform.commandResult)
            result=self.hardwareCodePyparsingStr.searchString(self.telnetManagePlatform.commandResult,True)
 
            #硬件型号取硬件code的第2和第3字节
            self.hardwareVersion=hardwareDict[int(result[0][HARDWARE_CODE][2:4])]
        except:
            self.telnetManagePlatform.logout()
            self.logging.error(u"**解析硬件版本信息出错")
            self.logging.info(u"**断开管理平台telnet连接")
            self.logging.info(u"由于意外，终止检查网元信息")
            traceback.print_exc()
            return PYPARSING_HARDWARE_VERSION_ERR   
            
        self.logging.info(u"**获取硬件版本信息为:%s"%(self.hardwareVersion))
            
        #获取当前运行软件分区
        try:
            result=self.currentVersionPyparsingStr.searchString(self.telnetManagePlatform.commandResult,True)
            self.currentSoftPartition    = result[0][CURRENT_SOFT_PARTITION]
            self.willUpdateSoftPartition = GET_WILL_UPDATE_SOFT_PARTITION[self.currentSoftPartition]
        except:
            self.telnetManagePlatform.logout()
            self.logging.error(u"**解析当前运行软件分区出错")
            self.logging.info(u"**断开管理平台telnet连接")            
            self.logging.info(u"由于意外，终止检查网元信息")
            traceback.print_exc()
            return PYPARSING_CURRENT_SOFT_PARTITION_ERR   
        
        self.logging.info(u"**获取当前运行版本分区信息为:%s"%(self.currentSoftPartition))
        
        #退出管理平台telnet            
        self.telnetManagePlatform.logout()
        self.logging.info(u"**断开管理平台telnet连接") 

        #接入平台登入操作
        self.logging.info(u"**telnet接入平台")
        result = self.telnetAccessPlatform.login(self.accessUserName,self.accessPassword)
        if result != TELNET_OK:
            controlDebug("can't login ac access platform: %s\n"%(self.neIp))
            self.logging.error(u"**telnet接入平台失败: 错误码为:%d"%(result))
            self.logging.info(u"由于意外，终止检查网元信息")
            return TELNET_ACCESS_PLATFORM_ERR

        self.telnetAccessPlatform.setCommand(self.telnet_access_commandPromtDict)

        
        #下发命令查看热备状态
        #主要是获取网元主备情况，这里还没有完成
        self.logging.info(u"**获取热备状态信息")
        result=self.telnetAccessPlatform.runCommand(self.telnet_access_comandDict[SHOW_HOTSTANDBY_GROUP_INFO_ALL])
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_access_comandDict[SHOW_HOTSTANDBY_GROUP_INFO_ALL]))
            self.telnetAccessPlatform.logout()
            self.logging.info(u"**获取热备状态信息失败，错误码为:%d"%(result))
            self.logging.info(u"**断开接入平台telnet连接") 
            self.logging.info(u"由于意外，终止检查网元信息")
            return GET_HOTSTANDBY_STATUS_ERR 
        
        #
        # 需要在此处添加网元主备状态的解析        
        #       
        
        #退出接入平台telnet 
        self.logging.info(u"**断开接入平台telnet连接") 
        self.telnetAccessPlatform.logout()        
        self.neState=u"网元检查正常"
        self.logging.info(u"完成检查网元信息") 
        return NE_OK
        
        
    def updateSoft(self,fileName,softPartition=None):
        '''
                     管理平台升级软件操作  
        '''
        self.logging.info(u"开始升级软件操作，软件版本:%s,目标分区为:%s"%(fileName,softPartition)) 
        
        if SOFT_PARTITION.has_key(softPartition):
            pass
        else:
            self.logging.error(u"**目标分区参数错误")
            self.logging.info(u"由于意外，终止升级软件操作")
            return SOFT_PARTITION_PARA_ERR
                    
        
        self.logging.info(u"**telnet管理平台")
        result = self.telnetManagePlatform.login(self.manageUserName, self.managePassword) 
        if result != TELNET_OK:
            controlDebug("can't login ac manage platform: %s\n"%(self.neIp))
            self.logging.error(u"**telnet管理平台失败: 错误码为:%d"%(result))
            self.logging.info(u"由于意外，终止升级软件操作")
            return TELNET_MANAGE_PLATFORM_ERR        
        
        self.telnetManagePlatform.setCommand(self.telnet_manage_commandPromt_dict)
        
        #通过ls命令,查询\root目录下是否存在文件名与函数传进来的fileName一致
        self.logging.info(u"**检查升级目录下是否存在升级文件:%s"%(fileName))
        result=self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[LS], self.softPath)
        self.logging.info(u"**获取升级目录下文件信息")
        self.logging.info(self.telnetManagePlatform.commandResult)
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_command_dict[LS]))
            self.logging.error(u"**获取升级目录文件失败，错误码为%d"%(result))
            self.telnetManagePlatform.logout()
            self.logging.info(u"**断开管理平台telnet连接") 
            self.logging.info(u"由于意外，终止升级软件操作")
            return RUN_LS_COMMAND_ERR
        
        
        try:
            #由于无法使用变量到CaselessLiteral，如下代码没余用到setResultsName,采用直接取值的方式
            fileNamePyparsingstr=CaselessLiteral(fileName)
            result=fileNamePyparsingstr.searchString(self.telnetManagePlatform.commandResult,True)
            if result[0][0]!=fileName:
                self.logging.error(u"**当前升级目录下不存在升级文件%s"%(fileName))
                self.telnetManagePlatform.logout()
                self.logging.info(u"**断开管理平台telnet连接") 
                self.logging.info(u"由于意外，终止升级软件操作")
                return GET_UPDATE_FILE_ERR
            self.updateFile = fileName
        except:
            self.logging.error(u"**解析升级目录下的文件信息失败")
            self.telnetManagePlatform.logout()
            self.logging.info(u"**断开管理平台telnet连接") 
            self.logging.info(u"由于意外，终止升级软件操作")
            traceback.print_exc()
            return PYPARSING_UPDATE_FILE_ERR  
        
         
        #下发upgrade命令
        self.logging.info(u"**下发upgrade命令：%s"%(self.telnet_manage_command_dict[UPGRADE]+SOFT_PARTITION[softPartition])) 
        result=self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[UPGRADE], SOFT_PARTITION[softPartition])
        self.logging.info(self.telnetManagePlatform.commandResult)
        
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_command_dict[UPGRADE]))
            self.logging.error(u"**upgrade命令执行失败,错误码为:%d"%(result))
            self.telnetManagePlatform.logout()
            self.logging.info(u"**断开管理平台telnet连接")
            self.logging.info(u"由于意外，终止升级软件操作")
            return RUN_UPGRADE_COMMAND_ERR
        
        #下发yes确认
        self.logging.info(u"**下发确认:%s"%(self.telnet_manage_command_dict[UPGRADE_YES]))
        result=self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[UPGRADE_YES])
        self.logging.info(self.telnetManagePlatform.commandResult)
        
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_command_dict[UPGRADE_YES]))
            self.logging.error(u"**yes确认命令执行失败,错误码为:%d"%(result))
            self.telnetManagePlatform.logout()
            self.logging.info(u"**断开管理平台telnet连接")
            self.logging.info(u"由于意外，终止升级软件操作")
            return RUN_UPGRADE_CONFIRM_COMMAND_ERR
        
        
        controlDebug(self.telnetManagePlatform.commandResult)
        
        self.logging.info(u"**断开管理平台telnet连接")
        self.telnetManagePlatform.logout()
        self.logging.info(u"完成升级软件操作")
        self.neState=u"上传软件完毕"
        return NE_OK
    
    
        
    def activeSoft(self,softPartition=None):
        '''管理平台激活软件操作'''
        
        self.logging.info(u"开始激活软件操作")
        if SOFT_PARTITION.has_key(softPartition):
            pass
        else:
            self.logging.error(u"**目标分区参数错误")
            self.logging.info(u"由于意外，终止升级软件操作")
            return SOFT_PARTITION_PARA_ERR
        
        self.logging.info(u"**telnet管理平台")
        result = self.telnetManagePlatform.login(self.manageUserName, self.managePassword) 
        if result != TELNET_OK:
            controlDebug("can't login ac manage platform: %s\n"%(self.neIp))
            self.logging.error(u"**telnet管理平台失败: 错误码为:%d"%(result))
            self.logging.info(u"由于意外，终止激活软件操作")            
            return TELNET_MANAGE_PLATFORM_ERR        
        
        self.telnetManagePlatform.setCommand(self.telnet_manage_commandPromt_dict)   
        
        #下发active命令
        self.logging.info(u"**下发软件激活命令:%s"%(self.telnet_manage_command_dict[ACTIVE]+SOFT_PARTITION[softPartition]))
        result = self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[ACTIVE], SOFT_PARTITION[softPartition])
        self.logging.info(self.telnetManagePlatform.commandResult)
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_command_dict[ACTIVE]))
            self.telnetManagePlatform.logout()
            self.logging.error(u"**软件激活命令执行失败，错误码为:%d"%(result))
            self.logging.info(u"**断开管理平台telnet连接")
            self.logging.info(u"由于意外，终止升级软件操作")
            return RUN_ACTIVE_COMMAND_ERR
        
        self.telnetManagePlatform.logout()
        self.logging.info(u"**断开管理平台telnet连接")
        self.logging.info(u"完成激活软件操作")
        return NE_OK


    def reboot(self):
        '''管理平台复位操作'''
        
        self.logging.info(u"开始管理平台复位操作")
        
        self.logging.info(u"**telnet管理平台")
        result = self.telnetManagePlatform.login(self.manageUserName, self.managePassword) 
        if result != TELNET_OK:
            controlDebug("can't login ac manage platform: %s\n"%(self.neIp))
            self.logging.error(u"**telnet管理平台失败: 错误码为:%d"%(result))
            self.logging.info(u"由于意外，终止激活软件操作")            
            return TELNET_MANAGE_PLATFORM_ERR        
        
        self.telnetManagePlatform.setCommand(self.telnet_manage_commandPromt_dict)   
        
        #下发复位命令
        self.logging.info(u"**下发复位命令:%s"%(self.telnet_manage_command_dict[REBOOT]))
        result = self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[REBOOT])    
        self.logging.info(self.telnetManagePlatform.commandResult)
            
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_command_dict[REBOOT]))
            self.telnetManagePlatform.logout()
            self.logging.error(u"**复位命令执行失败，错误码为:%d"%(result))
            self.logging.info(u"**断开管理平台telnet连接")
            self.logging.info(u"由于意外，终止升级软件操作")

            return RUN_REBOOT_COMMAND_ERR 
    
        #下发yes确认
        self.logging.info(u"**下发复位确认命令:%s"%(self.telnet_manage_command_dict[REBOOT_YES]))
        result=self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[REBOOT_YES])
        self.logging.info(self.telnetManagePlatform.commandResult)
        
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_command_dict[REBOOT_YES]))
            self.telnetManagePlatform.logout()
            self.logging.error(u"**复位确认命令执行失败，错误码为:%d"%(result))
            self.logging.info(u"**断开管理平台telnet连接")
            self.logging.info(u"由于意外，终止升级软件操作")
            return RUN_REBOOT_CONFIRM_COMMAND_ERR
        
        controlDebug(self.telnetManagePlatform.commandResult)
        self.logging.info(u"**断开管理平台telnet连接")
        self.logging.info(u"完成管理平台复位操作")
        return NE_OK
    
    
    def checkFileIsExist(self, fileName, path):
        '''
                     检查文件是否存在
        '''
        result = self.telnetManagePlatform.login(self.manageUserName, self.managePassword) 
        if result != TELNET_OK:
            controlDebug("can't login ac manage platform: %s\n"%(self.neIp))
            return TELNET_MANAGE_PLATFORM_ERR  
        
        result=self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[LS], path)
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_command_dict[LS]))
            self.telnetManagePlatform.logout()
            return RUN_LS_COMMAND_ERR
        try:
            #由于无法使用变量到CaselessLiteral，如下代码没余用到setResultsName,采用直接取值的方式
            
            fileNamePyparsingstr=CaselessLiteral(fileName)
            result=fileNamePyparsingstr.searchString(self.telnetManagePlatform.commandResult,True)
            if len(result)==0:
                return FILE_IS_NOT_EXIST
        except:
            self.telnetManagePlatform.logout()
            traceback.print_exc()
            return PYPARSING_FILE_ERR  
        
        self.telnetManagePlatform.logout()
        return FILE_IS_EXIST
    
        
    def pingTest(self):
        '''
        ping 网元,此处代码为网上抄袭而来
        '''
        if platform.system() == "Linux":
            cmd ="ping -c 4 %s"%self.neIp
        elif platform.system() == "Windows":     
            cmd ="ping -n 4 %s"%self.neIp
              
        outFile=self.neIp+"_ping.temp"
        ret =subprocess.call(cmd,shell=True,stdout=open(outFile,'w'),stderr=subprocess.STDOUT)

        controlDebug( "ping %s ret: %d"%(self.neIp,ret))
        if ret == 0 :
            return  NE_OK   
        else:
            return  NE_DOWN      
        

    def telnetManagePlatformTest(self):
        result = self.telnetManagePlatform.login(self.manageUserName, self.managePassword) 
        if result != TELNET_OK:
            controlDebug("can't login ac manage platform: %s\n"%(self.neIp))
            return TELNET_MANAGE_PLATFORM_ERR  
        
        self.telnetManagePlatform.logout()
        return NE_OK
        
    def telnetAccessPlatformTest(self):
        result = self.telnetAccessPlatform.login(self.accessUserName,self.accessPassword)
        if result != TELNET_OK:
            controlDebug("can't login ac access platform: %s\n"%(self.neIp))
            return TELNET_ACCESS_PLATFORM_ERR
        
        self.telnetAccessPlatform.logout()
        return NE_OK

    def afterRebootTest(self):
        '''复位后的连通性检查'''
        loop =1
        result=NE_DOWN
        
        self.logging.info(u"开始网元复位后连接测试")
        
#         #ping测试, 测试10次, 间隔10秒, 只要有1次成功,退出测试
#         self.logging.info(u"**ping测试")
#         while loop!=11:
#             result=self.pingTest()
#             if result == NE_OK:
#                 self.logging.info(u"**第%d次测试，测试成功"%(loop))
#                 loop=11
#             else:
#                 self.logging.warning(u"**第%d次测试，测试失败"%(loop))
#                 loop=loop+1
#                     
#             time.sleep(12)
#         
#         #如果ping不同，则认为网元失连，返回NE_DOWN    
#         if result != NE_OK:
#             self.logging.warning(u"连续100秒无法ping通网元，网元状态不正常")
#             return NE_DOWN
        
        #管理平台 接入平台测试，测试3次，间隔10秒，只要有1次成功,退出测试

        self.logging.info(u"**telnet管理平台测试")
        loop=1    
        result1 = NE_OK
        result2 = NE_OK        
        while loop!=10:
            result1=self.telnetManagePlatformTest()
            result2=self.telnetManagePlatformTest()
            
            if result1 == NE_OK:
                self.logging.info(u"**管理平台第%d次测试，测试成功"%(loop))
            else:
                self.logging.warning(u"**管理平台第%d次测试，测试失败"%(loop))

            if result2 == NE_OK:
                self.logging.info(u"**接入平台第%d次测试，测试成功"%(loop))
            else:
                self.logging.warning(u"**接入平台第%d次测试，测试失败"%(loop))
                
            if result1==NE_OK and result2==NE_OK:    
                loop = 4 
            else:   
                loop += 1
            
            time.sleep(10)
         
        if result1!= NE_OK or result2 !=NE_OK :
            self.logging.warning(u"telnet网元不正常，网元状态不正常")
            return  NE_DOWN
                    
        return NE_OK

    def afterRebootCheck(self,versionName):
        '''复位后软件版本和配置文件校验'''
        
        self.logging.info(u"开始网元复位后版本和配置校验")
        _softwareVersion = self.softwareVersion
        _hardwareVersion = self.hardwareVersion
        _currentSoftPartition = self.currentSoftPartition
        _willUpdateSoftPartition = self.willUpdateSoftPartition
        _saveConfigPath = self.saveConfigPath
        
        result =self.checkNe()
        if result != NE_OK:
            return result 
        
        result = self.saveNeConfigToLocal()
        if result != NE_OK:
            return result 
        
        #判断升级的版本是否是预期的版本
        if versionName != self.softwareVersion:
            self.logging.warning(u"升级后的版本%s与预期%s不符"%(self.softwareVersion,versionName))
            return UPDATE_VERSION_ERR
        else:
            self.logging.info(u"升级后的版本%s与预期%s一致"%(self.softwareVersion,versionName))
        
        #判断升级的路径是否是预期的路径        
#         if _willUpdateSoftPartition != self.currentSoftPartition:
#             self.logging.warning(u"升级后的软件路径%s与预期不符%s"%(self.currentSoftPartition,_willUpdateSoftPartition))
#             return UPDATE_PARTITION_ERR 
                
        #比较升级前后保留配置文件数目和名称是否一致        
        dirCmpObject =filecmp.dircmp(_saveConfigPath,self.saveConfigPath)        
        if dirCmpObject.diff_files !=[]:
            self.logging.warning(u"升级前后保留的配置文件不一致")
            self.logging.warning(u"升级前后保留的配置文件路径:%s",_saveConfigPath)
            self.logging.warning(u"升级前后保留的配置文件路径:%s",self.saveConfigPath)
            self.logging.warning(u"不同文件为: %s",dirCmpObject.diff_files)
            return CONFIG_FILE_DIFF
        
        #比较升级前后保留的配置文件内容是否一致
        result = filecmp.cmpfiles(_saveConfigPath,self.saveConfigPath,dirCmpObject.common)
        if result[1]!=[] or result[2]!=[]:
            self.logging.warning(u"升级前后保留的配置文件内容不一致")
            self.logging.warning(u"升级前后保留的配置文件路径:%s",_saveConfigPath)
            self.logging.warning(u"升级前后保留的配置文件路径:%s",self.saveConfigPath)
            self.logging.warning(u"不同文件为: %s",result[1:3])
            return CONFIG_FILE_CONTEXT_DIFF    
        
        self.logging.info(u"完成网元复位后版本和配置校验")   
        return NE_OK
      
    def afterRebootConfigCheck(self):
        #升级后配置检测
        
        _saveConfigPath = self.saveConfigPath
                        
        result = self.saveNeConfigToLocal()
        if result != NE_OK:
            return result 
                
        #比较升级前后保留配置文件数目和名称是否一致        
        dirCmpObject =filecmp.dircmp(_saveConfigPath,self.saveConfigPath)        
        if dirCmpObject.diff_files !=[]:
            self.logging.warning(u"升级前后保留的配置文件不一致")
            self.logging.warning(u"升级前后保留的配置文件路径:%s",_saveConfigPath)
            self.logging.warning(u"升级前后保留的配置文件路径:%s",self.saveConfigPath)
            self.logging.warning(u"不同文件为: %s",dirCmpObject.diff_files)
            return CONFIG_FILE_DIFF
        
        #比较升级前后保留的配置文件内容是否一致
        result = filecmp.cmpfiles(_saveConfigPath,self.saveConfigPath,dirCmpObject.common)
        if result[1]!=[] or result[2]!=[]:
            self.logging.warning(u"升级前后保留的配置文件内容不一致")
            self.logging.warning(u"升级前后保留的配置文件路径:%s",_saveConfigPath)
            self.logging.warning(u"升级前后保留的配置文件路径:%s",self.saveConfigPath)
            self.logging.warning(u"不同文件为: %s",result[1:3])
            return CONFIG_FILE_CONTEXT_DIFF
          
        self.logging.info(u"完成网元复位后配置校验")   
        return NE_OK        
    
                        
    def __enterSuperMode(self):
        result=self.telnetAccessPlatform.runCommand(self.telnet_access_comandDict[ENABLE_MODE])
        self.logging.info(self.telnetAccessPlatform.commandResult)
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_access_comandDict[ENABLE_MODE]))
            return SUPER_MODE_ERR
        
        result=self.telnetAccessPlatform.runCommand(self.telnet_access_comandDict[ENABLE_PASSWORD])
        self.logging.info(self.telnetAccessPlatform.commandResult)
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_access_comandDict[ENABLE_PASSWORD]))
            return SUPER_MODE_ERR
    
        return NE_OK
    
    
    def saveNeConfig(self):
        '''
                     保留当前运行配置
        '''
        self.logging.info(u"开始接入平台配置保存操作")
        
        #接入平台登入操作
        self.logging.info(u"**telnet接入平台")
        result = self.telnetAccessPlatform.login(self.accessUserName,self.accessPassword)
        if result != TELNET_OK:
            controlDebug("can't login ac access platform: %s\n"%(self.neIp))
            self.logging.error(u"**telnet接入平台失败: 错误码为:%d"%(result))
            self.logging.info(u"由于意外，终止接入平台配置保存操作")            
            return TELNET_ACCESS_PLATFORM_ERR

        self.telnetAccessPlatform.setCommand(self.telnet_access_commandPromtDict)
        
        #进入super模式
        self.logging.info(u"**进入接入平台super模式") 
        result = self.__enterSuperMode()
        
        if result != NE_OK :
            controlDebug("enter super mode err\n")
            self.telnetAccessPlatform.logout()
            self.logging.error(u"**进入接入平台super模式错误，错误码为:%d"%(result))
            self.logging.info(u"**断开接入平台telnet连接") 
            self.logging.info(u"由于意外，终止接入平台配置保存操作")
            return result   
        
        #下发配置保留命令
        self.logging.info(u"**下发配置保留命令")
        result=self.telnetAccessPlatform.runCommand(self.telnet_access_comandDict[COPY_CONFIG])
        self.logging.info(self.telnetAccessPlatform.commandResult)
        
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_access_comandDict[COPY_CONFIG]))
            self.telnetAccessPlatform.logout()
            self.logging.info(u"**断开接入平台telnet连接")
            self.logging.info(u"由于意外，终止接入平台配置保存操作")
            return GET_HOTSTANDBY_STATUS_ERR
        
        
        #退出接入平台telnet 
        self.telnetAccessPlatform.logout()   
        self.logging.info(u"**断开接入平台telnet连接")     
        self.logging.info(u"完成接入平台配置保存操作")
        self.neState="保留网元配置成功"
        return NE_OK
    
                
    def saveNeConfigToLocal(self):
        '''
                    保留网元配置文件到本地
        '''
        format = "%Y-%m-%d-%H-%M-%S" 
        dataStr=str(datetime.datetime.today().strftime(format))
        self.saveConfigPath =self.logPath + self.directorySeparator + "config_" + dataStr +self.directorySeparator
        
        if os.path.exists(self.saveConfigPath) == False:
            os.mkdir(self.saveConfigPath)

        self.logging.info(u"开始保留网元配置文件操作")
        self.logging.info(u"**ftp连接管理平台")
        result = self.ftpManagePlatform.login(self.manageUserName, self.managePassword)
        if result != FTP_OK:
            self.logging.error(u"**ftp连接管理平台失败，错误码为:%d"%(result))
            self.logging.info(u"由于意外，终止保留网元配置文件")            
            return FTP_LOGIN_MANAGE_PLATFORM_ERR
        
        #下载网元上的配置文件，以备不时之需
        self.noSavedConfigFile = []
        self.savedConfigFile   = []
        for fileName in self.ne_config_file_dict.keys():
            if self.checkFileIsExist(fileName, self.ne_config_file_dict[fileName])== FILE_IS_EXIST:
                result = self.ftpManagePlatform.getFile(self.ne_config_file_dict[fileName]+fileName , fileName , self.saveConfigPath)
                if result != FTP_OK:
                    self.logging.error(u"**保留配置文件:%s,失败"%(self.ne_config_file_dict[fileName]+fileName))
                    self.noSavedConfigFile.append(fileName)
                else:
                    self.logging.info(u"**保留配置文件:%s,成功"%(self.ne_config_file_dict[fileName]+fileName))
                    self.savedConfigFile.append(fileName)
            else:
                self.logging.warn(u"**没有配置文件:%s"%(self.ne_config_file_dict[fileName]+fileName))
                controlDebug(fileName + "is not exist")
                 
        self.logging.info(u"**ftp登出管理平台")         
        result = self.ftpManagePlatform.logout()
        if result != FTP_OK:
            self.logging.error(u"**ftp登出管理平台失败，错误码为:%d"%(result))
            self.logging.info(u"由于意外，终止保留网元配置文件")
            return FTP_LOGOUT_MANAGE_PLATFORM_ERR 
                        
        if self.noSavedConfigFile != []:
            self.logging.err(u"**没有配置文件被保存，请检查")
            self.logging.info(u"由于意外，终止保留网元配置文件")
            return SOME_CONFIG_FILE_NOT_SAVED       
        
        self.logging.info(u"完成保留网元配置文件操作")                  
        return NE_OK

    
    def updateVersionFile(self,versionFile,localPath):
        '''
        FTP上传版本文件
        '''
        
        self.logging.info(u"开始上传升级文件操作")
        
        self.logging.info(u"**ftp连接管理平台")
        result = self.ftpManagePlatform.login(self.manageUserName, self.managePassword)
        
        if result != FTP_OK:
            self.logging.error(u"**ftp连接管理平台失败，错误码为:%d"%(result))
            self.logging.info(u"由于意外，终止上传升级文件操作")
            return FTP_LOGIN_MANAGE_PLATFORM_ERR
                
        self.logging.info(u"**ftp上传文件 从本地目录:%s,上传文件:%s,至目标目录%s"%(localPath,versionFile,self.softPath))        
        result = self.ftpManagePlatform.putFile(versionFile, localPath, self.softPath)
        if result != FTP_OK:
            self.ftpManagePlatform.logout()
            self.logging.error(u"**ftp上传文件失败，错误码为:%d"%(result))
            self.logging.info(u"由于意外，终止上传升级文件操作")
            return FTP_PUT_SOFT_MANAGE_PLATFORM_ERR
        
        self.logging.info(u"**ftp登出管理平台")
        result = self.ftpManagePlatform.logout()
        if result != FTP_OK:
            self.logging.error(u"**ftp登出管理平台失败，错误码为:%d"%(result))
            self.logging.info(u"由于意外，终止上传升级文件操作")
            return FTP_LOGOUT_MANAGE_PLATFORM_ERR 

        self.logging.info(u"完成上传升级文件操作")                        
        return NE_OK
        
        
class updateConfig:
    '''
                 升级软件网元配置，
                记录默认使用的语言
    '''
    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        self.configFile  = ""
        self.language    = ""
        self.versionfile = ""
        self.neLists     = {}
           

    def getNeLists(self):
        return self.neLists
    
    def setConfigFile(self,configFile):
        self.configFile=configFile
        
    def getLanguage(self):
        '''设置界面语言'''
        controlDebug(self.language)
        return self.language
    
    def setLanguage(self, language):
        '''设置界面语言'''
        self.language = language
 
    def getVersionFile(self):
        '''设置界面语言'''
        controlDebug(self.versionfile)
        return self.versionfile
    
    def setVersionFile(self, versionfile):
        '''设置界面语言'''
        self.versionfile = versionfile

    def clearNe(self):
        self.neLists.clear()
                               
    def addNe(self,ne): 
        self.neLists[ne.neName] =ne   
    
    def delNe(self,ne):
        try:
            self.neLists.pop(ne.neName)
        except:
            traceback.print_exc()
            return DEL_NE_ERR
        return DEL_NE_OK
        
    def readConfig(self,configFile,path="."):
        '''读取服务器配置文件'''
        self.configFile=configFile
        neLists={}
        try:
            self.config.read(configFile)
            for section in self.config.sections():
                if str(section) == 'NE Section':
                    self.versionfile=self.config.get(section,"versionfile")
                else:    
                    neName=self.config.get(section,"neName")                 
                    neIp=self.config.get(section,"neIp")
                    accessUserName=self.config.get(section,"accessUserName")
                    accessPassword=self.config.get(section,"accessPassword")
                    manageUserName=self.config.get(section,"manageUserName")                                        
                    managePassword=self.config.get(section,"managePassword")
                    neLists[neName] = NE(neName,neIp,accessUserName,accessPassword,manageUserName,managePassword,path)
        except:
            traceback.print_exc()
            return READ_CONFIG_ERR
        
        if self.neLists != None:
            self.neLists.clear()
            for ne in self.neLists.items():
                del(ne)
                
        self.neLists=neLists
        return READ_CONFIG_OK
       
    def saveConfig(self,configFile=None):
        '''保存服务器配置文件'''
        self.config.add_section('NE Section')
        self.config.set('NE Section', 'versionfile', self.versionfile)
        
        for neKey in self.neLists.keys():
            NE='NE'+neKey
            try:
                self.config.add_section(NE)    
                self.config.set(NE,"neName",self.neLists[neKey].neName)
                self.config.set(NE,"neIp",self.neLists[neKey].neIp)
                self.config.set(NE,"accessUserName",self.neLists[neKey].accessUserName)
                self.config.set(NE,"accessPassword",self.neLists[neKey].accessPassword)
                self.config.set(NE,"manageUserName",self.neLists[neKey].manageUserName)    
                self.config.set(NE,"managePassword",self.neLists[neKey].managePassword)
            except:
                '''有重复会不添加到配置中，走这个异常流程'''
                traceback.print_exc()
        try:  
            if configFile==None:
                configFile=self.configFile
            with open(configFile, 'wb') as _configFile:
                self.config.write(_configFile)
            self.configFile= configFile
        except:
            traceback.print_exc()
            return  OPEN_CONFIG_FILE_ERR         
         
        return SAVE_CONFIG_OK 


             
if __name__ == '__main__':
    
    testWriteNeConfig = updateConfig()
    testWriteNeConfig.setConfigFile("test.conf")
    ne=NE("AC1", "1.1.1.1", "bnas", "bnas", "root", "fitap")
    testWriteNeConfig.addNe(ne)
#     testWriteNeConfig.addNe("AC2", "1.1.1.1", "bnas", "bnas", "root", "fitap")
#     testWriteNeConfig.addNe("AC3", "1.1.1.1", "bnas", "bnas", "root", "fitap")
    testWriteNeConfig.saveConfig()
# 
#     
#     testReadNeConfig = updateConfig()
#     testWriteNeConfig.readConfig("test.conf")
#     for item in testWriteNeConfig.neLists.keys():
#  
#         print(testWriteNeConfig.neLists[item].neName+","+
#               testWriteNeConfig.neLists[item].neIp+","+
#               testWriteNeConfig.neLists[item].accessUserName+","+
#               testWriteNeConfig.neLists[item].accessPassword+","+
#               testWriteNeConfig.neLists[item].manageUserName+","+
#               testWriteNeConfig.neLists[item].managePassword)

#     testNE =NE(neName = "AC",
#                neIp   = "10.1.1.2",
#                accessUserName = "bnas",
#                accessPassword = "bnas",
#                manageUserName = "root",
#                managePassword = "fitap^_^",
#                logpath="log")

#     testNE1 =NE(neName = "AC",
#                neIp   = "10.1.1.2",
#                accessUserName = "bnas",
#                accessPassword = "bnas",
#                manageUserName = "root",
#                managePassword = "fitap^_^",)
#     
#     testNE2 =NE(neName = "AC",
#                neIp   = "10.1.1.2",
#                accessUserName = "bnas",
#                accessPassword = "bnas",
#                manageUserName = "root",
#                managePassword = "fitap^_^",)
#         
#     print testNE
#     print testNE1
#     print testNE2
#     testNE.checkNe()
#     print testNE.hardwareVersion
#     print testNE.masterSlaveState
#     print testNE.softwareVersion
#     print testNE.currentSoftPartition
     
     
#     testNE.updateSoft("MIPS_1018R31T2.2_P7_ZTE","version0")
#     testNE.activeSoft("version0")
#     testNE.reboot()
#     print testNE.pingTest()

#     testNE.saveNeConfig()
#     for key in testNE.ne_config_file_dict:
#         result=testNE.checkFileIsExist(key, testNE.ne_config_file_dict[key])
#         if FILE_IS_EXIST == result:
#             print key + " is exist"
#         else:
#             print key + " is not exist"   
#         
#     testNE.saveNeConfigToLocal()        
#     

#     testNE.afterRebootTest()