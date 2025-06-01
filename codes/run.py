from storage import register, memory, variable
from convert import Precision, Length, Value
from addressing import Access, AddressingMode
from compiler import Instruction
import sys 

division_by_zero_exception = None 

class Except:
    def __init__(self, message, occur=False, ret_val=0):
        self.message = message
        self.occur = occur
        self.ret = ret_val

    def dispMSG(self):
        print(f"EXCEPTION: {self.message}")

    def isoccur(self):
        return self.occur

    def setReturn(self, value):
        self.ret = value

    def getReturn(self):
        return self.ret

class Program:
    def __init__(self, program_lines):
        register.setStorage(32)
        memory.setStorage(256) 

        register.store(variable['PC'], 0)
        register.store(variable['IR'], 0)   
        register.store(variable['SPR'], 112) 
        register.store(variable['TSP'], 111) 
        register.store(variable['BPR'], 168) 
        register.store(variable['NBP'], 167) 
        register.store(variable['CPR'], 152) 
        register.store(variable['NCP'], 151) 
        register.store(variable['VPR'], 200) 
        register.store(variable['NVP'], 199) 
        register.store(variable['MPR'], 216) 
        register.store(variable['NMP'], 215) 

    def run(self):
        print("Program execution started...")
        print("Program execution completed (conceptual).")


if __name__ == "__main__":
    division_by_zero_exception = Except("Attempted division by zero.")

    test_program_filename = "test_program.isa" 

    sample_program_lines = [
        "DEF START",
        "MOV 10, R1",
        "MOV 20, R2",
        "ADD R1, R2", 
        "PRNT R1",
        "SUB R1, R2", 
        "PRNT R1",
        "MOV 0, R3", 
        "DIV R1, R3", 
        "PRNT R1", 
        "JMP END", 
        "DEF END", 
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
        
        Instruction.encodeProgram(program_from_file)

        program_instance = Program(program_from_file)
        program_instance.run() 

    except Exception as e:
        print(f"An error occurred during program execution: {e}")