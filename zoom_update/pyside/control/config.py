# -*- coding: UTF-8 -*-
'''
Created on 2010-9-19

@author: x00163361
'''
import subprocess
import platform
from pyparsing import *
from debug import controlDebug ,classDecorator
import ConfigParser
from telnet import telnetAC ,TELNET_OK
from fileCheck import fileCheck,RMIOS_STR,VXWORKS_STR,LINUX_STR,VERSION_STR,BOOTLOADER_STR
from ftp import ftpAC ,FTP_OK

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
    
class NE:
    
    #接入平台telnet配置
    telnet_accesss_port = 23
    telnet_accesss_user_except_string = "Login:"
    telnet_accesss_password_except_string = "Password:"
    telnet_accesss_welcome_string=""
    telnet_accesss_prompt="BNOS>"
    
    #接入平台命令列表
    telnet_access_comandDict={SHOW_HOTSTANDBY_GROUP_INFO_ALL:"show hotstandby group-info all",
                              SHOW_HOTSTANDBY_GROUP_INFO:"show hotstandby group-info",
                              ENABLE_MODE:"enable",
                              ENABLE_PASSWORD:"super",
                              }

    telnet_access_commandPromtDict={telnet_access_comandDict[SHOW_HOTSTANDBY_GROUP_INFO_ALL]:"BNOS",
                                    telnet_access_comandDict[SHOW_HOTSTANDBY_GROUP_INFO]:"BNOS",
                                    telnet_access_comandDict[ENABLE_MODE]:"Password:",
                                    telnet_access_comandDict[ENABLE_PASSWORD]:"BNOS",                                                                        
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
                          "health-monitor-config" : "/etc/",
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
        
        
    def checkNe(self):
        '''检查网元，获取网元信息，软件版本，硬件版本，主备状态'''
         
        #管理平台登录操作
        result = self.telnetManagePlatform.login(self.manageUserName, self.managePassword) 
        if result != TELNET_OK:
            controlDebug("can't login ac manage platform: %s\n"%(self.neIp))
            return TELNET_MANAGE_PLATFORM_ERR
         
        self.telnetManagePlatform.setCommand(self.telnet_manage_commandPromt_dict)
        
        #下发版本查看命令 
        result=self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[GET_VERSION])
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_commandPromt_dict[GET_VERSION]))
            self.telnetManagePlatform.logout()
            return GET_SOFT_VERSION_ERR
         
        #获取软件版本
        try:
            
            tempstr= fileCheck.pyparsingstr[RMIOS_STR] +\
                     fileCheck.pyparsingstr[VXWORKS_STR] +\
                     fileCheck.pyparsingstr[LINUX_STR] +\
                     fileCheck.pyparsingstr[VERSION_STR]
            result=tempstr.searchString(self.telnetManagePlatform.commandResult,True)         
            self.softwareVersion=result[0][VERSION_STR]
        except:
            controlDebug("parsing software version err\n")
            self.telnetManagePlatform.logout()
            return PYPARSING_SOFTWARE_VERSION_ERR   
 
        #获取硬件版本
        try:
