'''
Output class
'''

import logging
from enum import Enum
import os
import copy
import json

DELIMITER_TITLE = ' :: '
LJUSTIFY = 13

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
    '''
    Handles printing output to specified location

    Args:
        output_location (OUT): Enum that describes location to print into
        output_type (OUTTYPE): How to format output
        file (file): file to print to if printing to file
        signature (str): used for embed titles
    '''

    def __init__(self, output_location:OUT, output_type:OUTTYPE=OUTTYPE.STRING, user=None, 
            file=None, signature:str=None, auto_clear=False):

        self.output_location = output_location
        self.output_type = output_type
        self.file = file
        self.user = user
        self.auto_clear = auto_clear

        self.cache = list()
        self.signature = signature

    def println(self, printout, output_location:OUT=None, file_name:str=None) -> None:
        self.print('\n' + printout, output_location=output_location, file_name=file_name)

    def print(self, printout, output_location:OUT=None, file_name:str=None, no_signature:bool=False) -> None:
        '''
        Determines appropriate printing channel and prints message

        Args:
            msg (str/dict): message to print
            
            logging_flag (OUT): temporary prints to this output location
                without altering the stored location within this object
        '''
        outlocation = self.output_location if output_location == None else output_location

        if self.output_type == OUTTYPE.JSON:
            if isinstance(printout, dict):
                output = json.dumps(printout)
            elif isinstance (printout, str):
                output = json.dumps({'MESSAGE':printout})
            elif isinstance (printout, json):
                output = printout
        else:
            output = ''
            if isinstance(printout, dict):
                for entry_key, entry_value in printout.items():
                    output += f'{entry_key}{DELIMITER_TITLE}{entry_value}\n'
            elif isinstance (printout, str):
                if not no_signature and not self.signature is None and len(self.signature):
                    output = f'{self.signature.ljust(LJUSTIFY) if LJUSTIFY != 0 else self.signature}{DELIMITER_TITLE}{printout}'
                else:
                    output = printout
            elif isinstance (printout, json):
                output = str(json.loads(printout))

            if outlocation == OUT.INFO:
                logging.info(output)
            elif outlocation == OUT.DEBUG:
                logging.debug(output)
            elif outlocation == OUT.WARN:
                logging.warning(output)
            elif outlocation == OUT.ERROR:
                logging.error(output)
            elif outlocation == OUT.CONSOLE:
                print(output)

        if (output_location == OUT.STORE):
            self.cache.append(output)

        elif (output_location == OUT.FILE):
            f = open(file_name, 'a')
            f.write(output)
            f.close


    def store(self, printout):
        self.print(printout, OUT.STORE, no_signature=True)

    def view_cache(self, output_redirect=None) -> None:
        '''
        prints cache
        '''
        if output_redirect == None:
            for line in self.cache:
                self.print(line, no_signature=True)
        else:
            for line in self.cache:
                self.print(line, output_location=output_redirect, no_signature=True)
        
        if self.auto_clear:
            self.cache.clear()

    def peek_cache(self, output_redirect=None) -> None:
        '''
        print the most recent entry in cache
        '''
        if not len(self.cache):
            return
        if output_redirect == None:
            self.print(self.cache[-1], no_signature=True)
        else:
            self.print(self.cache[-1], output_redirect=output_redirect, no_signature=True)

        if self.auto_clear:
            self.cache.pop(-1)

    def get_cache(self) -> list:
        '''
        returns a copy of the cache and clears cache
        '''
        cache_copy = copy.deepcopy(self.cache)
        self.cache.clear()
        return cache_copy

    def debug(self, data) :
        self.print(data, output_location=OUT.DEBUG)
    
    def info(self, data):
        self.print(data, output_location=OUT.INFO)
    
    def warn(self, data):
        self.print(data, output_location=OUT.WARN)
    
    def error(self, data):
        self.print(data, output_location=OUT.ERROR)
