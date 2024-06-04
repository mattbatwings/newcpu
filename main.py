from assembler import assemble
import sys
from common import *

# MAJOR, MINOR, PATCH, PRE-RELEASE IDENTIFIER, BUILD (https://semver.org)
VERSION = ['2','0','0','BETA','']
# display like "MAJOR.MINOR.PATCH[-PRE-RELEASE IDENT][+BUILD]", [] = omitted if empty
VER_FMT = "{0}.{1}.{2}[-{3}][+{4}]"

# Help message
help_mess = """Usage: python main.py <options> file...
Options:
  -O<file> --output <file>  Set output file.
  -h --help                 Print this message and quit.
  -V --version              Print version and quit."""

# Credits/license message (TODO: Add license from original once it's licensed)
credits_mess = """Credits:
  Original author is @MattBatWings at
   GitHub: https://github.com/MattBatWings
   YouTube: https://youtube.com/@MattBatWings

  Modifications by @ProtoSebastian at
   GitHub: https://github.com/ProtoSebastian"""

def print_version():
    print(credits_mess)
    to_print = ""
    idx=0
    while(idx<len(VER_FMT)):
        if(VER_FMT[idx]=='['):
            idx_end=find_nz(VER_FMT, ']',idx)
            substr=VER_FMT[idx:idx_end]
            keep=True
            idx2=0
            while(idx2<(idx_end-idx)):
                idx2=substr.find('{',idx2)+1
                if(idx2==0):
                    break
                idx2_end=find_nz(substr, '}',idx2)
                if(VERSION[int(substr[idx2:idx2_end])]==''):
                    keep=False
                    break
                idx2=idx2_end
            if(keep):
                to_print+=VER_FMT[idx+1:idx_end]
            idx=idx_end+1
        else:
            idx_end=find_nz(VER_FMT, '[',idx)
            to_print+=VER_FMT[idx:idx_end]
            idx=idx_end
    print(f"\nVersion format: {to_print.format('MAJOR','MINOR','PATCH','PRE-RELEASE','BUILD')}")
    print(f"Version.......: {to_print.format(*VERSION)}")

def print_help():
    print(help_mess)

def handle_unknown_switch(statement: str):
    print_help()
    fatal_error('main', f"Unknown switch statement '{statement}'.")

def main():
    # Fancy switch processing
    input_file =''          # no defaults. I mean, why would you default an input file??
    output_file='output.mc' # default to 'output.mc'
    input_files=0

    idx=1
    while(idx < len(sys.argv)):
        # Handle options
        term = sys.argv[idx]
        if(term.startswith('--')):
            match(term):
                case '--help':
                    print_help()
                    exit()
                case '--version':
                    print_version()
                    exit()
                case '--output':
                    idx += 1
                    output_file=sys.argv[idx]
                case other:
                    handle_unknown_switch(term)
        elif(term.startswith('-')):
            # Oo fancy match statementt (i'm tierd)
            match(term[:2]):
                # thing I need
                case '-h':
                    print_help()
                    exit()
                case '-V':
                    print_version()
                    exit()
                case '-O':
                    if(len(sys.argv[idx])!=2):
                        output_file=sys.argv[idx][2:]
                    else:
                        idx += 1
                        output_file=sys.argv[idx]
                case other:
                    handle_unknown_switch(term[:2])
        else:
            if(input_files!=0):
                # ruh roh
                fatal_error('main', "More than 1 input files specified.")
            input_file=term
            input_files+=1
        idx += 1
    if(input_file==''):
        print_help()
        fatal_error('main', "No input files were specified.")

    # Assemble
    assemble(input_file, output_file)

    # Success message
    print("main: Assembly successful.")
    # simulate('output.mc')


if __name__ == '__main__':
    main()
