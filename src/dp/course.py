from array import *
from ..io.output import *
import json
from collections import OrderedDict

import logging

class Course():

    def __init__(self, name, subject, id, credits=0):
        # main attributes
        self.name = name
        self.unique_name = name
        self.subject = subject
        self.course_id = id
        self.course_id2 = 0
        self.level = str(id)[0]
        self.credits = credits
        self.attributes = dict() # dict of lists of items, e.g. {[concentration, AI], [CI, true]}
        
        self.validate_course_id()

        if name != '' and name != 'NA':
            self.set_name(name)
        if subject != '' and subject != 'NA':
            self.set_subject(subject)
        if id != 0 and id != -1:
            self.set_id(id)
        if credits != -1:
            self.set_credits(credits)

        self.cross_listed = set() # set of cross listed courses that should be treated as same course
        self.description = "" # text to be displayed describing the class
        

    """ Some input data for courses may not be in the desired format. 

        For example, most courses have an ID in the form of ####, but some
        have ####.##. We separate the latter form into 
        courseid = #### (numbers prior to dot) and courseid2 = ## (after dot)
        
        All data is modified in place, no arguments and return necessary
    """
    def validate_course_id(self, output:Output=None) -> None:
        if output == None: output = Output(OUT.CONSOLE)
        self.course_id = str(self.course_id)
        if isinstance(self.course_id, str):
            if '.' in self.course_id:
                split_num = self.course_id.split('.')
                if len(split_num) == 2 and split_num[0].isdigit() and split_num[1].isdigit():
                    self.course_id = int(split_num[0])
                    self.course_id2 = int(split_num[1])
                else:
                    logging.error(f"COURSE PARSING: 2 part ID not <int>.<int> for course " + self.name)
                    
            elif not self.course_id.isdigit():
                logging.error(f"COURSE PARSING: course number is not a number for course " + self.name)
            else:
                self.course_id = int(self.course_id)
        elif not isinstance(self.course_id, int):
            logging.error(f"COURSE PARSING: course number is not a number for course " + self.name)


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
        return self.course_id
    
    def get_id2(self):
        return self.course_id2
    
    def get_credits(self):
        return self.credits
    
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

    def set_id(self, id):
        self.course_id = id
        self.remove_attribute_by_head('course_id')
        self.add_attribute(f'course_id.{id}')
        self.remove_attribute_by_head('level')
        self.add_attribute(f'level.{str(id)[0]}')

    def set_id2(self, id):
        self.course_id = id
        self.remove_attribute_by_head('course_id')
        self.add_attribute(f'course_id2.{id}')

    def set_credits(self, credits):
        self.credits = credits
        self.remove_attribute_by_head('credits')
        self.add_attribute(f'credits.{credits}')
    

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
        next = set()
        attr = attr.split('.')
        for matched_attr in matched_attrs:
            matched_attr = matched_attr.split('.')
            if len(matched_attr) > len(attr):
                next.add(matched_attr[len(attr)])
        return next
            
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
                

    """
    Returns:
        course (OrderedDict): all course attributes within an ordered dictionary
            includes name, id, id2, major, credits, CI, HASS_inquiry, crosslisted,
            concentrations, pathways, presequisites, restricted, description.

            Some attributes will be omitted if empty, includes all attributes that
            are the form of a list or set.
    """
    def json(self) -> OrderedDict:
        course = OrderedDict()
        course.update({'name':self.name})
        course.update({'id':self.course_id})
        if self.course_id2 != 0:
            course.update({'id2':self.course_id2})
        course.update({'subject':self.subject})
        course.update({'credits':self.credits})
        course.update({'description':self.description})
        course.update(self.attributes)
        return json.dumps(course)

    def __repr__(self):
        st = (f"{self.unique_name if self.unique_name else 'None'}: {self.subject if self.subject else 'None'} " + \
            f"{str(self.course_id)}{f'.{self.course_id2}' if self.course_id2 != 0 else ''}, " + \
            f"{self.credits} credits, " + \
            f"attributes: {self.attributes.keys()}" if len(self.attributes) > 0 else '' + '\n')
        return st.replace("set()", "none")

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, Course):
            return False
        if (self.name == other.name and self.course_id == other.course_id and self.course_id2 == other.course_id2 
            and self.subject == other.subject and self.credits == other.credits and self.cross_listed == other.cross_listed
            and self.attributes == other.attributes):
            return True
        return False

    def __hash__(self):
        return int(self.course_id) + len(self.attributes)*10 + len(self.name)*100 + len(self.description)*1000