
# Virtual CPU Emulator  
  
A Virtual CPU Emulator that executes assembly-like instructions, supports vector operations, and manages memory efficiently. It allows mathematical computations, memory storage, and vectorized arithmetic.  
  
## Features  
- **Automatic Memory Allocation**: Variables get automatically allocated along with there type.
- **Function Support**: VASM allows easy functional programming practices.
- **Native Vector Support**: Vectors are supported natively with lots of functionality.
- **Variable Reassignment** : Variables can be reallocated after initial declaration.
- **Easy Machine Code**: VASM is very easy and intuitive to work with.
- **Error Handling**: Built in debugger with very direct error handling.
- **Floating Number Support**: Floating point arithmetic is natively supported. 
-  **Extensible**: Easily extendable to support additional instructions or features.
## Specs
- **32-bit number processing.**
- **18 registers, 6 integer, 6 floating point, 6 vector.**
- **1 kilobyte of memory.**
## VASM Docs
### Valid Operators:
| Operator | Description                                                      |
| -------- | ---------------------------------------------------------------- |
| **MOVE**     | Move a value into a register or a variable.                      |
| **ADD**      | Adds a number to the specified register.                         |
| **SUB**      | Subtracts a number from the specified register.                  |
| **MUL**      | Multiplies a number from the specified register.                 |
| **DIV**      | Divides a number from the specified register.                    |
| **MOD**      | Sets the specified register to the remainder after division.     |
| **STORE**    | Stores the specified register into memory.                       |
| **LOADM**    | Loads a value from memory into the specified register.           |
| **PRINT**    | Prints a specified register, variable, or whatever is passed.    |
| **TEXT**     | Prints the ascii value of an int (soon to be deprecated).        |
| **JZ**       | Jumpts to a line or lable if the specified register is zero.     |
| **JNZ**      | Jumpts to a line or lable if the specified register is not zero. |
| **JMP**      | Jumpts to a line or lable.                                       |
| **HALT**     | Stops the program.                                               |
| **VAR**      | Initializes a variable.                                          |
| **INPUT**    | Takes an input and stores it in specified register or variable.  |
| **DEF**      | Defines a Function.                                              |
| **CALL**      | Calls a Function.                                              |
---
### Parameters
| Operator  | Parameter|
| --------- | ------------------------------------ |
| **MOVE**  | <VAR/REG>,<VAR/REG/INT/FLOAT/VECTOR> |
| **ADD**   | <​REG>,<VAR/REG/INT/FLOAT/VECTOR>     |
| **SUB**   | <​REG>,<VAR/REG/INT/FLOAT/VECTOR>     |
| **MUL**   | <​REG>,<VAR/REG/INT/FLOAT/VECTOR>     |
| **DIV**   | <​REG>,<VAR/REG/INT/FLOAT/VECTOR>     |
| **MOD**   | <​REG>,<VAR/REG/INT/FLOAT/VECTOR>     |
| **STORE** | <RE​G>,<I​NT>                          |
| **LOADM** | <RE​G>,<IN​T>                          |
| **PRINT** | <VAR/REG/ANY>                        |
| **TEXT**  | <REG/INT>                            |
| **JZ**    | <​REG>,<LABEL/INT>                    |
| **JNZ**   | <RE​G>,<LABEL/INT>                    |
| **JMP**   | <LABEL/INT>                          |
| **HALT**  | <IN​T>                                |
| **VAR**   | <STI​NG>,<STRING/INT/FLOAT/VECTOR>    |
| **INPUT** | <VAR/REG>,<STR​ING>                   |
| **DEF**   | <ST​RING>                             |
| **CALL**   | <​FUNCTION>                             |
### Types:
- **Integer** - Defined in the I1-I6 registers.
-  **Float** - Defined in the FF1-FF6 registers.
-  **Vector** - Defined in the V1-V6 registers.
### Functions and Labels:
- **Functions:**
	To declare a function use the **DEF** keyword followed a name and a colon  ie `DEF MyFunction:`. At the end of a function always add the **RETURN;** keyword. To call a function use the **CALL** operator followed by the function name.
- **Labels:**
	Labels are used to jump back to a specific part of your code, unlike functions they will not be skipped during execution. To create a label put your label names followed by an colon ie `MyLabel:`  and in a jmp/jz/ect operation put the label name ` JMP MyLabel`.

### General Syntax:
- All lines must end with **;**.
- Declare vectors as [ n n1 n2 ..] using a space to sperate values, you can use variables and registers as values so a vector like [ 3.3 4 FF3 variable 4.2] is valid.
- To add a comment use //
- You can not add floats to integer registers.
-   The value you want to modify always the first argument, ie **MOVE I1,3** and **ADD I1,I3** I1 is the register being modified for both.
- To separate arguments use **,** however don't add any spaces.
