import unittest
from assembler import assemble

class AssemblerTestCase(unittest.TestCase):
    
    def write_assembly_file(self, filename, lines):
        with open(filename, 'w') as f:
            f.write('\n'.join(lines))

    def read_machine_code_file(self, filename):
        with open(filename, 'r') as f:
            return f.read().splitlines()

    def run_test_case(self, assembly_lines, expected_machine_code, description):
        assembly_filename = 'test.as'
        output_filename = 'output.mc'
        
        self.write_assembly_file(assembly_filename, assembly_lines)
        assemble(assembly_filename, output_filename)
        
        actual_machine_code = self.read_machine_code_file(output_filename)
        
        self.assertEqual(actual_machine_code, expected_machine_code, f"{description}\nExpected: {expected_machine_code}\nGot: {actual_machine_code}")

    def test_nop_instruction(self):
        self.run_test_case(
            ["nop"], 
            ["0000000000000000"], 
            "NOP instruction"
        )

    def test_hlt_instruction(self):
        self.run_test_case(
            ["hlt"], 
            ["0001000000000000"], 
            "HLT instruction"
        )

    def test_add_instruction(self):
        self.run_test_case(
            ["add r1 r2 r3"], 
            ["0010000100100011"], 
            "ADD instruction"
        )

    def test_sub_instruction(self):
        self.run_test_case(
            ["sub r4 r5 r6"], 
            ["0011010001010110"], 
            "SUB instruction"
        )

    def test_nor_instruction(self):
        self.run_test_case(
            ["nor r7 r8 r9"], 
            ["0100011110001001"], 
            "NOR instruction"
        )

    def test_and_instruction(self):
        self.run_test_case(
            ["and r10 r11 r12"], 
            ["0101101010111100"], 
            "AND instruction"
        )

    def test_xor_instruction(self):
        self.run_test_case(
            ["xor r13 r14 r15"], 
            ["0110110111101111"], 
            "XOR instruction"
        )

    def test_rsh_instruction(self):
        self.run_test_case(
            ["rsh r1 r2"], 
            ["0111000100000010"], 
            "RSH instruction"
        )

    def test_ldi_instruction(self):
        self.run_test_case(
            ["ldi r2 123"], 
            ["1000001001111011"], 
            "LDI instruction"
        )

    def test_adi_instruction(self):
        self.run_test_case(
            ["adi r3 -56"], 
            ["1001001111001000"], 
            "ADI instruction"
        )

    def test_jmp_instruction(self):
        self.run_test_case(
            ["jmp 10"], 
            ["1010000000001010"], 
            "JMP instruction"
        )

    def test_brh_instruction(self):
        self.run_test_case(
            ["brh 2 15"], 
            ["1011100000001111"], 
            "BRH instruction"
        )

    def test_cal_instruction(self):
        self.run_test_case(
            ["cal 20"], 
            ["1100000000010100"], 
            "CAL instruction"
        )

    def test_ret_instruction(self):
        self.run_test_case(
            ["ret"], 
            ["1101000000000000"], 
            "RET instruction"
        )

    def test_lod_instruction(self):
        self.run_test_case(
            ["lod r4 r5 7"], 
            ["1110010001010111"], 
            "LOD instruction"
        )

    def test_str_instruction(self):
        self.run_test_case(
            ["str r6 r7 -8"], 
            ["1111011001111000"], 
            "STR instruction"
        )

    def test_using_labels(self):
        self.run_test_case(
            ["ldi r1 0", ".label inc r1", "jmp .label"], 
            ["1000000100000000", "1001000100000001", "1010000000000001"], 
            "Using labels"
        )

    def test_using_definitions(self):
        self.run_test_case(
            ["define MAX 10", "ldi r1 MAX"], 
            ["1000000100001010"], 
            "Using definitions"
        )

    def test_cmp_instruction(self):
        self.run_test_case(
            ["cmp nz r2"], 
            ["0011000100100000"], 
            "Pseudo-instruction CMP"
        )

    def test_mov_instruction(self):
        self.run_test_case(
            ["mov r1 r2"], 
            ["0010000100000010"], 
            "Pseudo-instruction MOV"
        )

    def test_inc_instruction(self):
        self.run_test_case(
            ["inc r1"], 
            ["1001000100000001"], 
            "Pseudo-instruction INC"
        )

    def test_dec_instruction(self):
        self.run_test_case(
            ["dec r1"], 
            ["1001000111111111"], 
            "Pseudo-instruction DEC"
        )

    def test_lsh_instruction(self):
        self.run_test_case(
            ["lsh r7 r6"], 
            ["0010011101110110"], 
            "Pseudo-instruction LSH"
        )

    def test_not_instruction(self):
        self.run_test_case(
            ["not r7 r6"], 
            ["0100011100000110"], 
            "Pseudo-instruction NOT"
        )

    def test_incrementing_counter(self):
        self.run_test_case(
            [
                "define COUNTER 0", 
                "ldi r1 COUNTER", 
                ".inc_label inc r1", 
                "jmp .inc_label"
            ], 
            [
                "1000000100000000", 
                "1001000100000001", 
                "1010000000000001"
            ], 
            "Incrementing Counter"
        )

    def test_complex_case(self):
        self.run_test_case(
            [
                "define A 1", 
                "define B 2", 
                "define C 3", 
                "nop", 
                "hlt", 
                "ldi r1 A", 
                ".jmp ldi r2 B", 
                "ldi r3 C", 
                "add r2 r3 r5", 
                "sub r5 r1 r4", 
                ".brh nor r1 r0 r6", 
                "and r1 r0 r7", 
                ".cal xor r1 r0 r8", 
                "rsh r1 r2", 
                "adi r6 6", 
                "jmp .jmp", 
                "brh z .brh", 
                "cal .cal", 
                "ret", 
                "lod r8 r9 2", 
                "str r6 r7 -2", 
                "cmp r1 r2", 
                "mov r6 r7", 
                "lsh r7 r6", 
                "inc r6", 
                "dec r6", 
                "not r0 r1"
            ], 
            [
                "0000000000000000", 
                "0001000000000000", 
                "1000000100000001", 
                "1000001000000010", 
                "1000001100000011", 
                "0010001000110101", 
                "0011010100010100", 
                "0100000100000110", 
                "0101000100000111", 
                "0110000100001000", 
                "0111000100000010", 
                "1001011000000110", 
                "1010000000000011", 
                "1011000000000111", 
                "1100000000001001", 
                "1101000000000000", 
                "1110100010010010", 
                "1111011001111110", 
                "0011000100100000", 
                "0010011000000111", 
                "0010011101110110", 
                "1001011000000001", 
                "1001011011111111", 
                "0100000000000001"
            ], 
            "Everything, just thrown into one"
        )

if __name__ == '__main__':
    unittest.main()
