from CPU.instruction_registrar import InstructionRegistrar
from CPU.virtual_cpu import VirtualCPU


class Compiler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.CPU = VirtualCPU()
        self.asm = self.load_file().split(';')
        self.instruction_index = 0
        self.memory_index = 0
        self.debug = True
        self.instruction_set = {
            "MOVE": self.handle_move,
            "ADD": self.handle_add,
            "SUB": self.handle_sub,
            "MUL": self.handle_mul,
            "DIV": self.handle_div,
            "MOD": self.handle_mod,
            "STORE": self.handle_store,
            "LOADM": self.handle_load_mem,
            "PRINT": self.handle_print,
            "TEXT": self.handle_print_ascii,
            "JZ": self.handle_jz,
            "JNZ": self.handle_jnz,
            "JMP": self.handle_jmp,
            "HALT": self.handle_halt,
            "VAR": self.handle_set_var,
            "INPUT": self.handle_input
        }
        self.variables = {}
        self.functions = {}
        self.labels = {}
        self.reg_names = ["I1", "I2", "I3", "I4", "I5", "I6", "FF1", "FF2", "FF3", "FF4", "FF5", "FF6", "V1", "V2",
                          "V3", "V4", "V5", "V6"]
        self.cpu_executor = InstructionRegistrar(self.CPU, self)
        self.preprocess_functions()
        self.read_asm()

    def report_error(self, message):
        line_num = self.instruction_index + 1
        code_line = self.asm[self.instruction_index].strip() if self.instruction_index < len(self.asm) else ""
        print(f"\033[31mFATAL ERROR at line {line_num}: {message}\n ====>{code_line}<====\033[0m")
        exit(1)

    def preprocess_functions(self):
        new_asm = []
        for line in self.asm:
            s = line.strip()
            if not s or s.startswith("//"):
                new_asm.append(line)
            elif s.startswith("DEF "):
                parts = s.split(":", 1)
                new_asm.append(parts[0].strip() + ":")
                if len(parts) > 1 and parts[1].strip():
                    new_asm.append(parts[1].strip())
            else:
                new_asm.append(line)
        self.asm = new_asm
        start_line = None
        current_function = None
        self.functions = {}
        self.labels = {}
        for i, line in enumerate(self.asm):
            s = line.strip()
            if not s or s.startswith("//"):
                continue
            if s.startswith("DEF "):
                if current_function is not None:
                    self.functions[current_function] = (start_line, i - 1)
                current_function = s.split()[1].rstrip(":")
                start_line = i
            elif s.startswith("RETURN") and current_function:
                self.functions[current_function] = (start_line, i)
                current_function = None
            if ":" in s and not s.startswith("DEF "):
                label_part, *instruction_part = s.split(":", 1)
                label_name = label_part.strip()
                self.labels[label_name] = i - 1
                if instruction_part and instruction_part[0].strip():
                    self.asm[i] = instruction_part[0].strip()
        if current_function is not None:
            self.functions[current_function] = (start_line, len(self.asm) - 1)

    def read_asm(self):
        while self.instruction_index < len(self.asm):
            instruction = self.asm[self.instruction_index].strip()
            if not instruction:
                self.instruction_index += 1
                continue
            if instruction.startswith("DEF "):
                function_name = instruction.split()[1].rstrip(":")
                self.instruction_index = self.functions[function_name][1] + 1
                continue
            parts = instruction.split(" ", 1)
            operator = parts[0]
            if operator == "CALL":
                function_name = parts[1].strip()
                if function_name in self.functions:
                    self.run_function(function_name)
                else:
                    self.report_error(f"Function '{function_name}' not found")
            elif operator in self.instruction_set:
                args = parts[1].strip().split(",") if len(parts) > 1 else []
                self.instruction_set[operator](*args)
            elif instruction.endswith(":"):
                pass
            else:
                print(f"\033[31mWARNING: Unknown instruction: {operator}, skipping...\033[0m")
            self.instruction_index += 1

    def run_function(self, function_name):
        if function_name not in self.functions:
            self.report_error(f"Function '{function_name}' not found")
        start, end = self.functions[function_name]
        original_index = self.instruction_index
        self.instruction_index = start + 1
        while self.instruction_index <= end:
            instruction = self.asm[self.instruction_index].strip()
            if not instruction or instruction.startswith("RETURN"):
                break
            parts = instruction.split(" ", 1)
            operator = parts[0]
            args = parts[1].strip().split(",") if len(parts) > 1 else []
            if operator in self.instruction_set:
                self.instruction_set[operator](*args)
            else:
                self.report_error(f"Unknown instruction: {operator}")
            self.instruction_index += 1
        self.instruction_index = original_index

    def handle_move(self, key, value):
        if key in self.reg_names:
            try:
                numeric_value = float(value)
                if key.startswith("I") and numeric_value.is_integer():
                    self.cpu_executor.move(key, int(numeric_value))
                elif key.startswith("FF"):
                    self.cpu_executor.move(key, numeric_value)
                else:
                    self.report_error(f"Cannot move {numeric_value} to {key} due to type mismatch")
                return
            except:
                if value.startswith("[") and value.endswith("]"):
                    tokens = value[1:-1].replace(",", " ").split()
                    if not (1 <= len(tokens) <= 32):
                        self.report_error(f"Vector length must be between 1 and 32, got {len(tokens)}")
                    vector = []
                    for token in tokens:
                        if token in self.reg_names:
                            reg_val = self.CPU.return_register(token)
                            vector.append(float(reg_val))
                        elif token in self.variables:
                            head, buf, typ = self.variables[token]
                            mem_val = self.CPU.return_memory(head)
                            vector.append(float(mem_val))
                        else:
                            try:
                                num_val = float(token)
                                vector.append(num_val)
                            except:
                                self.report_error(f"Invalid vector element: {token}")
                    if key.startswith("V"):
                        self.CPU.update_register(key, vector)
                    else:
                        self.report_error(f"Cannot move vector to {key}, expected a vector register")
                    return
                elif value in self.reg_names:
                    src_value = self.CPU.return_register(value)
                    if (key.startswith("I") and value.startswith("I")) or (
                            key.startswith("FF") and value.startswith("FF")) or (
                            key.startswith("V") and value.startswith("V")):
                        self.cpu_executor.move(key, src_value)
                    else:
                        self.report_error(f"Cannot move {value} to {key} due to type mismatch")
                    return
                elif value in self.variables:
                    head, buffer, var_type = self.variables[value]
                    if var_type == "string":
                        self.report_error(f"Cannot move string variable {value} to register {key}")
                    elif var_type == "int" and key.startswith("I"):
                        value_from_mem = self.CPU.return_memory(head)
                        self.cpu_executor.move(key, int(value_from_mem))
                    elif var_type == "int" and key.startswith("FF"):
                        value_from_mem = self.CPU.return_memory(head)
                        self.cpu_executor.move(key, float(value_from_mem))
                    elif var_type == "float" and key.startswith("FF"):
                        value_from_mem = self.CPU.return_memory(head)
                        self.cpu_executor.move(key, float(value_from_mem))
                    elif var_type == "vector" and key.startswith("V"):
                        vector_value = [self.CPU.return_memory(head + i) for i in range(buffer)]
                        self.CPU.update_register(key, vector_value)
                    else:
                        self.report_error(f"Cannot move {value} to {key} due to type mismatch")
                    return
                else:
                    self.report_error(f"Invalid value for MOVE operation: {value}")
        elif key in self.variables:
            head, buffer, var_type = self.variables[key]
            try:
                numeric_value = float(value)
                if var_type == "int" and numeric_value.is_integer():
                    self.CPU.update_memory(head, int(numeric_value))
                elif var_type == "float":
                    self.CPU.update_memory(head, numeric_value)
                else:
                    self.report_error(f"Cannot move {numeric_value} to {key} due to type mismatch")
                return
            except:
                if value.startswith("[") and value.endswith("]"):
                    tokens = value[1:-1].replace(",", " ").split()
                    if not (1 <= len(tokens) <= 32):
                        self.report_error(f"Vector length must be between 1 and 32, got {len(tokens)}")
                    for i, token in enumerate(tokens):
                        if token in self.reg_names:
                            token_val = self.CPU.return_register(token)
                            self.CPU.update_memory(head + i, float(token_val))
                        elif token in self.variables:
                            t_head, t_buf, t_type = self.variables[token]
                            token_val = self.CPU.return_memory(t_head)
                            self.CPU.update_memory(head + i, float(token_val))
                        else:
                            try:
                                token_val = float(token)
                                self.CPU.update_memory(head + i, token_val)
                            except:
                                self.report_error(f"Invalid vector element: {token}")
                    self.variables[key] = [head, len(tokens), "vector"]
                    return
                else:
                    values = [ord(char) for char in value.replace('"', "")]
                    if len(values) > buffer:
                        self.report_error(f"Memory buffer overflow by {len(values) - buffer} bytes")
                    for i, v in enumerate(values):
                        self.CPU.update_memory(head + i, v)
                    self.variables[key] = [head, buffer, "string"]
                    return
        else:
            self.report_error(f"Invalid key for MOVE operation: {key}")

    def handle_add(self, reg1, key):
        if reg1 in self.reg_names:
            if key in self.reg_names:
                self.cpu_executor.add(reg1, key)
            elif key in self.variables:
                head, buffer, var_type = self.variables[key]
                if var_type == "int" or var_type == "float":
                    value = self.CPU.return_memory(head)
                    if reg1.startswith("I"):
                        if var_type == "int":
                            self.CPU.update_register(reg1, self.CPU.return_register(reg1) + int(value))
                        else:
                            self.report_error(f"Cannot add a float variable to an integer register {reg1}")
                    elif reg1.startswith("FF"):
                        self.CPU.update_register(reg1, self.CPU.return_register(reg1) + float(value))
                    elif reg1.startswith("V"):
                        vector = self.CPU.return_register(reg1)
                        result = [x + float(value) for x in vector]
                        self.CPU.update_register(reg1, result)
                elif var_type == "vector":
                    if reg1.startswith("V"):
                        vector1 = self.CPU.return_register(reg1)
                        vector2 = [self.CPU.return_memory(head + i) for i in range(buffer)]
                        if len(vector1) == len(vector2):
                            result = [x + y for x, y in zip(vector1, vector2)]
                            self.CPU.update_register(reg1, result)
                        else:
                            self.report_error(f"Vector size mismatch: {len(vector1)} != {len(vector2)}")
                    else:
                        self.report_error(f"Cannot add a vector variable to a non-vector register {reg1}")
                else:
                    self.report_error(f"Cannot add a {var_type} variable to register {reg1}")
            else:
                if key.startswith("[") and key.endswith("]"):
                    try:
                        vector_literal = [float(x) for x in key[1:-1].split()]
                        if reg1.startswith("V"):
                            vector = self.CPU.return_register(reg1)
                            if len(vector) == len(vector_literal):
                                result = [x + y for x, y in zip(vector, vector_literal)]
                                self.CPU.update_register(reg1, result)
                            else:
                                self.report_error(f"Vector size mismatch: {len(vector)} != {len(vector_literal)}")
                        else:
                            self.report_error(f"Cannot add a vector literal to a non-vector register {reg1}")
                    except ValueError:
                        self.report_error(f"Invalid vector literal: {key}")
                else:
                    try:
                        operand = float(key)
                    except:
                        self.report_error(f"Invalid type for ADD operation. Got: {key}")
                    if reg1.startswith("I"):
                        value = self.CPU.return_register(reg1)
                        if operand.is_integer():
                            self.CPU.update_register(reg1, value + int(operand))
                        else:
                            self.report_error(f"Cannot add a float literal to an integer register {reg1}")
                    elif reg1.startswith("FF"):
                        value = self.CPU.return_register(reg1)
                        self.CPU.update_register(reg1, value + operand)
                    elif reg1.startswith("V"):
                        vector = self.CPU.return_register(reg1)
                        result = [x + operand for x in vector]
                        self.CPU.update_register(reg1, result)
        else:
            self.report_error(f"Invalid register for ADD operation: {reg1}")

    def handle_sub(self, reg1, key):
        if reg1 in self.reg_names:
            if key in self.reg_names:
                self.cpu_executor.sub(reg1, key)
            elif key in self.variables:
                head, buffer, var_type = self.variables[key]
                if var_type == "int" or var_type == "float":
                    value = self.CPU.return_memory(head)
                    if reg1.startswith("I"):
                        if var_type == "int":
                            self.CPU.update_register(reg1, self.CPU.return_register(reg1) - int(value))
                        else:
                            self.report_error(f"Cannot subtract a float variable from an integer register {reg1}")
                    elif reg1.startswith("FF"):
                        self.CPU.update_register(reg1, self.CPU.return_register(reg1) - float(value))
                    elif reg1.startswith("V"):
                        vector = self.CPU.return_register(reg1)
                        result = [x - float(value) for x in vector]
                        self.CPU.update_register(reg1, result)
                elif var_type == "vector":
                    if reg1.startswith("V"):
                        vector1 = self.CPU.return_register(reg1)
                        vector2 = [self.CPU.return_memory(head + i) for i in range(buffer)]
                        if len(vector1) == len(vector2):
                            result = [x - y for x, y in zip(vector1, vector2)]
                            self.CPU.update_register(reg1, result)
                        else:
                            self.report_error(f"Vector size mismatch: {len(vector1)} != {len(vector2)}")
                    else:
                        self.report_error(f"Cannot subtract a vector variable from a non-vector register {reg1}")
                else:
                    self.report_error(f"Cannot subtract a {var_type} variable from register {reg1}")
            else:
                if key.startswith("[") and key.endswith("]"):
                    try:
                        vector_literal = [float(x) for x in key[1:-1].split()]
                        if reg1.startswith("V"):
                            vector = self.CPU.return_register(reg1)
                            if len(vector) == len(vector_literal):
                                result = [x - y for x, y in zip(vector, vector_literal)]
                                self.CPU.update_register(reg1, result)
                            else:
                                self.report_error(f"Vector size mismatch: {len(vector)} != {len(vector_literal)}")
                        else:
                            self.report_error(f"Cannot subtract a vector literal from a non-vector register {reg1}")
                    except ValueError:
                        self.report_error(f"Invalid vector literal: {key}")
                else:
                    try:
                        operand = float(key)
                    except:
                        self.report_error(f"Invalid type for SUB operation. Got: {key}")
                    if reg1.startswith("I"):
                        value = self.CPU.return_register(reg1)
                        if operand.is_integer():
                            self.CPU.update_register(reg1, value - int(operand))
                        else:
                            self.report_error(f"Cannot subtract a float literal from an integer register {reg1}")
                    elif reg1.startswith("FF"):
                        value = self.CPU.return_register(reg1)
                        self.CPU.update_register(reg1, value - operand)
                    elif reg1.startswith("V"):
                        vector = self.CPU.return_register(reg1)
                        result = [x - operand for x in vector]
                        self.CPU.update_register(reg1, result)
        else:
            self.report_error(f"Invalid register for SUB operation: {reg1}")

    def handle_mul(self, reg1, key):
        if reg1 in self.reg_names:
            if key in self.reg_names:
                self.cpu_executor.mul(reg1, key)
            elif key in self.variables:
                head, buffer, var_type = self.variables[key]
                if var_type == "int" or var_type == "float":
                    value = self.CPU.return_memory(head)
                    if reg1.startswith("I"):
                        if var_type == "int":
                            self.CPU.update_register(reg1, self.CPU.return_register(reg1) * int(value))
                        else:
                            self.report_error(f"Cannot multiply an integer register {reg1} with a float variable")
                    elif reg1.startswith("FF"):
                        self.CPU.update_register(reg1, self.CPU.return_register(reg1) * float(value))
                    elif reg1.startswith("V"):
                        vector = self.CPU.return_register(reg1)
                        result = [x * float(value) for x in vector]
                        self.CPU.update_register(reg1, result)
                elif var_type == "vector":
                    if reg1.startswith("V"):
                        vector1 = self.CPU.return_register(reg1)
                        vector2 = [self.CPU.return_memory(head + i) for i in range(buffer)]
                        if len(vector1) == len(vector2):
                            result = [x * y for x, y in zip(vector1, vector2)]
                            self.CPU.update_register(reg1, result)
                        else:
                            self.report_error(f"Vector size mismatch: {len(vector1)} != {len(vector2)}")
                    else:
                        self.report_error(f"Cannot multiply a vector variable with a non-vector register {reg1}")
                else:
                    self.report_error(f"Cannot multiply a {var_type} variable with register {reg1}")
            else:
                if key.startswith("[") and key.endswith("]"):
                    try:
                        vector_literal = [float(x) for x in key[1:-1].split()]
                        if reg1.startswith("V"):
                            vector = self.CPU.return_register(reg1)
                            if len(vector) == len(vector_literal):
                                result = [x * y for x, y in zip(vector, vector_literal)]
                                self.CPU.update_register(reg1, result)
                            else:
                                self.report_error(f"Vector size mismatch: {len(vector)} != {len(vector_literal)}")
                        else:
                            self.report_error(f"Cannot multiply a vector literal with a non-vector register {reg1}")
                    except ValueError:
                        self.report_error(f"Invalid vector literal: {key}")
                else:
                    try:
                        operand = float(key)
                    except:
                        self.report_error(f"Invalid type for MUL operation. Got: {key}")
                    if reg1.startswith("I"):
                        value = self.CPU.return_register(reg1)
                        if operand.is_integer():
                            self.CPU.update_register(reg1, value * int(operand))
                        else:
                            self.report_error(f"Cannot multiply an integer register {reg1} with a float literal")
                    elif reg1.startswith("FF"):
                        value = self.CPU.return_register(reg1)
                        self.CPU.update_register(reg1, value * operand)
                    elif reg1.startswith("V"):
                        vector = self.CPU.return_register(reg1)
                        result = [x * operand for x in vector]
                        self.CPU.update_register(reg1, result)
        else:
            self.report_error(f"Invalid register for MUL operation: {reg1}")

    def handle_div(self, reg1, key):
        if reg1 in self.reg_names:
            if key in self.reg_names:
                self.cpu_executor.div(reg1, key)
            elif key in self.variables:
                head, buffer, var_type = self.variables[key]
                if var_type == "int" or var_type == "float":
                    value = self.CPU.return_memory(head)
                    if value == 0:
                        self.report_error("Division by zero")
                    if reg1.startswith("I"):
                        if var_type == "int":
                            self.CPU.update_register(reg1, self.CPU.return_register(reg1) // int(value))
                        else:
                            self.report_error(f"Cannot divide an integer register {reg1} by a float variable")
                    elif reg1.startswith("FF"):
                        self.CPU.update_register(reg1, self.CPU.return_register(reg1) / float(value))
                    elif reg1.startswith("V"):
                        vector = self.CPU.return_register(reg1)
                        result = [x / float(value) if value != 0 else 0 for x in vector]
                        self.CPU.update_register(reg1, result)
                elif var_type == "vector":
                    if reg1.startswith("V"):
                        vector1 = self.CPU.return_register(reg1)
                        vector2 = [self.CPU.return_memory(head + i) for i in range(buffer)]
                        if len(vector1) == len(vector2):
                            result = [x / y if y != 0 else 0 for x, y in zip(vector1, vector2)]
                            self.CPU.update_register(reg1, result)
                        else:
                            self.report_error(f"Vector size mismatch: {len(vector1)} != {len(vector2)}")
                    else:
                        self.report_error(f"Cannot divide a vector variable by a non-vector register {reg1}")
                else:
                    self.report_error(f"Cannot divide register {reg1} by a {var_type} variable")
            else:
                # Handle vector literals (e.g., [5 6 7])
                if key.startswith("[") and key.endswith("]"):
                    try:
                        # Parse the vector literal
                        vector_literal = [float(x) for x in key[1:-1].split()]
                        if reg1.startswith("V"):
                            vector = self.CPU.return_register(reg1)
                            if len(vector) == len(vector_literal):
                                result = [x / y if y != 0 else 0 for x, y in zip(vector, vector_literal)]
                                self.CPU.update_register(reg1, result)
                            else:
                                self.report_error(f"Vector size mismatch: {len(vector)} != {len(vector_literal)}")
                        else:
                            self.report_error(f"Cannot divide a vector literal by a non-vector register {reg1}")
                    except ValueError:
                        self.report_error(f"Invalid vector literal: {key}")
                else:
                    try:
                        operand = float(key)
                    except:
                        self.report_error(f"Invalid type for DIV operation. Got: {key}")
                    if operand == 0:
                        self.report_error("Division by zero")
                    if reg1.startswith("I"):
                        value = self.CPU.return_register(reg1)
                        if operand.is_integer():
                            self.CPU.update_register(reg1, value // int(operand))
                        else:
                            self.report_error(f"Cannot divide an integer register {reg1} by a float literal")
                    elif reg1.startswith("FF"):
                        value = self.CPU.return_register(reg1)
                        self.CPU.update_register(reg1, value / operand)
                    elif reg1.startswith("V"):
                        vector = self.CPU.return_register(reg1)
                        result = [x / operand if operand != 0 else 0 for x in vector]
                        self.CPU.update_register(reg1, result)
        else:
            self.report_error(f"Invalid register for DIV operation: {reg1}")

    def handle_mod(self, reg1, key):
        if reg1 in self.reg_names:
            if key in self.reg_names:
                self.cpu_executor.mod(reg1, key)
            elif key in self.variables:
                head, buffer, var_type = self.variables[key]
                if var_type == "int" or var_type == "float":
                    value = self.CPU.return_memory(head)
                    if value == 0:
                        self.report_error("Modulo by zero")
                    if reg1.startswith("I"):
                        if var_type == "int":
                            self.CPU.update_register(reg1, self.CPU.return_register(reg1) % int(value))
                        else:
                            self.report_error(
                                f"Cannot perform modulo on an integer register {reg1} with a float variable")
                    elif reg1.startswith("FF"):
                        self.CPU.update_register(reg1, self.CPU.return_register(reg1) % float(value))
                    elif reg1.startswith("V"):
                        vector = self.CPU.return_register(reg1)
                        result = [x % float(value) for x in vector]
                        self.CPU.update_register(reg1, result)
                elif var_type == "vector":
                    if reg1.startswith("V"):
                        vector1 = self.CPU.return_register(reg1)
                        vector2 = [self.CPU.return_memory(head + i) for i in range(buffer)]
                        if len(vector1) == len(vector2):
                            result = [x % y for x, y in zip(vector1, vector2)]
                            self.CPU.update_register(reg1, result)
                        else:
                            self.report_error(f"Vector size mismatch: {len(vector1)} != {len(vector2)}")
                    else:
                        self.report_error(
                            f"Cannot perform modulo on a vector variable with a non-vector register {reg1}")
                else:
                    self.report_error(f"Cannot perform modulo on register {reg1} with a {var_type} variable")
            else:
                if key.startswith("[") and key.endswith("]"):
                    try:
                        vector_literal = [float(x) for x in key[1:-1].split()]
                        if reg1.startswith("V"):
                            vector = self.CPU.return_register(reg1)
                            if len(vector) == len(vector_literal):
                                result = [x % y for x, y in zip(vector, vector_literal)]
                                self.CPU.update_register(reg1, result)
                            else:
                                self.report_error(f"Vector size mismatch: {len(vector)} != {len(vector_literal)}")
                        else:
                            self.report_error(
                                f"Cannot perform modulo on a vector literal with a non-vector register {reg1}")
                    except ValueError:
                        self.report_error(f"Invalid vector literal: {key}")
                else:
                    try:
                        operand = float(key)
                    except:
                        self.report_error(f"Invalid type for MOD operation. Got: {key}")
                    if operand == 0:
                        self.report_error("Modulo by zero")
                    if reg1.startswith("I"):
                        value = self.CPU.return_register(reg1)
                        if operand.is_integer():
                            self.CPU.update_register(reg1, value % int(operand))
                        else:
                            self.report_error(
                                f"Cannot perform modulo on an integer register {reg1} with a float literal")
                    elif reg1.startswith("FF"):
                        value = self.CPU.return_register(reg1)
                        self.CPU.update_register(reg1, value % operand)
                    elif reg1.startswith("V"):
                        vector = self.CPU.return_register(reg1)
                        result = [x % operand for x in vector]
                        self.CPU.update_register(reg1, result)
        else:
            self.report_error(f"Invalid register for MOD operation: {reg1}")

    def handle_store(self, reg, address):
        address = int(address)
        if reg in self.reg_names:
            value = self.CPU.return_register(reg)

            if isinstance(value, list) and reg.startswith("V"):
                self.CPU.update_memory(address, len(value))
                for i, v in enumerate(value):
                    self.CPU.update_memory(address + 1 + i, v)
            else:
                self.CPU.update_memory(address, value)
        else:
            self.report_error(f"Invalid register for STORE operation: {reg}")

    def handle_load_mem(self, reg, address):
        address = int(address)
        if reg.startswith("V"):
            length = self.CPU.return_memory(address)
            if not isinstance(length, int):
                self.report_error(f"Invalid vector length at address {address}")
                return
            value = [self.CPU.return_memory(address + 1 + i) for i in range(length)]
        else:
            value = self.CPU.return_memory(address)
        self.CPU.update_register(reg, value)

    def handle_print(self, key):
        if key in self.reg_names:
            self.cpu_executor.print(key)
            return
        try:
            head, buffer, var_type = self.variables[key]
            if var_type == "string":
                values = [chr(self.CPU.return_memory(head + i)) for i in range(buffer)]
                print("".join(values))
            elif var_type == "vector":
                values = [str(self.CPU.return_memory(head + i)) for i in range(buffer)]
                print(f"[{' '.join(values)}]")
            else:
                print(self.CPU.return_memory(head))

        except:
            print(key)

    def handle_print_ascii(self, reg):
        value = self.CPU.return_register(reg)
        print(chr(int(value)))

    def handle_jz(self, reg, pos):
        value = self.CPU.return_register(reg)
        if value == 0:
            if pos.isnumeric():
                self.instruction_index = int(pos) - 2
            elif pos in self.labels.keys():
                self.instruction_index = self.labels[pos]
            else:
                self.report_error(f"Invalid type for JZ operation. Got: {pos}")

    def handle_jnz(self, reg, pos):
        value = self.CPU.return_register(reg)
        if value != 0:
            if pos.isnumeric():
                self.instruction_index = int(pos) - 2
            elif pos in self.labels.keys():
                self.instruction_index = self.labels[pos]
            else:
                self.report_error(f"Invalid type for JNZ operation. Got: {pos}")

    def handle_jmp(self, pos):
        if pos.isnumeric():
            self.instruction_index = int(pos) - 2
        elif pos in self.labels.keys():
            self.instruction_index = self.labels[pos]
        else:
            self.report_error(f"Invalid type for JMP operation. Got: {pos}")

    def handle_halt(self, code):
        exit(int(code))

    def handle_input(self, key, text=""):
        value = input(text)
        if key in self.reg_names:
            if value.replace('.', '', 1).isdigit() and value.count('.') < 2:
                numeric_value = float(value)
                if key.startswith("I"):
                    if numeric_value.is_integer():
                        self.CPU.update_register(key, int(numeric_value))
                    else:
                        self.report_error(f"Cannot move float literal to integer register {key}")
                elif key.startswith("FF"):
                    self.CPU.update_register(key, numeric_value)
            else:
                self.report_error("Invalid type for INPUT operation. Got string when expecting number")
        else:
            if value.replace('.', '', 1).isdigit() and value.count('.') < 2:
                numeric_value = float(value)
                value = str(int(numeric_value)) if numeric_value.is_integer() else str(numeric_value)
            elif not value.isnumeric():
                value = '"' + value + '"'
            self.handle_set_var(key, value)

    def handle_set_var(self, name, data, buffer=None):
        memory_head = self.memory_index
        try:
            if data.replace('.', '', 1).isdigit() and data.count('.') < 2:
                numeric_value = float(data)
                if numeric_value.is_integer():
                    values = [int(numeric_value)]
                    var_type = "int"
                else:
                    values = [numeric_value]
                    var_type = "float"
            elif data.isnumeric():
                values = [int(data)]
                var_type = "int"
            elif data.startswith("[") and data.endswith("]"):
                tokens = data[1:-1].replace(",", " ").split()
                if not (1 <= len(tokens) <= 32):
                    self.report_error(f"Vector length must be between 1 and 32, got {len(tokens)}")
                values = []
                for token in tokens:
                    if token in self.reg_names:
                        token_val = self.CPU.return_register(token)
                        values.append(float(token_val))
                    elif token in self.variables:
                        t_head, t_buf, t_type = self.variables[token]
                        token_val = self.CPU.return_memory(t_head)
                        values.append(float(token_val))
                    else:
                        try:
                            token_val = float(token)
                            values.append(token_val)
                        except:
                            self.report_error(f"Invalid vector element: {token}")
                var_type = "vector"
            else:
                values = [ord(char) for char in data.replace('"', "")]
                var_type = "string"
            memory_buffer = len(values) if buffer is None else int(buffer)
            if len(values) > memory_buffer:
                self.report_error(f"Memory buffer overflow by {len(values) - memory_buffer} bytes")
            for i, value in enumerate(values):
                self.CPU.update_memory(memory_head + i, value)
            self.variables[name] = [memory_head, len(values), var_type]
        except Exception as e:
            self.report_error(str(e))

    def load_file(self):
        with open(self.file_path, 'r') as file:
            lines = file.readlines()
        cleaned_lines = []
        for line in lines:
            if '//' in line:
                line = line.split('//')[0]
            cleaned_lines.append(line)
        return "".join(cleaned_lines)