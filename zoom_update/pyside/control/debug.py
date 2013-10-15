# -*- coding: UTF-8 -*-
'''
Created on 2010-10-13

@author: x00163361
'''
#import os , sys
import locale
#pylint: disable=W0402 
import string
import re
#from config import *
import traceback

logFlag=1
printdebugFlag = 1
uiDebugFlag = 1
controlDebugFlag = 1
protocolFlag = 1

telnetFlag = 1
ftpFlag = 1

classFlag = 0

def getTextCoding():
    '''获取unicode编码'''
    textencoding = None
    lang = string.upper(locale.setlocale(locale.LC_ALL, ""))
    if re.match("UTF-8", lang) != None:
        # UTF-8编码
        textencoding = "utf-8"
    elif re.match(r"CHINESE|CP936", lang):
        # Windows下的GB编码
        textencoding = "gb18030"
        #print "windows "+textencoding
    elif re.match(r"GB2312|GBK|GB18030", lang):
        # Linux下的GB编码
        textencoding = "gb18030"
        #print "linux "+textencoding
    else:
        # 其他情况，抛个错误吧
        raise UnicodeError
    return textencoding

def uiDebug(*args):
    '''界面模块调试打印'''
    if uiDebugFlag == 1:
        printdebug(*args)
        
def controlDebug(*args):
    '''控制模块调试打印'''  
    if controlDebugFlag == 1:
        printdebug(*args)  
    
def protocolDebug(*args):  
    '''协议模块调试打印'''
    if protocolFlag ==  1:
        printdebug(*args)  

def telnetDebug(*args):  
    '''协议模块调试打印'''
    if telnetFlag ==  1:
        printdebug(*args)  

def ftpDebug(*args):  
    '''协议模块调试打印'''
    if ftpFlag ==  1:
        printdebug(*args)  


def classDebug(*args):
    if classFlag == 1:
        printdebug(*args)
                
def printdebug(*args):
    '''
        Debug打印
    '''
    if printdebugFlag == 0:
        pass
    else:
        try:
            textencoding = getTextCoding()
        #pylint: disable=W0702    
        except:
            traceback.print_exc()
            return    

        for arg in args:
            if type(arg) == str:
#                print "textencoding:"+textencoding
                print unicode(arg, textencoding)
            else: 
                print arg


def debug_required(func,name):   
    def warp(*args):
        classDebug("")
        classDebug("class %s *****************"%(name) + func.__name__ + ': start')
        try:
            classDebug("***args:" + str(args))
            return func(*args) 
        finally:
            classDebug("class %s *****************"%(name) + func.__name__ + ': end')
            classDebug("")     
    return warp   
   
   
class classDecorator(type):   
    def __new__(cls, name, bases, dct):   
        className= name
        for name, value in dct.iteritems():   
            if not name.startswith('_') and callable(value):
                value = debug_required(value,className)   
            dct[name] = value   
        return type.__new__(cls, name, bases, dct)  
                    
                
if __name__ == '__main__':
    print getTextCoding
    printdebug("aa")     
    printdebug(u"aa")
    printdebug(u"aa 你好")
    controlDebug(u"连接数据库成功")
    controlDebug("连接数据库成功")
    controlDebug("OK : sqlUserControl.__init__ 连接数据库成功")
    
    