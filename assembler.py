# All rights to this code go to the original owner, @MattBatWings
from common import *

###- CONSTANTS -###
# Number of registers
NUMBER_OF_REGISTERS = 16
# Opcode position; how much to shift opcode (in bits, left)
OPCODE_POSITION = 12
# Max length an instruction can have (in bits)
INSTRUCTION_MAX_LENGTH = 16

###- ALL POSSIBLE OPERANDS -###
# Operands
# Format : '<1 char label>':[<position>, <bit length>, <1: signed, 0: unsigned>, "<full name>"]
OPERANDS= {
           'F' : [8,  4, 0, "first register"], # First register
           'A' : [4,  4, 0, "register A"],     # Register A
           'B' : [0,  4, 0, "register B"],     # Register B
           'I' : [0,  8, 1, "immediate"],      # Immediate
           'C' : [10, 2, 0, "condition"],      # Condition
           'O' : [0,  4, 1, "offset"],         # Offset
           'M' : [0, 10, 0, "memory address"], # Memory address
          }

###- NATIVE INSTRUCTIONS -###
# Format: '<label>':[<opcode>, '<operand flags in order of use in opcode>', <opcode specific mask>]
# [A=0] means operand A is optional and defaults to 0
OPCODES = {
           'nop':[0x0, '', 0x0000],        # nop                     : Does nothing
           'hlt':[0x1, '', 0x0000],        # hlt                     : Halts machine
           'add':[0x2, 'FAB', 0x0000],     # add dest A B            : pseudo-code: dest <- A + B
           'sub':[0x3, 'FAB', 0x0000],     # sub dest A B            : pseudo-code: dest <- A - B
           'nor':[0x4, 'FAB', 0x0000],     # nor dest A B            : pseudo-code: dest <- !(A | B)
           'and':[0x5, 'FAB', 0x0000],     # and dest A B            : pseudo-code: dest <- A & B
           'xor':[0x6, 'FAB', 0x0000],     # xor dest A B            : pseudo-code: dest <- A ^ B
           'rsh':[0x7, 'FA', 0x0000],      # rsh dest A              : pseudo-code: dest <- A >> 1 (logical shift)
           'ldi':[0x8, 'FI', 0x0000],      # ldi dest immediate      : pseudo-code: dest <- immediate
           'adi':[0x9, 'FI', 0x0000],      # adi dest immediate      : pseudo-code: dest <- dest + immediate
           'jmp':[0xA, 'M', 0x0000],       # jmp address             : pseudo-code: PC <- address
           'brh':[0xB, 'CM', 0x0000],      # brh condition address   : pseudo-code: PC <- condition ? address : PC + 1
           'cal':[0xC, 'M', 0x0000],       # cal address             : pseudo-code: PC <- address (and push PC + 1 to stack)
           'ret':[0xD, '', 0x0000],        # ret                     : pseudo-code: PC <- top of stack (and pop stack)
           'lod':[0xE, 'FA[O=0]', 0x0000], # lod dest A [offset=0]   : pseudo-code: dest <- mem[A + offset]
           'str':[0xF, 'FA[O=0]', 0x0000]  # str source A [offset=0] : pseudo-code: mem[A + offset] <- source
          } # Opcodes

###- PSEUDO-INSTRUCTIONS -###
# Pseudo-instructions
# Format : 'label':['<resolution as formatted string>']
PSEUDOINS = {
             'cmp':['sub r0 {0} {1}'],  # cmp : sub r0 A B
             'mov':['add {0} {1} r0'],  # mov : add dest A r0
             'lsh':['add {0} {1} {1}'], # lsh : add dest A A
             'inc':['adi {0} 1'],       # inc : adi dest 1
             'dec':['adi {0} -1'],      # dec : adi dest -1
             'not':['nor {0} {1} r0'],  # not : nor dest A r0
            }

