import asyncio

from src.dp.degree_planner import Planner
from src.dp.user import User
from src.utils.output import *

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
    print("")
    while (1):
        cmd = input("(degree planner) >>> ")
        if cmd == "quit": 
            return
        command(cmd)

if __name__ == "__main__":
    terminal()