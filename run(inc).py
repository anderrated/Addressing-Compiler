import sys
import compiler
from addressing import Access, AddressingMode
import storage
from convert import Precision, Length

class Program:
	def __init__(self,program):
	def run(self):
	def getOp(self,inscode):
	def execute(self,result,opcode):
	def write(self,dest,src,movcode):
	@staticmethod
	def exception(name,value):
class Except:
	def __init__(self,msg,occur=True):
	def dispMSG(self):
	def isOccur(self):
	def setReturn(self,val):
	def getReturn(self):