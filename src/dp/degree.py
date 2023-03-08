'''
contains degree class and a set of helper functions
'''

import json
import timeit
from .course_template import *
from .graph import Graph
from .graph import Course_Overlap

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


    def generate_template_combinations(self, taken_courses) -> list:
        '''
        generates a list of all possible template combinations resulted from wildcard usage
        '''
        max_fulfillment_sets = list() # max fulfillment set for every template

        for template in self.templates:
            """
            compute fulfillment sets for all template in the order they appear in self.templates
            note that the order can influence fulfillment success, and earlier templates receive
            priority to being fulfilled
            """
            max_fulfillment_sets.append(get_course_match(template, taken_courses))

        # if template contains wildcards, this is how many templates can result from the wildcard
        bound_array = [len(e) for e in max_fulfillment_sets]

        # all possible combinations using all generated templates
        combos = generate_combinatorics(bound_array, 1)

        all_template_combinations = list()

        for combo in combos:
            templates_to_use = []

            # generates the combination of templates to use
            for i in range(0, len(combo)):
                # gets the fulfillment status to use based on the number in combo
                fulfillment_status = max_fulfillment_sets[i][combo[i] - 1]
                # gets the template we should use
                templates_to_use.append(fulfillment_status.get_template())

            all_template_combinations.append(templates_to_use)
        
        return all_template_combinations


    def fulfillment(self, taken_courses) -> None:
        '''
        Run fulfillment checking by generating all actual templates from wildcard templates
        and trying every combination to see which one is the best
        '''
        start = timeit.default_timer()
        # all fulfillment sets based on each possible combination of templates resulted from wildcard templates
        fulfillments = list()

        for template_set in self.generate_template_combinations(taken_courses):
            
            """
            all courses that can possibily fulfill this rule, we will choose a subset from this list
            that minimally impacts other rules
            """
            max_fulfillments = dict()
            for template in template_set:
                max_fulfillments.update({template:get_course_match(template, taken_courses)[0]})

            # runs fulfillment checking using this specific combination of templates
            all_fulfillment = dict()
            for template in template_set:
                all_fulfillment.update({template:self.template_fill(template, all_fulfillment, max_fulfillments)})

            for template in template_set:
                self.template_steal(template, all_fulfillment, max_fulfillments)

            fulfillments.append(all_fulfillment)

        # checks all fulfillment sets and return the best one
        best_fulfillment_set = None
        for fulfillment in fulfillments:
            if best_fulfillment_set is None or degree_num_unfulfilled(fulfillment) < degree_num_unfulfilled(best_fulfillment_set):
                best_fulfillment_set = fulfillment

        end = timeit.default_timer()
        print('\nfulfillment runtime: ', end - start, '\n')
        return best_fulfillment_set


    def template_fill(self, template:Template, all_fulfillment:dict, max_fulfillments:dict, order_courses:bool=False, force:bool=False) -> Fulfillment_Status:
        '''
        Computes fulfillment status of a single template

        Parameters:
            template (Template): template being fulfilled, must not contain wildcards
            all_fulfillment ({Template:Fulfillment_Status}): all previously fulfilled statuses
            taken_courses (set): courses taken by user

        Returns:
            fulfillment (Fulfillment_Status): fulfillment status of the current template
        '''

        requested_fulfillment = max_fulfillments.get(template)
        if order_courses:
            potential_courses = courses_sort_bindings(max_fulfillments, requested_fulfillment)
        else:
            potential_courses = requested_fulfillment.get_fulfillment_set()

        this_fulfillment = Fulfillment_Status(template, template.courses_required, set())

        """
        we grab all courses from potential_courses that won't disturb
        the fulfillment of previous rules
        """
        for course in potential_courses:
            if course_num_bindings(all_fulfillment, course) == 0:
                # course hasn't been added to any fulfillment sets yet
                this_fulfillment.add_fulfillment_course(course)
                all_fulfillment.update({template:this_fulfillment})
                continue

            if course_can_unbind(all_fulfillment, course):
                # we are free to remove the course from its original places and add it here
                course_destroy_bindings(all_fulfillment, course)
                this_fulfillment.add_fulfillment_course(course)
                all_fulfillment.update({template:this_fulfillment})
                continue

        return this_fulfillment


    def template_steal(self, template:Template, all_fulfillment:dict, max_fulfillments:dict):
        '''
        try to steal any courses it can from other templates
        '''
        this_fulfillment = all_fulfillment.get(template)
        while this_fulfillment.unfulfilled_count() > 0:
            # initial layer is all fulfillment statuses with excess
            bfs_roots = set()
            overlap_calculator = Course_Overlap(max_fulfillments)
            graph = Graph(set(all_fulfillment.values()), overlap_calculator)
            
            # generate links between fulfillment statuses
            for fulfillment_status1 in all_fulfillment.values():
                if fulfillment_status1.excess_count() > 0:
                    bfs_roots.add(fulfillment_status1)
                for fulfillment_status2 in all_fulfillment.values():
                    graph.try_add_connection(fulfillment_status1, fulfillment_status2)

            #print('graph: ' + str(graph))

            bfs = graph.bfs(bfs_roots)
            if not bfs.contains_child(this_fulfillment):
                break
            
            # calculates path to move courses
            path = bfs.get_path(this_fulfillment)
            print('path: ' + ' -> '.join([str(e) for e in path]))

            # shifts courses along the path such that we obtain a new course
            for i in range(0, len(path) - 1):
                giver = path[i]
                receiver = path[i + 1]
                transferred_course = graph.edge_data(giver, receiver, True)
                print('transferring course: ' + str(transferred_course))
                giver.remove_fulfillment_course(transferred_course)
                receiver.add_fulfillment_course(transferred_course)
                all_fulfillment.update({giver.get_template():giver})
            
            all_fulfillment.update({path[-1].get_template():path[-1]})


    def template_trade(self, template, all_fulfillment, max_fulfillments):
        '''
        try to exchange courses from other replacement templates by receiving
        a course that fulfills both self and the other replacement template
        '''
        this_fulfillment = all_fulfillment.get(template)


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

