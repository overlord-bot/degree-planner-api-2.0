'''
contains degree class and a set of helper functions
'''

import json
import timeit
from enum import Enum
from .course_template import *
from .graph import Graph
from .graph import Backwards_Overlap
from .graph import Forwards_Overlap

class Bind_Type(Enum):
    NR = 1
    R = 2
    ALL = 3

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
        self.templates = list()

    def add_template(self, template:Template):
        '''
        templates should be inserted in order of importance
        '''
        if not len(self.templates):
            template.importance = 0
        else:
            template.importance = self.templates[-1].importance - 1
        self.templates.append(template)

    def remove_template(self, template:Template):
        self.templates.remove(template)

    def has_template(self, template:Template):
        return template in self.templates
    

    ##############################################################################################
    # fulfillment computation
    ##############################################################################################

    def generate_template_combinations(self, taken_courses) -> list:
        '''
        generates a list of all possible template combinations resulted from wildcard usage
        '''
        # max fulfillment set for every template, including wildcards
        max_fulfillments = list()
        for template in self.templates:
            max_fulfillments.append(get_course_match(template, taken_courses))

        # if template contains wildcards, this is how many templates can result from the wildcard
        bound_array = [len(e) for e in max_fulfillments]

        # all possible combinations using all generated templates
        combos = generate_combinatorics(bound_array, 1)

        # we make a list of all the template combinations
        all_template_combinations = list()

        for combo in combos:
            templates_to_use = []

            # generates the combination of templates to use
            for i in range(0, len(combo)):
                # gets the fulfillment status to use based on the number in combo
                fulfillment_status = max_fulfillments[i][combo[i] - 1]
                # gets the template we should use
                templates_to_use.append(fulfillment_status.get_template())
            all_template_combinations.append(templates_to_use)
        
        return all_template_combinations


    def fulfillment(self, taken_courses:set) -> None:
        '''
        Run fulfillment checking by generating all actual templates from wildcard templates
        and trying every combination to see which one is the best
        '''
        start = timeit.default_timer()
        # all fulfillment sets based on each possible combination of templates resulted from wildcard templates
        potential_fulfillments = list()

        for template_set in self.generate_template_combinations(taken_courses):

            # all courses that fulfills each template
            max_fulfillments = dict()
            for template in template_set:
                max_fulfillments.update({template:get_course_match(template, taken_courses)[0]})

            # runs fulfillment checking using this specific combination of templates
            all_fulfillment = dict()
            for template in template_set:
                all_fulfillment.update({template:self.template_fill(template, all_fulfillment, max_fulfillments)})

            for template in template_set:
                self.template_steal(template, all_fulfillment, max_fulfillments)

            for template in template_set:
                self.template_trade(template, all_fulfillment, max_fulfillments)

            potential_fulfillments.append(all_fulfillment)

        # checks all fulfillment sets and return the best one
        best_fulfillment = None
        for fulfillment in potential_fulfillments:
            if best_fulfillment is None or num_unfulfilled_course_slots(fulfillment) < num_unfulfilled_course_slots(best_fulfillment):
                best_fulfillment = fulfillment

        end = timeit.default_timer()
        print('\nfulfillment runtime: ', end - start, '\n')
        return best_fulfillment


    def template_fill(self, template:Template, all_fulfillment:dict, max_fulfillments:dict, force:bool=False) -> Fulfillment_Status:
        '''
        Computes fulfillment status of a single template

        Parameters:
            template (Template): template being fulfilled, must not contain wildcards
            all_fulfillment ({Template:Fulfillment_Status}): all previously fulfilled statuses
            taken_courses (set): courses taken by user

        Returns:
            fulfillment (Fulfillment_Status): fulfillment status of the current template
        '''

        requested_courses = max_fulfillments.get(template).get_fulfillment_set()
        this_fulfillment = Fulfillment_Status(template, template.courses_required, set())

        """
        we grab all courses from potential_courses that won't disturb
        the fulfillment of previous templates
        """
        for course in requested_courses:
            if not len(bindings_all(all_fulfillment, course)) or (template.replacement and not len(bindings_with_NR_templates(all_fulfillment, course))):
                # course hasn't been added to any fulfillment sets yet, or if this template is replacement enabled
                # and the course is not in any no replacement templates
                this_fulfillment.add_fulfillment_course(course)
                all_fulfillment.update({template:this_fulfillment})
                continue

            if has_only_weak_bindings(all_fulfillment, course):
                # we are free to remove the course from its original places and add it here
                bindings_clear(all_fulfillment, course)
                this_fulfillment.add_fulfillment_course(course)
                all_fulfillment.update({template:this_fulfillment})
                continue

        return this_fulfillment


    def template_steal(self, template:Template, all_fulfillment:dict, max_fulfillments:dict) -> None:
        '''
        try to steal any courses it can from other templates
        '''
        this_fulfillment = all_fulfillment.get(template)

        while this_fulfillment.unfulfilled_count() > 0:
            # initial layer is all fulfillment statuses with excess
            bfs_roots = set()
            overlap_calculator = Backwards_Overlap(max_fulfillments)
            graph = Graph(set(all_fulfillment.values()), overlap_calculator)
            
            # generate links between fulfillment statuses
            for fulfillment_status1 in all_fulfillment.values():
                if fulfillment_status1.excess_count() > 0:
                    bfs_roots.add(fulfillment_status1)
                for fulfillment_status2 in all_fulfillment.values():
                    graph.try_add_connection(fulfillment_status1, fulfillment_status2)

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
                # for the ultimate transfer into this template, pick the course the maximizes the number of fulfillments
                # for other R templates
                if i == len(path) - 2:
                    transferred_courses = graph.edge_data(giver, receiver, False)
                    # if replacement, get courses that fill the maximum amount of bindings
                    if template.replacement:
                        transferred_course = sort_by_num_bindings(max_fulfillments, transferred_courses, Bind_Type.R)
                        transferred_course.reverse()
                        transferred_course = transferred_course[0]

                    # otherwise, avoid being greedy and taking courses that fulfill replaceable templates for yourself!
                    else:
                        transferred_course = sort_by_num_bindings(max_fulfillments, transferred_courses, Bind_Type.R)
                        transferred_course = transferred_course[0]

                else:
                    transferred_course = graph.edge_data(giver, receiver, True)
                print('transferring course: ' + str(transferred_course))
                giver.remove_fulfillment_course(transferred_course)
                receiver.add_fulfillment_course(transferred_course)
                all_fulfillment.update({giver.get_template():giver})
            
            all_fulfillment.update({path[-1].get_template():path[-1]})


    def template_trade(self, template:Template, all_fulfillment:dict, max_fulfillments:dict) -> None:
        '''
        try to exchange courses from other replacement templates by receiving
        a course that fulfills both self and the other replacement template

        note that input template must be a replacement enabled tempalte
        '''
        if not template.replacement:
            return

        this_fulfillment = all_fulfillment.get(template)
        while this_fulfillment.unfulfilled_count() > 0:
            requested_courses = max_fulfillments.get(template).get_fulfillment_set().difference(all_fulfillment.get(template).get_fulfillment_set())
            
            bfs_roots = set()
            overlap_calculator = Forwards_Overlap(max_fulfillments)
            graph = Graph(set(all_fulfillment.values()), overlap_calculator)
            
            # generate links between fulfillment statuses
            for fulfillment_status1 in all_fulfillment.values():
                if fulfillment_status1.excess_count() > 0:
                    bfs_roots.add(fulfillment_status1)
                for fulfillment_status2 in all_fulfillment.values():
                    graph.try_add_connection(fulfillment_status1, fulfillment_status2)

            bfs = graph.bfs(bfs_roots)
            # get donatable courses
            # donate those courses
            # see if this allows this course to be stolen via a dummy non-replacement template
            # if not, retract donations
            for course in requested_courses:
                bind_to_R_templates(all_fulfillment, max_fulfillments, course)
    


    def json(self) -> json:
        degree = dict()
        degree.update({self.name:self.templates})
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
    '''
    Print status_return dictionary in a neat string format
    '''
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


