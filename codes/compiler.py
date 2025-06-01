# compiler.py

from storage import register, memory, variable
from convert import Length, Precision, Value
from addressing import Access, AddressingMode # Ensure Access and AddressingMode are imported

# Grouped by Execute (E) and Write (W)
operations = [
    ["PRNT", "EOP"],  # 00
    ["MOV", "PUSH", "POP", "CALL", "RET", "SCAN", "DEF"],  # 01
    ["JEQ", "JNE", "JLT", "JLE", "JGT", "JGE", "JMP"],  # 10
    ["MOD", "ADD", "SUB", "MUL", "DIV"]  # 11
]

# [E+W bits] (index corresponds to 'operations' list groups)
# Category Codes are derived from the index within the 'operations' group, formatted to 5 bits.
operationCodes_EW = ["00", "01", "10", "11"]

class Instruction:
    @staticmethod
    def getAddressingMode(operand):
        """
        Converts an operand string into its 3-bit addressing mode code by calling
        the appropriate static method from AddressingMode.
        """
        if operand is None or operand == "None":
            return AddressingMode.register(None) # Default to register mode for no operand

        # Register Direct (R#)
        elif operand.startswith("R") and Value.isInteger(operand[1:]):
            return AddressingMode.register(operand)
        # Register Indirect (*R#)
        elif operand.startswith("*R") and Value.isInteger(operand[2:]):
            return AddressingMode.register_indirect(operand)
        # Immediate (#value or just a number)
        elif (operand.startswith("#") and Value.isNumber(operand[1:])) or \
             (Value.isNumber(operand) and not (operand.startswith('M') or operand.startswith('A') or operand.startswith('I'))):
            return AddressingMode.immediate(operand)
        # Indirect ([address] or [R#])
        elif operand.startswith("[") and operand.endswith("]"):
            return AddressingMode.indirect(operand)
        # Indexed (A#)
        elif operand.startswith("A") and Value.isInteger(operand[1:]):
            return AddressingMode.indexed(operand)
        # Special (I# for Index Registers) - often treated as direct register access for mode purposes
        elif operand.startswith("I") and Value.isInteger(operand[1:]):
            return AddressingMode.register(operand) # Treated as register direct for I#
        # Direct (label/variable names like START, END, M1 etc.)
        elif operand in variable:
            return AddressingMode.direct(operand)
        # Autoincrement/Autodecrement (assuming a specific syntax, e.g., R#+ or -R#)
        # If your ISA uses these, you'd add conditions here and call AddressingMode.autoinc/autodec
        # For example:
        # elif operand.endswith("+") and operand.startswith("R") and Value.isInteger(operand[1:-1]):
        #     return AddressingMode.autoinc(operand[:-1])
        # elif operand.startswith("-R") and Value.isInteger(operand[2:]):
        #     return AddressingMode.autodec(operand[1:])
        else:
            raise ValueError(f"Unknown addressing mode for operand: {operand}")

    @staticmethod
    def encodeOp(operand):
        """
        Encodes an operand into its 8-bit address/value representation.
        Handles registers, immediate values, direct addresses (labels/variables), and indirect.
        """
        if operand is None or operand == "None":
            return "00000000" # All zeros for no operand

        # Immediate values (e.g., "10", "#5")
        if (operand.startswith("#") and Value.isNumber(operand[1:])) or Value.isNumber(operand):
            val_str = operand[1:] if operand.startswith("#") else operand
            value = int(val_str)
            if not (0 <= value < 2**8): # Assuming 8-bit unsigned range for values
                raise ValueError(f"Immediate value {value} out of 8-bit range for operand: {operand}")
            return format(value, '08b')

        # Register direct (R#), Register Indirect (*R#), Indexed (A#), Special (I#)
        # For these, the 8-bit part is the numeric address of the register itself.
        elif (operand.startswith("R") and Value.isInteger(operand[1:])) or \
             (operand.startswith("*R") and Value.isInteger(operand[2:])) or \
             (operand.startswith("A") and Value.isInteger(operand[1:])) or \
             (operand.startswith("I") and Value.isInteger(operand[1:])):
            # If it's *R#, get the R# part
            reg_name = operand[1:] if operand.startswith("*") else operand
            if reg_name not in variable:
                raise ValueError(f"Register '{reg_name}' not defined in variable table for operand: {operand}")
            return format(variable[reg_name], '08b') # Get the numeric address of the register

        # Direct addressing (labels/variables like START, END, M1)
        elif operand in variable:
            # For direct addressing, the operand itself is the symbolic name (e.g., "START").
            # Its value in 'variable' is the actual numeric memory address.
            return format(variable[operand], '08b')

        # Indirect addressing ([address] or [R#])
        elif operand.startswith("[") and operand.endswith("]"):
            inner_operand = operand[1:-1] # Get content inside brackets
            # The inner operand can be a numeric address, a register name, or a label.
            # Recursively call encodeOp for the inner part to get its address.
            try:
                return Instruction.encodeOp(inner_operand) # This will resolve to an 8-bit binary string
            except Exception as e:
                raise ValueError(f"Error encoding inner indirect operand '{inner_operand}' for operand '{operand}': {e}")
        else:
            raise ValueError(f"Unrecognized operand for encoding: {operand}")

    @staticmethod
    def encode(instruction_line):
        """
        Encodes a single instruction line into a 32-bit binary instruction code.
        """
        # Replace commas with spaces to ensure operands are cleanly separated
        cleaned_line = instruction_line.replace(',', ' ')
        parts = cleaned_line.split() # Split by whitespace

        opcode_str = parts[0].upper()
        operand1 = parts[1] if len(parts) > 1 else None
        operand2 = parts[2] if len(parts) > 2 else None

        # 1. Encode Opcode (7 bits) = E/W bits (2 bits) + Category Code (5 bits)
        opcode_group_index = -1
        for i, group in enumerate(operations):
            if opcode_str in group:
                opcode_group_index = i
                break
        if opcode_group_index == -1:
            raise ValueError(f"Unknown opcode: {opcode_str}")

        ew_bits = operationCodes_EW[opcode_group_index]
        # Category code is the index of the opcode within its group, formatted to 5 bits
        category_code = format(operations[opcode_group_index].index(opcode_str), '05b')
        opcode_binary = ew_bits + category_code # This is 7 bits (2+5)

        # 2. Encode Addressing Modes (3 bits each)
        op1_mode = Instruction.getAddressingMode(operand1)
        op2_mode = Instruction.getAddressingMode(operand2)

        # 3. Encode Operand Addresses/Values (8 bits each)
        op1_addr = Instruction.encodeOp(operand1)
        op2_addr = Instruction.encodeOp(operand2)

        # Concatenate all parts to form the 32-bit instruction
        # Format: Opcode (7 bits) + Op1_Mode (3 bits) + Op1_Addr (8 bits) + Op2_Mode (3 bits) + Op2_Addr (8 bits) + Extra (3 bits)
        # Total = 7 + 3 + 8 + 3 + 8 + 3 = 32 bits
        extra_bits = "000" # Placeholder for now, or derive from instruction if needed

        instruction_code = opcode_binary + op1_mode + op1_addr + op2_mode + op2_addr + extra_bits
        
        # Ensure the final instruction code is exactly 32 bits long
        if len(instruction_code) != Length.instrxn:
            raise ValueError(f"Generated instruction code has incorrect length ({len(instruction_code)} bits) for instruction: {instruction_line}. Expected {Length.instrxn} bits.")

        return instruction_code

    @staticmethod
    def preEncode(program_lines):
        """
        First pass: identifies and stores addresses for labels (DEF) and blocks (DEB).
        Returns the original program lines for the second pass.
        """
        temp_pc = 0
        for line in program_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue # Skip empty lines and comments

            parts = line.split(maxsplit=2) # Use split without comma replacement for DEF/DEB parsing
            opcode_str = parts[0].upper()

            if opcode_str == "DEF":
                function_name = parts[1]
                variable[function_name] = temp_pc
                print(f"Defined function {function_name} at address {temp_pc}")
                continue # DEF instructions don't occupy a memory slot themselves

            elif opcode_str == "DEB":
                block_name = parts[1]
                variable[block_name] = temp_pc
                print(f"Defined block {block_name} at address {temp_pc}")
                continue # DEB instructions don't occupy a memory slot themselves

            # Only increment PC for actual executable instructions
            temp_pc += 1
        return program_lines # Return original lines for second pass

    @staticmethod
    def encodeProgram(program):
        """
        Main compilation function: performs two passes to encode the program.
        First pass for labels, second pass for instruction encoding.
        """
        # Get initial PC from register storage (numeric address)
        initial_pc = register.load(variable['PC'])
        
        # Perform the first pass to identify labels/blocks
        # This function modifies the global 'variable' dictionary
        processed_program_lines = Instruction.preEncode(program)

        encoded_instructions = []
        # --- Second pass: encode instructions ---
        # Use a temporary PC for instruction storage during encoding
        temp_pc_for_encoding = initial_pc

        for line in processed_program_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=2)
            opcode_str = parts[0].upper()

            # Skip DEF/DEB as they were handled in the first pass and are not executable instructions
            if opcode_str in ["DEF", "DEB"]:
                continue

            instruction_to_encode = line # Use the original line for encoding after label pass

            binary_instruction_code = Instruction.encode(instruction_to_encode)
            if binary_instruction_code:
                instruction_int_value = int(binary_instruction_code, 2)
                memory.store(temp_pc_for_encoding, instruction_int_value)
                encoded_instructions.append((temp_pc_for_encoding, binary_instruction_code, instruction_int_value))
                temp_pc_for_encoding += 1
        return encoded_instructions