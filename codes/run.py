from storage import register, memory, variable
from convert import Precision, Length, Value
from addressing import Access, AddressingMode
from compiler import Instruction, operations, operationCodes_EW # Import operations and operationCodes_EW directly
import sys # For exit in EOP

# Global exception instance for division by zero
division_by_zero_exception = None

class Except:
    def __init__(self, message, occur=False, ret_val=0):
        self.message = message
        self.occur = occur
        self.ret = ret_val

    def dispMSG(self):
        """Prints the exception message."""
        print(f"EXCEPTION: {self.message}")

    def isoccur(self):
        """Returns True if the exception has occurred."""
        return self.occur

    def setReturn(self, value):
        """Sets the return value of the exception."""
        self.ret = value

    def getReturn(self):
        """Returns the return value of the exception."""
        return self.ret

class Program:
    def __init__(self, program_lines):
        register.setStorage(32) # Initialize 32 registers
        memory.setStorage(256) # Initialize 256 memory slots

        # Use variable dictionary to get numeric addresses for registers
        register.store(variable['PC'], 0)
        register.store(variable['IR'], 0)   # Instruction Register (will hold current instruction address)
        register.store(variable['SPR'], 112) # Stack Pointer Register (base of stack area)
        register.store(variable['TSP'], 111) # Top Stack Pointer (initially points before first stack slot)
        register.store(variable['BPR'], 168) # Block Pointer Register (base of block area)
        register.store(variable['NBP'], 167) # Assuming NBP is just below BPR for now
        register.store(variable['CPR'], 152) # Assuming CPR is constant pointer
        register.store(variable['NCP'], 151) # Assuming NCP is just below CPR
        register.store(variable['VPR'], 200) # Assuming VPR is variable pointer
        register.store(variable['NVP'], 199) # Assuming NVP is just below VPR
        register.store(variable['MPR'], 216) # Assuming MPR is message pointer
        register.store(variable['NMP'], 215) # Assuming NMP is just below MPR

        # Encode the program during construction
        # The Instruction.encodeProgram handles both pre-encode (first pass) and encoding (second pass)
        Instruction.encodeProgram(program_lines)
        print("Program successfully compiled and loaded into memory.")


    @staticmethod
    def exception(exception_instance):
        """
        Static method to find and handle an exception.
        This simply sets the 'occur' attribute of the exception instance to True.
        """
        exception_instance.occur = True
        exception_instance.dispMSG()
        sys.exit(1) # Exit the program on unhandled exception


    def getOp(self, operand_binary_str, mode_binary_str):
        """
        Gets the effective address/value and the type of storage (memory, register, or value) of the operand.
        Returns a tuple: (effective_address_or_value, storage_type_string).
        storage_type_string can be 'memory', 'register', or 'value' (for immediate).
        """
        # Convert binary strings to integers
        operand_val = int(operand_binary_str, 2)

        # Map binary mode string to its meaning
        if mode_binary_str == AddressingMode.register(None): # "000" (R#)
            # Operand value is the register's numeric address
            return (operand_val, 'register')
        
        elif mode_binary_str == AddressingMode.register_indirect(None): # "001" (*R#)
            # Operand value is the register's numeric address. The content of that register is the effective address.
            reg_address = operand_val
            # Use Access.data to load the value from the register
            effective_address = Access.data(reg_address, flow=["reg"])
            return (effective_address, 'memory') # Points to memory

        elif mode_binary_str == AddressingMode.immediate(None): # "010" (#value or direct number)
            # Operand value is the immediate value itself. No address in storage.
            return (operand_val, 'value') # Indicates it's a direct value

        elif mode_binary_str == AddressingMode.indirect(None): # "011" ([address] or [R#])
            # Operand value is a memory address (or register address if it was [R#] resolved to R's address).
            # The content of that memory/register location is the effective address.
            pointer_address = operand_val
            # Use Access.data to load the value from memory (which is the effective address)
            effective_address = Access.data(pointer_address, flow=["mem", "reg"]) # Try memory first, then register
            return (effective_address, 'memory') # Points to memory

        elif mode_binary_str == AddressingMode.indexed(None): # "100" (A#)
            # Operand value is the numeric address of an index register (A#).
            # The content of this index register contains a base address.
            index_reg_address = operand_val
            # Use Access.data to load the base address stored in the index register
            base_address = Access.data(index_reg_address, flow=["reg"])
            return (base_address, 'memory') # Points to memory

        # Special (I# for Index Registers) - if treated as register direct for execution too
        # This will be the same as register direct.
        # elif mode_binary_str == AddressingMode.special(None): # "101" (I#)
        #     special_reg_address = operand_val
        #     return (special_reg_address, 'register')

        elif mode_binary_str == AddressingMode.direct(None): # "110" (label/variable names)
            # Operand value is directly the memory address.
            return (operand_val, 'memory')

        # Auto-increment/decrement - these modes usually imply an indirect access
        # with a side effect. The `getOp` here just resolves the initial address.
        # The actual increment/decrement is handled when the instruction executes.
        elif mode_binary_str == AddressingMode.autoinc(None): # "001"
            reg_address = operand_val
            # The effective address is the current value of the register before increment
            effective_address = Access.data(reg_address, flow=["reg"])
            # The increment itself happens during instruction execution if this is the source operand
            # or implicitly when writing to this operand if it's the destination
            return (effective_address, 'memory') # Typically points to memory

        elif mode_binary_str == AddressingMode.autodec(None): # "001"
            reg_address = operand_val
            # The decrement happens *before* the value is used.
            # So, we first decrement the register, then get the new value.
            current_val = Access.data(reg_address, flow=["reg"])
            new_val = current_val - 1
            Access.store('register', reg_address, new_val) # Store the decremented value back
            return (new_val, 'memory') # Effective address is the new value

        # Stack addressing - PUSH/POP/TOP are often separate instructions that
        # utilize stack pointers. If it's an operand mode for a general instruction,
        # it might point to the top of the stack.
        elif mode_binary_str == AddressingMode.stack(None): # "011"
            tsp_val = Access.data('TSP', flow=["reg"])
            return (tsp_val, 'memory') # Points to the top of the stack

        else: # "111" - Undefined/Reserved
            raise ValueError(f"Unsupported addressing mode: {mode_binary_str}")


    def write(self, dest_addr_binary, dest_mode_binary, value_to_write):
        """
        Performs Write operations (e.g., MOV, PUSH, POP, SCAN).
        This method will store `value_to_write` into the location specified by `dest_addr_binary` and `dest_mode_binary`.
        """
        dest_effective_addr, dest_type = self.getOp(dest_addr_binary, dest_mode_binary)

        if dest_type == 'register':
            Access.store('register', dest_effective_addr, value_to_write)
        elif dest_type == 'memory':
            Access.store('memory', dest_effective_addr, value_to_write)
        else: # Attempt to write to an immediate value (not possible)
            raise ValueError(f"Attempted to write to an immediate value or unsupported destination type: {dest_type}")


    def execute(self, opcode_str, op1_addr_binary, op1_mode_binary, op2_addr_binary, op2_mode_binary):
        """
        Performs Execute operations (e.g., ADD, SUB, MUL, DIV, PRNT, JMP, JEQ, JNE, CALL, RET).
        """
        # Helper to load value from resolved operand
        def get_operand_value(addr_or_val_tuple, operand_binary_str, mode_binary_str):
            addr_or_val, op_type = addr_or_val_tuple

            # Handle auto-increment for source operands
            if mode_binary_str == AddressingMode.autoinc(None):
                reg_address = int(operand_binary_str, 2) # Get the numeric address of the register
                current_val = Access.data(reg_address, flow=["reg"]) # Value *before* increment
                Access.store('register', reg_address, current_val + 1) # Perform increment
                return Access.data(current_val, flow=["mem"]) # Return data at original address
            
            if op_type == 'value':
                return addr_or_val
            elif op_type == 'register':
                return Access.data(addr_or_val, flow=["reg"])
            elif op_type == 'memory':
                return Access.data(addr_or_val, flow=["mem"])
            else:
                raise ValueError(f"Unknown operand type: {op_type}")

        # Resolve operands once for operations that need their values
        op1_resolved = self.getOp(op1_addr_binary, op1_mode_binary)
        op2_resolved = self.getOp(op2_addr_binary, op2_mode_binary)

        if opcode_str == "ADD":
            val1 = get_operand_value(op1_resolved, op1_addr_binary, op1_mode_binary)
            val2 = get_operand_value(op2_resolved, op2_addr_binary, op2_mode_binary)
            result = val1 + val2
            self.write(op1_addr_binary, op1_mode_binary, result) # Store result back to operand1's location
        
        elif opcode_str == "SUB":
            val1 = get_operand_value(op1_resolved, op1_addr_binary, op1_mode_binary)
            val2 = get_operand_value(op2_resolved, op2_addr_binary, op2_mode_binary)
            result = val1 - val2
            self.write(op1_addr_binary, op1_mode_binary, result)

        elif opcode_str == "MUL":
            val1 = get_operand_value(op1_resolved, op1_addr_binary, op1_mode_binary)
            val2 = get_operand_value(op2_resolved, op2_addr_binary, op2_mode_binary)
            result = val1 * val2
            self.write(op1_addr_binary, op1_mode_binary, result)

        elif opcode_str == "DIV":
            val1 = get_operand_value(op1_resolved, op1_addr_binary, op1_mode_binary)
            val2 = get_operand_value(op2_resolved, op2_addr_binary, op2_mode_binary)
            if val2 == 0:
                Program.exception(division_by_zero_exception) # Trigger division by zero exception
            result = val1 // val2 # Integer division
            self.write(op1_addr_binary, op1_mode_binary, result)

        elif opcode_str == "PRNT":
            val = get_operand_value(op1_resolved, op1_addr_binary, op1_mode_binary)
            print(f"PRNT: {val}")

        elif opcode_str == "MOV": # MOV is a Write operation, but handled here for simplicity for now.
            val_to_move = get_operand_value(op1_resolved, op1_addr_binary, op1_mode_binary)
            self.write(op2_addr_binary, op2_mode_binary, val_to_move)

        elif opcode_str == "JMP":
            # op1_resolved should be the target address (e.g., from 'DEF END' label)
            target_address = op1_resolved[0] # The effective address is the jump target
            if op1_resolved[1] != 'memory': # JMP targets are typically memory addresses (labels)
                 raise ValueError(f"JMP instruction expects a direct memory address as target, got {op1_resolved[1]}")
            Access.store('register', 'PC', target_address) # Set PC directly to target address

        elif opcode_str == "EOP":
            print("EOP encountered. Program finished.")
            sys.exit(0) # Program ends successfully

        # Implement other opcodes here:
        elif opcode_str == "PUSH":
            val_to_push = get_operand_value(op1_resolved, op1_addr_binary, op1_mode_binary)
            # Get current TSP value (which points to the last occupied stack slot)
            tsp_val = Access.data('TSP', flow=["reg"])
            new_tsp = tsp_val + 1 # Stack grows upwards (towards higher addresses)
            Access.store('register', 'TSP', new_tsp) # Update TSP
            Access.store('memory', new_tsp, val_to_push) # Store value at new TSP

        elif opcode_str == "POP":
            tsp_val = Access.data('TSP', flow=["reg"])
            spr_val = Access.data('SPR', flow=["reg"]) # Stack Pointer Register (base of stack)
            if tsp_val < spr_val: # Check for stack underflow
                raise IndexError("Stack Underflow: Attempted to pop from an empty stack.")
            
            popped_value = Access.data(tsp_val, flow=["mem"]) # Get value from top of stack
            new_tsp = tsp_val - 1 # Decrement TSP
            Access.store('register', 'TSP', new_tsp) # Update TSP
            self.write(op1_addr_binary, op1_mode_binary, popped_value) # Store popped value to destination

        elif opcode_str == "CALL":
            # Push current PC + 1 (return address) onto stack
            return_address = Access.data('PC', flow=["reg"])
            tsp_val = Access.data('TSP', flow=["reg"])
            new_tsp = tsp_val + 1
            Access.store('register', 'TSP', new_tsp)
            Access.store('memory', new_tsp, return_address)
            
            # Jump to target address
            target_address = op1_resolved[0]
            if op1_resolved[1] != 'memory': # CALL targets are typically memory addresses (functions)
                raise ValueError(f"CALL instruction expects a direct memory address as target, got {op1_resolved[1]}")
            Access.store('register', 'PC', target_address) # Set PC to target address

        elif opcode_str == "RET":
            # Pop return address from stack into PC
            tsp_val = Access.data('TSP', flow=["reg"])
            spr_val = Access.data('SPR', flow=["reg"])
            if tsp_val < spr_val: # Check for stack underflow
                raise IndexError("Stack Underflow: Attempted to return from an empty stack (no CALL).")
            
            return_address = Access.data(tsp_val, flow=["mem"])
            new_tsp = tsp_val - 1
            Access.store('register', 'TSP', new_tsp)
            Access.store('register', 'PC', return_address) # Set PC to return address

        elif opcode_str == "SCAN":
            user_input = input("SCAN: Enter a value: ")
            try:
                # Attempt to convert to integer first, then float if integer fails
                value_from_input = int(user_input)
            except ValueError:
                try:
                    value_from_input = float(user_input)
                except ValueError:
                    print("Invalid input. Storing 0.")
                    value_from_input = 0
            self.write(op1_addr_binary, op1_mode_binary, value_from_input)

        elif opcode_str in ["JEQ", "JNE", "JLT", "JLE", "JGT", "JGE", "MOD"]:
            # These require more sophisticated flag handling or direct comparison.
            # For simplicity in this example, they are placeholders.
            # For the given test program, these are not directly tested.
            print(f"WARNING: Opcode {opcode_str} is not fully implemented yet.")
            pass
        
        elif opcode_str == "DEF": # DEF is handled during compilation, not execution
            pass 
        else:
            print(f"ERROR: Unhandled opcode during execution: {opcode_str} at PC {Access.data('PC', flow=['reg']) - 1}") # PC already incremented
            sys.exit(1)


    def run(self):
        """
        Executes each Instruction Code starting from the address pointed by 'PC'.
        """
        print("Program execution started...")
        
        while True:
            current_pc = Access.data('PC', flow=["reg"]) # Load current PC value

            # Fetch instruction
            try:
                instruction_int = Access.data(current_pc, flow=["mem"], is_code=True)
            except KeyError: # Should not happen if memory is properly initialized by setStorage
                print(f"Attempted to fetch instruction from invalid memory address: {current_pc}")
                break # Halt if PC points to invalid memory

            # Ensure 32-bit binary string representation
            instruction_binary = format(instruction_int, '032b') 

            # Decode instruction components
            # Opcode is 7 bits now (EW (2) + Category (5))
            opcode_binary = instruction_binary[0:7] 
            op1_mode_binary = instruction_binary[7:10] # 3 bits
            op1_addr_binary = instruction_binary[10:18] # 8 bits
            op2_mode_binary = instruction_binary[18:21] # 3 bits
            op2_addr_binary = instruction_binary[21:29] # 8 bits
            # Remaining 3 bits (instruction_binary[29:32]) are extra/unused.

            # Map opcode_binary back to mnemonic (e.g., "MOV", "ADD")
            opcode_str = "UNKNOWN"
            ew_bits = opcode_binary[0:2]
            category_code_bin = opcode_binary[2:7] # This is now 5 bits

            # Convert category_code_bin to an integer to find its index in the operations list
            category_index = int(category_code_bin, 2)
            
            # Find the group based on ew_bits
            opcode_group_index = -1
            for i, ew in enumerate(operationCodes_EW):
                if ew == ew_bits:
                    opcode_group_index = i
                    break
            
            if opcode_group_index != -1:
                # Get the operations list for this group
                group_operations = operations[opcode_group_index]
                if category_index < len(group_operations):
                    opcode_str = group_operations[category_index]
            
            if opcode_str == "UNKNOWN":
                print(f"ERROR: Unknown opcode encountered: {opcode_binary} at PC: {current_pc}")
                break # Halt on unknown opcode

            # Increment PC for next instruction BEFORE execution,
            # so jumps can correctly set the *next* instruction.
            # If a JMP/CALL/RET happens, it will override this PC.
            Access.store('register', 'PC', current_pc + 1)

            # Execute the instruction
            self.execute(opcode_str, op1_addr_binary, op1_mode_binary, op2_addr_binary, op2_mode_binary)

            # EOP will call sys.exit(), so no need for explicit break here.
            # JMP/CALL/RET modify PC directly, so the next loop iteration will fetch from the new PC.

        print("Program execution completed.")


