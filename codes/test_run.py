from storage import memory, register
from run import run_from_file

def initialize_storage():
    # Reset storage to known state
    register.data = {}
    memory.data = {}
    
    # Initialize PC and IR
    register.store('PC', 0)
    register.store('IR', 0)
    
    # Initialize test registers
    register.store(1, 0)  # R1
    register.store(2, 0)  # R2
    
    # Initialize test memory
    memory.store(1, 0)  # M1

# Create test program file
with open('test_program.txt', 'w') as f:
    f.write("MOV R1 5\n")
    f.write("MOV R2 10\n")
    f.write("ADD R1 R2\n")
    f.write("MOV M1 R1\n")

# Initialize storage
initialize_storage()

# Run the program
run_from_file('test_program.txt')

# Verify results
print("Test Results:")
print(f"R1: {register.load(1)} (expected: 15.0)")
print(f"R2: {register.load(2)} (expected: 10.0)")
print(f"M1: {memory.load(1)} (expected: 15.0)")

# Check for exceptions
if hasattr(run_from_file, 'exception') and run_from_file.exception.isOccur():
    print("Exception occurred:", run_from_file.exception.message)
else:
    print("No exceptions occurred")