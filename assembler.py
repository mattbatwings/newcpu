def assemble(assembly_filename, output_filename):
    assembly_file = open(assembly_filename, 'r')
    machine_code_file = open(output_filename, 'w')
    lines = (line.strip() for line in assembly_file)

    # Remove comments and blanklines
    lines = [line.split('/')[0] for line in lines]
    lines = [line for line in lines if line.strip()]
    
    # Populate symbol table
    symbols = {}
    
    registers = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15']
    for index, symbol in enumerate(registers):
        symbols[symbol] = index

    opcodes = ['nop', 'hlt', 'add', 'sub', 'nor', 'and', 'xor', 'rsh', 'ldi', 'adi', 'jmp', 'brh', 'cal', 'ret', 'lod', 'str']
    for index, symbol in enumerate(opcodes):
        symbols[symbol] = index

    conditions = ['eq', 'ne', 'ge', 'lt']
    conditions2 = ['=', '!=', '>=', '<']
    conditions3 = ['z', 'nz', 'c', 'nc']
    conditions4 = ['zero', 'notzero', 'carry', 'notcarry']
    for index, symbol in enumerate(conditions):
        symbols[symbol] = index
    for index, symbol in enumerate(conditions2):
        symbols[symbol] = index
    for index, symbol in enumerate(conditions3):
        symbols[symbol] = index
    for index, symbol in enumerate(conditions4):
        symbols[symbol] = index

    ports = ['pixel_x', 'pixel_y', 'draw_pixel', 'clear_pixel', 'load_pixel', 'buffer_screen', 'clear_screen_buffer', 
             'write_char', 'buffer_chars', 'clear_chars_buffer', 'show_number', 'clear_number', 'signed_mode', 'unsigned_mode', 'rng', 'controller_input']
    for index, symbol in enumerate(ports):
        symbols[symbol] = index + 240

    for i in range(256):
        symbols[f'"{chr(i)}"'] = i

    symbols['"space"'] = 32
    
    # Add definitions to symbol table
    # expects all definitions to be above assembly
    def is_definition(word):
        return word == 'define'
    
    def is_label(word):
        return word[0] == '.'
    
    offset = 0
    offset_label = 0
    for index, line in enumerate(lines):
        words = [word.lower() for word in line.split()]
        if is_definition(words[0]):
            symbols[words[1]] = int(eval(words[2]))
            offset += 1
        elif is_label(words[0]):
            symbols[words[0]] = index - offset - offset_label
            offset_label += len(words) < 2
    
    # Generate machine code
    def resolve(word):
        if word[0] in '-0123456789':
            return int(word)
        if symbols.get(word) is None:
            exit(f'Could not resolve {word}')

        return symbols[word]

    for i in range(offset, len(lines)):
        words = [word.lower() for word in lines[i].split()]

        # Remove label, we have it in symbols now
        if is_label(words[0]):
            words = words[1:]
            
        # Catch the error from empty line after label
        if words == []:
            continue
        
        # Pseudo-instructions
        if words[0] == 'cmp':
            words = ['sub', words[1], words[2], registers[0]] # sub A B r0
        elif words[0] == 'mov':
            words = ['add', words[1], registers[0], words[2], ] # add A r0 dest
        elif words[0] == 'lsh':
            words = ['add', words[1], words[2], words[2]] # add A A dest
        elif words[0] == 'inc':
            words = ['adi', words[1], '1'] # adi dest 1
        elif words[0] == 'dec':
            words = ['adi', words[1], '-1'] # adi dest -1
        elif words[0] == 'not':
            words = ['nor', words[1], registers[0], words[2]] # nor A r0 dest
        
        # Begin machine code translation
        opcode = words[0]
        machine_code = symbols[opcode] << 12
        words = [resolve(word) for word in words]

        # Number of operands check
        if opcode in ['nop', 'hlt', 'ret'] and len(words) != 1:
            exit(f'Incorrect number of operands for {opcode} on line {i}')
        
        if opcode in ['jmp', 'cal'] and len(words) != 2:
            exit(f'Incorrect number of operands for {opcode} on line {i}')

        if opcode in ['rsh', 'ldi', 'adi', 'brh'] and len(words) != 3:
            exit(f'Incorrect number of operands for {opcode} on line {i}')

        if opcode in ['add', 'sub', 'nor', 'and', 'xor', 'lod', 'str'] and len(words) != 4:
            exit(f'Incorrect number of operands for {opcode} on line {i}')

        # Reg A
        if opcode in ['add', 'sub', 'nor', 'and', 'xor', 'rsh', 'ldi', 'adi', 'lod', 'str']:
            if words[1] != (words[1] % (2 ** 4)):
                exit(f'Invalid reg A for {opcode} on line {i}')
            machine_code |= (words[1] << 8)

        # Reg B
        if opcode in ['add', 'sub', 'nor', 'and', 'xor', 'lod', 'str']:
            if words[2] != (words[2] % (2 ** 4)):
                exit(f'Invalid reg B for {opcode} on line {i}')
            machine_code |= (words[2] << 4)

        # Reg C
        if opcode in ['add', 'sub', 'nor', 'and', 'xor', 'rsh']:
            if words[-1] != (words[-1] % (2 ** 4)):
                exit(f'Invalid reg C for {opcode} on line {i}')
            machine_code |= words[-1]

        # Immediate
        if opcode in ['ldi', 'adi']:
            if words[2] < -128 or words[2] > 255: # 2s comp [-128, 127] or uint [0, 255]
                exit(f'Invalid immediate for {opcode} on line {i}')
            machine_code |= words[2] & (2 ** 8 - 1)
        
        # Instruction memory address
        if opcode in ['jmp', 'brh', 'cal']:
            if words[-1] != (words[-1] % (2 ** 10)):
                exit(f'Invalid instruction memory address for {opcode} on line {i}')
            machine_code |= words[-1]

        # Condition
        if opcode in ['brh']:
            if words[1] != (words[1] % (2 ** 2)):
                exit(f'Invalid condition for {opcode} on line {i}')
            machine_code |= (words[1] << 10)

        # Offset
        if opcode in ['lod', 'str']:
            if words[3] < -8 or words[3] > 7: # 2s comp [-7, 8]
                exit(f'Invalid offset for {opcode} on line {i}')
            machine_code |= words[3] & (2 ** 4 - 1)

        as_string = bin(machine_code)[2:].rjust(16, '0')
        machine_code_file.write(f'{as_string}\n')
