'''
contains degree class and a set of helper functions
'''

import json
from .course_template import *

class Degree():
    '''
    Stores a list of rules, inserted in order of importance

    Rules will be computed sequentially for fulfillment. A rule computed first will
    be guaranteed the fact that subsequential rules cannot remove courses from its
    fulfillment set if it does not have any excess.

    rules can additionally be marked as high priority to compute its fulfillment first
    '''

    def __init__(self, name):
        self.name = name
        self.templates = list() # rules should be inserted in order of importance

    def fulfillment_all_wildcard_combos(self, taken_courses) -> None:
        '''
        Run fulfillment checking by generating all actual templates from wildcard templates
        and trying every combination to see which one is the best
        '''
        max_fulfillment_sets = list() # max fulfillment set for every template

        for template in self.templates:
            fulfillment_sets = get_course_match(template, taken_courses, True)

            # since get_course_match returns empty list if no fulfillment is found, we add
            # a template with an empty fulfillment set to make sure generate_combinatorics works
            if len(fulfillment_sets) == 0:
                fulfillment_sets.append(Fulfillment_Status(template, template.courses_required, set()))

            max_fulfillment_sets.append(fulfillment_sets)

        bound_array = [len(e) for e in max_fulfillment_sets] # number of actual templates/fulfillment sets per template
        combos = generate_combinatorics(bound_array, 1) # all possible combinations

        fulfillments = list()

        for combo in combos:
            templates_to_use = []
            print(f'combo: {combo}')
            for i in range(0, len(combo)):
                fulfillment_status = max_fulfillment_sets[i][combo[i] - 1]
                templates_to_use.append(fulfillment_status.get_template())
            fulfillment = self.fulfillment(templates_to_use, taken_courses)
            fulfillments.append(fulfillment)

        best_fulfillment_missing_count = 10000000
        best_fulfillment_set = None
        for fulfillment in fulfillments:
            missing = degree_num_unfulfilled(fulfillment)
            if missing < best_fulfillment_missing_count:
                best_fulfillment_set = fulfillment
                best_fulfillment_missing_count = missing

        return best_fulfillment_set

    '''
    def fulfillment(self, taken_courses, fulfillment_set) -> None:
    '''

    def fulfillment_of_template(self, template:Template, all_fulfillment:dict, taken_courses:set, no_recursion=False) -> list:
        '''
        Computes fulfillment status of a single rule

        Parameters:
            rule (Rule): rule being fulfilled
            all_fulfillment ({Rule:[Fulfillment_Status]}): all previously fulfilled statuses,
                passed by reference
            taken_courses (set): courses taken by user

        Returns:
            fulfillment ([Fulfillment_Status]): a list of fulfillment_status objects
        '''

        fulfilled_statuses = list()
        all_fulfillment.pop(template, None)
        """
        all courses that can possibily fulfill this rule, we will choose a subset from this list
        that minimally impacts other rules
        """

        requested_statuses_return = get_course_match(template, taken_courses, True)
        for requested_status_return in requested_statuses_return:
            """
            we order courses based on how many 'excessively fulfilled' sets it will impact

            an excessively fulfilled set refers to a template in which the fulfilled set
            is larger than required count, and thus can sacrifice a certain amount of courses
            from its fulfillment set without impacting its fulfilled status
            """
            requested_courses_ordered = courses_sort_bindings(all_fulfillment, requested_status_return)
            fulfillment_set = set()

            """
            we greedily grab courses from requested_courses_ordered that won't disturb
            the fulfillment of previous rules
            """
            for course in requested_courses_ordered:
                # a non no_replacement rule may share any course with another non no_replacement rule
                if not template.no_replacement and course_has_no_bindings(course, all_fulfillment):
                    fulfillment_set.add(course)
                    continue
                if not course_num_weak_bindings(all_fulfillment, course):
                    continue
                course_destroy_bindings(all_fulfillment, course)
                fulfillment_set.add(course)
            
            if not no_recursion and len(fulfillment_set) < requested_status_return.get_required_count():
                for prev_template, prev_fulfillments in all_fulfillment.items():
                    recompute = False
                    for curr_course in requested_courses_ordered:
                        if course_num_bindings({'rule':prev_fulfillments}, curr_course):
                            recompute = True
                    if not recompute:
                        continue
                    self.fulfillment_of_template(prev_template, all_fulfillment, taken_courses, True)
                    break
                return self.fulfillment_of_template(template, all_fulfillment, taken_courses, True)

            requested_status_return.set_fulfillment_set(fulfillment_set)
            fulfilled_statuses.append(requested_status_return)
            all_fulfillment.update({template:fulfilled_statuses})

        return fulfilled_statuses


    def fulfillment(self, templates:list, taken_courses:set) -> dict:
        '''
        Computes fulfillment of taken_courses against the degree rules

        Returns:
            status_return (dict): [rule : [fulfillment_status]]
                the fulfillment_statuses within the list represents the fulfillment
                of each template within that rule
        '''
        status_return = dict()

        """
        reorders self.rules by putting high priority rules in front

        for i in range(len(self.rules) - 1, 0, -1):
            if self.rules[i].high_priority:
                rule = self.rules.pop(i)
                self.rules.insert(0, rule)
        """
        for template in templates:
            status_return.update({template:self.fulfillment_of_template(template, status_return, taken_courses)})

        return status_return


    def json(self):
        '''
        Return this class as a json file
        '''
        degree = dict()
        degree.update({self.name:self.rules})
        return json.dumps(degree)


    def __repr__(self):
        rep = f"{self.name}: \n"
        return rep


    def __eq__(self, other):
        if not isinstance(other, Degree):
            return False
        if self.name == other.name and self.rules == other.rules:
            return True
        return False


    def __hash__(self):
        i = 0
        for rule in self.rules:
            i += hash(rule)
        i += hash(self.name)
        return i


