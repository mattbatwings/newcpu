from assembler import assemble
from schematic import make_schematic
import sys


def main():
    program = 'mandelbrot'
    
    as_filename = f'programs/{program}.as'
    mc_filename = f'programs/{program}.mc'
    schem_filename = f'programs/{program}.schem'

    assemble(as_filename, mc_filename)
    make_schematic(mc_filename, schem_filename)

if __name__ == '__main__':
    main()


# cpusnake.schem - GOOD
# cputetris.schem - GOOD