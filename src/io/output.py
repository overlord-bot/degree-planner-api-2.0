import logging
from enum import Enum
import os
import copy

DELIMITER_TITLE = '---'
DELIMITER_BLOCK = '###'

class OUT(Enum):
    NONE = 0

    CONSOLE = 1
    INFO = 2
    DEBUG = 3
    WARN = 4
    ERROR = 5

    STORE = 6
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

        self.cache = list()
        self.MAX_MSG_LENGTH = 2000
        self.signature = signature


    """ Determines appropriate printing channel and prints message

    Args:
        msg (str): message to print
        
        logging_flag (OUT): temporary prints to this output location
            without altering the stored location within this object
    """
    def print(self, msg, output_location:OUT=None, file_name:str=None) -> None:
        
        outlocation = self.output_location if output_location == None else output_location

        json_output = dict()
        if self.output_type == OUTTYPE.JSON:
            json_output.update({'UNNAMED BLOCK' if msg.find(DELIMITER_TITLE) == -1 else msg.split(DELIMITER_TITLE)[0] : msg if msg.find(DELIMITER_TITLE) == -1 else msg.split(DELIMITER_TITLE)[1]})
        else:
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

        if (self.output_location == OUT.FILE):
            f = open(file_name, 'a')
            f.write(str(msg))
            f.close

        elif (self.output_location == OUT.STORE):
            self.cache.append(msg)
            return
    

    def print_cache(self, output_redirect=None):
        if output_redirect == None:
            for line in self.cache:
                self.print(line)
        else:
            for line in self.cache:
                self.print(line, output_location=output_redirect)
        self.cache.clear()

    
    def get_cache(self):
        cache_copy = copy.deepcopy(self.cache)
        self.cache.clear()
        return cache_copy
        
