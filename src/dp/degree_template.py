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
        s += f"  replacement: {self.replacement}\n"
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
        return i


###################################################################################################
#
# CONTEXT FREE GRAMMAR PARSING (thanks programming languages I do not miss you)
#
###################################################################################################


def course_fulfills_template(template:Template, course:Course) -> tuple[bool, dict]:
    conditions = dict()
    for attr in template.template_course.attributes.keys():
        if 'NA' in attr or 'ANY' in attr or '-1' in attr:
            continue
        if not parse_attribute(attr, course, conditions):
            return False, {}
    # print(f'conditions for {course} in {template} : {conditions}')
    return True, conditions

def single_attribute_evaluation(attr:str, course:Course) -> tuple[str, dict]:
    attr = attr.strip()
    if attr == '':
        return True, {}
    if attr == 'True':
        return True, {}
    if attr == 'False':
        return False, {}
    if attr in ('True', 'False', True, False):
        return attr
    if '*' in attr:
        matches = course.get_attributes_by_head(attr[:attr.find('*') - 1])
        return len(matches) > 0, {attr:matches}
    if '#' in attr:
        return len(course.get_attributes_by_head(attr[:attr.find('#') - 1])) > 0, {}
    return course.has_attribute(attr), {}

def parse_attribute(input:str, course:Course, true_given_for_wildcards:dict=None) -> str:
    '''
    Input -> Attribute
    Input -> True|False
    Input -> (Input)
    Input -> Input & Input
    Input -> Input | Input

    single_attribute_evaluation(Attribute, course) -> True|False

    returns a True or False value based on whether the course fulfills the template
    '''
    # print('accepted input ' + str(input))

    if '(' in input:
        open_bracket_loc = input.find('(')
        close_bracket_loc = len(input) # we allow close brackets to be omitted if it's at the end of the input
        passed_bracket_count = 0

        # calculate the location of the closing bracket for the current bracket
        for i in range(open_bracket_loc + 1, len(input)):
            if input[i] == '(':
                passed_bracket_count += 1
            if input[i] == ')':
                if passed_bracket_count == 0:
                    close_bracket_loc = i
                    break
                passed_bracket_count -= 1

        new_string = input[: open_bracket_loc] + str(parse_attribute(input[open_bracket_loc + 1 : close_bracket_loc], course, true_given_for_wildcards)) + input[close_bracket_loc + 1:]
        return parse_attribute(new_string, course, true_given_for_wildcards)
    
    elif '&' in input:
        and_loc = input.find('&')
        return parse_attribute(input[: and_loc], course, true_given_for_wildcards) and parse_attribute(input[and_loc + 1:], course, true_given_for_wildcards)
    
    elif '|' in input:
        and_loc = input.find('|')
        return parse_attribute(input[: and_loc], course, true_given_for_wildcards) or parse_attribute(input[and_loc + 1:], course, true_given_for_wildcards)
    
    else:
        truth, true_given_entries = single_attribute_evaluation(input, course)
        if len(true_given_entries):
            true_given_for_wildcards.update(true_given_entries)
        return truth


def get_course_match(template:Template, courses) -> list:
    fulfillment_sets = list() # all possible fulfillments based on different combinations resulting from wildcard sauge
    all_conditions = dict() # all possible wildcard replacement conditions that can influence the result (wildcard branching)

    # current fulfillment set, will be added only if current template does not contain wildcards
    # (recursive calls remove one wildcard at a time), so essentially "leaf" branches
    # get to add their fulfillment to fulfillment_sets
    curr_fulfillment = Fulfillment_Status(template, template.courses_required, set())

    for course in courses:
        good_match, conditions = course_fulfills_template(template, course)

        # updates all_conditions with possible values for wildcard replacement
        for condition, condition_sat_set in conditions.items():
            current_condition_set = all_conditions.get(condition, set())
            current_condition_set.update(condition_sat_set)
            all_conditions.update({condition:current_condition_set})

        # if this is a leaf call (no wildcard branching), add to current fulfillment set
        if good_match and not len(conditions):
            curr_fulfillment.add_fulfillment_course(course)

    # if this is a leaf call (no wildcard branching), add to main fulfillment set
    if not len(all_conditions):
        fulfillment_sets.append(curr_fulfillment)

    # if there are wildcard branching needed (we only need to pop the first one, the rest is handled by the following recursive calls
    # as each recursive call only needs to handle one)
    if not len(all_conditions):
        return fulfillment_sets
    wildcard_attr, wildcard_choices = all_conditions.popitem()

    for choice in wildcard_choices:
        # for each branching choice, make a copy of the template with the wildcard replaced with a possible value
        template_cpy = copy.deepcopy(template)

        # a temporary dictionary holding the old/new values, since we cannot update dictionary keys
        # while iterating through it
        replace_attributes = dict()

        for attribute_str in template_cpy.template_course.attributes.keys():
            if wildcard_attr not in attribute_str:
                continue

            # we make a note of the replacements needed by storing it in replace_attributes
            attribute_str_update = attribute_str.replace(wildcard_attr, choice)
            replace_attributes.update({attribute_str:attribute_str_update})

        # we commit the changes to the dictionary while iterating through the replace_attributes we made previously
        for old, new in replace_attributes.items():
            template_cpy.template_course.remove_attribute(old)
            template_cpy.template_course.add_attribute(new)

        # recursively call this function, we're guaranteed that the final return values all are wildcard-free
        fulfillment_sets.extend(get_course_match(template_cpy, courses))

    # print(f'all conditions: ' + str(all_conditions))
    # print(f'fulfillments: ' + str([repr(e) for e in fulfillment_sets]))

    return fulfillment_sets


def get_course_match_old(template:Template, course_pool=None, head=True) -> list:
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
        elif len(template.course_set):
            course_pool = {e for e in course_pool if e in template.course_set}
    leaf = True

    for target_attribute in template.template_course.attributes.keys():
        if 'NA' in target_attribute or 'ANY' in target_attribute or '-1' in target_attribute:
            continue

        # any course without a wildcard is considered a leaf
        if '*' not in target_attribute:
            if '/' in target_attribute:
                # if we find the or symbol, compute match with each attr in the disjunction
                # then take the union
                or_union = set()
                for or_attr in target_attribute.split('/'):
                    or_union.update({e for e in course_pool if e.has_attribute(or_attr)})
                course_pool = or_union
            else:
                course_pool = {e for e in course_pool if e.has_attribute(target_attribute)}
            # print('course pool match: ' + str({str(e) for e in course_pool}))
        else:
            leaf = False

    for target_attribute in template.template_course.attributes.values():
        if '*' in target_attribute:
            possible_values = set()
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
