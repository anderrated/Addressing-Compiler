from storage import register, memory, variable
from convert import Length, Precision, Value
from addressing import Access, AddressingMode

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
        if operand is None:
            return "000"  # Default to register
        elif operand.startswith("R"):
            return "000"  # Register
        elif operand.startswith("*R"):
            return "001"  # Register indirect
        elif operand.startswith("["):
            return "011"  # Indirect
        elif operand.startswith("A"):
            return "100"  # Indexed
        elif operand.startswith("stack_") or operand in ["push", "pop"]:
            return "101"  # Stack (default to push)
        elif operand.isdigit():
            return "010"  # Immediate / direct
        else:
            return "010"  # Default to direct

    @staticmethod
    def preEncode(instrxns):
        new_instrxns = []
        for instr in instrxns:
            parts = instr.strip().split()
            if not parts:
                continue

            op = parts[0]

            # Skip markers
            if op in ["DEV", "DEB"]:
                continue

            # DEF: define label as current PC address
            elif op == "DEF":
                label = parts[1]
                pc = int(register.load("PC"))
                variable.store(label, pc)
                continue

            # Conditional jumps: convert to SUB + JXX
            elif op in ["JEQ", "JNE", "JLT", "JLE", "JGT", "JGE"]:
                op1, op2 = parts[1], parts[2]
                new_instrxns.append(f"SUB {op1} {op2}")
                new_instrxns.append(f"{op} {op1}")
            
            else:
                new_instrxns.append(instr)

        return new_instrxns

    @staticmethod
    def encode(inst):
        parts = inst.strip().split()
        if not parts:
            return None

        op = parts[0]
        op1 = parts[1] if len(parts) > 1 else None
        op2 = parts[2] if len(parts) > 2 else None

        # Determine opcode
		# i = E_W ; group = Cat
        for i, group in enumerate(operations):
            if op in group:
                E_W = operationCodes[0][i]
                Cat = operationCodes[1][group.index(op)]
                break
        else:
            raise ValueError(f"Unknown operation: {op}")

        opcode = E_W + Cat  # 5 bits

        # Addressing modes
        op1_mode = Instruction.getAddressingMode(op1)
        op1_addr = Instruction.encodeOp(op1)

        op2_mode = Instruction.getAddressingMode(op2)
        op2_addr = Instruction.encodeOp(op2)

        extra_bits = "00000"

        return opcode + op1_mode + op1_addr + op2_mode + op2_addr + extra_bits

    @staticmethod
    def encodeOp(operand):
        if operand is None:
            return "00000000"
        try:
            addr = variable.load(operand)
            return format(int(addr), '08b')
        except:
            if operand.isdigit(): # Immediate
                return format(int(operand), '08b')
            elif operand.startswith("*R"): # Register Indirect
                return format(int(variable.load(operand[1:])), '08b')
            elif operand.startswith("[") and operand.endswith("]"): # Indirect Memory
                inner = operand[1:-1]
                return format(int(inner), '08b')
            else:
                raise ValueError(f"Unrecognized operand: {operand}")

    @staticmethod
    def encodeProgram(program):
        addr = int(register.load("PC"))
        compiled = Instruction.preEncode(program)

        for inst in compiled:
            binary = Instruction.encode(inst)
            if binary:
                instruction_int = int(binary, 2)
                memory.store(addr, instruction_int)
                print(f"{addr}: {binary} ({instruction_int})")  # Optional: debug output
                addr += 1

# Example program (for testing)
program = [
    "DEF START",
    "MOV R1 10",
    "MOV R2 5",
    "ADD R1 R2",
    "JEQ R1 R2",
    "EOP"
]

# Encode and store in memory
Instruction.encodeProgram(program)
