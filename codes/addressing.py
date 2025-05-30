import storage
from convert import Precision

class Access:
    @staticmethod
    def data(addr, flow=["var"]):
        if flow[0] == "var":
            # Direct variable access
            return storage.variable.load(addr)
        elif flow[0] == "reg":
            # Register access
            value = storage.register.load(addr)
            if len(flow) > 1 and flow[1] == "indirect":
                # Indirect: value in register is address in memory
                return storage.memory.load(value)
            return value
        elif flow[0] == "indexed":
            # Indexed addressing: addr is (base, index)
            base, index = addr
            address = storage.memory.load(base) + storage.register.load(index)
            return storage.memory.load(address)
        else:
            raise ValueError(f"Unknown flow type: {flow}")

    @staticmethod
    def store(typ, addr, value):
        if typ == "mem":
            storage.memory.store(addr, value)
        elif typ == "reg":
            storage.register.store(addr, value)
        elif typ == "var":
            storage.variable.store(addr, value)
        else:
            raise ValueError(f"Unknown storage type: {typ}")

class AddressingMode:
    @staticmethod
    def immediate(var):
        raise NotImplementedError("Immediate mode not implemented.")

    @staticmethod
    def relative(displace):
        raise NotImplementedError("Relative mode not implemented.")

    @staticmethod
    def based(displace):
        raise NotImplementedError("Based mode not implemented.")

    @staticmethod
    def indexed(displace):
        return Access.data(displace, flow=["indexed"])

    @staticmethod
    def register(reg_addr):
        return Access.data(reg_addr, flow=["reg"])

    @staticmethod
    def register_indirect(reg_addr):
        return Access.data(reg_addr, flow=["reg", "indirect"])

    @staticmethod
    def direct(var_addr):
        return Access.data(var_addr, flow=["var"])

    @staticmethod
    def indirect(var_addr):
        # First get the address stored at var_addr, then load from memory
        pointer = storage.variable.load(var_addr)
        return storage.memory.load(pointer)

    @staticmethod
    def autoinc(reg_addr):
        value = storage.register.load(reg_addr)
        storage.register.store(reg_addr, value + 1)
        return value

    @staticmethod
    def autodec(reg_addr):
        value = storage.register.load(reg_addr)
        storage.register.store(reg_addr, value - 1)
        return value

    @staticmethod
    def stack(stack_option):
        # Assume stack pointer is in register "SPR" and stack top pointer is "TSP"
        spr = "SPR"
        tsp = "TSP"
        if stack_option == "push":
            # Increment stack pointer, then store value at new top
            sp = storage.register.load(spr) + 1
            storage.register.store(spr, sp)
            storage.register.store(tsp, sp)
            return sp
        elif stack_option == "pop":
            # Get top, then decrement stack pointer
            sp = storage.register.load(spr)
            storage.register.store(spr, sp - 1)
            storage.register.store(tsp, sp - 1)
            return sp
        elif stack_option == "top":
            # Return current top of stack
            return storage.register.load(tsp)
        else:
            raise ValueError(f"Unknown stack option: {stack_option}")