###- MACROS (MULTI-LINE PSEUDO-INSTRUCTIONS) -###
# Macros
# Format : 'label':['<resolution as formatted string>']
# - formatted string must be separated by newlines ('\n')
MACROS = {
          'nnd':['and {0} {1} {2}\n'+   # nnd dest A B : and dest A B
                 'not {0} {0}'       ], #                not dest dest   # do the bitwise "not AND" operation on registers A, B and store the result in dest

          'xnr':['xor {0} {1} {2}\n'+   # xnr dest A B : xor dest A B
                 'not {0} {0}'       ], #                not dest dest   # do the bitwise "not XOR" operation on registers A, B and store the result in dest

          'orr':['nor {0} {1} {2}\n'+   # orr dest A B : nor dest A B
                 'not {0} {0}'       ], #                not dest dest   # do the bitwise "OR" operation on registers A, B and store the result in dest

          'nim':['not {0} {2}\n'+       # nim dest A B : not dest B
                 'and {0} {0} {1}'   ], #                and dest dest A # do the bitwise "not IMPLIES" operation on registers A, B and store the result in dest
                                        # !(A -> B) = A & (!B)

          'imp':["nim {0} {1} {2}\n"+   # imp dest A B : nim dest A B
                 "not {0} {0}"       ], #                not dest dest   # do the bitwise "IMPLIES" operation on registers A, B and store the result in dest
                                        # A -> B = !(!(A -> B))
#--------------------------------------------------------------------------------#
          'use_devices':      ['ldi {0} 248'],      # use_display rbp : ldi rbp 240         # store pixel display's base pointer in rbp

          'set_x':            ['str {1} {0} -8'],   # set_x rbp rX : str rX rbp 0           # store value at rX into pixel display's X port

          'set_xi':           ['ldi {1} {2}\n'+     # set_xi rbp rBuf imm : ldi rBuf imm
                               'set_x {0} {1}' ],   #                       set_x rbp rBuf  # store immediate value into pixel display's X port

          'set_y':            ['str {1} {0} -7'],   # set_y rbp rY : str rY rbp 1           # store value at rY into pixel display's Y port

          'set_yi':           ['ldi {1} {2}\n'+     # set_yi rbp rBuf imm : ldi rBuf imm
                               'set_y {0} {1}' ],   #                       set_y rbp rBuf  # store immediate value into pixel display's Y port

          'set_pixel':        ['str r0 {0} -6'],    # set_pixel rbp : str r0 rbp 2          # trigger pixel display's Draw Pixel port to draw current pixel

          'clr_pixel':        ['str r0 {0} -5'],    # clr_pixel rbp : str r0 rbp 3          # trigger pixel display's Clear Pixel port to clear current pixel

          'get_pixel':        ['lod {1} {0} -4'],   # get_pixel rbp rDest : lod rDest rbp 4 # load pixel at current pixel position

          'cpy_disp_buffer':  ['str r0 {0} -3'],    # cpy_disp_buffer rbp : str r0 rbp 5    # copy pixel display buffer to screen

          'clr_disp_buffer':  ['str r0 {0} -2'],    # clr_disp_buffer rbp : str r0 rbp 6    # clear pixel display buffer

          'clr_display':['clr_disp_buffer {0}\n'+   # clr_display rbp : clr_disp_buffer rbp
                         'cpy_disp_buffer {0}'   ], #                   cpy_disp_buffer rbp # clear both display and display buffer
#--------------------------------------------------------------------------------#
          'add_char':         ['str {1} {0} -1'],   # add_char rbp rChar  : str rChar rbp 0 # append character at rChar to character display buffer

          'add_chari':        ['ldi {1} {2}\n'+     # add_chari rbp rBuf imm : ldi rBuf imm
                               'add_char {0} {1}'], #                          add_char rbp rBuf
                                                                                            # append immediate character imm to character display buffer

          'cpy_char_buffer':  ['str r0 {0} 0'],     # cpy_char_buffer rbp : str r0 rbp 1    # copy character display buffer to char display

          'clr_char_buffer':  ['str r0 {0} 1'],     # clr_char_buffer rbp : str r0 rbp 2    # clear character display buffer

          'clr_char_display': ['clr_char_buffer {0}\n'+   # clr_char_display rbp : clr_char_buffer rbp
                               'cpy_char_buffer {0}'   ], #                        cpy_char_buffer rbp
                                                                                            # clear both char display and buffer
#--------------------------------------------------------------------------------#
          'set_num':          ['str {1} {0} 2'],    # set_num rbp rNum : str rNum rbp       # set number display's buffer to number in rNum

          'set_numi':         ['ldi {1} {2}\n'+     # set_numi rbp rBuf imm : ldi rBuf imm
                               'set_num {0} {1}'],  #                         set_num rbp rBuf
                                                                                            # set number display's buffer to immediate imm

          'clr_num_display':  ['str r0 {0} 3'],     # clr_num_display rbp : str r0 rbp 1    # clear number display

          'num_mode_signed':  ['str r0 {0} 4'],     # num_mode_signed rbp : str r0 rbp 2    # set number display to signed mode

          'num_mode_unsigned':['str r0 {0} 5'],     # num_mode_unsigned rbp : str r0 rbp 3  # set number display to unsigned mode
#--------------------------------------------------------------------------------#
          'get_rng':          ['lod {1} {0} 6'],    # get_rng rbp rDest : lod rDest rbp     # put a random number in rDest

          'get_cont_state':   ['lod {1} {0} 7'],    # get_cont_state rbp rDest : lod rDest rbp
                                                                                            # put the controller's current state in rDest
         }