######################################
# HELPER FUNCTIONS
######################################

def print_fulfillment(status_return:dict) -> str:
    """
    Print status_return dictionary in a neat string format
    """
    printout = ''
    for template, status_list in status_return.items():
        printout += f"Template '{template.name}':\n"
        for status in status_list:
            printout += (f"  Template '{status.template.name}':" + \
                f"\n    required count: {status.get_required_count()}" + \
                f"\n    actual count: {status.get_actual_count()}\n")
            simplified_fulfillment_set = set()
            for course in status.get_fulfillment_set():
                simplified_fulfillment_set.add(course.get_unique_name())
            printout += f"    fulfillment set: {simplified_fulfillment_set}\n"
    return printout

def generate_combinatorics(bound:list, start_index=1) -> list:
    if len(bound) == 0:
        return [[]]
    bound_cpy = copy.copy(bound)
    last_num = bound_cpy.pop(-1)
    nth_combo = []
    for i in range(start_index, last_num + start_index):
        prev_combos = generate_combinatorics(bound_cpy)
        for prev_combo in prev_combos:
            prev_combo.append(i)
            nth_combo.append(prev_combo)
    return nth_combo

def generate_bound(fulfillment_sets):
    bound = list()
    for fulfill_set in fulfillment_sets.values():
        bound.append(len(fulfill_set))
    return bound

def course_has_no_bindings(course, status:dict):
    '''
    Course is not in any rule with no_replacement, meaning another non no_replacement
    rule may use this rule for its fulfillment
    '''
    for template, fulfillment_statuses in status.items():
        for fulfillment_status in fulfillment_statuses:
            if course in fulfillment_status.get_fulfillment_set() and template.no_replacement:
                return False
    return True


def courses_sort_bindings(status_return:dict, requested_status_return:list) -> list:
    """
    bucket sort algorithm O(n) time, can be replaced by priority queue
    that runs in O(log(n)) time but I value my sanity
    
    if you wish to implement a priority queue system in this God forsakened chaos
    of a program then knock yourself out
    """
    requested_courses_ordered = list()

    requested_courses_bucket_sort = list()
    for course in requested_status_return.get_fulfillment_set():
        num_appear = course_num_bindings(status_return, course)
        for _ in range(0, num_appear - len(requested_courses_bucket_sort) + 1):
            requested_courses_bucket_sort.append(list())
        requested_courses_bucket_sort[num_appear].append(course)
    for bucket in requested_courses_bucket_sort:
        requested_courses_ordered.extend(bucket)
    return requested_courses_ordered


def course_num_weak_bindings(status:dict, course) -> bool:
    """
    Whether removing this course from all existing fulfillment sets will cause a fulfilled
    template to become unfulfilled
    """
    for fulfillment_statuses in status.values():
        for fulfillment_status in fulfillment_statuses:
            if course in fulfillment_status.get_fulfillment_set() and fulfillment_status.excess_count() == 0:
                return False
    return True


def course_destroy_bindings(status:dict, course) -> None:
    """
    Removes course from all existing fulfillment sets
    """
    for fulfillment_statuses in status.values():
        for fulfillment_status in fulfillment_statuses:
            if course in fulfillment_status.get_fulfillment_set():
                fulfillment_status.remove_fulfillment_course(course)


def course_num_bindings(status:dict, course) -> int:
    """
    Total number of appearances of course in all fulfillment sets
    """
    count = 0
    for fulfillment_statuses in status.values():
        for fulfillment_status in fulfillment_statuses:
            if course in fulfillment_status.get_fulfillment_set():
                count += 1
    return count


def degree_num_unfulfilled(status:dict) -> int:
    """
    Total number of unfulfilled courses across all fulfillment sets
    """
    count = 0
    for template_dict in status.values():
        for template_status in template_dict:
            count += max(0, template_status.get_required_count() - template_status.get_actual_count())
    return count
