'''
Command line shell for degree planner
'''

import sys
import logging
from datetime import datetime

from src.dp.planner import Planner
from src.user.user import User
from src.io.output import *

planner = Planner()
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
    print(f"  {datetime.now()}")
    if len(sys.argv) > 1 and '-d' in sys.argv:
        print("  logging all debugging info")
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    print("")
    output = Output(OUT.CONSOLE, output_type=OUTTYPE.STRING, signature='DP', auto_clear=True)
    while 1:
        user_input = input("(degree planner) >>> ")
        if user_input.casefold() == "quit":
            return
        planner.user_input(user, user_input, output)

if __name__ == "__main__":
    terminal()
