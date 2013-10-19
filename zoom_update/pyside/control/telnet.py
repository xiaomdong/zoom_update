# -*- coding: UTF-8 -*-
import telnetlib
import traceback 
import socket
from debug import *

#错误码
TELNET_CODE_BASE                = 100

TELNET_OK                       = TELNET_CODE_BASE + 0
TELNET_CONNECT_ERR              = TELNET_CODE_BASE + 1
TELNET_USER_PASSWORD_ERR        = TELNET_CODE_BASE + 2
TELNET_EXCEPT_ERROR             = TELNET_CODE_BASE + 3
TELNET_NO_EXCEPT_USERSTRING     = TELNET_CODE_BASE + 4
TELNET_NO_EXCEPT_PASSWORDSTRING = TELNET_CODE_BASE + 5
TELNET_NO_EXCEPT_WELCOMESTRING  = TELNET_CODE_BASE + 6
TELNET_NO_EXCEPT_PROMPTSTRING   = TELNET_CODE_BASE + 7
COMMAND_NO_DEFINE               = TELNET_CODE_BASE + 8
COMMAND_NO_EXCEPT_STR           = TELNET_CODE_BASE + 9 
COMMAND_RUN_ERR                 = TELNET_CODE_BASE + 10    
TELNET_NO_LOGIN                 = TELNET_CODE_BASE + 11                  
TELNET_TIME_OUT                 = TELNET_CODE_BASE + 12


# ERR_ServerIsNotExit = -10
# ERR1 = -1
# ERR2 = -2
# ERR3 = -3
# ERR3 = -4
    
class telnetAC():
    '''
    telnet 类,不考虑超时处理,所以使用时采用login -> setCommand-> runCommand->处理命令结果 ->logout 的方式执行
    '''
#     __metaclass__ = classDecorator 
    timeout = 10 #预计设置telnet10秒超时
    
    def __init__(self, targetIp, port, userString, passwordString, welcomeString, prompt):
        self.status = TELNET_NO_LOGIN         #telnet 状态
        self.targetIp = targetIp      
        self.port = port
        self.userString = userString          #telnet 用户输入提示符
        self.passwordString = passwordString  #telnet 用户密码提示符
        self.welcomeString = welcomeString    #telnet 用户密码成功后的欢迎提示符
        self.prompt = prompt                  #telnet 一般输入提示符
        self.logined = False                  #telnet 是否已经登陆 
        self.telnet = None                    #telnet 实例
        self.command = {}                     #telnet 注册命令
        self.commandResult = None             #telnet 命令执行结果
        
        
    def setCommand(self, commandDict):
        '''
                     注册命令，命令结构体，{"命令输入","命令输入后的提示符"} 
                     举例如下:{"cat /proc/rmi/mips-version\n" : "cwcos#"}
        '''
        self.command=commandDict
        telnetDebug("setCommand:"+str(commandDict))
            
            
    def runCommand(self, command , arg=None):
        '''
                     运行命令，不管命令执行成功或者失败，只抓取命令输出，
                     将命令结果，保存在self.commandResult中，由使用者自
                     行分析结果             
        '''
        self.commandResult = None
        
        if self.logined != True:
            self.status = TELNET_NO_LOGIN
            telnetDebug("telnet not logined")
            return TELNET_NO_LOGIN
        
        if self.command.has_key(command) == False:
            self.status = COMMAND_NO_DEFINE
            telnetDebug("%s COMMAND_NO_DEFINE"%(command))
            return COMMAND_NO_DEFINE
           
        try:
            telnetDebug("run command %s"%(command))
            if arg ==None:
                self.telnet.write(command + "\r")
            else:
                self.telnet.write(command + arg + "\r")
            
            #如果命令有预期的返回值则需要检查，没有就不用检测        
            if self.command[command] != None:
#                 result = self.telnet.expect([self.command[command]], self.timeout)
                #由于激活命令特殊，需要超时时间很长，这里修改为60秒
                result = self.telnet.expect([self.command[command]], 60)
                telnetDebug(result)
                
                #-1 命令输入后的提示符，表示返回值与预期不符
                if result[0] == -1:
                    telnetDebug("command: %scan't match the except string" % (self.command[command]))
                    self.status = COMMAND_RUN_ERR
                else:
                    self.commandResult = result[2]
                    self.status = TELNET_OK
                    telnetDebug(self.commandResult)
            else:
                result = self.telnet.read_eager()
                self.commandResult=result
                self.status = TELNET_OK
                telnetDebug(self.commandResult) 
        except:
            traceback.print_exc()
            self.status = TELNET_EXCEPT_ERROR
            return TELNET_EXCEPT_ERROR
        
#         self.telnet.write("\r\n")
#         self.status = TELNET_OK
        return TELNET_OK

    def runCommandWithExpect(self, command ,expectStr, arg=None):
        '''
                     运行命令，不管命令执行成功或者失败，只抓取命令输出，
                     将命令结果，保存在self.commandResult中，由使用者自
                     行分析结果             
        '''
        self.commandResult = None
        
        if self.logined != True:
            self.status = TELNET_NO_LOGIN
            telnetDebug("telnet not logined")
            return TELNET_NO_LOGIN
        
           
        try:
            telnetDebug("run command %s"%(command))
            if arg ==None:
                self.telnet.write(command + "\r")
            else:
                self.telnet.write(command + arg + "\r")
            print "expectStr: %s"%(expectStr)
            result = self.telnet.expect([expectStr], 60)
            telnetDebug(result)
                
            #-1 命令输入后的提示符，表示返回值与预期不符
            if result[0] == -1:
                telnetDebug("command: %scan't match the except string" % (command))
                self.status = COMMAND_RUN_ERR
            else:
                self.commandResult = result[2]
                self.status = TELNET_OK
                telnetDebug(self.commandResult)

        except:
            traceback.print_exc()
            self.status = TELNET_EXCEPT_ERROR
            return TELNET_EXCEPT_ERROR
        
