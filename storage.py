from convert import Precision, Length
import copy

class Storage:
	def __init__(self, data={}):
		self.data = copy.deepcopy(data)
	def load(self, address, isCode=False):
		if type(address)==type(str()) and len(address)==Length.precision:
			address = Precision.spbin2dec(address)
		value = self.data[address]
		if not isCode:
			value = Precision.spbin2dec(value)
		return value
	def store(self,address,value):
		if type(address)==type(str()) and len(address)==Length.precision:
			address = Precision.spbin2dec(address)
		if type(value)==type(str()):
			self.data[address] = value
		else:
			self.data[address] = Precision.dec2spbin(value)
	def setStorage(self,stolen):
		for i in range(stolen):
			try:
				self.load(i)
			except:
				self.store(i,0)
	def dispStorage(self):
		for k,v in self.data.items():
			print(f"{k}: {v} = {Precision.spbin2dec(v)}")
	def dispStorageSlot(self,key,isCode=False):
		try:
			v = self.load(key)
			print(f"{key}: {v}")
		except:
			print(f"Address: {key} does not exists!")
	@staticmethod
	# predefined values
	def setVariable(var,name,addr,value):
		variable.store(name,addr)
		var.store(addr,value)
	def setVariables(name,base,stolen=0):
		if len(name)>1:
			stolen = len(name)
		for i in range(stolen):
			if len(name)>1:
				variable.store(name[i],base+i)
			else:
				variable.store(name+str(i+1),base+i)
	# temporary values
	def setTmpVariable(name,addr,startswith="tmp_"):
		data[0].store(startswith+name,addr)
	def setTmpVariables(name_arr,addr_arr,startswith="tmp_"):
		for name,addr in zip(name_arr,addr_arr):
			data[0].store(startswith+name,addr)
	def removeVariables(startsWith="tmp_"):
		data[0] = {key: value for key, value in variable.items() if not key.startswith(startsWith)}
	def removeVariable(name,startsWith="tmp_"):
		data[0].pop(startsWith+name)
			
memory = Storage()
register = Storage()
# R#, A#, I#, others
register_list = ["BR","DR1","DR2","FR","IR","PC","SPR","TSP","CPR","NCP","BPR","NBP","VPR","NVP","MPR","NMP"]
variable = Storage()
#Registers
br = 8	# acc = 9; ir = 12;
		# pc = 13; spr = 14; cpr = 16;
		# bpr = 18; vpr = 20; msgr = 22
#Memory
mbr = 8
mapr = 72
mspr = 112
mcpr = 152
mbpr = 168
mvpr = 200
mmpr = 216
memory_list = [mbr,0,0,0,mbr,mbr,mspr,mspr,mcpr,mcpr,mbpr,mbpr,mvpr,mvpr,mmpr,mmpr]
for i in range(len(register_list)):
	Storage.setVariable(register,register_list[i],br+i,memory_list[i])
# Storage.setVariable(register,"BR",br,mbr)
# Storage.setVariable(register,"DR1",br+1,0)
# Storage.setVariable(register,"DR2",br+2,0)
# Storage.setVariable(register,"FR",br+3,0)
# Storage.setVariable(register,"IR",br+4,mbr)
# Storage.setVariable(register,"PC",br+5,mbr)
# Storage.setVariable(register,"SPR",br+6,mspr)
# Storage.setVariable(register,"TSP",br+7,mspr)
# Storage.setVariable(register,"CPR",br+8,mcpr)
# Storage.setVariable(register,"NCP",br+9,mcpr+1)
# Storage.setVariable(register,"BPR",br+10,mbpr)
# Storage.setVariable(register,"NBP",br+11,mbpr+1)
# Storage.setVariable(register,"VPR",br+12,mvpr)
# Storage.setVariable(register,"NVP",br+13,mvpr+1)
# Storage.setVariable(register,"MPR",br+14,mmpr)
# Storage.setVariable(register,"NMP",br+15,mmpr+1)
varpr = 1
var_reglen = 7
Storage.setVariables("R",varpr,var_reglen)	# R1 to R7
Storage.setVariables("M",varpr,var_reglen)	# M1 to M7
apr = 24
array_reglen = 4
index_reglen = 2
Storage.setVariables("A",apr,array_reglen)	# A1 to A4
Storage.setVariables("I",apr+array_reglen,index_reglen)	# I1 to I2
reg_len = 32
register.setStorage(reg_len)
mem_len = 256
memory.setStorage(mem_len)
data = [variable, register, memory]
#printing the specified list
toShowStr = "000"
toShow = [c=='1' for c in toShowStr]
label = ["Variable", "Register", "Memory"]
for i,show in enumerate(toShow):
	if show:
		print(label[i])
		data[i].dispStorage()
"""
Storages:
Variable		Storage for special values in register and memory (variables, blocks, specialialized registers,etc.)
						-	Contains 32-bit Precision binary format (accurate upto 2^16 or 65536 for at most 2 decimal places)
Memory			Storage that mimics the computer memory with 256 slots (contains 32-bit instruction, 32-bit Precision values)
Registers		Storage that mimics the computer register with 32 slots (contains only 32-bit Precision values)

Memmory:
1-7 	GPM							(M#)
8-71 	Instructions				(Y)
72-111 	Arrays						(X)
112-151	Stack
152-167	Constants					(Non-Functional)
168-199	Blocks
200-215 Variables					(Non-Functional)
216-255	Messages
0		Special

Register
1-7		GPR							(R#)
8-23	Specialized
	8	Based Register				(BR)
	9	Double Register 1st 32-bit	(DR1) - Non-Functional
	10	Double Register 2nd 32-bit	(DR2) - Non-Functional
	11	Float Register				(FR)
	12	Instruction Register		(IR)
	13	Program Counter				(PC)
	14	Stack Pointer				(SPR)
	15	Top Stack Pointer			(TSP)
	16	Constant Pointer			(CPR)
	17	Next Constant Pointer		(NCP)
	18	Block Pointer				(BPR)
	19	Next Block Pointer			(NBP)
	20	Variable Pointers			(VPR)
	21	Next Variable Pointer		(NVP)
	22	Message Pointer				(MPR)
	23	Next Message Pointer		(NMP)
24-27	Array Pointers				(A#)
28-29	Array Indexes				(I#)
30		Accumulator					(ACC) - Non-Functional
0		Special
"""