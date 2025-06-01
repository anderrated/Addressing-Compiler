import sys
from addressing import Access, AddressingMode
import storage
from convert import Precision, Length

storage.register.store('PC', 0)
storage.register.store('IR', 0)

import compiler

class Except(Exception):
    def __init__(self, msg, occur=True):
        super().__init__(msg)
        self.message = msg
        self.occur = occur
        self.ret = None
    
    def dispMSG(self):
        print(f"Exception: {self.message}")
    
    def isOccur(self):
        return self.occur is True
    
    def setReturn(self, val):
        self.ret = val
    
    def getReturn(self):
        return self.ret

class Program:
    def __init__(self, program):
        # pre_encoded = compiler.Instruction.preEncode(program)
        # compiler.Instruction.encodeProgram(pre_encoded)
        compiler.Instruction.encodeProgram(program)
    
    def run(self):
        try:
            while True:
                ir_addr = storage.register.load('IR')
                
                instruction_code = storage.memory.load(ir_addr)
                if instruction_code is None:
                    break

                instruction_code = int(instruction_code)  # Ensure it's an int

                opcode = instruction_code & 0x1F
                
                execute_bit = opcode & 0x01
                write_bit = (opcode >> 1) & 0x01
                
                op1_result = self.getOp(instruction_code, 1) if self._has_operand(instruction_code, 1) else None
                op2_result = self.getOp(instruction_code, 2) if self._has_operand(instruction_code, 2) else None
                
                exec_result = None
                if execute_bit:
                    exec_result = self.execute((op1_result, op2_result), opcode)
                
                if write_bit and op1_result:
                    src = exec_result if execute_bit else op2_result
                    self.write(op1_result, src, opcode)
                
                self._increment_pc()
                
        except Exception as e:
            print(f"DEBUG: Exception occurred: {e}")
            exception_obj = self.exception("RUNTIME_ERROR", str(e))
            exception_obj.dispMSG()
    
    def getOp(self, inscode, op_num=1):
        if op_num == 1:
            mode = (inscode >> 5) & 0x07
            addr = (inscode >> 8) & 0xFF
        else:
            mode = (inscode >> 16) & 0x07
            addr = (inscode >> 19) & 0xFF

        print(f"DEBUG: getOp(inscode={inscode}, op_num={op_num}) mode={mode} addr={addr}")

        if mode == 0 and addr >= 65:
            addr -= 64  
        if mode == 7:
            return None

        addressing_modes = {
            0: lambda a: (AddressingMode.register(a), 'register'),
            1: lambda a: (AddressingMode.register_indirect(a), 'memory'),
            2: lambda a: (AddressingMode.direct(a), 'memory'),
            3: lambda a: (AddressingMode.indirect(a), 'memory'),
            4: lambda a: (AddressingMode.indexed(a), 'memory'),
            5: lambda a: (AddressingMode.stack('push'), 'memory'),
            6: lambda a: (AddressingMode.stack('pop'), 'memory')
        }

        try:
            if mode in addressing_modes:
                value, storage_type = addressing_modes[mode](addr)
                return {'value': value, 'address': addr, 'storage_type': storage_type}
            else:
                raise ValueError(f"Invalid addressing mode: {mode}")
        except Exception as e:
            raise self.exception("ADDRESSING_ERROR", str(e))

    
    def execute(self, operands, opcode):
        """Perform Execute operations
        Parameters:
        - operands: tuple of (op1_result, op2_result)
        - opcode: operation code
        Returns: result of execution
        """
        op1, op2 = operands
        category = (opcode >> 2) & 0x07
        execute_bit = opcode & 0x01
        write_bit = (opcode >> 1) & 0x01
        
        try:
            if execute_bit and not write_bit:
                return self._handle_jump_operations(category, op1, op2)
            
            elif execute_bit and write_bit:
                return self._handle_arithmetic_operations(category, op1, op2)
            
        except Exception as e:
            raise self.exception("EXECUTION_ERROR", str(e))
        
        return None
    
    def write(self, dest, src, movcode):

        try:
            value = src['value'] if isinstance(src, dict) and 'value' in src else src

            if dest['storage_type'] == 'register':
                Access.store('reg', dest['address'], value)

            elif dest['storage_type'] == 'memory':
                Access.store('mem', dest['address'], value)

            elif dest['storage_type'] == 'stack':
                sp = AddressingMode.stack('push')  
                Access.store('mem', sp, value)

            else:
                raise self.exception("WRITE_ERROR", f"Unknown storage type: {dest['storage_type']}")

        except Exception as e:
            raise self.exception("WRITE_ERROR", str(e))

    
    @staticmethod
    def exception(name, value):
        messages = {
            "DIVISION_BY_ZERO": f"Division by zero: {value}",
            "ADDRESSING_ERROR": f"Addressing error: {value}",
            "EXECUTION_ERROR": f"Execution error: {value}",
            "WRITE_ERROR": f"Write error: {value}",
            "RUNTIME_ERROR": f"Runtime error: {value}",
            "FILE_ERROR": f"File error: {value}"
        }
        return Except(messages.get(name, f"Unknown error ({name}): {value}"))
    
    def _has_operand(self, inscode, op_num):
        mode = (inscode >> (5 if op_num == 1 else 16)) & 0x07
        return mode != 7
    
    def _increment_pc(self):
        pc = storage.register.load('PC') + 1
        storage.register.store('PC', pc)
        storage.register.store('IR', pc)
    
    def _handle_jump_operations(self, category, op1, op2):
        if category == 6:  # JMP
            if op1:
                storage.register.store('PC', op1['address'])
                storage.register.store('IR', op1['address'])
        return None
    
    def _handle_arithmetic_operations(self, category, op1, op2):
        if not (op1 and op2):
            return None
            
        val1, val2 = op1['value'], op2['value']
        
        operations = {
            0: lambda: val1 % self._safe_divide(val1, val2, 'MOD'),  # MOD
            1: lambda: val1 + val2,  # ADD
            2: lambda: val1 - val2,  # SUB
            3: lambda: val1 * val2,  # MUL
            4: lambda: val1 // self._safe_divide(val1, val2, 'DIV')  # DIV
        }
        
        return operations.get(category, lambda: None)()
    
    def _safe_divide(self, dividend, divisor, operation):
        if divisor == 0:
            raise self.exception("DIVISION_BY_ZERO", f"{operation} operation")
        return divisor

division_by_zero_exception = Except("Division by zero occurred", False)

def run_from_file(filename):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
        
        instructions = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):  
                instructions.append(line)  
        
        program = Program(instructions)
        program.run()
        
    except FileNotFoundError:
        file_exception = Program.exception("FILE_ERROR", f"File {filename} not found")
        file_exception.dispMSG()
    except Exception as e:
        file_exception = Program.exception("FILE_ERROR", str(e))
        file_exception.dispMSG()

if __name__ == "__main__":
    storage.register.store('PC', 0)
    storage.register.store('IR', 0)

    if len(sys.argv) > 1:
        filename = sys.argv[1]
        run_from_file(filename)
    else:
        test_program = [
            'MOV R1 10',
            'MOV R2 5',
            'ADD R3 R1 R2',
            'PRNT R3',
            'EOP'
        ]
        
        program = Program(test_program)
        program.run()