def possible_combinations_of_wildcard_templates(all_fulfillment:dict):
    bound = list()
    for fulfill_set in all_fulfillment.values():
        bound.append(len(fulfill_set))
    return bound


def sort_by_num_bindings(all_fulfillment:dict, requested_courses:list, sort_type:Bind_Type=Bind_Type.ALL) -> list:
    '''
    Bucket sort that sorts courses inside requested_courses by the number of bindings they have
    with courses within all_fulfillment, from least to most
    '''
    requested_courses_ordered = list()

    buckets = list()

    for course in requested_courses:
        # determine the appropriate bucket to put each course in
        if sort_type == Bind_Type.ALL:
            num_appear = len(bindings_all(all_fulfillment, course))
        elif sort_type == Bind_Type.NR:
            num_appear = len(bindings_with_NR_templates(all_fulfillment, course))
        elif sort_type == Bind_Type.R:
            num_appear = len(bindings_with_R_templates(all_fulfillment, course))
        else:
            print('error in sort_by_num_bindings, invalid sort_type given')
            return requested_courses

        # generate the necessary empty buckets
        for _ in range(0, num_appear - len(buckets) + 1):
            buckets.append(list())

        # append to the appropriate bucket
        buckets[num_appear].append(course)

    # condense the buckets into a single list
    for bucket in buckets:
        requested_courses_ordered.extend(bucket)
    return requested_courses_ordered


