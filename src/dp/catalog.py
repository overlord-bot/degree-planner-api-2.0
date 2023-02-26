from array import *
import copy
import json

from .course import Course
from .degree import Degree
from .course_template import Template
from .search import Search
from ..io.output import *

class Catalog():

    def __init__(self, name="main"):
        # catalog will be a list of courses and degrees
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

    def add_degree(self, degree:Degree):
        self.__degree_list.update({degree.name:degree})

    def add_degrees(self, degrees:set):
        for d in degrees:
            self.__degree_list.update({d.name:d})

    def get_course(self, course_name:str) -> Course:
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
        return self.__course_list.values()

    def get_all_course_names(self):
        return self.__course_list.keys()

    def get_degree(self, degree_name:str):
        return self.__degree_list.get(degree_name, None)

    def get_all_degrees(self):
        return self.__degree_list.values()

    """ Matches against entire catalog
    """
    def get_course_match(self, target_template:Template) -> dict:
        return get_course_match(target_template, self.__course_list.values(), True)

    def get_best_course_match(self, target_template:Template) -> set:
        return get_best_course_match(target_template, self.__course_list.values())

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


""" Intakes a criteria of courses that we want returned
    For example, if the template specifies 2000 as course ID, then all 2000 level courses inside
    the template's course list is returned
    
    Parameters: a template with ONLY the attributes we want to require changed to their required states

    Returns: { fulfilled template (useful for when wildcards are used) : course set }
"""
def get_course_match(template:Template, course_pool=None, head=False) -> dict:
    output = Output(OUT.CONSOLE)
    course_sets = dict()

    if head:
        head = False
        if isinstance(template, Course):
            template = Template(template.get_unique_name() + ' template', template)
        if course_pool == None:
            course_pool = template.course_set
        elif template.course_set:
            course_pool = {e for e in course_pool if e in template.course_set}

    leaf = True

    for target_attribute in template.template_course.attributes.values():
        if 'NA' in target_attribute or 'ANY' in target_attribute or '-1' in target_attribute:
            continue
        if '*' not in target_attribute:
            course_pool = {e for e in course_pool if e.has_attribute(target_attribute)}
        else:
            leaf = False

    for target_attribute in template.template_course.attributes.values():
        if '*' in target_attribute:

            ''' DEBUG
            for course in course_pool:
                print('all before wildcard: ' + str(course.get_all_before_wildcard(target_attribute)))
                print('get next: ' + str(course.get_next(course.get_all_before_wildcard(target_attribute))))
                break
            '''

            possible_values_sets = [course.get_next(course.get_all_before_wildcard(target_attribute)) for course in course_pool if len(course.get_next(course.get_all_before_wildcard(target_attribute)))]
            possible_values = set()
            for possible_values_set in possible_values_sets:
                possible_values = possible_values.union(possible_values_set)
            for val in possible_values:
                template_copy = copy.deepcopy(template)
                template_copy.template_course.replace_wildcard(target_attribute, val)
                course_sets.update(get_course_match(template_copy, course_pool))
    if leaf:
        course_sets.update({template:copy.deepcopy(course_pool)})
    return course_sets

def get_best_course_match(target_template:Template, course_pool:set) -> set:
    matched_pools = get_course_match(target_template, course_pool, True)
    
    size = 0
    best_template = target_template
    best_fulfillment = set()
    for k, v in matched_pools.items():
        if len(v) > size:
            size = len(v)
            best_template = k
            best_fulfillment = v
    return best_fulfillment