#         self.telnet.write("\r\n")
#         self.status = TELNET_OK
        return TELNET_OK
        
    def logout(self):
        '''
                     退出telent
        '''
        if self.logined == True:
            self.telnet.close()
            self.logined = False    
            self.status = TELNET_NO_LOGIN
            del self.telnet
            self.telnet = None
                
    def login(self, user, password):
        '''
                    登陆telnet，校验用户提示，校验密码提示，校验登陆结果提示
        '''
        if self.logined == False :
            try:
                self.telnet = telnetlib.Telnet(self.targetIp, self.port, self.timeout)
#                 self.telnet.set_debuglevel(1)
            except:
                traceback.print_exc()
                self.status = TELNET_CONNECT_ERR
                return TELNET_CONNECT_ERR
        
            try:
                result = self.telnet.expect([self.userString], self.timeout)
                if result[0] == -1:
                    telnetDebug("login can't match user string")
                    self.status = TELNET_NO_EXCEPT_USERSTRING
                    return TELNET_NO_EXCEPT_USERSTRING
                
                self.telnet.write(user + "\r")
                result = self.telnet.expect([self.passwordString], self.timeout)
                if result[0] == -1:
                    telnetDebug("login can't match password string")
                    self.status = TELNET_NO_EXCEPT_PASSWORDSTRING
                    return TELNET_NO_EXCEPT_PASSWORDSTRING
                
                self.telnet.write(password + "\r")          
                if "" != self.welcomeString:
                    result = self.telnet.expect([self.welcomeString], self.timeout)
                    if result[0] == -1:
                        telnetDebug("login can't match welcome String")
                        self.status = TELNET_NO_EXCEPT_WELCOMESTRING
                        return TELNET_NO_EXCEPT_PROMPTSTRING
                         
                result = self.telnet.expect([self.prompt], self.timeout)
                if result[0] == -1:
                    telnetDebug("login can't match user prompt String")
                    self.status = TELNET_NO_EXCEPT_PROMPTSTRING
                    return TELNET_NO_EXCEPT_PROMPTSTRING
            except:
                traceback.print_exc()
                self.status = TELNET_EXCEPT_ERROR
                return TELNET_EXCEPT_ERROR
             
            self.status = TELNET_OK
            self.logined = True
            telnetDebug("login SUCESSED")
            
        return TELNET_OK
     
    
if  __name__ == "__main__":
    ip = "10.1.1.2"
    user = "root"
    password = "fitap^_^"
        
    telnet_manage_port = 87
    telnet_manage_user_except_string = "cwcos login"
    telnet_manage_password_except_string = "Password"
    telnet_manage_welcome_string = "Welcome to Centralize wireless Controller Operating System"
    telnet_manage_prompt = "cwcos#"
        
    testTelnet = telnetAC(ip,
                        telnet_manage_port,
                        telnet_manage_user_except_string,
                        telnet_manage_password_except_string,
                        telnet_manage_welcome_string,
                        telnet_manage_prompt)
    testTelnet.login(user, password) 
    
# #     commandDic={"cat /proc/rmi/mips-version\n" : "cwcos#"}
# #     
# #     testTelnet.setCommand(commandDic)
# #     testTelnet.runCommand("cat /proc/rmi/mips-version\n")
# 
# #     testTelnet.logout()
# #     testTelnet.runCommand("cat /proc/rmi/mips-version\n")
#     
# 
# #     print "1  get socket :" +str(testTelnet.telnet.get_socket())
# #     from time import sleep
# #     sleep(100)
# #     print "get socket :" +str(testTelnet.telnet.get_socket())
# #     sleep(300)
# #     print "2  get socket :" +str(testTelnet.telnet.get_socket())
# #     testTelnet.runCommand("cat /proc/rmi/mips-version\n")
# #     sleep(500)
# #     print "3  get socket :" +str(testTelnet.telnet.get_socket())
# #     testTelnet.runCommand("cat /proc/rmi/mips-version\n")
# #     sleep(700)
# #     print "4  get socket :" +str(testTelnet.telnet.get_socket())
# #     testTelnet.runCommand("cat /proc/rmi/mips-version\n")
# 
# 
#     ip = "10.1.1.2"
#     user = "bnas"
#     password = "bnas"
#      
#     telnet_accesss_port = 23
#     telnet_accesss_user_except_string = "Login:"
#     telnet_accesss_password_except_string = "Password:"
#     telnet_accesss_welcome_string=""
#     telnet_accesss_prompt="BNOS>"
#      
#     testTelnet = telnetAC(ip,
#                         telnet_accesss_port,
#                         telnet_accesss_user_except_string,
#                         telnet_accesss_password_except_string,
#                         telnet_accesss_welcome_string,
#                         telnet_accesss_prompt)
#    
#     testTelnet.login(user, password) 
# 


