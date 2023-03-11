'''
User class and Flag enum that indicates command queue status for the user
'''

from enum import Enum
import json
from .schedule import Schedule
from queue import Queue

class Flag(Enum):
    '''
    For command queue use
    '''
    CMD_PAUSED = 100
    CMD_RUNNING = 101

class User():
    '''
    Stores user identification, schedules, course eligibility and command queue operatons info
    '''
    def __init__(self, id):
        self.id = id # unique id for user
        self.username = str(id) # username to display
        self.__schedules = dict() # all schedules this user created <schedule name, Schedule>
        self.curr_schedule = "" # schedule to modify

        self.flag = set()

        # command queue handling
        self.command_queue = Queue()
        self.command_queue_locked = False
        self.command_decision = None
        self.command_paused = None

        # list of rules that determines the set of courses the student is allowed to take
        # (need to statisify only one rule)
        self.eligibility_rules = list()


    def get_all_schedules(self) -> list:
        '''
        Creates a copied list of all current schedule objects
        '''
        return list(self.__schedules.values())


    def get_schedule(self, schedule_name:str) -> Schedule:
        '''
        Returns schedule if found, otherwise None
        '''
        if schedule_name not in self.__schedules:
            return None
        return self.__schedules.get(schedule_name)


    def new_schedule(self, schedule_name:str, SEMESTERS_MAX:int=10) -> None:
        '''
        Creates a new schedule if the schedule does not yet exist
        '''
        if self.__schedules.get(schedule_name, None) is not None:
            return
        schedule = Schedule(schedule_name, SEMESTERS_MAX)
        self.__schedules.update({schedule_name : schedule})


    def add_schedule(self, schedule_name:str, schedule:Schedule):
        '''
        Add schedule from input to schedules
        '''
        self.__schedules.update({schedule_name : schedule})


    def get_current_schedule(self) -> str:
        '''
        Get schedule name being actively editted for this user
        '''
        return self.get_schedule(self.curr_schedule)


    def rename_schedule(self, old_name:str, new_name:str) -> bool:
        '''
        Renames existing schedule only if new name does not already exist

        Returns:
            success (bool): whether rename was successful
        '''
        if old_name not in self.__schedules or new_name in self.__schedules:
            return False
        else:
            self.__schedules.update({new_name : self.__schedules.get(old_name)})
            self.__schedules.pop(old_name)
            return True

    def json(self) -> json:
        '''
        Creates json file of this class
        '''
        user = dict()
        user.update({'username':self.username})
        user.update({'id':self.id})
        schedules = list()
        for s in self.__schedules.keys():
            schedules.append(s)
        user.update({'schedules':schedules})
        user.update({'commands in queue':self.command_queue.qsize()})
        return json.dumps(user)

    def __repr__(self):
        schedule_names = ""
        for s in self.__schedules.keys():
            schedule_names += f"[ {s} ] "
        return f"{str(self.username)}'s schedules: {schedule_names}"


    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        if self.username == other.username:
            return True
        return False


    def __hash__(self):
        return hash(self.id)
