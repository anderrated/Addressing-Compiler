# storage.py

from convert import Precision, Length
import copy

class Storage:
    def __init__(self, data={}):
        self.data = copy.deepcopy(data)

    def load(self, address, isCode=False):
        # Ensure address is an integer for lookup.
        if isinstance(address, str):
            try:
                address = int(address)
            except ValueError:
                if address.startswith('0b'):
                    address = int(address, 2)
                else:
                    raise ValueError(f"Invalid address format: {address}")

        if address not in self.data:
            # If the address doesn't exist, initialize it to 0 before loading.
            self.store(address, 0)

        value = self.data[address]

        if not isCode and isinstance(value, str):
            try:
                value = Precision.spbin2dec(value)
            except ValueError as e:
                raise ValueError(f"Error converting stored value at address {address} from binary to decimal: {e}. Value: {value}")
        return value

    def store(self, address, value):
        # Ensure address is an integer for lookup.
        if isinstance(address, str):
            try:
                address = int(address)
            except ValueError:
                if address.startswith('0b'):
                    address = int(address, 2)
                else:
                    raise ValueError(f"Invalid address format: {address}")

        if isinstance(value, str):
            self.data[address] = value
        elif isinstance(value, int):
            self.data[address] = value
        elif isinstance(value, float):
            self.data[address] = Precision.dec2spbin(value)
        else:
            raise TypeError(f"Unsupported value type for storage at address {address}: {type(value)}")

    def setStorage(self, stolen):
        # This method ensures all slots up to 'stolen' are initialized.
        for i in range(stolen):
            if i not in self.data:
                self.store(i, 0) # Initialize with an integer 0

    def dispStorage(self):
        for k, v in self.data.items():
            if isinstance(v, int):
                v_bin = bin(v)[2:].zfill(Length.instrxn)
                print(f"{k}: {v_bin} = {Precision.spbin2dec(v_bin)}")
            elif isinstance(v, str):
                print(f"{k}: {v} = {Precision.spbin2dec(v)}")
            else:
                print(f"{k}: {v} (unhandled type)")

    def dispStorageSlot(self, key, isCode=False):
        try:
            v = self.load(key, isCode)
            if isCode:
                print(f"{key}: {bin(v)[2:].zfill(Length.instrxn)}")
            else:
                print(f"{key}: {v}")
        except KeyError:
            print(f"Address: {key} does not exist!")
        except Exception as e:
            print(f"Error displaying slot {key}: {e}")

# --- Global instances and Initialization (Outside the Storage class) ---
memory = Storage()
register = Storage()

# List of specialized register names
register_list = ["BR","DR1","DR2","FR","IR","PC","SPR","TSP","CPR","NCP","BPR","NBP","VPR","NVP","MPR","NMP"]

variable = {} # The global 'variable' dictionary maps symbolic names to their numeric addresses.

# Define base addresses for specialized registers and memory sections
br = 8
mspr = 112
mcpr = 152
mbpr = 168
mvpr = 200
mmpr = 216

# Initial values for specialized registers
memory_list = [br,0,0,0,br,br,mspr,mspr,mcpr,mcpr,mbpr,mbpr,mvpr,mvpr,mmpr,mmpr]

# Initialize specialized registers (BR, DR1, ..., NMP)
for i in range(len(register_list)):
    reg_name = register_list[i]
    reg_address = br + i
    reg_initial_value = memory_list[i] if i < len(memory_list) else 0
    variable[reg_name] = reg_address
    register.store(reg_address, reg_initial_value)

# Initialize General Purpose Registers (R1 to R7)
varpr = 1 # Base address for GPRs
var_reglen = 7
for i in range(var_reglen):
    reg_name = f"R{i+1}"
    reg_address = varpr + i
    variable[reg_name] = reg_address
    register.store(reg_address, 0)

# Initialize Memory Variables (M1 to M7) - assuming these are distinct memory addresses
for i in range(var_reglen):
    mem_name = f"M{i+1}"
    mem_address = varpr + i # Adjust if memory variables have different address space
    variable[mem_name] = mem_address
    memory.store(mem_address, 0)

# Initialize Array Pointers (A1 to A4)
apr = 24 # Base address for Array Pointers, assumed to be in registers
array_reglen = 4
for i in range(array_reglen):
    array_name = f"A{i+1}"
    array_address = apr + i
    variable[array_name] = array_address
    register.store(array_address, 0)

# Initialize Index Registers (I1 to I2)
index_reglen = 2
for i in range(index_reglen):
    index_name = f"I{i+1}"
    index_address = apr + array_reglen + i # Continue addressing from A#
    variable[index_name] = index_address
    register.store(index_address, 0)

# Set initial storage sizes and ensure all slots are initialized to 0
reg_len = 32
register.setStorage(reg_len)
mem_len = 256
memory.setStorage(mem_len)

# This list is used by display functions (e.g., in run.py's main block)
data = [variable, register, memory]