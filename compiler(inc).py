import storage
from addressing import Access, AddressingMode
from convert import Length, Precision, Value

operations = [["PRNT","EOP"],["MOV","PUSH","POP","CALL","RET","SCAN","DEF"],["JEQ","JNE","JLT","JLE","JGT","JGE","JMP"],["MOD","ADD","SUB","MUL","DIV"]]
operationCodes = [["00","01","10","11"],["000","001","010","011","100","101","110","111"]]
class Instruction:
	@staticmethod
	def preEncode(instrxns):
	def encode(inst):
	def encodeOp(operand):
	def encodeProgram(program):
