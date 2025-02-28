import math


class InstructionRegistrar:
    def __init__(self, CPU, compiler):
        self.CPU = CPU
        self.compiler = compiler

    def _get_store_as(self, reg):
        if reg in self.CPU.int_registers:
            return "int"
        elif reg in self.CPU.ff_registers:
            return "ff"
        elif reg in self.CPU.vector_registers:
            return "vector"
        else:
            self.compiler.report_error(f"Invalid register type: {reg}")

    def _check_registers_type(self, reg1, reg2, operation):
        if (reg1 in self.CPU.int_registers and reg2 in self.CPU.ff_registers) or (
                reg1 in self.CPU.ff_registers and reg2 in self.CPU.int_registers):
            self.compiler.report_error(
                f"Cannot perform {operation} between integer and floating point registers ({reg1}, {reg2})")
        if ((reg1 in self.CPU.vector_registers) and (
                reg2 in self.CPU.int_registers or reg2 in self.CPU.ff_registers)) or (
        ((reg1 in self.CPU.int_registers or reg1 in self.CPU.ff_registers) and reg2 in self.CPU.vector_registers)):
            self.compiler.report_error(
                f"Cannot perform {operation} between vector and non-vector registers ({reg1}, {reg2})")

    def add(self, reg1, reg2):
        self._check_registers_type(reg1, reg2, "addition")
        store_as = self._get_store_as(reg1)
        if reg1 in self.CPU.vector_registers and reg2 in self.CPU.vector_registers:
            v_reg1 = self.CPU.return_register(reg1)
            v_reg2 = self.CPU.return_register(reg2)
            if len(v_reg1) != len(v_reg2):
                self.compiler.report_error("Vector registers must have the same length for addition")
            result = [v_reg1[i] + v_reg2[i] for i in range(len(v_reg1))]
            if store_as == "int":
                result = [round(x) for x in result]
            self.CPU.update_register(reg1, result)
        else:
            v_reg1 = self.CPU.return_register(reg1)
            v_reg2 = self.CPU.return_register(reg2)
            result = v_reg1 + v_reg2
            if store_as == "int":
                result = round(result)
            self.CPU.update_register(reg1, result)

    def sub(self, reg1, reg2):
        self._check_registers_type(reg1, reg2, "subtraction")
        store_as = self._get_store_as(reg1)
        if reg1 in self.CPU.vector_registers and reg2 in self.CPU.vector_registers:
            v_reg1 = self.CPU.return_register(reg1)
            v_reg2 = self.CPU.return_register(reg2)
            if len(v_reg1) != len(v_reg2):
                self.compiler.report_error("Vector registers must have the same length for subtraction")
            result = [v_reg1[i] - v_reg2[i] for i in range(len(v_reg1))]
            if store_as == "int":
                result = [round(x) for x in result]
            self.CPU.update_register(reg1, result)
        else:
            v_reg1 = self.CPU.return_register(reg1)
            v_reg2 = self.CPU.return_register(reg2)
            result = v_reg1 - v_reg2
            if store_as == "int":
                result = round(result)
            self.CPU.update_register(reg1, result)

    def mul(self, reg1, reg2):
        self._check_registers_type(reg1, reg2, "multiplication")
        store_as = self._get_store_as(reg1)
        if reg1 in self.CPU.vector_registers and reg2 in self.CPU.vector_registers:
            v_reg1 = self.CPU.return_register(reg1)
            v_reg2 = self.CPU.return_register(reg2)
            if len(v_reg1) != len(v_reg2):
                self.compiler.report_error("Vector registers must have the same length for multiplication")
            result = [v_reg1[i] * v_reg2[i] for i in range(len(v_reg1))]
            if store_as == "int":
                result = [round(x) for x in result]
            self.CPU.update_register(reg1, result)
        else:
            v_reg1 = self.CPU.return_register(reg1)
            v_reg2 = self.CPU.return_register(reg2)
            result = v_reg1 * v_reg2
            if store_as == "int":
                result = round(result)
            self.CPU.update_register(reg1, result)

    def div(self, reg1, reg2):
        self._check_registers_type(reg1, reg2, "division")
        store_as = self._get_store_as(reg1)
        if reg1 in self.CPU.vector_registers and reg2 in self.CPU.vector_registers:
            v_reg1 = self.CPU.return_register(reg1)
            v_reg2 = self.CPU.return_register(reg2)
            if len(v_reg1) != len(v_reg2):
                self.compiler.report_error("Vector registers must have the same length for division")
            result = [v_reg1[i] / v_reg2[i] if v_reg2[i] != 0 else 0 for i in range(len(v_reg1))]
            if store_as == "int":
                result = [round(x) for x in result]
            self.CPU.update_register(reg1, result)
        else:
            v_reg1 = self.CPU.return_register(reg1)
            v_reg2 = self.CPU.return_register(reg2)
            if v_reg2 == 0:
                self.compiler.report_error("Division by zero")
            result = v_reg1 / v_reg2
            if store_as == "int":
                result = round(result)
            self.CPU.update_register(reg1, result)

    def mod(self, reg1, reg2):
        self._check_registers_type(reg1, reg2, "modulo")
        store_as = self._get_store_as(reg1)
        if reg1 in self.CPU.vector_registers and reg2 in self.CPU.vector_registers:
            v_reg1 = self.CPU.return_register(reg1)
            v_reg2 = self.CPU.return_register(reg2)
            if len(v_reg1) != len(v_reg2):
                self.compiler.report_error("Vector registers must have the same length for modulo")
            result = [v_reg1[i] % v_reg2[i] for i in range(len(v_reg1))]
            if store_as == "int":
                result = [round(x) for x in result]
            self.CPU.update_register(reg1, result)
        else:
            v_reg1 = self.CPU.return_register(reg1)
            v_reg2 = self.CPU.return_register(reg2)
            result = v_reg1 % v_reg2
            if store_as == "int":
                result = round(result)
            self.CPU.update_register(reg1, result)

    def dot_product(self, reg1, reg2):
        if reg1 in self.CPU.vector_registers and reg2 in self.CPU.vector_registers:
            v_reg1 = self.CPU.return_register(reg1)
            v_reg2 = self.CPU.return_register(reg2)
            if len(v_reg1) != len(v_reg2):
                self.compiler.report_error("Vector registers must have the same length for dot product")
            result = sum(v_reg1[i] * v_reg2[i] for i in range(len(v_reg1)))
            store_as = self._get_store_as(reg1)
            if store_as == "int":
                result = round(result)
            self.CPU.update_register(reg1, result)
        else:
            self.compiler.report_error("Dot product can only be performed between vector registers.")

    def magnitude(self, reg):
        if reg in self.CPU.vector_registers:
            v_reg = self.CPU.return_register(reg)
            result = math.sqrt(sum(x ** 2 for x in v_reg))
            store_as = self._get_store_as(reg)
            if store_as == "int":
                result = round(result)
            self.CPU.update_register(reg, result)
        else:
            self.compiler.report_error("Magnitude can only be calculated for vector registers.")

    def normalize(self, reg):
        if reg in self.CPU.vector_registers:
            v_reg = self.CPU.return_register(reg)
            mag = math.sqrt(sum(x ** 2 for x in v_reg))
            if mag == 0:
                self.compiler.report_error("Cannot normalize a zero vector.")
            normalized = [x / mag for x in v_reg]
            store_as = self._get_store_as(reg)
            if store_as == "int":
                normalized = [round(x) for x in normalized]
            self.CPU.update_register(reg, normalized)
        else:
            self.compiler.report_error("Normalization can only be performed on vector registers.")

    def store(self, reg, address):
        value = self.CPU.return_register(reg)
        value_type = "int" if isinstance(value, int) else "float"
        self.CPU.update_memory(address, value, value_type)

    def move(self, reg, value):
        if reg in self.CPU.int_registers or reg in self.CPU.ff_registers or reg in self.CPU.vector_registers:
            try:
                numeric_value = float(value)
                if reg in self.CPU.int_registers:
                    if numeric_value.is_integer():
                        self.CPU.update_register(reg, int(numeric_value))
                    else:
                        self.compiler.report_error(f"Cannot move floating point literal to {reg} due to type mismatch")
                elif reg in self.CPU.ff_registers:
                    self.CPU.update_register(reg, numeric_value)
                else:
                    self.compiler.report_error(f"Expected vector literal for {reg}")
                return
            except:
                if value.startswith("[") and value.endswith("]"):
                    tokens = value[1:-1].replace(",", " ").split()
                    if not (1 <= len(tokens) <= 32):
                        self.compiler.report_error(f"Vector length must be between 1 and 32, got {len(tokens)}")
                    vector = []
                    for token in tokens:
                        if token in self.CPU.int_registers or token in self.CPU.ff_registers or token in self.CPU.vector_registers:
                            reg_val = self.CPU.return_register(token)
                            vector.append(float(reg_val))
                        else:
                            try:
                                num_val = float(token)
                                vector.append(num_val)
                            except:
                                self.compiler.report_error(f"Invalid vector element: {token}")
                    if reg in self.CPU.vector_registers:
                        self.CPU.update_register(reg, vector)
                    else:
                        self.compiler.report_error(f"Cannot move vector literal to {reg}")
                    return
                elif value in self.CPU.int_registers or value in self.CPU.ff_registers or value in self.CPU.vector_registers:
                    src_value = self.CPU.return_register(value)
                    if (reg in self.CPU.int_registers and value in self.CPU.int_registers) or (
                            reg in self.CPU.ff_registers and value in self.CPU.ff_registers) or (
                            reg in self.CPU.vector_registers and value in self.CPU.vector_registers):
                        self.CPU.update_register(reg, src_value)
                    else:
                        self.compiler.report_error(f"Cannot move {value} to {reg} due to type mismatch")
                    return
                else:
                    self.compiler.report_error(f"Invalid value for MOVE operation: {value}")
        else:
            self.compiler.report_error(f"Invalid key for MOVE operation: {reg}")

    def print(self, reg):
        if reg in self.CPU.int_registers or reg in self.CPU.ff_registers or reg in self.CPU.vector_registers:
            print(self.CPU.return_register(reg))
        else:
            print(reg)
