from ..io.output import *
from ..user.user import *
from ..dp.command import *

class Command_Handler():

    def __init__(self):
        self.debug = Output(OUT.DEBUG)


    def input_handler(self, user:User, user_input:str) -> bool:
        ''' MAIN FUNCTION FOR ACCEPTING COMMAND ENTRIES

        Args:
            user (User): user object containing all user data and unique user ID
            message (str): string to be parsed as command or submitted to a waiting
                active command
            output (Output): user interface output

        Returns:
            bool: whether input was successfully executed
        '''

        if Flag.CMD_PAUSED in user.flag:
            ''' this means that the system is awaiting a response from the user '''
            user.command_queue_locked = True
            user.command_decision = user_input.strip().casefold()

        else:
            ''' we add a new command to the user's command queue 
            only if they're not actively processing commands '''

            if user.command_queue_locked:
                io.print(f'queue busy, please try again later')
                return False

            user.command_queue_locked = True
            user.command_queue.join()
            commands = self.parse_command(user_input, io)

            for command in commands:
                user.command_queue.put(command)

        self.command_executor(user, io)
        user.command_queue_locked = False
        io.debug(f'user {user.username} unlocked their command queue')
        return True