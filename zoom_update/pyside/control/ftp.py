# -*- coding: UTF-8 -*-
'''
Created on 2009-3-24

@author: xiaodong
'''
import os
from ftplib import FTP
import traceback
import filecmp
from debug import ftpDebug,controlDebug,classDecorator

FTP_BASE = 400
FTP_INIT                 = FTP_BASE + 0
FTP_OK                   = FTP_BASE + 1
FTP_ERR                  = FTP_BASE + 2
FTP_LOGIN_EXCEPT         = FTP_BASE + 3
FTP_CONNECT_EXCEPT       = FTP_BASE + 4
FTP_LOGOUT_EXCEPT        = FTP_BASE + 5
FTP_SET_PWD_EXCEPT       = FTP_BASE + 6
FTP_GET_FILE_EXCEPT      = FTP_BASE + 7
FTP_PUT_FILE_EXCEPT      = FTP_BASE + 8
FTP_GET_PWD_EXCEPT       = FTP_BASE + 9

ERR_UpdatePathIsNotExit = -1
ERR_FtpServerIsNotExit  = -2
ERR3=-1
ERR4=-1
ERR5=-1


class ftpAC():
#     __metaclass__ = classDecorator
    
    def __init__(self,targetIp):
        self.targetIp    = targetIp
        self.ftpHandle   = None
        self.status      = FTP_INIT
        self.logined     = False
        self.currentPath = None
        
    def login(self , username , password):
        '''
        ftp 登录
        '''    
        try:
            self.ftpHandle=FTP(self.targetIp)
        except:
            traceback.print_exc()
            return FTP_CONNECT_EXCEPT    

        try:
            self.ftpHandle.login(username,password)
        except:    
            traceback.print_exc()
            return FTP_LOGIN_EXCEPT
        
        ftpDebug("FTP_OK")            
        return FTP_OK 
    
    def logout(self):
        '''
        ftp 登出
        '''
        try:
#             self.ftpHandle.quit()
            self.ftpHandle.close()
        except:
            traceback.print_exc()
            return FTP_LOGOUT_EXCEPT
            
        ftpDebug("FTP_OK")
        return FTP_OK
    
    def getPWD(self):
        '''
                     获取当前路径
        '''
        try:
            self.currentPath=self.ftpHandle.pwd()
        except:
            traceback.print_exc()
            self.currentPath = None
            return FTP_GET_PWD_EXCEPT    
        return FTP_OK
    
    
    def setPWD(self, path):
        '''
                    设置当期路径
        '''
        try:
            self.ftpHandle.cwd(path)
        except:
            traceback.print_exc()
            return FTP_SET_PWD_EXCEPT
        
        self.currentPath = path
        return FTP_OK    
        
    
    
    def putFile(self , fileName , localPath, serverPath ):
        '''
        ftp 上传文件
        '''
        result = self.getPWD()
        if result != FTP_OK:
            return result
        
        currentPath= self.currentPath
        if serverPath!=None:
            self.setPWD(serverPath)

        try:
            fileHandle =  open(localPath +fileName,'rb')
            self.ftpHandle.storbinary('STOR '+fileName, fileHandle)
            fileHandle.close()
        except:
            traceback.print_exc()
            return FTP_PUT_FILE_EXCEPT    
                    
        self.setPWD(currentPath)
        return FTP_OK
    
    def getFile(self , fileName , saveFileName, savePath):
        '''
        ftp 下载文件
        '''
        try:
            fileHandle = open(savePath + saveFileName,'wb')
            self.ftpHandle.retrbinary('RETR '+fileName, fileHandle.write)
            fileHandle.close()
        except:
            traceback.print_exc()
            return FTP_GET_FILE_EXCEPT
             
        return FTP_OK

if  __name__=="__main__":
    ftpClient=ftpAC("10.1.1.2")
#     ftpClient=ftpAC("10.1.1.4")
    ftpClient.login("root","fitap^_^")
    
    
#     ftpClient.logout()
    ftpClient.putFile("test.txt", "d:\\", '/root/')
    
    ftpClient.getFile("test.txt", "test1.txt","e:\\")
    
    
#    ftpClient.updateAllFile()
#    ftpClient.backupAllFileAfterUpdate()
#    ftpClient.compareAllFile()
    