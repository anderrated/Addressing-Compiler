from storage import register, memory, variable
from convert import Length, Precision, Value
from addressing import Access, AddressingMode

operations = [
    ["PRNT", "EOP"],
    ["MOV", "PUSH", "POP", "CALL", "RET", "SCAN", "DEF"],
    ["JEQ", "JNE", "JLT", "JLE", "JGT", "JGE", "JMP"],
    ["MOD", "ADD", "SUB", "MUL", "DIV"]
]

operationCodes = [
    ["00", "01", "10", "11"],
    ["000", "001", "010", "011", "100", "101", "110", "111"]
]

class Instruction:
    @staticmethod
    def getAddressingMode(operand):
        if operand is None or operand == "None":
            return "000"
        elif operand.startswith("R") and Value.isInteger(operand[1:]):
            return "000"
        elif operand.startswith("*R") and Value.isInteger(operand[2:]):
            return "001"
        elif (operand.startswith("#") and Value.isNumber(operand[1:])) or \
             (Value.isNumber(operand) and not (operand.startswith('M') or operand.startswith('A') or operand.startswith('I'))):
            return "010"
        elif operand.startswith("[") and operand.endswith("]"):
            return "011"
        elif operand.startswith("A") and Value.isInteger(operand[1:]):
            return "100"
        elif operand.startswith("I") and Value.isInteger(operand[1:]):
            return "101"
        elif operand in variable:
            return "110"
        else:
            raise ValueError(f"Unknown addressing mode for operand: {operand}")

    @staticmethod
    def encodeOp(operand):
        if operand is None or operand == "None":
            return "00000000"
        if (operand.startswith("#") and Value.isNumber(operand[1:])) or Value.isNumber(operand):
            val_str = operand[1:] if operand.startswith("#") else operand
            value = int(val_str)
            if not (0 <= value < 2**8):
                raise ValueError(f"Immediate value {value} out of 8-bit range for operand: {operand}")
            return format(value, '08b')
        elif (operand.startswith("R") and Value.isInteger(operand[1:])) or \
             (operand.startswith("*R") and Value.isInteger(operand[2:])) or \
             (operand.startswith("A") and Value.isInteger(operand[1:])) or \
             (operand.startswith("I") and Value.isInteger(operand[1:])):
            reg_name = operand[1:] if operand.startswith("*") else operand
            if reg_name not in variable:
                raise ValueError(f"Register '{reg_name}' not defined in variable table for operand: {operand}")
            return format(variable[reg_name], '08b')
        elif operand in variable:
            return format(variable[operand], '08b')
        elif operand.startswith("[") and operand.endswith("]"):
            inner_operand = operand[1:-1]
            try:
                return Instruction.encodeOp(inner_operand)
            except Exception as e:
                raise ValueError(f"Error encoding inner indirect operand '{inner_operand}' for operand '{operand}': {e}")
        else:
            raise ValueError(f"Unrecognized operand for encoding: {operand}")

    @staticmethod
    def encode(instruction_line):
        cleaned_line = instruction_line.replace(',', ' ')
        parts = cleaned_line.split()
        opcode_str = parts[0].upper()
        operand1 = parts[1] if len(parts) > 1 else None
        operand2 = parts[2] if len(parts) > 2 else None
        opcode_group_index = -1
        for i, group in enumerate(operations):
            if opcode_str in group:
                opcode_group_index = i
                break
        if opcode_group_index == -1:
            raise ValueError(f"Unknown opcode: {opcode_str}")
        ew_bits = operationCodes[0][opcode_group_index]
        category_code = operationCodes[1][operations[opcode_group_index].index(opcode_str)]
        opcode_binary = ew_bits + category_code
        op1_mode = Instruction.getAddressingMode(operand1)
        op2_mode = Instruction.getAddressingMode(operand2)
        op1_addr = Instruction.encodeOp(operand1)
        op2_addr = Instruction.encodeOp(operand2)
        extra_bits = "00000"
        instruction_code = opcode_binary + op1_mode + op1_addr + op2_mode + op2_addr + extra_bits
        if len(instruction_code) != Length.instrxn:
            raise ValueError(f"Generated instruction code has incorrect length ({len(instruction_code)} bits) for instruction: {instruction_line}. Expected {Length.instrxn} bits.")
        return instruction_code

    @staticmethod
    def preEncode(program_lines):
        temp_pc = 0
        for line in program_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=2)
            opcode_str = parts[0].upper()
            if opcode_str == "DEF":
                function_name = parts[1]
                variable[function_name] = temp_pc
                print(f"Defined function {function_name} at address {temp_pc}")
                continue
            elif opcode_str == "DEB":
                block_name = parts[1]
                variable[block_name] = temp_pc
                print(f"Defined block {block_name} at address {temp_pc}")
                continue
            temp_pc += 1
        return program_lines

    @staticmethod
    def encodeProgram(program):
        initial_pc = register.load(variable['PC'])
        processed_program_lines = Instruction.preEncode(program)
        encoded_instructions = []
        temp_pc_for_encoding = initial_pc
        for line in processed_program_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=2)
            opcode_str = parts[0].upper()
            if opcode_str in ["DEF", "DEB"]:
                continue
            instruction_to_encode = line
            binary_instruction_code = Instruction.encode(instruction_to_encode)
            if binary_instruction_code:
                instruction_int_value = int(binary_instruction_code, 2)
                memory.store(temp_pc_for_encoding, instruction_int_value)
                encoded_instructions.append((temp_pc_for_encoding, binary_instruction_code, instruction_int_value))
                temp_pc_for_encoding += 1
        return encoded_instructions