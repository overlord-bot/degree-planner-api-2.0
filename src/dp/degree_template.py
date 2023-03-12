'''
Course Template object
'''

import copy
from .course import Course
from .fulfillment_status import Fulfillment_Status

class Template():
    '''
    This class contains a template course, which contains attributes that
    serves as a filter for courses, and a course set, which is the pool of
    courses we filter from.
    '''

    def __init__(self, name, template_course=None, course_set=None, replacement=False, courses_required=1):
        if template_course == None: template_course = Course('ANY', 'ANY', 'ANY')
        if course_set == None: course_set = set()

        self.name = name
        self.template_course = template_course
        self.course_set = course_set
        self.courses_required = courses_required

        self.replacement = replacement
        self.importance = 0 # used internally by degree, higher the number the more important it is


    def __repr__(self):
        s = f"Template {self.name}:\n"
        s += f"  {repr(self.template_course)}\n"
        s += f"course_set: "
        s += ",".join(self.course_set)
        return s
    
    def __str__(self):
        return self.name

    def __len__(self):
        return len(self.course_set)

    def __eq__(self, other):
        if not isinstance(other, Template):
            return False
        
        if other.template_course != self.template_course:
            return False
        
        mylist = self.course_set
        otherlist = other.course_set

        for course in mylist:
            if course not in otherlist:
                return False
            otherlist.remove(course)
        if otherlist:
            if other.template_course != self.template_course:
                return False
        return True
    
    def __lt__(self, other):
        return self.importance < other.importance

    def __gt__(self, other):
        return self.importance > other.importance

    def __add__(self, other):
        return Template(f'{self.name} + {other.name}', self.template_course + other.template_course, 
            self.course_set.union(other.course_set), self.replacement & other.replacement, self.courses_required + other.courses_required)

    def __hash__(self):
        i = hash(self.template_course)**2
        for course in self.course_set:
            i += hash(course)
        return i

def get_course_match(template:Template, course_pool=None, head=True) -> list:
    ''' Intakes a criteria of courses that we want returned
        For example, if the template specifies 2000 as course ID, then all 2000 level courses inside
        the template's course list is returned
    
        Parameters: a template with ONLY the attributes we want to require changed to their required states

        Returns: [ Fulfillment_Status ] : a list of fulfillment_status objects each containing template course
            used, required course count and fulfillment set
    '''
    fulfillment_sets = list()

    if head:
        if isinstance(template, Course):
            template = Template(template.get_unique_name() + ' template', template)
        if course_pool is None:
            course_pool = template.course_set
        elif template.course_set:
            course_pool = {e for e in course_pool if e in template.course_set}

    leaf = True

    for target_attribute in template.template_course.attributes.values():
        if 'NA' in target_attribute or 'ANY' in target_attribute or '-1' in target_attribute:
            continue

        # any course without a wildcard is considered a leaf
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
            for course in course_pool:
                possible_values = possible_values.union(course.get_next(course.get_all_before_wildcard(target_attribute)))
            for val in possible_values:
                template_copy = copy.deepcopy(template)
                template_copy.template_course.replace_wildcard(target_attribute, val)
                fulfillment_sets.extend(get_course_match(template_copy, course_pool, False))
    if leaf:
        fulfillment_sets.append(Fulfillment_Status(template, template.courses_required, course_pool))
        
    # return an empty fulfillment set if there are no matches
    if head and not len(fulfillment_sets):
        fulfillment_sets.append(Fulfillment_Status(template, template.courses_required, course_pool))
        
    return fulfillment_sets
