from storage import memory, register, variable, register_list
from convert import Precision, Length, Value

register_list = [
    'PC', 'IR', 'SPR', 'TSP', 'BPR', 'NBP', 'MPR', 'NMP', 'I1', 'I2',
    'BR', 'DR1', 'DR2', 'FR', 'CPR', 'NCP', 'VPR', 'NVP'
]

class Access:
    @staticmethod
    def data(address_or_reg_name, is_code=False):
        print(f"DEBUG Access.data: address_or_reg_name={address_or_reg_name} ({type(address_or_reg_name)})")

        if isinstance(address_or_reg_name, int):
            return memory.load(address_or_reg_name, isCode=is_code)

        elif isinstance(address_or_reg_name, str):
            if address_or_reg_name in register_list:
                return register.load(variable[address_or_reg_name], isCode=is_code)

            elif address_or_reg_name.startswith('R') and Value.isInteger(address_or_reg_name[1:]):
                if address_or_reg_name in variable:
                    return register.load(variable[address_or_reg_name], isCode=is_code)
                else:
                    raise ValueError(f"Undefined GPR: {address_or_reg_name}")

            elif (address_or_reg_name.startswith('A') and Value.isInteger(address_or_reg_name[1:])) or \
                 (address_or_reg_name.startswith('I') and Value.isInteger(address_or_reg_name[1:])):
                if address_or_reg_name in variable:
                    return register.load(variable[address_or_reg_name], isCode=is_code)
                else:
                    raise ValueError(f"Undefined register type: {address_or_reg_name}")

            elif address_or_reg_name in variable:
                resolved_addr = variable[address_or_reg_name]
                if isinstance(resolved_addr, (int, str)):
                    return memory.load(resolved_addr, isCode=is_code)
                else:
                    raise ValueError(f"Variable '{address_or_reg_name}' resolved to non-address value: {resolved_addr}")

            elif Value.isNumber(address_or_reg_name):
                return memory.load(int(address_or_reg_name), isCode=is_code)

            else:
                raise ValueError(f"Cannot resolve operand for data access: {address_or_reg_name}")
        else:
            raise TypeError(f"Invalid type for address_or_reg_name: {type(address_or_reg_name)}")

    @staticmethod
    def store(address_or_reg_name, value, is_code=False):
        print(f"DEBUG Access.store: address_or_reg_name={address_or_reg_name} ({type(address_or_reg_name)}), value={value}")

        if isinstance(address_or_reg_name, int):
            return memory.store(address_or_reg_name, value)

        elif isinstance(address_or_reg_name, str):
            if address_or_reg_name in register_list:
                register.store(variable[address_or_reg_name], value)
                return

            elif address_or_reg_name.startswith('R') and Value.isInteger(address_or_reg_name[1:]):
                if address_or_reg_name in variable:
                    register.store(variable[address_or_reg_name], value)
                    return
                else:
                    raise ValueError(f"Undefined GPR: {address_or_reg_name}")

            elif (address_or_reg_name.startswith('A') and Value.isInteger(address_or_reg_name[1:])) or \
                 (address_or_reg_name.startswith('I') and Value.isInteger(address_or_reg_name[1:])):
                if address_or_reg_name in variable:
                    register.store(variable[address_or_reg_name], value)
                    return
                else:
                    raise ValueError(f"Undefined register type for store: {address_or_reg_name}")

            elif address_or_reg_name in variable:
                resolved_addr = variable[address_or_reg_name]
                if isinstance(resolved_addr, (int, str)):
                    memory.store(resolved_addr, value)
                    return
                else:
                    raise ValueError(f"Variable '{address_or_reg_name}' resolved to non-address value: {resolved_addr} for store.")

            elif Value.isNumber(address_or_reg_name):
                memory.store(int(address_or_reg_name), value)
                return

            else:
                raise ValueError(f"Cannot resolve operand for data store: {address_or_reg_name}")
        else:
            raise TypeError(f"Invalid type for address_or_reg_name: {type(address_or_reg_name)}")

class AddressingMode:
    @staticmethod
    def immediate(value):
        return value, 'immediate' # Special type for immediate values

    @staticmethod
    def relative(current_address, displacement):
        return current_address + displacement, 'memory'

    @staticmethod
    def based(base_register_addr, displacement):
        base_value = Access.data(base_register_addr, is_register=True)
        return base_value + displacement, 'memory'


    @staticmethod
    def indexed(index_reg_name, displacement):
        # index_reg_name should be 'I1' or 'I2'
        idx_value = Access.data(index_reg_name, is_register=True)
        effective_address = idx_value + displacement
        return effective_address, 'memory'

    @staticmethod
    def register(reg_name):
        return reg_name, 'register'

    @staticmethod
    def register_indirect(reg_name):
        addr_in_reg = Access.data(reg_name, is_register=True)
        return addr_in_reg, 'memory'

    @staticmethod
    def direct(var_addr):
        return var_addr, 'memory'

    @staticmethod
    def indirect(var_addr):
        addr_in_memory = Access.data(var_addr, is_register=False)
        return addr_in_memory, 'memory'

    @staticmethod
    def autoinc(reg_name):
        original_addr = Access.data(reg_name, is_register=True)
        # Assuming increment by 1 for addresses (or size of data, simplified to 1 for now)
        new_addr = original_addr + 1
        Access.store('register', reg_name, new_addr)
        return original_addr, 'memory'

    @staticmethod
    def autodec(reg_name):
        original_addr = Access.data(reg_name, is_register=True)
        # Assuming decrement by 1 for addresses
        new_addr = original_addr - 1
        Access.store('register', reg_name, new_addr)
        return new_addr, 'memory'

    @staticmethod
    def stack(stack_option):
        spr_val = Access.data('SPR', is_register=True)
        tsp_val = Access.data('TSP', is_register=True)

        if stack_option == 'PUSH':
            new_tsp = tsp_val + 1
            Access.store('register', 'TSP', new_tsp) # Update TSP
            return new_tsp, 'memory' # Return address where value *will be* stored

        elif stack_option == 'POP':
            if tsp_val < spr_val: # Check for stack underflow (empty stack)
                raise IndexError("Stack Underflow: Attempted to pop from an empty stack.")
            popped_address = tsp_val
            new_tsp = tsp_val - 1
            Access.store('register', 'TSP', new_tsp) # Update TSP
            return popped_address, 'memory'

        elif stack_option == 'TOP':
            if tsp_val < spr_val: # Check for stack underflow (empty stack)
                raise IndexError("Stack Underflow: Attempted to read from an empty stack (TOP).")
            return tsp_val, 'memory'
        else:
            raise ValueError(f"Invalid stack option: {stack_option}. Must be 'PUSH', 'POP', or 'TOP'.")