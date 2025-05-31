from storage import register, memory, variable
from addressing import Access, AddressingMode
from convert import Length, Precision, Value

# Grouped by Execute (E) and Write (W)
operations = [
	["PRNT", "EOP"],  # 00
	["MOV", "PUSH", "POP", "CALL", "RET", "SCAN", "DEF"],  # 01
	["JEQ", "JNE", "JLT", "JLE", "JGT", "JGE", "JMP"],  # 10
	["MOD", "ADD", "SUB", "MUL", "DIV"]  # 11
]

# [E+W bits], [Category Code]
operationCodes = [
	["00", "01", "10", "11"],
	["000", "001", "010", "011", "100", "101", "110", "111"]
]

class Instruction:
	@staticmethod
	def getAddressingMode(operand):
		# Determine the addressing mode based on operand format
		if operand is None:
			return "000"  # Default: register
		if operand.startswith("R"):
			return "000"  # Register addressing
		elif operand.startswith("*R"):
			return "001"  # Register indirect addressing (e.g., *R1)
		elif operand.startswith("["):
			return "011"  # Indirect memory (e.g., [100])
		elif operand.startswith("A"):
			return "100"  # Indexed addressing (array pointer)
		elif operand.isdigit():
			return "010"  # Direct/immediate value
		elif operand.startswith("stack_") or operand in ["push", "pop"]:
			return "101"  # Stack addressing (placeholder for expansion)
		else:
			return "010"  # Default to direct if unrecognized

	@staticmethod
	def preEncode(instrxns):
		new_instrxns = []
		for instr in instrxns:
			parts = instr.strip().split()
			op = parts[0]

			if op in ["DEF", "DEB", "DEV"]:
				# Skip encoding DEF/DEB/DEV bc they are markers
				continue

			elif op in ["JEQ", "JNE", "JLT", "JLE", "JGT", "JGE"]:
				# Convert: JEQ X Y → SUB X Y, JEQ X
				op1 = parts[1]
				op2 = parts[2]
				# First: SUB X Y
				new_instrxns.append(f"SUB {op1} {op2}")
				# Then: JEQ X
				new_instrxns.append(f"{op} {op1}")
			
			else:
				# Regular instruction, keep it
				new_instrxns.append(instr)
		
		return new_instrxns

	@staticmethod
	def encode(inst):
		parts = inst.strip().split()
		op = parts[0] # Command: e.g. MOV
		op1 = parts[1] if len(parts) > 1 else None # Operand 1 : e.g. R1
		op2 = parts[2] if len(parts) > 2 else None # Operand 2 : e.g. R2

		# Find opcode = E_W + Cat = 5 bits total
		for i, group in enumerate(operations):
			if op in group:
				E_W = operationCodes[0][i] # Execute and Write bits
				Cat = operationCodes[1][group.index(op)] # Category bits
				break
		else:
			raise ValueError(f"Unknown operation: {op}")

		opcode = E_W + Cat  # 5 bits

		# Compute addressing modes and operand addresses
		op1_mode = Instruction.getAddressingMode(op1)
		op1_addr = Instruction.encodeOp(op1) if op1 else "00000000"

		op2_mode = Instruction.getAddressingMode(op2)
		op2_addr = Instruction.encodeOp(op2) if op2 else "00000000"

		extra_bits = "00000"

		return opcode + op1_mode + op1_addr + op2_mode + op2_addr + extra_bits

	# convert operands into 8-bit binary strings
	# returns address in binary 
	# storage comes from storage.py !! important
	@staticmethod
	def encodeOp(operand):
		if operand is None:
			return "00000000"
		try:
			address = variable.load(operand)
			return format(int(address), '08b')
		except:
			if operand.isdigit():  # Immediate constant
				return format(int(operand), '08b')
			else:
				raise ValueError(f"Unrecognized operand: {operand}")

	@staticmethod
	def encodeProgram(program):
		addr = int(register.load("PC")) # Which address to put the 32 bit instruction
		for inst in Instruction.preEncode(program):
			binary = Instruction.encode(inst)
			memory.store(addr, binary)
			print(f"{addr}: {binary}")  # Shows what was stored
			addr += 1


# Example program for testing
program = [
	"MOV R1 R2",
	"ADD R1 R3",
	"PUSH R1",
	"JEQ R1 R2",
	"DEF FUNC1"
]

Instruction.encodeProgram(program)
