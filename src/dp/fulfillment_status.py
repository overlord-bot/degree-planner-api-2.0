'''
Fulfillment_Status class
'''

import json
from .course import Course
from .catalog import *


class Fulfillment_Status():
    '''
    A data structure to store information on fulfillment status of a template
    '''

    def __init__(self, template, required_count:int=0, fulfillment_set:set=None):
        if fulfillment_set == None: fulfillment_set = set()
        self.template = template
        self.required = required_count
        self.fulfillment_set = fulfillment_set

    def get_required_count(self) -> int:
        return self.required
    
    def set_required_count(self, requires) -> None:
        self.required = requires

    def get_actual_count(self) -> int:
        return len(self.fulfillment_set)
    
    def get_fulfillment_set(self) -> set:
        return self.fulfillment_set
    
    def set_fulfillment_set(self, fulfillment_set:set) -> None:
        self.fulfillment_set = fulfillment_set

    def set_template(self, template) -> None:
        self.template = template

    def get_template(self):
        return self.template

    """
    returns whether the element is added (not previously present)
    """
    def add_fulfillment_course(self, course:Course) -> bool:
        len_original = len(self.fulfillment_set)
        self.fulfillment_set.add(course)
        return len_original != len(self.fulfillment_set)

    """
    returns whether the element requested to be removed is present (successful removal)
    """
    def remove_fulfillment_course(self, course:Course) -> bool:
        len_original = len(self.fulfillment_set)
        self.fulfillment_set.discard(course)
        return len_original != len(self.fulfillment_set)

    def unfulfilled_count(self) -> int:
        return max(0, self.get_required_count() - self.get_actual_count())
    
    def excess_count(self) -> int:
        return max(0, self.get_actual_count() - self.get_required_count())
    
    def json(self) -> json:
        '''
        Return this class as a json file
        '''
        stat = dict()
        stat.update({'template':self.template})
        stat.update({'required count':self.get_required_count()})
        stat.update({'fulfillment set':self.get_fulfillment_set()})
        return json.dumps(stat)
    
    def __repr__(self) -> str:
        return f"template: {self.template}\nrequired count: {self.required}\nfulfillment set: {self.fulfillment_set}"
    
    def __eq__(self, other):
        return self.template == other.template and self.required == other.required and self.fulfillment_set == other.fulfillment_set
    
    def __len__(self):
        return self.get_actual_count()
    
    def __hash__(self):
        c = 0
        for course in self.fulfillment_set:
            c += hash(course.get_unique_name())
        return hash(self.template) + self.required + c
