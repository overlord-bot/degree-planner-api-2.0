'''
Command line shell for degree planner
'''

import sys
import logging

from src.dp.degree_planner import Planner
from src.dp.user import User
from src.io.output import *

planner = Planner('API2.0')
user = User(1)

def terminal():
    '''
    Infinite loop that calls command(user_input) upon user input
    and exits when it receives 'quit' input from user
    '''
    print("Welcome to Degree Planner API 2.0")
    print("  open source under MIT License")
    print("  Project Overlord 2022")
    print("  YACS.n 2023")
    if len(sys.argv) > 1:
        if '-a' in sys.argv:
            print("  logging all debug info")
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.WARNING)

    print("")
    output = Output(OUT.CONSOLE, output_type=OUTTYPE.STRING, signature='Alan', auto_clear=True)
    io = DPIO(user, output, output)
    while 1:
        user_input = input("(degree planner) >>> ")
        if user_input.casefold() == "quit":
            return
        planner.input_handler(user, user_input, io)

if __name__ == "__main__":
    terminal()
