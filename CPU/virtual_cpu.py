import struct


class VirtualCPU:
    def __init__(self):
        self.int_registers = {"I1": 0, "I2": 0, "I3": 0, "I4": 0, "I5": 0, "I6": 0}
        self.ff_registers = {"FF1": 0.0, "FF2": 0.0, "FF3": 0.0, "FF4": 0.0, "FF5": 0.0, "FF6": 0.0}
        self.vector_registers = {"V1": [0.0] * 8, "V2": [0.0] * 8, "V3": [0.0] * 8, "V4": [0.0] * 8, "V5": [0.0] * 8,
                                 "V6": [0.0] * 8}
        self.memory = [None] * 1000

    def _update_overflow(self):
        for reg in self.int_registers:
            value = self.int_registers[reg]
            value %= 2 ** 32
            if value >= 2 ** 31:
                value -= 2 ** 32
            self.int_registers[reg] = value
        for reg in self.ff_registers:
            sign_bit, exponent, mantissa = self.float_to_ieee754(self.ff_registers[reg])
            self.ff_registers[reg] = self.ieee754_to_float(sign_bit, exponent, mantissa)

    def update_register(self, register, value):
        if register in self.int_registers:
            self.int_registers[register] = int(value)
        elif register in self.ff_registers:
            sign_bit, exponent, mantissa = self.float_to_ieee754(value)
            self.ff_registers[register] = self.ieee754_to_float(sign_bit, exponent, mantissa)
        elif register in self.vector_registers:
            if isinstance(value, list) and (1 <= len(value) <= 32):
                self.vector_registers[register] = [float(x) for x in value]
            else:
                print(
                    "\033[31mFATAL ERROR: Vector register must be assigned a list of floats with length between 1 and 32.\033[0m")
                exit(1)
        self._update_overflow()

    def update_memory(self, address, value):
        self.memory[address] = value
        self._update_overflow()

    def release_register(self, register):
        if register in self.int_registers:
            self.int_registers[register] = 0
        elif register in self.ff_registers:
            self.ff_registers[register] = 0.0
        elif register in self.vector_registers:
            self.vector_registers[register] = [0.0]
        self._update_overflow()

    def return_register(self, register):
        if register in self.int_registers:
            return self.int_registers[register]
        elif register in self.ff_registers:
            return self.ff_registers[register]
        elif register in self.vector_registers:
            return self.vector_registers[register]

    def return_memory(self, address):
        return self.memory[address]

    def return_memory_type(self, address):
        return self.memory_types[address]

    def float_to_ieee754(self, f):
        packed = struct.pack('!f', f)
        binary = ''.join(f'{b:08b}' for b in packed)
        sign_bit = int(binary[0], 2)
        exponent = int(binary[1:9], 2) - 127
        mantissa = int(binary[9:], 2)
        return sign_bit, exponent, mantissa

    def ieee754_to_float(self, sign_bit, exponent, mantissa):
        exponent_val = (1 - 127) if exponent == 0 else exponent
        mantissa_value = 1 + mantissa / (2 ** 23)
        return ((-1) ** sign_bit) * (2 ** exponent_val) * mantissa_value
