def assemble(assembly_filename, output_filename):
    assembly_file = open(assembly_filename, 'r')
    machine_code_file = open(output_filename, 'w')
    lines = (line.strip() for line in assembly_file)

    def remove_comment(comment_symbol, line):
        return line.split(comment_symbol)[0]

    # remove comments and blanklines
    lines = [remove_comment("/", line) for line in lines]
    lines = [line for line in lines if line.strip()]
    
    symbols = {}
    
    registers = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7']
    for index, symbol in enumerate(registers):
        symbols[symbol] = index

    opcodes = ['nop', 'hlt', 'jmp', 'brh', 'cal', 'ret', 'pld', 'pst', 'mld', 'mst', 'ldi', 'adi', 'add', 'sub', 'bit', 'rsh']
    for index, symbol in enumerate(opcodes):
        symbols[symbol] = index

    conditions = ['eq', 'ne', 'hi', 'lo']
    for index, symbol in enumerate(conditions):
        symbols[symbol] = index

    bitwise_types = ['or', 'and', 'xor', 'implies', 'nor', 'nand', 'xnor', 'nimplies']
    for index, symbol in enumerate(bitwise_types):
        symbols[symbol] = index
    
    def is_definition(word):
        return word == 'define'
    
    def is_label(word):
        return word[0] == '.'
    
    # add definitions and labels to symbol table
    # expects all definitions to be above assembly
    offset = 0
    for index, line in enumerate(lines):
        words = [word.lower() for word in line.split()]
        if is_definition(words[0]):
            symbols[words[1]] = int(words[2])
            offset += 1
        elif is_label(words[0]):
            symbols[words[0]] = index - offset
    
    # generate machine code
    def resolve(word):
        if word[0] in '-0123456789':
            return int(word)
        if symbols.get(word) is None:
            exit(f'Could not resolve {word}')
        return symbols[word]

    for i in range(offset, len(lines)):
        words = [word.lower() for word in lines[i].split()]

        # remove label, we have it in symbols now
        if is_label(words[0]):
            words = words[1:]
        
        # special ops
        if words[0] == 'cmp':
            words = ['sub', registers[0], words[1], words[2]]
        elif words[0] == 'mov':
            words = ['add', words[1], words[2], registers[0]]
        elif words[0] == 'lsh':
            words = ['add', words[1], words[2], words[2]]
        elif words[0] == 'inc':
            words = ['adi', words[1], words[2], '#1']
        elif words[0] == 'dec':
            words = ['adi', words[1], words[2], '#-1']
        elif words[0] == 'orr':
            words = ['bit', words[1], words[2], 'or', words[3]]
        elif words[0] == 'and':
            words = ['bit', words[1], words[2], 'and', words[3]]
        elif words[0] == 'xor':
            words = ['bit', words[1], words[2], 'xor', words[3]]
        elif words[0] == 'imp':
            words = ['bit', words[1], words[2], 'implies', words[3]]
        elif words[0] == 'nor':
            words = ['bit', words[1], words[2], 'nor', words[3]]
        elif words[0] == 'nnd':
            words = ['bit', words[1], words[2], 'nand', words[3]]
        elif words[0] == 'xnr':
            words = ['bit', words[1], words[2], 'xnor', words[3]]
        elif words[0] == 'nmp':
            words = ['bit', words[1], words[2], 'nimplies', words[3]]
        elif words[0] == 'not':
            words = ['bit', words[1], words[2], 'nor', registers[0]]
        
        # begin machine code translation
        opcode = words[0]
        if not (opcode in symbols):
            exit(f'Unknown symbol "{opcode}" on line {i}')
        machine_code = (symbols[opcode] << 12)
        words = [resolve(word) for word in words]

        # number of operands check
        if opcode in ['nop', 'hlt', 'ret'] and len(words) != 1:
            exit(f'Incorrect number of operands for {opcode} on line {i}')
        
        if opcode in ['jmp', 'cal'] and len(words) != 2:
            exit(f'Incorrect number of operands for {opcode} on line {i}')

        if opcode in ['brh', 'pld', 'pst', 'mld', 'mst', 'ldi', 'adi', 'rsh'] and len(words) != 3:
            exit(f'Incorrect number of operands for {opcode} on line {i}')

        if opcode in ['add', 'sub'] and len(words) != 4:
            exit(f'Incorrect number of operands for {opcode} on line {i}')

        if opcode in ['bit'] and len(words) != 5:
            exit(f'Incorrect number of operands for {opcode} on line {i}')

        # instruction memory address
        if opcode in ['jmp', 'brh', 'cal']:
            if words[-1] != (words[-1] % (2 ** 10)):
                exit(f'Invalid instruction memory address for {opcode} on line {i}')
            machine_code |= words[-1]

        # condition
        if opcode in ['brh']:
            if words[1] != (words[1] % (2 ** 2)):
                exit(f'Invalid condition for {opcode} on line {i}. Available conditions: {conditions}')
            machine_code |= (words[1] << 10)

        # first register
        if opcode in ['pld', 'pst', 'mld', 'mst', 'ldi', 'adi', 'add', 'sub', 'bit', 'rsh']:
            if words[1] != (words[1] % (2 ** 3)):
                exit(f'Invalid first register for {opcode} on line {i}')
            machine_code |= (words[1] << 9)

        # port
        if opcode in ['pld', 'pst']:
            if words[2] != (words[2] % (2 ** 8)):
                exit(f'Invalid port for {opcode} on line {i}')
            machine_code |= words[2]

        # offset
        if opcode in ['mld', 'mst']:
            if words[2] != (words[2] % (2 ** 8)):
                exit(f'Invalid offset for {opcode} on line {i}')
            machine_code |= words[2]

        # immediate
        if opcode in ['ldi', 'adi']:
            if words[2] != (words[2] % (2 ** 8)):
                exit(f'Invalid immediate for {opcode} on line {i}')
            machine_code |= words[2]

        # reg A
        if opcode in ['add', 'sub', 'bit', 'rsh']:
            if words[2] != (words[2] % (2 ** 3)):
                exit(f'Invalid reg A for {opcode} on line {i}')
            machine_code |= (words[2] << 6)

        # reg B
        if opcode in ['add', 'sub', 'bit']:
            if words[-1] != (words[-1] % (2 ** 3)):
                exit(f'Invalid reg B for {opcode} on line {i}')
            machine_code |= words[-1]

        # operation
        if opcode in ['bit']:
            if words[3] != (words[3] % (2 ** 3)):
                exit(f'Invalid operation for {opcode} on line {i}')
            machine_code |= (words[3] << 3)

        as_string = bin(machine_code)[2:].rjust(16, '0')
        machine_code_file.write(f'{as_string}\n')