#             controlDebug(self.telnetManagePlatform.commandResult)
            result=self.hardwareCodePyparsingStr.searchString(self.telnetManagePlatform.commandResult,True)
 
            #硬件型号取硬件code的第2和第3字节
            self.hardwareVersion=hardwareDict[int(result[0][HARDWARE_CODE][2:4])]
        except:
            controlDebug("parsing hardware version err\n")
            self.telnetManagePlatform.logout()
            return PYPARSING_HARDWARE_VERSION_ERR   
            
        #获取当前运行软件分区
        try:
            result=self.currentVersionPyparsingStr.searchString(self.telnetManagePlatform.commandResult,True)
            self.currentSoftPartition    = result[0][CURRENT_SOFT_PARTITION]
            self.willUpdateSoftPartition = GET_WILL_UPDATE_SOFT_PARTITION[self.currentSoftPartition]
        except:
            controlDebug("parsing current soft partion  err\n")
            self.telnetManagePlatform.logout()
            return PYPARSING_CURRENT_SOFT_PARTITION_ERR   
        
        #退出管理平台telnet            
        self.telnetManagePlatform.logout()


        #接入平台登入操作
        #主要是获取网元主备情况，这里还没有完成
        result = self.telnetAccessPlatform.login(self.accessUserName,self.accessPassword)
        if result != TELNET_OK:
            controlDebug("can't login ac access platform: %s\n"%(self.neIp))
            return TELNET_ACCESS_PLATFORM_ERR

        self.telnetAccessPlatform.setCommand(self.telnet_access_commandPromtDict)

        #下发命令查看热备状态
        result=self.telnetAccessPlatform.runCommand(self.telnet_access_comandDict[SHOW_HOTSTANDBY_GROUP_INFO_ALL])
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_access_comandDict[SHOW_HOTSTANDBY_GROUP_INFO_ALL]))
            self.telnetAccessPlatform.logout()
            return GET_HOTSTANDBY_STATUS_ERR 
        
        #
        # 需要在此处添加网元主备状态的解析        
        #       
        
        #退出接入平台telnet 
        self.telnetAccessPlatform.logout()        
        self.neState=CONNECT_OK
        return NE_OK
        
        
    def updateSoft(self,fileName,softPartition=None):
        #管理平台升级软件操作
        result = self.telnetManagePlatform.login(self.manageUserName, self.managePassword) 
        if result != TELNET_OK:
            controlDebug("can't login ac manage platform: %s\n"%(self.neIp))
            return TELNET_MANAGE_PLATFORM_ERR        
        
        self.telnetManagePlatform.setCommand(self.telnet_manage_commandPromt_dict)
        
        #通过ls命令,查询\root目录下是否存在文件名与函数传进来的fileName一致
        result=self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[LS], self.softPath)
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_command_dict[LS]))
            self.telnetManagePlatform.logout()
            return RUN_LS_COMMAND_ERR
        try:
            #由于无法使用变量到CaselessLiteral，如下代码没余用到setResultsName,采用直接取值的方式
#             print fileName
#             print self.telnetManagePlatform.commandResult
            fileNamePyparsingstr=CaselessLiteral(fileName)
            result=fileNamePyparsingstr.searchString(self.telnetManagePlatform.commandResult,True)
            if result[0][0]!=fileName:
                return GET_UPDATE_FILE_ERR
            self.updateFile = fileName
        except:
            controlDebug("1 parsing root softfile err\n")
            self.telnetManagePlatform.logout()
            return PYPARSING_UPDATE_FILE_ERR  
        
         
        #下发upgrade命令
        if SOFT_PARTITION.has_key(softPartition):
            result=self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[UPGRADE], SOFT_PARTITION[softPartition])
        else:
            self.telnetManagePlatform.logout()
            return SOFT_PARTITION_PARA_ERR
            
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_command_dict[UPGRADE]))
            self.telnetManagePlatform.logout()
            return RUN_UPGRADE_COMMAND_ERR
        
        #下发yes确认
        result=self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[UPGRADE_YES])
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_command_dict[UPGRADE_YES]))
            self.telnetManagePlatform.logout()
            return RUN_UPGRADE_CONFIRM_COMMAND_ERR
        
        controlDebug(self.telnetManagePlatform.commandResult)
        self.telnetManagePlatform.logout() 
        self.neState=CONNECT_OK
        return NE_OK
    
        
    def activeSoft(self,softPartition=None):
        #管理平台激活软件操作
        result = self.telnetManagePlatform.login(self.manageUserName, self.managePassword) 
        if result != TELNET_OK:
            controlDebug("can't login ac manage platform: %s\n"%(self.neIp))
            return TELNET_MANAGE_PLATFORM_ERR        
        
        self.telnetManagePlatform.setCommand(self.telnet_manage_commandPromt_dict)   
        
        #下发active命令
        if SOFT_PARTITION.has_key(softPartition):
            result = self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[ACTIVE], SOFT_PARTITION[softPartition])
        else:
            self.telnetManagePlatform.logout()    
            return SOFT_PARTITION_PARA_ERR
