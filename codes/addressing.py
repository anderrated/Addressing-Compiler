# addressing.py

from storage import memory, register, variable
from convert import Precision, Length, Value

class Access:
    """
    Provides methods to access and modify data in memory and registers.
    """
    @staticmethod
    def data(addr, flow=["var"], is_code=False):
        """
        Retrieves data from memory or a register based on the address and flow.
        addr: The address, register name, or variable name.
        flow: A list indicating the order of lookup: "var", "reg", "mem".
              - "var": Check 'variable' dictionary for symbolic names.
              - "reg": Check registers.
              - "mem": Check memory.
        is_code: Boolean, True if loading an instruction.
        """
        # Ensure addr is a string if it's a symbolic name, or int if a direct address.
        # This function aims to return the actual *value* at the effective location.

        for f_type in flow:
            if f_type == "var":
                if isinstance(addr, str) and addr in variable:
                    resolved_addr = variable[addr]
                    # If resolved_addr itself is a register address (e.g., PC, R1)
                    if resolved_addr in register.data and not (0 <= resolved_addr < memory.max_size): # Assuming memory.max_size distinguishes memory from register addresses
                         return register.load(resolved_addr, isCode=is_code)
                    # If it's a memory address
                    elif isinstance(resolved_addr, int):
                        return memory.load(resolved_addr, isCode=is_code)
                    else:
                        raise ValueError(f"Variable '{addr}' resolved to an unhandleable address: {resolved_addr}")
            
            if f_type == "reg":
                # Try to load directly from register if addr is a known register name or its numeric address
                if isinstance(addr, str) and addr in variable and variable[addr] in register.data:
                    return register.load(variable[addr], isCode=is_code)
                elif isinstance(addr, int) and addr in register.data:
                    return register.load(addr, isCode=is_code)

            if f_type == "mem":
                # Try to load directly from memory if addr is a direct memory address (int)
                if isinstance(addr, int) and addr in memory.data:
                    return memory.load(addr, isCode=is_code)
                # Or if it's a string representation of a memory address
                elif isinstance(addr, str):
                    try:
                        mem_address = int(addr)
                        return memory.load(mem_address, isCode=is_code)
                    except ValueError:
                        pass # Not a direct numeric address, continue to next flow type or raise error

        # If after checking all flow types, the address is still not resolved
        raise ValueError(f"Could not resolve data for address '{addr}' with flow '{flow}'.")

    @staticmethod
    def store(typ, addr, value):
        """
        Stores a value in either memory or a register.
        typ: 'memory' or 'register'
        addr: The numeric address or the symbolic register/variable name.
        value: The value to store.
        """
        if typ == 'register':
            if isinstance(addr, str) and addr in variable:
                register.store(variable[addr], value)
            elif isinstance(addr, int):
                register.store(addr, value)
            else:
                raise ValueError(f"Invalid register store target: {addr}")
        elif typ == 'memory':
            if isinstance(addr, str) and addr in variable:
                memory.store(variable[addr], value)
            elif isinstance(addr, int):
                memory.store(addr, value)
            else:
                raise ValueError(f"Invalid memory store target: {addr}")
        else:
            raise ValueError(f"Unsupported storage type: {typ}. Must be 'memory' or 'register'.")


class AddressingMode:
    """
    Defines addressing modes as static methods, returning their 3-bit binary codes.
    These methods can also encapsulate mode-specific logic.
    """

    @staticmethod
    def immediate(var):
        """
        Returns the 3-bit code for Immediate addressing.
        'var' is the immediate value itself (e.g., "#10" or "5").
        """
        # This method is primarily for compiler to get the mode code.
        # Actual value handling is in compiler's encodeOp.
        return "010" # 3-bit code for immediate

    @staticmethod
    def indexed(displace):
        """
        Returns the 3-bit code for Indexed addressing.
        'displace' is typically the index register (A#).
        """
        return "100" # 3-bit code for indexed

    @staticmethod
    def register(reg_addr):
        """
        Returns the 3-bit code for Register Direct addressing.
        'reg_addr' is the register name (e.g., "R1").
        """
        return "000" # 3-bit code for register direct

    @staticmethod
    def register_indirect(reg_addr):
        """
        Returns the 3-bit code for Register Indirect addressing.
        'reg_addr' is the register name (e.g., "*R1").
        """
        return "001" # 3-bit code for register indirect

    @staticmethod
    def direct(var_addr):
        """
        Returns the 3-bit code for Direct addressing.
        'var_addr' is the symbolic variable/label name (e.g., "START", "M1").
        """
        return "110" # 3-bit code for direct

    @staticmethod
    def indirect(var_addr):
        """
        Returns the 3-bit code for Indirect addressing.
        'var_addr' is the address/register holding the actual address (e.g., "[100]", "[R1]").
        """
        return "011" # 3-bit code for indirect

    @staticmethod
    def autoinc(reg_addr):
        """
        Returns the 3-bit code for auto-increment addressing.
        Note: The actual increment logic should be handled by the runtime (run.py)
              when an operand of this mode is processed.
        """
        # Typically represented by a Register Indirect mode with specific execution semantics.
        # For encoding, it's often a variant of Register Indirect. Let's use 001 for now.
        return "001" # Using register indirect for encoding, runtime handles auto-inc semantics.

    @staticmethod
    def autodec(reg_addr):
        """
        Returns the 3-bit code for auto-decrement addressing.
        Note: The actual decrement logic should be handled by the runtime (run.py)
              when an operand of this mode is processed.
        """
        # Similar to auto-increment, often a variant of Register Indirect.
        return "001" # Using register indirect for encoding, runtime handles auto-dec semantics.

    @staticmethod
    def stack(stack_option):
        """
        Returns the 3-bit code for stack addressing.
        'stack_option' can be 'PUSH', 'POP', 'TOP'.
        Note: The actual stack operations (push/pop/top) are handled by the runtime (run.py)
              or the instruction itself (e.g., PUSH, POP instructions).
        """
        # Stack operations often involve indirect addressing through stack pointers.
        # For encoding, we can represent it as a form of indirect addressing or a special mode.
        # Given the existing instruction set, PUSH/POP/TOP are separate instructions
        # that *use* stack-related addressing. If it's used as an operand mode,
        # it might be treated as a form of indirect addressing.
        return "011" # Using indirect for encoding, runtime handles stack semantics.