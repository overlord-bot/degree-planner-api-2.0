'''
Course class
'''

import json
from collections import OrderedDict
from ..io.output import *

class Course():
    '''
    Course object containing a dictionary of attributes that uniquely defines the course
    and can be used to search/filter for it

    It also has attributes for fast access which should remain consistent with the attribute
    dictionary
    '''

    def __init__(self, name, subject, id):
        # main attributes
        self.unique_name = name

        self.name = name
        self.subject = subject
        self.course_id = id

        self.embedding_relevance = None # relative distances to the embedding of all keywords within this courses's subject

        # dict of lists of items, e.g. {'concentration.ai':[concentration, ai], 'ci.true':[ci, true]}
        self.attributes = dict()
        self.keywords = list()

        if name not in ('', 'NA', 'ANY'):
            self.set_name(name)
        if subject not in ('', 'NA', 'ANY'):
            self.set_subject(subject)
        if id not in (0, -1, '', 'NA', 'ANY'):
            self.set_id(id)
            if len(str(id)):
                self.set_level(str(id)[0])

        self.description = "" # text to be displayed describing the class
        

    """ 
    Getters
    """
    
    def get_name(self):
        return self.name
    
    def get_unique_name(self):
        return self.unique_name
    
    def get_subject(self):
        return self.subject
    
    def get_id(self):
        return self.course_id
    
    # determines the level of the course, 1000=1, 2000=2, 4000=4, etc
    def get_level(self):
        return self.attr('level')
    
    def get_credits(self):
        return self.attr('credits')
    
    def get_crosslisted(self):
        return [self.val(e) for e in self.get_attributes_by_head('cross_listed')]
    

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
            self.unique_name = f"{self.get_subject().casefold()} {str(self.get_id())} {self.get_name().strip().casefold()}"
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

    def set_credits(self, course_credits):
        self.remove_attribute_by_head('credits')
        self.add_attribute(f'credits.{course_credits}')

    def set_level(self, level):
        self.remove_attribute_by_head('level')
        self.add_attribute(f'level.{level}')
    

    """
    Attributes are expressed as elements joined by periods, 
    but are internally stored in this class as a list
    """
    
    def add_attribute(self, attr) -> None:
        if isinstance(attr, list):
            attr = '.'.join(attr)
        self.attributes.update({attr.casefold():attr.casefold().split('.')})

    def replace_attribute(self, old_head, attr) -> None:
        '''
        removes all attributes with the given head, and replaces it with the provided attribute
        '''
        if isinstance(attr, list):
            attr = '.'.join(attr)
        self.remove_attribute_by_head(old_head)
        self.add_attribute(attr)

    def remove_attribute(self, attr) -> None:
        '''
        removes attribute with exact match
        '''
        if isinstance(attr, list):
            attr = '.'.join(attr)
        self.attributes.pop(attr)

    def has_attribute(self, attr) -> bool:
        '''
        finds if the attribute exactly matches one stored here
        '''
        if isinstance(attr, list):
            attr = '.'.join(attr)
        return attr in self.attributes.keys()
    
    def val(self, attr) -> str:
        '''
        helper function to return everything in the provided attribute string after the first period
        '''
        attr = attr.split('.')
        if len(attr) < 2:
            return None
        attr.pop(0)
        return '.'.join(attr)
    
    def attr(self, attr:str) -> str:
        '''
        finds unique attribute match within self and returns the value
        '''
        attrs = self.get_attributes_by_head(attr)
        if len(attrs) != 1:
            return None
        return self.val(attrs[0])
    
    def get_attributes_by_head(self, queried_attr) -> list:
        if isinstance(queried_attr, list):
            queried_attr = '.'.join(queried_attr)
        queried_attr = queried_attr.split('.')
        matched_attrs = list()
        for attr_string, attribute in self.attributes.items():
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
                matched_attrs.append(attr_string)
        return matched_attrs
    
    def remove_attribute_by_head(self, queried_attr) -> int:
        '''
        removes all attributes matching the provided head
        '''
        if isinstance(queried_attr, list):
            queried_attr = '.'.join(queried_attr)
        queried_attr = queried_attr.split('.')
        remove_list = list()
        count = 0
        for attr_string, attribute in self.attributes.items():
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
                remove_list.append(attr_string)
                count += 1
        for e in remove_list:
            self.attributes.pop(e)
        return count
    
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
        st = (f"{self.unique_name if self.unique_name else 'None'}:\n{self.get_credits()} credits\n" + \
            f"crosslisted with: {str([str(e) for e in self.get_crosslisted()])}\n" + \
            f"attributes: {list(self.attributes.keys())}" if len(self.attributes) > 0 else '' + '\n')
        return st.replace("set()", "none")

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, Course):
            return False
        if (self.name == other.name and self.course_id == other.course_id
            and self.subject == other.subject and self.attributes == other.attributes):
            return True
        return False
    
    def __add__(self, other):
        course = Course('ANY', 'ANY', 'ANY')
        for attr in self.attributes:
            course.add_attribute(attr)
        for attr in other.attributes:
            course.add_attribute(attr)
        course.description = self.description + '\n\n' + other.description
        return course

    def __hash__(self):
        return hash(self.course_id) + len(self.attributes)*10 + hash(self.unique_name)*100
    