#             result = self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[ACTIVE], SOFT_PARTITION[self.currentSoftPartition]+"\r")

        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_command_dict[ACTIVE]))
            self.telnetManagePlatform.logout()
            return RUN_ACTIVE_COMMAND_ERR
        
        self.telnetManagePlatform.logout()
        return NE_OK

    def reboot(self):
        #管理平台复位操作
        result = self.telnetManagePlatform.login(self.manageUserName, self.managePassword) 
        if result != TELNET_OK:
            controlDebug("can't login ac manage platform: %s\n"%(self.neIp))
            return TELNET_MANAGE_PLATFORM_ERR        
        
        self.telnetManagePlatform.setCommand(self.telnet_manage_commandPromt_dict)   
        
        #下发复位命令
        result = self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[REBOOT])        
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_command_dict[REBOOT]))
            self.telnetManagePlatform.logout()
            return RUN_REBOOT_COMMAND_ERR 
    
        #下发yes确认
        result=self.telnetManagePlatform.runCommand(self.telnet_manage_command_dict[REBOOT_YES])
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_manage_command_dict[REBOOT_YES]))
            self.telnetManagePlatform.logout()
            return RUN_REBOOT_CONFIRM_COMMAND_ERR
        
        controlDebug(self.telnetManagePlatform.commandResult)
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
            controlDebug("parsing %s err\n"%(path+fileName))
            self.telnetManagePlatform.logout()
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
            return  NE_ALIVE   
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
             

    def __enterSuperMode(self):
        result=self.telnetAccessPlatform.runCommand(self.telnet_access_comandDict[ENABLE_MODE])
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_access_comandDict[ENABLE_MODE]))
            return GET_HOTSTANDBY_STATUS_ERR
        
        result=self.telnetAccessPlatform.runCommand(self.telnet_access_comandDict[ENABLE_PASSWORD])
        if result != TELNET_OK:
            controlDebug("run command %s err\n"%(self.telnet_access_comandDict[ENABLE_PASSWORD]))
            return GET_HOTSTANDBY_STATUS_ERR
    
        return NE_OK
    
    def saveNeConfig(self):
        '''
                     保留当前运行配置
        '''
        
        #接入平台登入操作
        result = self.telnetAccessPlatform.login(self.accessUserName,self.accessPassword)
        if result != TELNET_OK:
            controlDebug("can't login ac access platform: %s\n"%(self.neIp))
            return TELNET_ACCESS_PLATFORM_ERR

        self.telnetAccessPlatform.setCommand(self.telnet_access_commandPromtDict)

        
        #进入super模式 
        result = self.__enterSuperMode()

        
        #下发配置保留命令
        if result == NE_OK :
            result=self.telnetAccessPlatform.runCommand(self.telnet_access_comandDict[SHOW_HOTSTANDBY_GROUP_INFO_ALL])
            if result != TELNET_OK:
                controlDebug("run command %s err\n"%(self.telnet_access_comandDict[SHOW_HOTSTANDBY_GROUP_INFO_ALL]))
                self.telnetAccessPlatform.logout()
                return GET_HOTSTANDBY_STATUS_ERR
        else:
            controlDebug("enter super mode err\n")
        
        
        #退出接入平台telnet 
        self.telnetAccessPlatform.logout()        
        self.neState=NE_OK
        return NE_OK
    
                
    def saveNeConfigToLocal(self,savePath):
        '''
                    保留网元配置文件到本地
        '''
        result = self.ftpManagePlatform.login(self.manageUserName, self.managePassword)
        if result != FTP_OK:
            return FTP_LOGIN_MANAGE_PLATFORM_ERR
        
        #下载网元上的配置文件，以备不时之需
        self.noSavedConfigFile = []
        self.savedConfigFile   = []
        for fileName in self.ne_config_file_dict.keys():
            if self.checkFileIsExist(fileName, self.ne_config_file_dict[fileName])== FILE_IS_EXIST:
                result = self.ftpManagePlatform.getFile(self.ne_config_file_dict[fileName]+fileName , fileName , savePath)
                if result != FTP_OK:
                    self.noSavedConfigFile.append(fileName)
                else:
                    self.savedConfigFile.append(fileName)
            else:
                controlDebug(fileName + "is not exist")
                 
        result = self.ftpManagePlatform.logout()
        if result != FTP_OK:
            return FTP_LOGOUT_MANAGE_PLATFORM_ERR 
                        
        if self.noSavedConfigFile != []:
            return SOME_CONFIG_FILE_NOT_SAVED                         
        return NE_OK

    
    def updateVersionFile(self,versionFile,localPath):
        '''
        FTP上传版本文件
        '''
        result = self.ftpManagePlatform.login(self.manageUserName, self.managePassword)
        if result != FTP_OK:
            return FTP_LOGIN_MANAGE_PLATFORM_ERR
                
        result = self.ftpManagePlatform.putFile(versionFile, localPath, self.softPath)
        if result != FTP_OK:
            self.ftpManagePlatform.logout()
            return FTP_PUT_SOFT_MANAGE_PLATFORM_ERR
        
        result = self.ftpManagePlatform.logout()
        if result != FTP_OK:
            return FTP_LOGOUT_MANAGE_PLATFORM_ERR 
                        
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
                       
    def addNe(self,neName,neIp,accessUserName,accessPassword,manageUserName,managePassword): 
        self.neLists[neName] =NE(neName,neIp,accessUserName,accessPassword,manageUserName,managePassword)   
    
    def delNe(self,neName):
        try:
            self.neLists.pop(neName)
        except:
            controlDebug("del NE:%s err"%(neName))
            return DEL_NE_ERR
        return DEL_NE_OK
        
    def readConfig(self,configFile):
        '''读取服务器配置文件'''
        self.configFile=configFile
        neLists={}
        try:
            self.config.read(self.configFile)
            for section in self.config.sections():