# Main execution block
if __name__ == "__main__":
    division_by_zero_exception = Except("Attempted division by zero.")

    test_program_filename = "test_program.isa" # Change this to your group's shortcut extension

    sample_program_lines = [
        "DEF START",
        "MOV 10, R1",  # R1 = 10
        "MOV 20, R2",  # R2 = 20
        "ADD R1, R2",  # R1 = R1 + R2 = 10 + 20 = 30
        "PRNT R1",     # Prints 30
        "SUB R1, R2",  # R1 = R1 - R2 = 30 - 20 = 10
        "PRNT R1",     # Prints 10
        "MOV 0, R3",   # R3 = 0
        "DIV R1, R3",  # R1 = R1 / R3 = 10 / 0 (should cause exception)
        "PRNT R1",     # This line should not be reached if exception halts program
        "JMP END",     # Jump to END if no exception (won't be reached after DIV 0)
        "DEF END",     # Label for jump
        "EOP"
    ]

    try:
        with open(test_program_filename, 'w') as f:
            for line in sample_program_lines:
                f.write(line + '\n')
        
        print(f"Created sample program file: {test_program_filename}")

        with open(test_program_filename, 'r') as f:
            program_from_file = [line.strip() for line in f.readlines()]
        
        print("\nRunning program from test_program.isa...\n")
        
        # Program constructor now handles compilation
        program_instance = Program(program_from_file)
        program_instance.run() # This calls the actual run method

    except Exception as e:
        print(f"An error occurred during program execution: {e}")