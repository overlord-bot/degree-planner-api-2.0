import asyncio
import sys

from src.dp.degree_planner import Planner
from src.dp.user import User
from src.io.output import *

planner = Planner('API2.0')
user = User(1)

def command(cmd):
    asyncio.run(command_call(cmd))

async def command_call(cmd):
    await planner.message_handler(user, cmd)

def terminal():
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
    while (1):
        cmd = input("(degree planner) >>> ")
        if cmd.casefold() == "quit": 
            return
        command(cmd)

if __name__ == "__main__":
    terminal()