###- UTILITY -###
# Definition check
def is_definition(word):
    return word == 'define'
# Label check
def is_label(word):
    return (word[0] == '.') | ((word[-1] == ':') << 1)
# Macro check
def is_macro(word):
    return word in MACROS
# Resolve symbols
def resolve(word, line, symbols):
    if word[0] in '-0123456789':
        return int(word)
    if symbols.get(word) is None:
        fatal_error("assembler", f'{assembly_filename}:{line}: Could not resolve \'{word}\'.')
    return symbols[word]
# Strip line of comments
def remove_comment(comment_symbols, line):
    index=strfind(line, comment_symbols)
    if(index==-1):
        return line
    return line[:index]

###- MAIN THING -###
# Assemble function
def assemble(assembly_filename, output_filename):
    try:
        assembly_file = open(assembly_filename, 'r')
    except FileNotFoundError:
        fatal_error('assembler', f'{assembly_filename}: File not found.')
    machine_code_file = open(output_filename, 'w')
    lines = (line.strip() for line in assembly_file)

    # Remove comments and blanklines
    lines = [[remove_comment("/;#", line).strip(), idx+1] for idx, line in enumerate(lines)]

    # Populate symbol table
    symbols = {}

    # Generate register names
    registers = ['r{0}'.format(x) for x in range(NUMBER_OF_REGISTERS)]
    for index, symbol in enumerate(registers):
        symbols[symbol] = index

    # Calculate number of operands and add to pseudo-instruction element
    for pop in PSEUDOINS:
        popcodeinfo=PSEUDOINS[pop]
        nums=[int(word[1:len(word)-1]) for word in popcodeinfo[0].split() if word[0]=='{']
        if(len(nums)==0):
            pseudoins[pop].insert(0, 0)
        else:
            PSEUDOINS[pop].insert(0, max(nums)+1)
    
    # Calculate number of operands and add to macro element
    for macro in MACROS:
        macroinfo=MACROS[macro]
        nums=[int(word[1:len(word)-1]) for word in macroinfo[0].split() if word[0]=='{']
        if(len(nums)==0):
            MACROS[macro].insert(0, 0)
        else:
            MACROS[macro].insert(0, max(nums)+1)
    
    # Make opcodes more machine-friendly
    for opcode in OPCODES:
        processed_opcode=[]
        operands=OPCODES[opcode][1]
        idx=0
        minimum_operands=0
        while(idx<len(operands)):
            if(operands[idx]=='['):
                idx_end=operands.find(']', idx)
                if(idx_end==-1):
                    fatal_error('assembler', f"loading stage: syntax error: No closing brace for operand \'{operands[idx+1]}\' in opcode \'{opcode}\'.")
                substr=operands[idx+1:idx_end]
                if(substr[2:]==''):
                    fatal_error('assembler', f"loading stage: wtf: No default defined for operand \'{substr[0]}\' for opcode \'{opcode}\'.")
                processed_opcode.append([substr[0], int(substr[2:])])
                idx=idx_end+1
                minimum_operands-=1
            else:
                idx_end=operands.find('[', idx)
                if(idx_end==-1):
                    idx_end += len(operands) + 1
                substr=operands[idx:idx_end]
                processed_opcode = processed_opcode + [[x] for x in substr]
                idx=idx_end
        maximum_operands=len(processed_opcode)
        minimum_operands=minimum_operands+maximum_operands
        processed_opcode=[processed_opcode, minimum_operands, maximum_operands]
        OPCODES[opcode][1]=processed_opcode

    # Validity check
    for opcode in OPCODES:
        operands=OPCODES[opcode][1][0]
        maxim=1
        for idx, operand in enumerate(operands):
            if(maxim <= len(operand)):
                maxim=len(operand)
            else:
                fatal_error('assembler', f"loading stage: wtf: Optional operand \'{operands[idx-1][0]}\' declared inbetween necessary ones in \'{opcode}\'! (Will cause problems later)")

    for symbol in OPCODES:
        symbols[symbol] = OPCODES[symbol][0] # Add corresponding numeral opcode

    conditions = [ 'eq'  , 'ne'     , 'ge'   , 'lt'      ,
                   '='   , '!='     , '>='   , '<'       ,
                   'z'   , 'nz'     , 'c'    , 'nc'      ,
                   'zero', 'notzero', 'carry', 'notcarry', ] # Possible conditions
    for index, symbol in enumerate(conditions):
        symbols[symbol] = index & 3 #0b11
    
    # Resolve macros
    cont=True
    while(cont):
        new_lines=lines.copy()
        offset=0
        cont=False
        for index, line in enumerate(lines):
            line_number=line[1]
            line=line[0]
            words = [word.lower() for word in line.split()]
            if(len(words)==0): continue
            if is_macro(words[0]):
                cont=True
                macroinfo=macros[words[0]]
                if macroinfo[0] != (len(words)-1):
                    fatal_error('assembler', f"pre-assembly stage: {assembly_filename}:{line_number}: Incorrect number of operands for macro \'{words[0]}\'")
                gen_lines= macroinfo[1].format(*words[1:]).split('\n')
                new_lines.pop(index + offset)
                offset -= 1
                for gline in gen_lines:
                    offset += 1
                    new_lines.insert(index + offset, [gline, line_number])
        lines=new_lines
    
    # Definitions and labels
    offset = 0
    for index, line in enumerate([line for line in lines if line[0]!='']):
        line_number=line[1]
        line=line[0]
        words = [word.lower() for word in line.split()]

        if is_definition(words[0]):
            symbols[words[1]] = int(words[2])
            offset += 1
        elif is_label(words[0]):
            if(is_label(words[0])==1):
                symbols[words[0]] = index - offset # This assumes we put code after the label, which many don't
            elif(is_label(words[0])==2):
                symbols['.'+words[0][:-1]] = index - offset
            else:
                fatal_error('assembler', f"pre-assembly stage: syntax error: {assembly_filename}:{line_number}: Both \':\' and \'.\' indicator used for label.")
            # Compensates for code that is not put in the same line as the label definition
            if(len(words)<2):
                offset+=1
    
    # Clean lines of definitions and labels for machine code translation step
    for i, b in enumerate(lines):
        line_number=b[1]
        b=b[0]
        words = [word.lower() for word in b.split()]
        if(len(words)==0): continue
        if(is_label(words[0])!=0):
            end_of_label=strfind(b, " \t")
            if(end_of_label==-1):
                lines[i]=['', line_number]
            else:
                lines[i]=[b[end_of_label:].strip(), line_number]
        elif(is_definition(words[0])):
            lines[i]=['', line_number]
    lines=[[line[0].strip(), line[1]] for line in lines]

    # Start assembling
    for i in range(len(lines)):
        # Decompose instruction
        line_number=lines[i][1]
        words = [word.lower() for word in split_string(lines[i][0], ", ")]
        if len(words)==0: continue
        
        # Resolve pseudo-instructions
        if words[0] in PSEUDOINS:
            popcode     = words[0]
            popcodeinfo = PSEUDOINS[popcode]
            if popcodeinfo[0] != len(words)-1:
                fatal_error("assembler", f"{assembly_filename}:{line_number}: Incorrect number of operands for pseudo-instruction \'{popcode}\'")
            words=popcodeinfo[1].format(*words[1:]).split()
        
        # Begin machine code translation
        current_opcode = words[0]
        # Resolve opcode
        machine_code = 0
        try:
            machine_code |= symbols[current_opcode] << OPCODE_POSITION
        except KeyError:
            fatal_error("assembler", f'{assembly_filename}:{line_number}: Unknown opcode \'{current_opcode}\'')
        # Resolve operands
        words = [resolve(word, line_number, symbols) for word in words]

        # Number of operands check
        if(  OPCODES[current_opcode][1][-2] > (len(words)-1)):
            fatal_error("assembler", f'{assembly_filename}:{line_number}: Not enough operands for \'{current_opcode}\'')
        elif(OPCODES[current_opcode][1][-1] < (len(words)-1)):
            fatal_error("assembler", f'{assembly_filename}:{line_number}: Too many operands for \'{current_opcode}\'')

        # Check operands and assemble instruction
        for idx, opcode in enumerate(OPCODES[current_opcode][1][0]):
            if((len(words)-2)<idx):
                words.append(opcode[1])
            opinfo = OPERANDS[opcode[0]]
            mask   = (1<<opinfo[1]) - 1
            if opinfo[2] and (words[idx+1]<0):
                words[idx+1]=(~words[idx+1])+1
            if words[idx+1] != (words[idx+1] & mask):
                fatal_error("assembler", f'{assembly_filename}:{line_number}: Invalid {opinfo[3]} for \'{current_opcode}\'')
            machine_code |= (words[idx+1] & mask) << opinfo[0] # Just to be safe, it's ANDed with the mask

        # OR with opcode-specific mask
        machine_code |= OPCODES[current_opcode][2]

        # Write to output file
        as_string = bin(machine_code)[2:].rjust(INSTRUCTION_MAX_LENGTH, '0')
        machine_code_file.write(f'{as_string}\n')
