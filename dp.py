'''
Command line shell for degree planner
'''
# pylint: disable=line-too-long
import sys
import logging
from datetime import datetime

from src.dp.planner import Planner
from src.user.user import User
from src.io.output import Output

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

    ENABLE_TENSORFLOW = True
    if len(sys.argv) > 1:
        if '-d' in sys.argv:
            print("  logging all debugging info")
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.WARNING)
        if '-f' in sys.argv:
            ENABLE_TENSORFLOW = False

    print("")
    planner = Planner(ENABLE_TENSORFLOW=ENABLE_TENSORFLOW)
    user = User(1, "user1")
    output = Output(Output.OUT.CONSOLE, output_type=Output.OUTTYPE.STRING, signature='DP', auto_clear=True)
    while 1:
        user_input = input("(degree planner) >>> ")
        if user_input.casefold() == "quit":
            return
        planner.user_input(user, user_input, output)

if __name__ == "__main__":
    terminal()
