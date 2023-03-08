'''
contains degree class and a set of helper functions
'''

import json
from .course_template import *
from .graph import Graph

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
        # all fulfillment sets based on each possible combination of templates resulted from wildcard templates
        fulfillments = list()

        for template_combo in self.generate_template_combinations(taken_courses):
            # runs fulfillment checking using this specific combination of templates
            fulfillment_set = dict()
            for template in template_combo:
                fulfillment_set.update({template:self.fulfillment_of_template(template, fulfillment_set, taken_courses)})

            fulfillments.append(fulfillment_set)

        # checks all fulfillment sets and return the best one
        best_fulfillment_set = None
        for fulfillment in fulfillments:
            if best_fulfillment_set is None or degree_num_unfulfilled(fulfillment) < degree_num_unfulfilled(best_fulfillment_set):
                best_fulfillment_set = fulfillment

        return best_fulfillment_set

    '''
    def fulfillment(self, taken_courses, fulfillment_set) -> None:
    '''

    def fulfillment_of_template(self, template:Template, all_fulfillment:dict, taken_courses:set) -> list:
        '''
        Computes fulfillment status of a single template

        Parameters:
            template (Template): template being fulfilled, must not contain wildcards
            all_fulfillment ({Template:Fulfillment_Status}): all previously fulfilled statuses
            taken_courses (set): courses taken by user

        Returns:
            fulfillment (Fulfillment_Status): fulfillment status of the current template
        '''
        max_fulfillments = dict() # max fulfillment set for every template

        for t in self.templates:
            """
            compute all desired courses for all templates
            """
            max_fulfillments.update({t:get_course_match(t, taken_courses)[0]})

        # all_fulfillment.pop(template, None)

        """
        all courses that can possibily fulfill this rule, we will choose a subset from this list
        that minimally impacts other rules
        """
        requested_status_return = get_course_match(template, taken_courses)[0]
        """
        we order courses based on how many 'excessively fulfilled' sets it will impact

        an excessively fulfilled set refers to a template in which the fulfilled set
        is larger than required count, and thus can sacrifice a certain amount of courses
        from its fulfillment set without impacting its fulfilled status
        """
        requested_courses_ordered = courses_sort_bindings(all_fulfillment, requested_status_return)

        this_fulfillment = Fulfillment_Status(template, template.courses_required, set())
        all_fulfillment.update({template:this_fulfillment})

        """
        we greedily grab courses from requested_courses_ordered that won't disturb
        the fulfillment of previous rules
        """
        for course in requested_courses_ordered:
            # a non no_replacement rule may share any course with another non no_replacement rule
            if course_has_no_bindings(course, all_fulfillment):
                this_fulfillment.add_fulfillment_course(course)
                all_fulfillment.update({template:this_fulfillment})
                continue

            # if we can't add this course without breaking already fulfilled templates,
            # use inverse bfs to "wiggle" previous fulfllment sets to get ourselves the
            # course we want
            if not course_can_unbind(all_fulfillment, course):
                """
                TODO: here is the inverse bfs search algorithm
                """
                print('beginning bfs')
                # initial layer is all fulfillment statuses with excess
                bfs_roots = set()
                graph = Graph(set(all_fulfillment.values()))
                
                # generate links between fulfillment statuses
                for fulfillment_status1 in all_fulfillment.values():
                    if fulfillment_status1.excess_count() > 0:
                        bfs_roots.add(fulfillment_status1)
                    for fulfillment_status2 in all_fulfillment.values():
                        if any(i in max_fulfillments.get(fulfillment_status2.get_template()).get_fulfillment_set() for i in fulfillment_status1.get_fulfillment_set()):
                            graph.add_connection(fulfillment_status1, fulfillment_status2)

                print('graph: ' + str(graph))

                bfs = graph.bfs(bfs_roots)
                if not bfs.contains_node(this_fulfillment):
                    continue

                path = bfs.get_path(this_fulfillment)

                print('path: ' + ' -> '.join([str(e) for e in path]))
                continue

            # otherwise, we are free to remove the course from its original places and add it here
            course_destroy_bindings(all_fulfillment, course)
            this_fulfillment.add_fulfillment_course(course)
            all_fulfillment.update({template:this_fulfillment})

        return this_fulfillment

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

def in_2dlist(element, my_list):
    return any(element in sublist for sublist in my_list)

def print_fulfillment(status_return:dict) -> str:
    """
    Print status_return dictionary in a neat string format
    """
    printout = ''
    for status in status_return.values():
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
    for template, fulfillment_status in status.items():
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


def course_can_unbind(status:dict, course) -> bool:
    """
    Whether removing this course from all existing fulfillment sets will cause a fulfilled
    template to become unfulfilled
    """
    for fulfillment_status in status.values():
        if course in fulfillment_status.get_fulfillment_set() and fulfillment_status.excess_count() == 0:
            return False
    return True


def course_destroy_bindings(status:dict, course) -> None:
    """
    Removes course from all existing fulfillment sets
    """
    for fulfillment_status in status.values():
        if course in fulfillment_status.get_fulfillment_set():
            fulfillment_status.remove_fulfillment_course(course)


def course_num_bindings(status:dict, course) -> int:
    """
    Total number of appearances of course in all fulfillment sets
    """
    count = 0
    for fulfillment_status in status.values():
        if isinstance(course, list):
            for c in course:
                if c in fulfillment_status.get_fulfillment_set():
                    count += 1
        elif course in fulfillment_status.get_fulfillment_set():
            count += 1
    return count


def degree_num_unfulfilled(status:dict) -> int:
    """
    Total number of unfulfilled courses across all fulfillment sets
    """
    count = 0
    for fulfillment_status in status.values():
        count += max(0, fulfillment_status.get_required_count() - fulfillment_status.get_actual_count())
    return count
