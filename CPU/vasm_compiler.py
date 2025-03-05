from CPU.instruction_registrar import InstructionRegistrar
from CPU.virtual_cpu import VirtualCPU


class Compiler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.CPU = VirtualCPU()
        self.asm = self.load_file().split(';')
        self.instruction_index = 0
        self.memory_index = 0
        self.stack_index = 0
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
            "PRINTF": self.handle_print_newlinw,
            "TEXT": self.handle_print_ascii,
            "JZ": self.handle_jz,
            "JNZ": self.handle_jnz,
            "JG": self.handle_jg,
            "JGE": self.handle_jge,
            "JL": self.handle_jl,
            "JLE": self.handle_jle,
            "JMP": self.handle_jmp,
            "HALT": self.handle_halt,
            "VAR": self.handle_set_var,
            "INPUT": self.handle_input,
            "PUSH": self.handle_push,
            "POP": self.handle_pop
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

    def parse_operand(self, operand):
        if '[' in operand and operand.endswith(']'):
            try:
                base = operand[:operand.index('[')]
                index_str = operand[operand.index('[') + 1: -1]
                if index_str in self.reg_names:
                    if index_str.startswith("V") or index_str.startswith("FF"):
                        self.report_error("Um what are you even trying to do?")
                    else:
                        index = self.CPU.return_register(index_str)
                elif index_str in self.variables:
                    head, buffer, var_type = self.variables[base]
                    if var_type == "vector" or var_type == "float":
                        self.report_error("Um what are you even trying to do?")
                    else:
                        index = self.CPU.return_memory(head)
                else:
                    index = int(index_str)
                return base, index
            except Exception:
                return operand, None
        return operand, None

    def handle_move(self, key, value):
        target_base, target_index = self.parse_operand(key)
        if target_base in self.reg_names:
            if target_index is not None and not target_base.startswith("V"):
                self.report_error(f"Cannot index non-vector register {target_base}")
                return
            try:
                numeric_value = float(value)
                if target_index is None:
                    if target_base.startswith("I") and numeric_value.is_integer():
                        self.cpu_executor.move(target_base, int(numeric_value))
                    elif target_base.startswith("FF"):
                        self.cpu_executor.move(target_base, numeric_value)
                    elif target_base.startswith("V"):
                        self.report_error(f"Cannot assign scalar to entire vector register {target_base}")
                    else:
                        self.report_error(f"Unknown register type for {target_base}")
                else:
                    vector = self.CPU.return_register(target_base)
                    if target_index < 0 or target_index >= len(vector):
                        self.report_error(f"Index {target_index} out of range for register {target_base}")
                        return
                    vector[target_index] = numeric_value
                    self.CPU.update_register(target_base, vector)
                return
            except ValueError:
                pass
            if value.startswith("[") and value.endswith("]"):
                if target_index is not None:
                    self.report_error(f"Cannot assign vector literal to a vector element {target_base}[{target_index}]")
                    return
                tokens = value[1:-1].replace(",", " ").split()
                if not (1 <= len(tokens) <= 32):
                    self.report_error(f"Vector length must be between 1 and 32, got {len(tokens)}")
                    return
                vector = []
                for token in tokens:
                    if token in self.reg_names:
                        reg_val = self.CPU.return_register(token)
                        try:
                            vector.append(float(reg_val))
                        except Exception:
                            self.report_error(f"Invalid conversion of register {token} value to float")
                            return
                    elif token in self.variables:
                        head, buf, typ = self.variables[token]
                        mem_val = self.CPU.return_memory(head)
                        vector.append(float(mem_val))
                    else:
                        try:
                            vector.append(float(token))
                        except Exception:
                            self.report_error(f"Invalid vector element: {token}")
                            return
                self.CPU.update_register(target_base, vector)
                return
            if ('[' in value and value.endswith(']')):
                src_base, src_index = self.parse_operand(value)
            else:
                src_base, src_index = value, None

            if src_base in self.reg_names or src_base in self.variables:
                if src_base in self.reg_names:
                    if src_index is None:
                        src_val = self.CPU.return_register(src_base)
                    else:
                        if not src_base.startswith("V"):
                            self.report_error(f"Cannot index non-vector register {src_base}")
                            return
                        vec = self.CPU.return_register(src_base)
                        if src_index < 0 or src_index >= len(vec):
                            self.report_error(f"Index {src_index} out of range for register {src_base}")
                            return
                        src_val = vec[src_index]
                else:
                    head, buf, typ = self.variables[src_base]
                    if src_index is None:
                        if typ == "vector":
                            src_val = [self.CPU.return_memory(head + i) for i in range(buf)]
                        else:
                            src_val = self.CPU.return_memory(head)
                    else:
                        if typ != "vector":
                            self.report_error(f"Cannot index non-vector variable {src_base}")
                            return
                        if src_index < 0 or src_index >= buf:
                            self.report_error(f"Index {src_index} out of range for variable {src_base}")
                            return
                        src_val = self.CPU.return_memory(head + src_index)
                if target_index is None:
                    if target_base.startswith("I"):
                        try:
                            num = float(src_val)
                            if num.is_integer():
                                self.cpu_executor.move(target_base, int(num))
                            else:
                                self.report_error(f"Type mismatch: expected integer, got {src_val}")
                            return
                        except Exception:
                            self.report_error(f"Invalid source value: {src_val}")
                            return
                    elif target_base.startswith("FF"):
                        try:
                            num = float(src_val)
                            self.cpu_executor.move(target_base, num)
                            return
                        except Exception:
                            self.report_error(f"Invalid source value: {src_val}")
                            return
                    elif target_base.startswith("V"):
                        if isinstance(src_val, list):
                            self.CPU.update_register(target_base, src_val)
                            return
                        else:
                            self.report_error(f"Expected vector, got scalar for register {target_base}")
                            return
                    else:
                        self.report_error(f"Unknown register type for {target_base}")
                        return
                else:
                    try:
                        num = float(src_val)
                    except Exception:
                        self.report_error(
                            f"Type mismatch: expected scalar for vector element assignment, got {src_val}")
                        return
                    vec = self.CPU.return_register(target_base)
                    if target_index < 0 or target_index >= len(vec):
                        self.report_error(f"Index {target_index} out of range for register {target_base}")
                        return
                    vec[target_index] = num
                    self.CPU.update_register(target_base, vec)
                    return
            self.report_error(f"Invalid value for MOVE operation: {value}")
            return
        elif target_base in self.variables:
            head, buffer, var_type = self.variables[target_base]
            if target_index is not None and var_type != "vector":
                self.report_error(f"Cannot index non-vector variable {target_base}")
                return

            try:
                numeric_value = float(value)
                if target_index is None:
                    if var_type == "int" and numeric_value.is_integer():
                        self.CPU.update_memory(head, int(numeric_value))
                    elif var_type == "float":
                        self.CPU.update_memory(head, numeric_value)
                    else:
                        self.report_error(f"Cannot move {numeric_value} to {target_base} due to type mismatch")
                    return
                else:
                    if target_index < 0 or target_index >= buffer:
                        self.report_error(f"Index {target_index} out of range for variable {target_base}")
                        return
                    self.CPU.update_memory(head + target_index, numeric_value)
                    return
            except ValueError:
                pass
            if value.startswith("[") and value.endswith("]"):
                if target_index is not None:
                    self.report_error(f"Cannot assign vector literal to a vector element {target_base}[{target_index}]")
                    return
                tokens = value[1:-1].replace(",", " ").split()
                if not (1 <= len(tokens) <= 32):
                    self.report_error(f"Vector length must be between 1 and 32, got {len(tokens)}")
                    return
                for i, token in enumerate(tokens):
                    if token in self.reg_names:
                        token_val = self.CPU.return_register(token)
                        try:
                            self.CPU.update_memory(head + i, float(token_val))
                        except Exception:
                            self.report_error(f"Invalid conversion of register {token} value to float")
                            return
                    elif token in self.variables:
                        t_head, t_buf, t_type = self.variables[token]
                        token_val = self.CPU.return_memory(t_head)
                        self.CPU.update_memory(head + i, float(token_val))
                    else:
                        try:
                            token_val = float(token)
                            self.CPU.update_memory(head + i, token_val)
                        except Exception:
                            self.report_error(f"Invalid vector element: {token}")
                            return
                self.variables[target_base] = [head, len(tokens), "vector"]
                return
            if ('[' in value and value.endswith(']')):
                src_base, src_index = self.parse_operand(value)
            else:
                src_base, src_index = value, None

            if src_base in self.reg_names or src_base in self.variables:
                if src_base in self.reg_names:
                    if src_index is None:
                        src_val = self.CPU.return_register(src_base)
                    else:
                        if not src_base.startswith("V"):
                            self.report_error(f"Cannot index non-vector register {src_base}")
                            return
                        vec = self.CPU.return_register(src_base)
                        if src_index < 0 or src_index >= len(vec):
                            self.report_error(f"Index {src_index} out of range for register {src_base}")
                            return
                        src_val = vec[src_index]
                else:
                    t_head, t_buf, t_type = self.variables[src_base]
                    if src_index is None:
                        if t_type == "vector":
                            src_val = [self.CPU.return_memory(t_head + i) for i in range(t_buf)]
                        else:
                            src_val = self.CPU.return_memory(t_head)
                    else:
                        if t_type != "vector":
                            self.report_error(f"Cannot index non-vector variable {src_base}")
                            return
                        if src_index < 0 or src_index >= t_buf:
                            self.report_error(f"Index {src_index} out of range for variable {src_base}")
                            return
                        src_val = self.CPU.return_memory(t_head + src_index)
                if target_index is None:
                    if var_type == "int":
                        try:
                            num = float(src_val)
                            if num.is_integer():
                                self.CPU.update_memory(head, int(num))
                            else:
                                self.report_error(f"Type mismatch: expected integer, got {src_val}")
                            return
                        except Exception:
                            self.report_error(f"Invalid source value: {src_val}")
                            return
                    elif var_type == "float":
                        try:
                            num = float(src_val)
                            self.CPU.update_memory(head, num)
                            return
                        except Exception:
                            self.report_error(f"Invalid source value: {src_val}")
                            return
                    elif var_type == "vector":
                        if isinstance(src_val, list):
                            for i, elem in enumerate(src_val):
                                self.CPU.update_memory(head + i, elem)
                            self.variables[target_base] = [head, len(src_val), "vector"]
                            return
                        else:
                            self.report_error(f"Expected vector, got scalar for variable {target_base}")
                            return
                    else:
                        self.report_error(f"Unknown variable type for {target_base}")
                        return
                else:
                    try:
                        num = float(src_val)
                    except Exception:
                        self.report_error(
                            f"Type mismatch: expected scalar for vector element assignment, got {src_val}")
                        return
                    if target_index < 0 or target_index >= buffer:
                        self.report_error(f"Index {target_index} out of range for variable {target_base}")
                        return
                    self.CPU.update_memory(head + target_index, num)
                    return
            values = [ord(char) for char in value.replace('"', "")]
            if len(values) > buffer:
                self.report_error(f"Memory buffer overflow by {len(values) - buffer} bytes")
                return
            for i, v in enumerate(values):
                self.CPU.update_memory(head + i, v)
            self.variables[target_base] = [head, buffer, "string"]
            return
        else:
            self.report_error(f"Invalid key for MOVE operation: {key}")
            return

    def handle_add(self, reg1, key):
        rbase, rindex = self.parse_operand(reg1)
        kbase, kindex = self.parse_operand(key)
        if rbase in self.reg_names:
            if kbase in self.reg_names:
                if kindex is not None:
                    vec2 = self.CPU.return_register(kbase)
                    if kindex < 0 or kindex >= len(vec2):
                        self.report_error("Index out of range for " + kbase)
                        return
                    op = vec2[kindex]
                else:
                    op = self.CPU.return_register(kbase)
            elif kbase in self.variables:
                head, buf, var_type = self.variables[kbase]
                if var_type in ("int", "float"):
                    op = float(self.CPU.return_memory(head))
                elif var_type == "vector":
                    if kindex is not None:
                        if kindex < 0 or kindex >= buf:
                            self.report_error("Index out of range for variable " + kbase)
                            return
                        op = self.CPU.return_memory(head + kindex)
                    else:
                        op = [self.CPU.return_memory(head + i) for i in range(buf)]
                else:
                    self.report_error("Cannot add a " + var_type + " variable to register " + rbase)
                    return
            else:
                if key.startswith("[") and key.endswith("]"):
                    try:
                        tokens = key[1:-1].split()
                        op = [float(x) for x in tokens]
                    except:
                        self.report_error("Invalid vector literal: " + key)
                        return
                else:
                    try:
                        op = float(key)
                    except:
                        self.report_error("Invalid type for ADD operation. Got: " + key)
                        return
            if rindex is None:
                if rbase.startswith("I"):
                    if isinstance(op, list):
                        self.report_error("Cannot add vector to integer register " + rbase)
                        return
                    val = self.CPU.return_register(rbase)
                    if float(op).is_integer():
                        self.CPU.update_register(rbase, val + int(op))
                    else:
                        self.report_error("Cannot add float to integer register " + rbase)
                        return
                elif rbase.startswith("FF"):
                    if isinstance(op, list):
                        self.report_error("Cannot add vector to float register " + rbase)
                        return
                    val = self.CPU.return_register(rbase)
                    self.CPU.update_register(rbase, val + float(op))
                elif rbase.startswith("V"):
                    vec = self.CPU.return_register(rbase)
                    if isinstance(op, list):
                        if len(vec) != len(op):
                            self.report_error("Vector size mismatch: " + str(len(vec)) + " != " + str(len(op)))
                            return
                        self.CPU.update_register(rbase, [x + y for x, y in zip(vec, op)])
                    else:
                        self.CPU.update_register(rbase, [x + op for x in vec])
            else:
                if not rbase.startswith("V"):
                    self.report_error("Cannot index non-vector register " + rbase)
                    return
                vec = self.CPU.return_register(rbase)
                if rindex < 0 or rindex >= len(vec):
                    self.report_error("Index out of range for register " + rbase)
                    return
                elem = vec[rindex]
                if isinstance(op, list):
                    self.report_error("Cannot add vector literal to vector element")
                    return
                if rbase.startswith("I"):
                    if float(op).is_integer():
                        vec[rindex] = elem + int(op)
                    else:
                        self.report_error("Cannot add float to integer register element " + rbase)
                        return
                else:
                    vec[rindex] = elem + float(op)
                self.CPU.update_register(rbase, vec)
        else:
            self.report_error("Invalid register for ADD operation: " + reg1)

    def handle_sub(self, reg1, key):
        rbase, rindex = self.parse_operand(reg1)
        kbase, kindex = self.parse_operand(key)
        if rbase in self.reg_names:
            if kbase in self.reg_names:
                if kindex is not None:
                    vec2 = self.CPU.return_register(kbase)
                    if kindex < 0 or kindex >= len(vec2):
                        self.report_error("Index out of range for " + kbase)
                        return
                    op = vec2[kindex]
                else:
                    op = self.CPU.return_register(kbase)
            elif kbase in self.variables:
                head, buf, var_type = self.variables[kbase]
                if var_type in ("int", "float"):
                    op = float(self.CPU.return_memory(head))
                elif var_type == "vector":
                    if kindex is not None:
                        if kindex < 0 or kindex >= buf:
                            self.report_error("Index out of range for variable " + kbase)
                            return
                        op = self.CPU.return_memory(head + kindex)
                    else:
                        op = [self.CPU.return_memory(head + i) for i in range(buf)]
                else:
                    self.report_error("Cannot subtract a " + var_type + " variable from register " + rbase)
                    return
            else:
                if key.startswith("[") and key.endswith("]"):
                    try:
                        tokens = key[1:-1].split()
                        op = [float(x) for x in tokens]
                    except:
                        self.report_error("Invalid vector literal: " + key)
                        return
                else:
                    try:
                        op = float(key)
                    except:
                        self.report_error("Invalid type for SUB operation. Got: " + key)
                        return
            if rindex is None:
                if rbase.startswith("I"):
                    if isinstance(op, list):
                        self.report_error("Cannot subtract vector from integer register " + rbase)
                        return
                    val = self.CPU.return_register(rbase)
                    if float(op).is_integer():
                        self.CPU.update_register(rbase, val - int(op))
                    else:
                        self.report_error("Cannot subtract float from integer register " + rbase)
                        return
                elif rbase.startswith("FF"):
                    if isinstance(op, list):
                        self.report_error("Cannot subtract vector from float register " + rbase)
                        return
                    val = self.CPU.return_register(rbase)
                    self.CPU.update_register(rbase, val - float(op))
                elif rbase.startswith("V"):
                    vec = self.CPU.return_register(rbase)
                    if isinstance(op, list):
                        if len(vec) != len(op):
                            self.report_error("Vector size mismatch: " + str(len(vec)) + " != " + str(len(op)))
                            return
                        self.CPU.update_register(rbase, [x - y for x, y in zip(vec, op)])
                    else:
                        self.CPU.update_register(rbase, [x - op for x in vec])
            else:
                if not rbase.startswith("V"):
                    self.report_error("Cannot index non-vector register " + rbase)
                    return
                vec = self.CPU.return_register(rbase)
                if rindex < 0 or rindex >= len(vec):
                    self.report_error("Index out of range for register " + rbase)
                    return
                elem = vec[rindex]
                if isinstance(op, list):
                    self.report_error("Cannot subtract vector literal from vector element")
                    return
                if rbase.startswith("I"):
                    if float(op).is_integer():
                        vec[rindex] = elem - int(op)
                    else:
                        self.report_error("Cannot subtract float from integer register element " + rbase)
                        return
                else:
                    vec[rindex] = elem - float(op)
                self.CPU.update_register(rbase, vec)
        else:
            self.report_error("Invalid register for SUB operation: " + reg1)

    def handle_mul(self, reg1, key):
        rbase, rindex = self.parse_operand(reg1)
        kbase, kindex = self.parse_operand(key)
        if rbase in self.reg_names:
            if kbase in self.reg_names:
                if kindex is not None:
                    vec2 = self.CPU.return_register(kbase)
                    if kindex < 0 or kindex >= len(vec2):
                        self.report_error("Index out of range for " + kbase)
                        return
                    op = vec2[kindex]
                else:
                    op = self.CPU.return_register(kbase)
            elif kbase in self.variables:
                head, buf, var_type = self.variables[kbase]
                if var_type in ("int", "float"):
                    op = float(self.CPU.return_memory(head))
                elif var_type == "vector":
                    if kindex is not None:
                        if kindex < 0 or kindex >= buf:
                            self.report_error("Index out of range for variable " + kbase)
                            return
                        op = self.CPU.return_memory(head + kindex)
                    else:
                        op = [self.CPU.return_memory(head + i) for i in range(buf)]
                else:
                    self.report_error("Cannot multiply a " + var_type + " variable with register " + rbase)
                    return
            else:
                if key.startswith("[") and key.endswith("]"):
                    try:
                        tokens = key[1:-1].split()
                        op = [float(x) for x in tokens]
                    except:
                        self.report_error("Invalid vector literal: " + key)
                        return
                else:
                    try:
                        op = float(key)
                    except:
                        self.report_error("Invalid type for MUL operation. Got: " + key)
                        return
            if rindex is None:
                if rbase.startswith("I"):
                    if isinstance(op, list):
                        self.report_error("Cannot multiply integer register " + rbase + " with vector")
                        return
                    val = self.CPU.return_register(rbase)
                    if float(op).is_integer():
                        self.CPU.update_register(rbase, val * int(op))
                    else:
                        self.report_error("Cannot multiply integer register " + rbase + " with float")
                        return
                elif rbase.startswith("FF"):
                    if isinstance(op, list):
                        self.report_error("Cannot multiply float register " + rbase + " with vector")
                        return
                    val = self.CPU.return_register(rbase)
                    self.CPU.update_register(rbase, val * float(op))
                elif rbase.startswith("V"):
                    vec = self.CPU.return_register(rbase)
                    if isinstance(op, list):
                        if len(vec) != len(op):
                            self.report_error("Vector size mismatch: " + str(len(vec)) + " != " + str(len(op)))
                            return
                        self.CPU.update_register(rbase, [x * y for x, y in zip(vec, op)])
                    else:
                        self.CPU.update_register(rbase, [x * op for x in vec])
            else:
                if not rbase.startswith("V"):
                    self.report_error("Cannot index non-vector register " + rbase)
                    return
                vec = self.CPU.return_register(rbase)
                if rindex < 0 or rindex >= len(vec):
                    self.report_error("Index out of range for register " + rbase)
                    return
                elem = vec[rindex]
                if isinstance(op, list):
                    self.report_error("Cannot multiply vector literal with vector element")
                    return
                if rbase.startswith("I"):
                    if float(op).is_integer():
                        vec[rindex] = elem * int(op)
                    else:
                        self.report_error("Cannot multiply integer register element " + rbase + " with float")
                        return
                else:
                    vec[rindex] = elem * float(op)
                self.CPU.update_register(rbase, vec)
        else:
            self.report_error("Invalid register for MUL operation: " + reg1)

    def handle_div(self, reg1, key):
        rbase, rindex = self.parse_operand(reg1)
        kbase, kindex = self.parse_operand(key)
        if rbase in self.reg_names:
            if kbase in self.reg_names:
                if kindex is not None:
                    vec2 = self.CPU.return_register(kbase)
                    if kindex < 0 or kindex >= len(vec2):
                        self.report_error("Index out of range for " + kbase)
                        return
                    op = vec2[kindex]
                else:
                    op = self.CPU.return_register(kbase)
            elif kbase in self.variables:
                head, buf, var_type = self.variables[kbase]
                if var_type in ("int", "float"):
                    op = float(self.CPU.return_memory(head))
                elif var_type == "vector":
                    if kindex is not None:
                        if kindex < 0 or kindex >= buf:
                            self.report_error("Index out of range for variable " + kbase)
                            return
                        op = self.CPU.return_memory(head + kindex)
                    else:
                        op = [self.CPU.return_memory(head + i) for i in range(buf)]
                else:
                    self.report_error("Cannot divide register " + rbase + " by a " + var_type + " variable")
                    return
            else:
                if key.startswith("[") and key.endswith("]"):
                    try:
                        tokens = key[1:-1].split()
                        op = [float(x) for x in tokens]
                    except:
                        self.report_error("Invalid vector literal: " + key)
                        return
                else:
                    try:
                        op = float(key)
                    except:
                        self.report_error("Invalid type for DIV operation. Got: " + key)
                        return
            if (isinstance(op, (int, float)) and float(op) == 0) or (
                    isinstance(op, list) and any(float(x) == 0 for x in op)):
                self.report_error("Division by zero")
                return
            if rindex is None:
                if rbase.startswith("I"):
                    if isinstance(op, list):
                        self.report_error("Cannot divide integer register " + rbase + " by vector")
                        return
                    val = self.CPU.return_register(rbase)
                    if float(op).is_integer():
                        self.CPU.update_register(rbase, val // int(op))
                    else:
                        self.report_error("Cannot divide integer register " + rbase + " by float")
                        return
                elif rbase.startswith("FF"):
                    if isinstance(op, list):
                        self.report_error("Cannot divide float register " + rbase + " by vector")
                        return
                    val = self.CPU.return_register(rbase)
                    self.CPU.update_register(rbase, val / float(op))
                elif rbase.startswith("V"):
                    vec = self.CPU.return_register(rbase)
                    if isinstance(op, list):
                        if len(vec) != len(op):
                            self.report_error("Vector size mismatch: " + str(len(vec)) + " != " + str(len(op)))
                            return
                        result = [x / y if float(y) != 0 else 0 for x, y in zip(vec, op)]
                        self.CPU.update_register(rbase, result)
                    else:
                        self.CPU.update_register(rbase, [x / float(op) if float(op) != 0 else 0 for x in vec])
            else:
                if not rbase.startswith("V"):
                    self.report_error("Cannot index non-vector register " + rbase)
                    return
                vec = self.CPU.return_register(rbase)
                if rindex < 0 or rindex >= len(vec):
                    self.report_error("Index out of range for register " + rbase)
                    return
                elem = vec[rindex]
                if isinstance(op, list):
                    self.report_error("Cannot divide by vector literal for a single element")
                    return
                if float(op) == 0:
                    self.report_error("Division by zero")
                    return
                if rbase.startswith("I"):
                    if float(op).is_integer():
                        vec[rindex] = elem // int(op)
                    else:
                        self.report_error("Cannot divide integer register element " + rbase + " by float")
                        return
                else:
                    vec[rindex] = elem / float(op)
                self.CPU.update_register(rbase, vec)
        else:
            self.report_error("Invalid register for DIV operation: " + reg1)

    def handle_mod(self, reg1, key):
        rbase, rindex = self.parse_operand(reg1)
        kbase, kindex = self.parse_operand(key)
        if rbase in self.reg_names:
            if kbase in self.reg_names:
                if kindex is not None:
                    vec2 = self.CPU.return_register(kbase)
                    if kindex < 0 or kindex >= len(vec2):
                        self.report_error("Index out of range for " + kbase)
                        return
                    op = vec2[kindex]
                else:
                    op = self.CPU.return_register(kbase)
            elif kbase in self.variables:
                head, buf, var_type = self.variables[kbase]
                if var_type in ("int", "float"):
                    op = float(self.CPU.return_memory(head))
                elif var_type == "vector":
                    if kindex is not None:
                        if kindex < 0 or kindex >= buf:
                            self.report_error("Index out of range for variable " + kbase)
                            return
                        op = self.CPU.return_memory(head + kindex)
                    else:
                        op = [self.CPU.return_memory(head + i) for i in range(buf)]
                else:
                    self.report_error(
                        "Cannot perform modulo on register " + rbase + " with a " + var_type + " variable")
                    return
            else:
                if key.startswith("[") and key.endswith("]"):
                    try:
                        tokens = key[1:-1].split()
                        op = [float(x) for x in tokens]
                    except:
                        self.report_error("Invalid vector literal: " + key)
                        return
                else:
                    try:
                        op = float(key)
                    except:
                        self.report_error("Invalid type for MOD operation. Got: " + key)
                        return
            if (isinstance(op, (int, float)) and float(op) == 0) or (
                    isinstance(op, list) and any(float(x) == 0 for x in op)):
                self.report_error("Modulo by zero")
                return
            if rindex is None:
                if rbase.startswith("I"):
                    if isinstance(op, list):
                        self.report_error("Cannot perform modulo on integer register " + rbase + " with vector")
                        return
                    val = self.CPU.return_register(rbase)
                    if float(op).is_integer():
                        self.CPU.update_register(rbase, val % int(op))
                    else:
                        self.report_error("Cannot perform modulo on integer register " + rbase + " with float")
                        return
                elif rbase.startswith("FF"):
                    if isinstance(op, list):
                        self.report_error("Cannot perform modulo on float register " + rbase + " with vector")
                        return
                    val = self.CPU.return_register(rbase)
                    self.CPU.update_register(rbase, val % float(op))
                elif rbase.startswith("V"):
                    vec = self.CPU.return_register(rbase)
                    if isinstance(op, list):
                        if len(vec) != len(op):
                            self.report_error("Vector size mismatch: " + str(len(vec)) + " != " + str(len(op)))
                            return
                        self.CPU.update_register(rbase, [x % y for x, y in zip(vec, op)])
                    else:
                        self.CPU.update_register(rbase, [x % float(op) for x in vec])
            else:
                if not rbase.startswith("V"):
                    self.report_error("Cannot index non-vector register " + rbase)
                    return
                vec = self.CPU.return_register(rbase)
                if rindex < 0 or rindex >= len(vec):
                    self.report_error("Index out of range for register " + rbase)
                    return
                elem = vec[rindex]
                if isinstance(op, list):
                    self.report_error("Cannot perform modulo with vector literal for a single element")
                    return
                if float(op) == 0:
                    self.report_error("Modulo by zero")
                    return
                if rbase.startswith("I"):
                    if float(op).is_integer():
                        vec[rindex] = elem % int(op)
                    else:
                        self.report_error("Cannot perform modulo on integer register element " + rbase + " with float")
                        return
                else:
                    vec[rindex] = elem % float(op)
                self.CPU.update_register(rbase, vec)
        else:
            self.report_error("Invalid register for MOD operation: " + reg1)

    def handle_store(self, reg, address):
        address = int(address)
        base, idx = self.parse_operand(reg)
        if base in self.reg_names:
            value = self.CPU.return_register(base)
            if base.startswith("V"):
                if isinstance(value, list):
                    if idx is None:
                        self.CPU.update_memory(address, len(value))
                        for i, v in enumerate(value):
                            self.CPU.update_memory(address + 1 + i, v)
                    else:
                        if idx < 0 or idx >= len(value):
                            self.report_error(
                                "STORE operation error: index " + str(idx) + " out of range for register " + base + ".")
                            return
                        self.CPU.update_memory(address, value[idx])
                else:
                    self.report_error("STORE operation error: register " + base + " is not a vector as expected.")
            else:
                if idx is not None:
                    self.report_error("STORE operation error: scalar register " + base + " cannot be indexed.")
                    return
                self.CPU.update_memory(address, value)
        else:
            self.report_error("STORE operation error: invalid register " + reg + ".")

    def handle_load_mem(self, reg, address):
        address = int(address)
        base, idx = self.parse_operand(reg)
        if base in self.reg_names:
            if base.startswith("V"):
                if idx is None:
                    length = self.CPU.return_memory(address)
                    if not isinstance(length, int):
                        self.report_error(
                            "LOAD_MEM operation error: invalid vector length at memory address " + str(address) + ".")
                        return
                    value = [self.CPU.return_memory(address + 1 + i) for i in range(length)]
                    self.CPU.update_register(base, value)
                else:
                    value = self.CPU.return_memory(address)
                    vec = self.CPU.return_register(base)
                    if not isinstance(vec, list):
                        self.report_error("LOAD_MEM operation error: register " + base + " is expected to be a vector.")
                        return
                    if idx < 0 or idx >= len(vec):
                        self.report_error(
                            "LOAD_MEM operation error: index " + str(idx) + " out of range for register " + base + ".")
                        return
                    vec[idx] = value
                    self.CPU.update_register(base, vec)
            else:
                if idx is not None:
                    self.report_error("LOAD_MEM operation error: scalar register " + base + " cannot be indexed.")
                    return
                value = self.CPU.return_memory(address)
                self.CPU.update_register(base, value)
        else:
            self.report_error("LOAD_MEM operation error: invalid register " + reg + ".")

    def handle_print(self, key, end=""):
        base, index = self.parse_operand(key)
        if base in self.reg_names:
            if base.startswith("V") and index is not None:
                vec = self.CPU.return_register(base)
                if index < 0 or index >= len(vec):
                    self.report_error("Index " + str(index) + " out of range for register " + base)
                    return
                print(vec[index], end=end)
            else:
                self.cpu_executor.print(base,end)
            return
        try:
            head, buffer, var_type = self.variables[base]
            if var_type == "string":
                if index is not None:
                    if index < 0 or index >= buffer:
                        self.report_error("Index " + str(index) + " out of range for variable " + base)
                        return
                    print(chr(self.CPU.return_memory(head + index)),end=end)
                else:
                    values = [chr(self.CPU.return_memory(head + i)) for i in range(buffer)]
                    print("".join(values),end=end)
            elif var_type == "vector":
                if index is not None:
                    if index < 0 or index >= buffer:
                        self.report_error("Index " + str(index) + " out of range for vector variable " + base)
                        return
                    print(self.CPU.return_memory(head + index),end=end)
                else:
                    values = [str(self.CPU.return_memory(head + i)) for i in range(buffer)]
                    print(f"[{' '.join(values)}]",end=end)
            else:
                if index is not None:
                    self.report_error("Scalar variable " + base + " cannot be indexed")
                else:
                    print(self.CPU.return_memory(head),end=end)
        except:
            print(key,end=end)

    def handle_print_newlinw(self, key):
        self.handle_print(key, end="\n")

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

    def handle_jg(self, reg, pos):
        value = self.CPU.return_register(reg)
        if value > 0:
            if pos.isnumeric():
                self.instruction_index = int(pos) - 2
            elif pos in self.labels.keys():
                self.instruction_index = self.labels[pos]
            else:
                self.report_error(f"Invalid type for JG operation. Got: {pos}")

    def handle_jl(self, reg, pos):
        value = self.CPU.return_register(reg)
        if value < 0:
            if pos.isnumeric():
                self.instruction_index = int(pos) - 2
            elif pos in self.labels.keys():
                self.instruction_index = self.labels[pos]
            else:
                self.report_error(f"Invalid type for JL operation. Got: {pos}")

    def handle_jge(self, reg, pos):
        value = self.CPU.return_register(reg)
        if value >= 0:
            if pos.isnumeric():
                self.instruction_index = int(pos) - 2
            elif pos in self.labels.keys():
                self.instruction_index = self.labels[pos]
            else:
                self.report_error(f"Invalid type for JGE operation. Got: {pos}")

    def handle_jle(self, reg, pos):
        value = self.CPU.return_register(reg)
        if value <= 0:
            if pos.isnumeric():
                self.instruction_index = int(pos) - 2
            elif pos in self.labels.keys():
                self.instruction_index = self.labels[pos]
            else:
                self.report_error(f"Invalid type for JLE operation. Got: {pos}")

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
            self.memory_index += len(values)
        except Exception as e:
            self.report_error(str(e))

    def handle_push(self, key):
        base, index = self.parse_operand(key)
        if base in self.reg_names:
            if base.startswith("V"):
                if index is None:
                    self.report_error("Cannot push entire vector register " + base + " to stack; specify an index.")
                    return
                else:
                    vec = self.CPU.return_register(base)
                    if index < 0 or index >= len(vec):
                        self.report_error("Index " + str(index) + " out of range for register " + base + ".")
                        return
                    value = vec[index]
            else:
                if index is not None:
                    self.report_error("Register " + base + " is scalar and cannot be indexed.")
                    return
                value = self.CPU.return_register(base)
        elif base in self.variables:
            head, buffer, var_type = self.variables[base]
            if var_type == "vector":
                if index is None:
                    self.report_error("Cannot push entire vector variable " + base + " to stack; specify an index.")
                    return
                else:
                    if index < 0 or index >= buffer:
                        self.report_error("Index " + str(index) + " out of range for variable " + base + ".")
                        return
                    value = self.CPU.return_memory(head + index)
            else:
                if index is not None:
                    self.report_error("Variable " + base + " is scalar and cannot be indexed.")
                    return
                value = self.CPU.return_memory(head)
        else:
            self.report_error("Invalid key for PUSH operation: " + key)
            return
        self.CPU.call_stack[self.stack_index] = value
        self.stack_index += 1

    def handle_pop(self, key):
        if self.stack_index <= 0:
            self.report_error("Stack underflow: no values to pop.")
            return
        self.stack_index -= 1
        value = self.CPU.call_stack[self.stack_index]
        base, index = self.parse_operand(key)
        if base in self.reg_names:
            if base.startswith("V"):
                if index is None:
                    self.report_error("Cannot pop to an entire vector register " + base + "; specify an index.")
                    return
                else:
                    vec = self.CPU.return_register(base)
                    if index < 0 or index >= len(vec):
                        self.report_error("Index " + str(index) + " out of range for register " + base + ".")
                        return
                    vec[index] = value
                    self.CPU.update_register(base, vec)
            else:
                if index is not None:
                    self.report_error("Register " + base + " is scalar and cannot be indexed.")
                    return
                self.CPU.update_register(base, value)
        elif base in self.variables:
            head, buffer, var_type = self.variables[base]
            if var_type == "vector":
                if index is None:
                    self.report_error("Cannot pop to an entire vector variable " + base + "; specify an index.")
                    return
                else:
                    if index < 0 or index >= buffer:
                        self.report_error("Index " + str(index) + " out of range for variable " + base + ".")
                        return
                    self.CPU.update_memory(head + index, value)
                    if float(value).is_integer():
                        new_type = "int"
                    else:
                        new_type = "float"
                    self.variables[base] = [head, buffer, new_type]
            else:
                if index is not None:
                    self.report_error("Variable " + base + " is scalar and cannot be indexed.")
                    return
                self.CPU.memory[head] = value
                if float(value).is_integer():
                    new_type = "int"
                else:
                    new_type = "float"
                self.variables[base] = [head, buffer, new_type]
        else:
            self.report_error("Invalid key for POP operation: " + key)

    def load_file(self):
        with open(self.file_path, 'r') as file:
            lines = file.readlines()
        cleaned_lines = []
        for line in lines:
            if '//' in line:
                line = line.split('//')[0]
            cleaned_lines.append(line)
        return "".join(cleaned_lines)
