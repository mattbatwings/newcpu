from common import *

# possible states
STATES = {
          'HLT':1,  # Halted state
          'ACT':0,  # Active state
         }

# Operands
# Format : '<label>':[<position>, <bit length>, <1: signed, 0: unsigned>,
#                     "<full name>"]
OPS     = {
           'First'     : [8,  4, 0, "first register"], # First register
           'A'         : [4,  4, 0, "register A"],     # Register A
           'B'         : [0,  4, 0, "register B"],     # Register B
           'Immediate' : [0,  8, 1, "immediate"],      # Immediate
           'Condition' : [10, 2, 0, "condition"],      # Condition
           'Offset'    : [0,  4, 1, "offset"],         # Offset
           'Opcode'    : [12, 4, 0, "opcode"],         # Opcode
           'Mem'       : [0, 10, 0, "memory address"], # Memory address
          }

class batpu_v2:
    def __init__(self,
                 word_size=8,  progmem_word_size=16,
                 reg=4, mem=8, progmem=10,  
                 pc_start=0):
        # each register is 1 byte
        # each memory location holds 1 byte
        # each program memory location holds 2 bytes
        # defaults:
        #  16 registers
        #  256 memory locations (256 bytes, 16 used as memory-mapped ports so
        #                        240 usable bytes)
        #  1024 program memory locations (1024 instructions, 2 bytes per
        #                                 instruction, 2048 bytes)

        # 0-initialize everything
        self.REGISTERS= [0] * (1 << reg)     # registers
        self.MEMORY   = [0] * (1 << mem)     # memory
        self.PROGMEM  = [0] * (1 << progmem) # program memory
        self.STACK    = []                   # stack

        # word size (effects register and memory sizes)
        self.WORD_SIZE = word_size
        # program memory word size (specific to program memory)
        self.PROGMEM_WORD_SIZE = progmem_word_size

        # length of program memory addresses
        self.PROGMEM_ADDRESS_LENGTH = progmem
        # length of memory addresses
        self.MEMORY_ADDRESS_LENGTH  = mem

        # FLAGS['Z'] = Zero, FLAGS['C'] = Carry
        self.FLAGS    = {
                         'Z':0,
                         'C':0,
                        }
        # Program Counter initialized to pc_start
        self.PC       = pc_start
        # start active
        self.state    = STATES['ACT']

        self.OPERANDS    = {}
        for key in OPS:
            self.OPERANDS[key] = 0

        self.OPCODES = [self.NOP,
                        self.HLT,
                        self.ADD,
                        self.SUB,
                        self.NOR,
                        self.AND,
                        self.XOR,
                        self.RSH,
                        self.LDI,
                        self.ADI,
                        self.JMP,
                        self.BRH,
                        self.CAL,
                        self.RET,
                        self.LOD,
                        self.STR,]

    def load_program(self, machinecode_file):
        # load program
        file_handler = open(machinecode_file, 'r')
        program = file_handler.readlines()
        file_handler.close()
        # flash ROM
        for idx in range(len(self.PROGMEM)):
            self.PROGMEM[idx] = 0

        for idx in range(len(program)):
            try:
                current_instruction = int(program[idx], 2)
                if(current_instruction >= (1 << self.PROGMEM_WORD_SIZE)):
                    raise ValueError
                self.PROGMEM[idx] = current_instruction
            except ValueError:
                fatal_error("simulator.py", f"{machinecode_file}:{idx + 1}: Bad instruction.")

    def read_reg(self, idx):
        try:
            return self.REGISTERS[idx]
        except IndexError:
            self.coredump("Processor attempted to read from illegal register. (r%d)" % (idx))

    def write_reg(self, idx, value):
        try:
            if(idx == 0): return
            self.REGISTERS[idx] = value & ((1 << self.WORD_SIZE) - 1)
        except IndexError:
            self.coredump("Processor attempted to write to illegal register. (r%d)" % (idx))

    def read_memory(self, idx, offset=0):
        try:
            return self.MEMORY[idx + offset]
        except IndexError:
            self.coredump("Processor attempted to read from illegal memory location. (%d %+d)" % (idx, offset))

    def write_memory(self, idx, value, offset=0):
        try:
            self.MEMORY[idx + offset] = value & ((1 << self.WORD_SIZE) - 1)
        except IndexError:
            self.coredump("Processor attempted to write to illegal memory location. (%d %+d)" % (idx, offset))

    def read_progmem(self, idx):
        try:
            return self.PROGMEM[idx]
        except IndexError:
            self.coredump(f"Processor attempted to read from illegal program memory location. ({idx})")
    # no write function. what? It's a ROM

    def push_stack(self, value):
        self.STACK.append(value & ((1 << self.PROGMEM_ADDRESS_LENGTH) - 1))

    def pop_stack(self, value):
        try:
            return self.STACK.pop(-1)
        except IndexError:
            self.coredump("Processor attempted to pop illegal position on stack.")

    def jump(self, new_address):
        try:
            if(new_address >= (1 << self.PROGMEM_ADDRESS_LENGTH)):
                raise IndexError
            self.PC = new_address
        except IndexError:
            self.coredump(f"Processor attempted to jump to illegal program memory location. ({new_address})")
        
    # next instruction
    def advance(self):
        try:
            self.PC = self.PC + 1
            if(self.PC >= (1 << self.PROGMEM_ADDRESS_LENGTH)):
                raise IndexError
        except IndexError:
            self.coredump("Processor reached the end of program memory.")

    def decompose_instruction(self, instruction):
        # decompose instruction into operands
        for key in self.OPERANDS:
            self.OPERANDS[key] = (instruction >> OPS[key][0]) & ((1 << OPS[key][1]) - 1)
            # if operand is signed and negative, turn negative
            if(
               (OPS[key][2] != 0) and
               ((self.OPERANDS[key] & (1 << (OPS[key][1] - 1))) != 0)
              ):
                self.OPERANDS[key] -= (1 << OPS[key][1]) - 1

    def handle_flags(self, value):
        # set flags
        self.FLAGS['Z'] = ((value & ((1 << self.WORD_SIZE) - 1) == 0))
        self.FLAGS['C'] = (value >= (1 << self.WORD_SIZE))

    def step(self):
        instruction = self.read_progmem(self.PC)
        self.decompose_instruction(instruction)
        self.OPCODES[self.OPERANDS['Opcode']]()

    def coredump(self, message):
        # dump flags
        print(f"Flags:\n\tZ: {int(self.FLAGS['Z'])} C: {int(self.FLAGS['C'])}\n")
        # dump register contents
        print("Registers:")
        for idx in range(len(self.REGISTERS)):
            print("\tr%d: 0x%02X (%d)" %
                  (idx, self.REGISTERS[idx], self.REGISTERS[idx]))
        print()

        # show Program Counter
        print(f"PC: {self.PC}\n")

        # dump program memory
        print("Program memory: (%d hardware words [%d])" %
              (1 << self.PROGMEM_ADDRESS_LENGTH, self.PROGMEM_WORD_SIZE))
        width = 8
        idx = 0
        while(idx < (1 << self.PROGMEM_ADDRESS_LENGTH)):
            print("0x%04X, " % (self.PROGMEM[idx]), end='')
            idx += 1
            if((idx % width) == 0):
                print()
        print()
        # dump memory
        print("Memory: (%d words [%d])" %
              (1 << self.MEMORY_ADDRESS_LENGTH, self.WORD_SIZE))
        width = 8
        idx = 0
        while(idx < (1 << self.MEMORY_ADDRESS_LENGTH)):
            print("0x%02X, " % (self.MEMORY[idx]), end='')
            idx += 1
            if((idx % width) == 0):
                print()
        print()
        # display message and exit
        exit(f"{message}\nCore dumped.")

    # returns true if CPU is halted
    def halted(self):
        if(self.state == STATES['HLT']):
            return True
        elif(self.state == STATES['ACT']):
            return False
        raise Exception(f"what: Unknown machine state {self.state}")

    # operations
    def NOP(self):
        # no operation
        # do nothing
        self.advance()

    def HLT(self):
        # halt machine
        self.state = STATES['HLT'] # put machine in halted state
        self.coredump("Processor halted.")

    def ADD(self):
        # adds 2 registers
        new_value = self.read_reg(self.OPERANDS['A']) + self.read_reg(self.OPERANDS['B'])
        self.handle_flags(new_value)
        self.write_reg(self.OPERANDS['First'], new_value)
        self.advance()

    def SUB(self):
        # subtracts 2 registers
        new_value = self.read_reg(self.OPERANDS['A']) - self.read_reg(self.OPERANDS['B'])
        self.handle_flags(new_value)
        self.write_reg(self.OPERANDS['First'], new_value)
        self.advance()

    def NOR(self):
        # does the NOR operation on A and B, puts result in First
        new_value = ~(self.read_reg(self.OPERANDS['A']) |
                      self.read_reg(self.OPERANDS['B']))
        self.handle_flags(new_value)
        self.write_reg(self.OPERANDS['First'], new_value)
        self.advance()

    def AND(self):
        # does the AND operation on A and B, puts result in First
        new_value = self.read_reg(self.OPERANDS['A']) & self.read_reg(self.OPERANDS['B'])
        self.handle_flags(new_value)
        self.write_reg(self.OPERANDS['First'], new_value)
        self.advance()

    def XOR(self):
        # does the XOR operation on A and B, puts result in First
        new_value = self.read_reg(self.OPERANDS['A']) ^ self.read_reg(self.operands['B'])
        self.write_reg(self.OPERANDS['First'], new_value)
        self.advance()

    def RSH(self):
        # shifts bits in A right by 1 place, puts result in First
        self.write_reg(
                       self.OPERANDS['First'],
                       self.read_reg(self.OPERANDS['A']) >> 1
                      )
        self.advance()

    def LDI(self):
        # puts Immediate into First
        self.write_reg(
                       self.OPERANDS['First'],
                       self.OPERANDS['Immediate']
                      )
        self.advance()

    def ADI(self):
        # adds Immediate with First
        new_value = self.read_reg(self.OPERANDS['First']) + self.OPERANDS['Immediate']
        self.handle_flags(new_value)
        self.write_reg(self.OPERANDS['First'], new_value)
        self.advance()

    def JMP(self):
        # set Program Counter to Address
        self.jump(self.OPERANDS['Mem'])

    def BRH(self):
        # set Program Counter to Address if condition is true
        cond_true = False

        match (self.OPERANDS['Condition']):
            case 0b00:
                cond_true = (self.FLAGS['Z'] == 1)
            case 0b01:
                cond_true = (self.FLAGS['Z'] == 0)
            case 0b10:
                cond_true = (self.FLAGS['C'] == 0)
            case 0b11:
                cond_true = (self.FLAGS['C'] == 1)

        if(cond_true):
            self.JMP()
        else:
            self.advance()

    def CAL(self):
        # push Program Counter (+ 1) to stack before jumping
        self.push_stack(self.PC + 1)
        self.JMP()

    def RET(self):
        # pop stack and set Program Counter to it
        self.jump(self.pop_stack())

    def LOD(self):
        # load word at memory address in A (+ offset) into First
        self.write_reg(
                       self.OPERANDS['First'],
                       self.read_memory(
                                        self.read_reg(self.OPERANDS['A']),
                                        self.OPERANDS['Offset']
                                       )
                      )
        self.advance()

    def STR(self):
        # store word in First into memory address at A (+ offset)
        self.write_memory(
                          self.read_reg(self.OPERANDS['A']),
                          self.read_reg(self.OPERANDS['First']),
                          self.OPERANDS['Offset']
                         )
        self.advance()
