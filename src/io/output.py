import logging
from enum import Enum
import os

DELIMITER_TITLE = '---'
DELIMITER_BLOCK = '###'

class OUT(Enum):
    NONE = 0

    CONSOLE = 1
    INFO = 2
    DEBUG = 3
    WARN = 4
    ERROR = 5

    CACHE = 6
    FILE = 7

class OUTTYPE(Enum):
    STRING = 1
    JSON = 2

class Output():

    """ Handles printing output to specified location
    
    Args:
        output_location (OUT): Enum that describes location to print into
        output_type (OUTTYPE): How to format output
        file (file): file to print to if printing to file
        signature (str): used for embed titles
    """
    def __init__(self, output_location:OUT, output_type:OUTTYPE=OUTTYPE.STRING, user=None, 
            file=None, signature:str=''):
        
        self.output_location = output_location
        self.output_type = output_type
        self.file = file
        self.user = user

        self.__msg_cache_hold = ""
        self.message_max_length = 2000
        self.signature = signature


    """ Determines appropriate printing channel and prints message

    Args:
        msg (str): message to print
        
        logging_flag (OUT): temporary prints to this output location
            without altering the stored location within this object
    """
    async def print(self, msg:str, json_output:dict=None, output_location:OUT=None, file_name:str=None) -> None:
        
        outlocation = self.output_location if output_location == None else output_location

        if json_output != None:
            json_output.update({'' if msg.find(DELIMITER_TITLE) == -1 else msg.split(DELIMITER_TITLE)[0] : msg if msg.find(DELIMITER_TITLE) == -1 else msg.split(DELIMITER_TITLE)[1]})
            return

        msg = msg.replace(DELIMITER_TITLE, ' :: ')

        if outlocation == OUT.INFO:
            logging.info(msg)
        elif outlocation == OUT.DEBUG:
            logging.debug(msg)
        elif outlocation == OUT.WARN:
            logging.warning(msg)
        elif outlocation == OUT.ERROR:
            logging.error(msg)

        elif outlocation == OUT.CONSOLE:
            print(msg)

        elif (self.output_location == OUT.FILE):
            f = open(file_name, 'a')
            f.write(msg)
            f.close
    

    """ Creates a temporary cache to store strings, which can then be
        outputted at once when print_cache is called.

    Args:
        msg (string): message to hold
    """
    def print_hold(self, msg):
        msg = msg.replace(DELIMITER_BLOCK, '\n')
        msg = msg.replace(DELIMITER_TITLE, ' :: ')
        self.__msg_cache_hold += msg + "\n"
        return


    """ Prints all content inside message cache, calls upon print() for printing
    """
    async def print_cache(self, output_redirect=None):
        if output_redirect == None:
            await self.print(self.__msg_cache_hold)
        else:
            await self.print(self.__msg_cache_hold, output_location=output_redirect)
        self.__msg_cache_hold = ''

    

