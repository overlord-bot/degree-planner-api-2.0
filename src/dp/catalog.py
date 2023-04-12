'''
Catalog class
'''

import json

from .course import Course
from .degree import Degree
from .template import *
from ..math.search import Search
from ..recommender.recommender import Recommender
from ..io.output import *

class Catalog():
    '''
    A list of courses and degreees, one catalog should be generated for every planner

    Contains functions to find course match based on a template course and pool of courses
    to search from
    '''

    def __init__(self, enable_tensorflow=True):
        # TODO also store graphs for further analysis and course prediction of free electives
        self.__course_list = dict() # course name as key
        self.__degree_list = dict() # degree name as key

        self.tags = dict() # { subject : [tags] }
        self.recommender = Recommender(self, enable_tensorflow=enable_tensorflow)
        self.searcher = Search()
        self.debug = Output(OUT.DEBUG)

    def reindex(self, enable_recommender=True):
        self.debug.info('starting search indexing')
        self.searcher.update_items(self.course_names())
        self.searcher.generate_index()
        self.debug.info('finished search indexing')

        if not enable_recommender:
            return
        
        self.debug.info('starting recommender reindex')
        self.recommender.reindex()
        self.debug.info('finished recommender reindex')

    def load_cache(self):
        self.recommender.load_cache()

    def add_course(self, course):
        if hasattr(course, '__iter__'):
            for c in course:
                self.__course_list.update({c.unique_name:c})
            return
        self.__course_list.update({course.unique_name:course})

    def remove_course(self, course):
        if isinstance(course, str):
            self.__course_list.pop(course, None)
        else:
            self.__course_list.pop(course.unique_name, None)

    def add_degree(self, degree:Degree):
        self.__degree_list.update({degree.name:degree})

    def has_degree(self, degree):
        if isinstance(degree, Degree):
            return degree.name in self.__degree_list
        elif isinstance(degree, str):
            return degree in self.__degree_list

    def remove_degree(self, degree):
        if isinstance(degree, str):
            self.__degree_list.pop(degree, None)
        else:
            self.__degree_list.pop(degree.name, None)

    def get_course(self, unique_name:str) -> Course:
        '''
        Parameters:
            course_name (str): name of course to get. Must be a unique name

        Returns:
            course (Course): course if found, otherwise None
        '''
        name = self.search(unique_name)
        if len(name) == 0:
            self.debug.print('CANNNT FIND COURSE ' + unique_name, OUT.WARN)
            return None
        if len(name) == 1:
            return self.__course_list.get(name[0], None)
        else:
            self.debug.print(f"CATALOG ERROR: catalog get course non unique course found: {str(name)}", OUT.WARN)
            return self.__course_list.get(name[0], None)

    def search(self, course_name:str) -> str:
        return self.searcher.search(course_name.casefold())

    def courses(self):
        return self.__course_list.values()

    def course_names(self):
        return list(self.__course_list.keys())

    def get_degree(self, degree_name:str):
        return self.__degree_list.get(degree_name, None)

    def degrees(self):
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
    
    def __str__(self):
        count1 = 1
        printout = ""
        for course in self.__course_list.values():
            printout+=str(count1) + ": " + str(course) + "\n"
            count1+=1
        count1 = 1
        for degree in self.__degree_list.values():
            printout+=str(count1) + ": " + repr(degree) + "\n"
            count1+=1
        return printout

    def __iter__(self):
        for course in self.__course_list.values():
            yield course

    def __eq__(self, other):
        if not isinstance(other, Catalog):
            return False
        return self.courses() == other.courses()

    def __len__(self):
        return len(self.__course_list)
