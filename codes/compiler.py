import storage
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
				# Then:a JEQ X
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

		# Default: register addressing mode
		op1_mode = "000"
		op1_addr = Instruction.encodeOp(op1) if op1 else "00000000"

		op2_mode = "000"
		op2_addr = Instruction.encodeOp(op2) if op2 else "00000000"

		extra_bits = "00000"

		return opcode + op1_mode + op1_addr + op2_mode + op2_addr + extra_bits

	@staticmethod
	# convert operands into 8-bit binary strings
	# returns address in binary 
	def encodeOp(operand):
		if operand is None:
			return "00000000"
		if operand.startswith("R"):  # Register R1-R7
			return format(int(operand[1:]), '08b')
		elif operand.startswith("A"):  # Array A1-A4
			return format(10 + int(operand[1:]) - 1, '08b')  # e.g., A1 = 10
		elif operand == "PC":
			return format(20, '08b')
		elif operand == "IR":
			return format(21, '08b')
		elif operand == "BR":
			return format(22, '08b')
		elif operand == "SPR":
			return format(23, '08b')
		elif operand == "TSP":
			return format(24, '08b')
		elif operand == "BPR":
			return format(25, '08b')
		elif operand == "NBP":
			return format(26, '08b')
		elif operand == "MPR":
			return format(27, '08b')
		elif operand == "NMP":
			return format(28, '08b')
		elif operand == "I1":
			return format(29, '08b')
		elif operand == "I2":
			return format(30, '08b')
		elif operand.isdigit():  # Immediate value
			return format(int(operand), '08b')
		else:
			raise ValueError(f"Unrecognized operand: {operand}")

	@staticmethod
	def encodeProgram(program):
		addr = int(storage.register.load("PC"))
		for inst in Instruction.preEncode(program):
			binary = Instruction.encode(inst)
			storage.memory.store(addr, binary)
			addr += 1

# Example program for testing
program = [
	"MOV R1 R2",
	"ADD R1 R3",
	"PUSH R1"
]

Instruction.encodeProgram(program)
