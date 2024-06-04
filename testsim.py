from common import *
import simulator

CPU = simulator.batpu_v2()
CPU.load_program("output.mc")
while not CPU.halted():
    CPU.step()
