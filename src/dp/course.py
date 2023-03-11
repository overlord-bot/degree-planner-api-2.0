'''
Course class
'''

import json
from collections import OrderedDict
import logging

from ..io.output import *

class Course():
    '''
    Course object containing a dictionary of attributes that uniquely defines the course
    and can be used to search/filter for it

    It also has attributes for fast access which should remain consistent with the attribute
    dictionary
    '''

    def __init__(self, name, subject, id, course_credits=0):
        # main attributes
        self.name = name
        self.unique_name = name
        self.subject = subject
        self.course_id = id
        self.course_id2 = 0
        self.level = str(id)[0]
        self.course_credits = course_credits

        # dict of lists of items, e.g. {'concentration.ai':[concentration, ai], 'ci.true':[ci, true]}
        self.attributes = dict()
        
        self.validate_course_id()

        if name not in ('', 'NA', 'ANY'):
            self.set_name(name)
        if subject not in ('', 'NA', 'ANY'):
            self.set_subject(subject)
        if id not in (0, -1, '', 'NA', 'ANY'):
            self.set_id(id)
        if course_credits != -1:
            self.set_credits(course_credits)

        self.cross_listed = set() # set of cross listed courses that should be treated as same course
        self.description = "" # text to be displayed describing the class
        
    def validate_course_id(self, output:Output=None) -> None:
        ''' Some input data for courses may not be in the desired format.

            For example, most courses have an ID in the form of ####, but some
            have ####.##. We separate the latter form into
            courseid = #### (numbers prior to dot) and courseid2 = ## (after dot)

            All data is modified in place, no arguments and return necessary
        '''
        if output is None: output = Output(OUT.CONSOLE)
        self.course_id = str(self.course_id)
        if isinstance(self.course_id, str):
            if '.' in self.course_id:
                split_num = self.course_id.split('.')
                if len(split_num) == 2 and split_num[0].isdigit() and split_num[1].isdigit():
                    self.course_id = int(split_num[0])
                    self.course_id2 = int(split_num[1])
                else:
                    logging.error(f"COURSE PARSING: 2 part ID not <int>.<int> for course " + self.name)
                    
            elif not self.course_id.isdigit() and self.course_id != 'ANY':
                logging.error(f"COURSE PARSING: course id ({self.course_id}) is not a number for course " + self.name)
            elif self.course_id != 'ANY':
                self.course_id = int(self.course_id)
        if not isinstance(self.course_id, int) and self.course_id != 'ANY':
            logging.error(f"COURSE PARSING: course id ({self.course_id}) is not a number for course " + self.name)


    """ 
    Getters
    """

    # determines the level of the course, 1000=1, 2000=2, 4000=4, etc
    def get_level(self):
        return self.level
    
    def get_name(self):
        return self.name
    
    def get_unique_name(self):
        return self.unique_name
    
    def get_subject(self):
        return self.subject
    
    def get_id(self):
        if isinstance(self.course_id, int) or self.course_id.isdigit():
            return int(self.course_id)
        return self.course_id
    
    def get_id2(self):
        return self.course_id2
    
    def get_credits(self):
        return self.course_credits
    
    def get_crosslisted(self):
        return self.cross_listed
    

    """
    Setters
    """
    
    def set_name(self, name):
        self.name = name
        self.generate_unique_name()
        self.remove_attribute_by_head('name')
        self.add_attribute(f'name.{name}')

    def generate_unique_name(self):
        if self.name == "":
            self.unique_name = ""
        else:
            self.unique_name = f"{self.subject.casefold()} {str(self.course_id)} {self.name.strip().casefold()}"
            self.unique_name = self.unique_name.replace(',', '')
        self.remove_attribute_by_head('unique_name')
        self.add_attribute(f'unique_name.{self.unique_name}')

    def set_subject(self, subject):
        self.subject = subject
        self.remove_attribute_by_head('subject')
        self.add_attribute(f'subject.{subject}')

    def set_id(self, course_id):
        self.course_id = course_id
        self.remove_attribute_by_head('course_id')
        self.add_attribute(f'course_id.{course_id}')
        self.remove_attribute_by_head('level')
        self.add_attribute(f'level.{str(course_id)[0]}')

    def set_id2(self, course_id):
        self.course_id = course_id
        self.remove_attribute_by_head('course_id')
        self.add_attribute(f'course_id2.{course_id}')

    def set_credits(self, course_credits):
        self.course_credits = course_credits
        self.remove_attribute_by_head('course_credits')
        self.add_attribute(f'course_credits.{course_credits}')
    

    """
    Attributes are expressed as elements joined by periods, 
    but are internally stored in this class as a list
    """
    
    def add_attribute(self, attr) -> None:
        if isinstance(attr, list):
            attr = '.'.join(attr)
        self.attributes.update({attr:attr.split('.')})

    def replace_attribute(self, old_head, attr) -> None:
        if isinstance(attr, list):
            attr = '.'.join(attr)
        self.remove_attribute_by_head(old_head)
        self.add_attribute(attr)

    def remove_attribute(self, attr) -> None:
        if isinstance(attr, list):
            attr = '.'.join(attr)
        self.attributes.pop(attr)

    def has_attribute(self, attr) -> bool:
        if isinstance(attr, list):
            attr = '.'.join(attr)
        return attr in self.attributes.keys()
    
    def get_attributes_by_head(self, queried_attr) -> list:
        if isinstance(queried_attr, list):
            queried_attr = '.'.join(queried_attr)
        queried_attr = queried_attr.split('.')
        matched_attrs = list()
        for attribute in self.attributes.values():
            if len(attribute) < len(queried_attr):
                continue
            i = 0
            good_match = True
            while i < min(len(attribute), len(queried_attr)):
                if attribute[i] != queried_attr[i]:
                    good_match = False
                    break
                i += 1
            if good_match:
                matched_attrs.append('.'.join(attribute))
        return matched_attrs
    
    def remove_attribute_by_head(self, queried_attr) -> int:
        if isinstance(queried_attr, list):
            queried_attr = '.'.join(queried_attr)
        queried_attr = queried_attr.split('.')
        remove_list = list()
        count = 0
        for attribute in self.attributes.values():
            if len(attribute) < len(queried_attr):
                continue
            i = 0
            good_match = True
            while i < min(len(attribute), len(queried_attr)):
                if attribute[i] != queried_attr[i]:
                    good_match = False
                    break
            if good_match:
                remove_list.append('.'.join(attribute))
                count += 1
        for e in remove_list:
            self.attributes.pop(e)
        return count
    
    def replace_wildcard(self, attr, val):
        if isinstance(attr, list):
            attr = '.'.join(attr)
        prior_elements = self.get_all_before_wildcard(attr)
        prior_elements += '.' + val
        self.remove_attribute(attr)
        self.add_attribute(prior_elements)
    
    def has_attribute_head(self, attr) -> bool:
        if isinstance(attr, list):
            attr = '.'.join(attr)
        return len(self.get_attributes_by_head(attr)) > 0
    
    def get_next(self, attr) -> set:
        if isinstance(attr, list):
            attr = '.'.join(attr)
        matched_attrs = self.get_attributes_by_head(attr)
        next_elements = set()
        attr = attr.split('.')
        for matched_attr in matched_attrs:
            matched_attr = matched_attr.split('.')
            if len(matched_attr) > len(attr):
                next_elements.add(matched_attr[len(attr)])
        return next_elements
            
    def get_all_before_wildcard(self, attr) -> list:
        if isinstance(attr, list):
            attr = '.'.join(attr)
        attr = attr.split('.')
        r_attr = list()
        for e in attr:
            if e == '*':
                break
            r_attr.append(e)
        return '.'.join(r_attr)
                
    def json(self) -> OrderedDict:
        '''
        Returns:
            course (OrderedDict): all course attributes within an ordered dictionary
                includes name, id, id2, major, credits, CI, HASS_inquiry, crosslisted,
                concentrations, pathways, presequisites, restricted, description.

                Some attributes will be omitted if empty, includes all attributes that
                are the form of a list or set.
        '''
        course = OrderedDict()
        for v in self.attributes.keys():
            elements = v.split('.')
            key = elements.pop(0)
            if (len(elements) == 1):
                rest = elements[0]
            else:
                rest = elements
            course.update({key : rest})
        return json.dumps(course)

    def __repr__(self):
        st = (f"{self.unique_name if self.unique_name else 'None'}: {self.subject if self.subject else 'None'} " + \
            f"{str(self.course_id)}{f'.{self.course_id2}' if self.course_id2 != 0 else ''}, " + \
            f"{self.course_credits} credits, " + \
            f"attributes: {list(self.attributes.keys())}" if len(self.attributes) > 0 else '' + '\n')
        return st.replace("set()", "none")

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, Course):
            return False
        if (self.name == other.name and self.course_id == other.course_id and self.course_id2 == other.course_id2 
            and self.subject == other.subject and self.course_credits == other.course_credits and self.cross_listed == other.cross_listed
            and self.attributes == other.attributes):
            return True
        return False
    
    def __add__(self, other):
        course = Course('ANY', 'ANY', 'ANY')
        for attr in self.attributes:
            course.add_attribute(attr)
        for attr in other.attributes:
            course.add_attribute(attr)
        course.description = self.description + '\n\n' + other.description
        course.cross_listed = self.cross_listed.union(other.cross_listed)
        return course

    def __hash__(self):
        return hash(self.course_id) + len(self.attributes)*10 + len(self.name)*100 + len(self.description)*1000
    