def print_fulfillment(all_fulfillment:dict) -> str:
    """
    Print status_return dictionary in a neat string format
    """
    printout = ''
    for status in all_fulfillment.values():
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


def generate_bound(all_fulfillment:dict):
    bound = list()
    for fulfill_set in all_fulfillment.values():
        bound.append(len(fulfill_set))
    return bound


def courses_sort_bindings(all_fulfillment:dict, requested_fulfillment:list) -> list:
    """
    bucket sort algorithm O(n) time, can be replaced by priority queue
    that runs in O(log(n)) time but I value my sanity
    
    if you wish to implement a priority queue system in this God forsakened chaos
    of a program then knock yourself out
    """
    requested_courses_ordered = list()

    requested_courses_bucket_sort = list()
    for course in requested_fulfillment.get_fulfillment_set():
        num_appear = course_num_bindings(all_fulfillment, course)
        for _ in range(0, num_appear - len(requested_courses_bucket_sort) + 1):
            requested_courses_bucket_sort.append(list())
        requested_courses_bucket_sort[num_appear].append(course)
    for bucket in requested_courses_bucket_sort:
        requested_courses_ordered.extend(bucket)
    return requested_courses_ordered


def course_can_unbind(all_fulfillment:dict, course) -> bool:
    """
    true if removing this course from all existing fulfillment sets will not cause a fulfilled
    template to become unfulfilled
    """
    for fulfillment_status in all_fulfillment.values():
        if course in fulfillment_status.get_fulfillment_set() and fulfillment_status.excess_count() == 0:
            return False
    return True


def course_destroy_bindings(all_fulfillment:dict, course) -> None:
    """
    Removes course from all existing fulfillment sets
    """
    for fulfillment_status in all_fulfillment.values():
        if course in fulfillment_status.get_fulfillment_set():
            fulfillment_status.remove_fulfillment_course(course)


def course_num_bindings(all_fulfillment:dict, course) -> int:
    """
    Total number of appearances of course in all fulfillment sets
    """
    count = 0
    for fulfillment_status in all_fulfillment.values():
        if isinstance(course, list):
            for c in course:
                if c in fulfillment_status.get_fulfillment_set():
                    count += 1
        elif course in fulfillment_status.get_fulfillment_set():
            count += 1
    return count


def degree_num_unfulfilled(all_fulfillment:dict) -> int:
    """
    Total number of unfulfilled courses across all fulfillment sets
    """
    count = 0
    for fulfillment_status in all_fulfillment.values():
        count += max(0, fulfillment_status.get_required_count() - fulfillment_status.get_actual_count())
    return count