#                 print section
                if str(section) == 'NE Section':
                    self.versionfile=self.config.get(section,"versionfile")
                else:    
                    neName=self.config.get(section,"neName")                 
                    neIp=self.config.get(section,"neIp")
                    accessUserName=self.config.get(section,"accessUserName")
                    accessPassword=self.config.get(section,"accessPassword")
                    manageUserName=self.config.get(section,"manageUserName")                                        
                    managePassword=self.config.get(section,"managePassword")
                    neLists[neName] = NE(neName,neIp,accessUserName,accessPassword,manageUserName,managePassword)
        except:
            controlDebug(u"读取配置问题有问题")
            return READ_CONFIG_ERR
        
        if self.neLists != None:
            self.neLists.clear()
            for ne in self.neLists.items():
                del(ne)
                
        self.neLists=neLists
        return READ_CONFIG_OK
       
    def saveConfig(self):
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
                controlDebug(u"添加配置有问题:"+NE+","+
                           self.neLists[neKey].neName+","+
                           self.neLists[neKey].neIp+","+
                           self.neLists[neKey].accessUserName+","+
                           self.neLists[neKey].accessPassword+","+
                           self.neLists[neKey].manageUserName+","+
                           self.neLists[neKey].managePassword)
           
        try:     
            with open(self.configFile, 'wb') as configfile:
                self.config.write(configfile)
        except:
            return  OPEN_CONFIG_FILE_ERR         
         
        return SAVE_CONFIG_OK 
         
if __name__ == '__main__':
    
#     testWriteNeConfig = updateConfig()
#     testWriteNeConfig.setConfigFile("test.conf")
#     testWriteNeConfig.addNe("AC1", "1.1.1.1", "bnas", "bnas", "root", "fitap")
#     testWriteNeConfig.addNe("AC2", "1.1.1.1", "bnas", "bnas", "root", "fitap")
#     testWriteNeConfig.addNe("AC3", "1.1.1.1", "bnas", "bnas", "root", "fitap")
#     testWriteNeConfig.saveConfig()
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

    testNE =NE(neName = "AC",
               neIp   = "10.1.1.2",
               accessUserName = "bnas",
               accessPassword = "bnas",
               manageUserName = "root",
               managePassword = "fitap^_^",)

    testNE1 =NE(neName = "AC",
               neIp   = "10.1.1.2",
               accessUserName = "bnas",
               accessPassword = "bnas",
               manageUserName = "root",
               managePassword = "fitap^_^",)
    
    testNE2 =NE(neName = "AC",
               neIp   = "10.1.1.2",
               accessUserName = "bnas",
               accessPassword = "bnas",
               manageUserName = "root",
               managePassword = "fitap^_^",)
        
    print testNE
    print testNE1
    print testNE2
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
#     testNE.saveNeConfigToLocal("E:\\test\\")        
#     