'''
Catalog class and get_course_match functions
'''

import json

from .course import Course
from .degree import Degree
from .course_template import *
from .search import Search
from ..io.output import *

class Catalog():
    '''
    A list of courses and degreees, one catalog should be generated for every planner

    Contains functions to find course match based on a template course and pool of courses
    to search from
    '''

    def __init__(self, name="main"):
        # TODO also store graphs for further analysis and course prediction of free electives
        self.name = name
        self.output = Output(OUT.CONSOLE)
        self.__course_list = dict() # course name as key
        self.__degree_list = dict() # degree name as key

        self.search = Search()
        self.lock = False

        # search must be reindexed after modification to course list
        self.reindex_flag = False

    def reindex(self):
        self.search.update_items(self.__course_list.keys())
        self.search.generate_index()

    def add_course(self, course:Course):
        self.reindex_flag = True
        self.__course_list.update({course.unique_name:course})

    def add_courses(self, courses:set):
        self.reindex_flag = True
        for c in courses:
            self.__course_list.update({c.unique_name:c})

    def remove_course(self, course:Course):
        self.__course_list.pop(course, None)

    def add_degree(self, degree:Degree):
        self.__degree_list.update({degree.name:degree})

    def add_degrees(self, degrees:set):
        for d in degrees:
            self.__degree_list.update({d.name:d})

    def remove_degree(self, degree:Degree):
        self.__degree_list.pop(degree, None)

    def get_course(self, course_name:str) -> Course:
        '''
        Parameters:
            course_name (str): name of course to get. Must be a unique name

        Returns:
            course (Course): course if found, otherwise None
        '''
        if self.reindex_flag:
            self.reindex()
            self.reindex_flag = False
        name = self.search.search(course_name.casefold())
        if len(name) == 0:
            return None
        if len(name) == 1:
            return self.__course_list.get(name[0], None)
        else:
            print(f"CATALOG ERROR: catalog get course non unique course found: {str(name)}")
            return self.__course_list.get(name[0], None)

    def get_all_courses(self):
        return list(self.__course_list.values())

    def get_all_course_names(self):
        return list(self.__course_list.keys())

    def get_degree(self, degree_name:str):
        return self.__degree_list.get(degree_name, None)

    def get_all_degrees(self):
        return self.__degree_list.values()

    def get_course_match(self, target_template:Template) -> list:
        ''' Intakes a criteria of courses that we want returned
            matches against the entire catalog

            Returns:
                matched dictionary (dict): { template : course set }
        '''
        return get_course_match(target_template, self.__course_list.values(), True)

    def json(self):
        catalog = dict()
        catalog.update({'courses':list(self.__course_list.keys())})
        catalog.update({'degrees':list(self.__degree_list.keys())})
        return json.dumps(catalog)

    def __repr__(self):
        count1 = 1
        printout = ""
        for course in self.__course_list.values():
            printout+=str(count1) + ": " + repr(course) + "\n"
            count1+=1
        count1 = 1
        for degree in self.__degree_list.values():
            printout+=str(count1) + ": " + repr(degree) + "\n"
            count1+=1
        return printout

    def __eq__(self, other):
        if not isinstance(other, Catalog):
            return False
        return self.get_all_courses() == other.get_all_courses()

    def __len__(self):
        return len(self.__course_list)
