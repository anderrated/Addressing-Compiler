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
		self.message = message
		self.occur = occur
		self.ret = None
	def dispMSG(self):
		print(f"Exception: {self.message}")
	def isOccur(self):
		return self.occur is True
	def setReturn(self,val):
		self.ret = val
	def getReturn(self):
		return self.ret