def has_only_weak_bindings(all_fulfillment:dict, course) -> bool:
    '''
    true if removing this course from all existing fulfillment sets will not cause a fulfilled
    template to become unfulfilled
    '''
    for fulfillment_status in all_fulfillment.values():
        if course in fulfillment_status.get_fulfillment_set() and fulfillment_status.excess_count() == 0:
            return False
    return True


def bindings_clear(all_fulfillment:dict, course) -> None:
    '''
    Removes course from all existing fulfillment sets
    '''
    for fulfillment_status in all_fulfillment.values():
        if course in fulfillment_status.get_fulfillment_set():
            fulfillment_status.remove_fulfillment_course(course)


def bind_to_R_templates(all_fulfillment:dict, max_fulfillments:dict, course:Course) -> None:
    '''
    add the course to all fulfillment sets that are replacement enabled
    '''
    for fulfillment_status in all_fulfillment.values():
        if fulfillment_status.get_template().replacement and course in max_fulfillments.get(fulfillment_status.get_template()).get_fulfillment_set():
            fulfillment_status.add_fulfillment_course(course)
            print('added course ' + repr(course) + ' to R template')


def bindings_with_R_templates(all_fulfillment:dict, course:Course) -> list:
    '''
    Total number of appearances of course in fulfillment sets that allow replacement
    '''
    host_fulfillment_statuses = list()
    for fulfillment_status in all_fulfillment.values():
        if not fulfillment_status.get_template().replacement and course in fulfillment_status.get_fulfillment_set():
            host_fulfillment_statuses.append(fulfillment_status)
    return host_fulfillment_statuses


def bindings_with_NR_templates(all_fulfillment:dict, course) -> list:
    '''
    Total number of appearances of course in fulfillment sets that do not allow replacement
    '''
    host_fulfillment_statuses = list()
    for fulfillment_status in all_fulfillment.values():
        if fulfillment_status.get_template().replacement and course in fulfillment_status.get_fulfillment_set():
            host_fulfillment_statuses.append(fulfillment_status)
    return host_fulfillment_statuses


def bindings_all(all_fulfillment:dict, course) -> list:
    '''
    Total number of appearances of course in all fulfillment sets
    '''
    host_fulfillment_statuses = list()
    for fulfillment_status in all_fulfillment.values():
        if course in fulfillment_status.get_fulfillment_set():
            host_fulfillment_statuses.append(fulfillment_status)
    return host_fulfillment_statuses


def num_unfulfilled_course_slots(all_fulfillment:dict) -> int:
    '''
    Total number of unfulfilled courses across all fulfillment sets
    '''
    count = 0
    for fulfillment_status in all_fulfillment.values():
        count += max(0, fulfillment_status.get_required_count() - fulfillment_status.get_actual_count())
    return count
