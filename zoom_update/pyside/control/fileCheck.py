# -*- coding: UTF-8 -*-
'''
Created on 2013��9��13��

@author: xd
'''
# import sys
from pyparsing import oneOf,CaselessLiteral,Word,printables,Combine,StringStart,WordStart
from debug import controlDebug,classDecorator
import string

#错误码
FILE_CODE_BASE = 200
OPEN_FILE_OK       = FILE_CODE_BASE + 0
OPEN_FILE_ERR      = FILE_CODE_BASE + 1
READ_FILE_ERR      = FILE_CODE_BASE + 3
VERIFY_VERSION_ERR = FILE_CODE_BASE + 4
VERIFY_VERSION_OK  = FILE_CODE_BASE + 5

#版本关键字
RMIOS_STR      = "rmios"
VXWORKS_STR    = "vxworks"
LINUX_STR      = "linux"
VERSION_STR    = "version"
BOOTLOADER_STR = "bootloader"

class fileCheck():
    '''
          这里存在一个问题，版本里的描述必须按照vxworsk,rmios,linux,mips,bootloader的名称进行命名
          否则需要修改，
          这里先放宽检测条件，命名可以没有规则
    '''
#     __metaclass__ = classDecorator
    pyparsingstr={
                   RMIOS_STR   :Combine(CaselessLiteral("rmios")+Word(printables)).setResultsName(RMIOS_STR),
                   VXWORKS_STR :Combine(CaselessLiteral("vxworks")+Word(printables)).setResultsName(VXWORKS_STR),
                   LINUX_STR   :Combine(CaselessLiteral("linux")+Word(printables)).setResultsName(LINUX_STR),
                   VERSION_STR :Combine(oneOf("MIPS POWERPC X86",caseless=False)+Word(printables)).setResultsName(VERSION_STR),
                   BOOTLOADER_STR :Combine(CaselessLiteral("bootloader")+Word(printables)).setResultsName(BOOTLOADER_STR)
                   } 

#     pyparsingstr={
#                    RMIOS_STR   :Word(printables).setResultsName(RMIOS_STR),
#                    VXWORKS_STR :Word(printables).setResultsName(VXWORKS_STR),
#                    LINUX_STR   :Word(printables).setResultsName(LINUX_STR),
#                    VERSION_STR :Word(printables).setResultsName(VERSION_STR),
#                    BOOTLOADER_STR :Word(printables).setResultsName(BOOTLOADER_STR)
#                    }
     
    def __init__(self,file):
        self.file=file

        self.versionLen        = 0x30    #文件版本号的最大读取长度
        self.offsetDic={ 
                         RMIOS_STR   :0X140, #rmios版本号在文件的偏移
                         VXWORKS_STR :0X240, #vxworks版本号在文件的偏移
                         LINUX_STR   :0X340, #linux版本号在文件中的偏移
                         VERSION_STR :0X440, #大版本号在文件中的偏移
                         BOOTLOADER_STR :0x540, #bootrom版本号在文件中的偏移
                        }
        self.version={}
        
    def getVersion(self):
        '''
                            检查文件，获取文件版本,校验文件版本号
        '''
        fd=[]
        try:
            fd=open(self.file,"rb")
        except:
            controlDebug("open file %s err"%self.file)
            return OPEN_FILE_ERR
        try:
            for key in self.offsetDic.keys():
                fd.seek(self.offsetDic[key])
                buf = fd.read(self.versionLen)
                self.version[key]=buf.strip(chr(0))
                controlDebug(self.version[key])
        except:
            controlDebug("read file %s err"%self.file)
            return READ_FILE_ERR        
        fd.close()
        
        return OPEN_FILE_OK
    
    def verifyVersion(self):
        try:
            for key in self.version.keys():
                parstring = self.pyparsingstr[key]
                result=parstring.parseString(self.version[key])
                controlDebug("result : "+str(result))
        except:  
            controlDebug("verify version: %s, %s ,err"%(key,self.version[key]))  
            return  VERIFY_VERSION_ERR
        return VERIFY_VERSION_OK
    
if __name__ == '__main__':
    f= fileCheck('''..\\test\MIPS_1018R31T2.2_P7_ZTE''') 
    f.getVersion()
    f.verifyVersion()
    
  