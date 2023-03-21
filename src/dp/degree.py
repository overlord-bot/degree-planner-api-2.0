'''
contains degree class and a set of helper functions
'''

import json
import timeit
from enum import Enum
from .degree_template import *
from .graph import Graph
from .graph import Backwards_Overlap
from ..io.output import *

class Bind_Type(Enum):
    NR = False
    R = True
    ALL = 2

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
        self.DEBUG = Output(OUT.DEBUG, signature='DEGREE')

    def add_template(self, template:Template):
        '''
        templates should be inserted in order of importance
        '''
        if not len(self.templates):
            template.importance = 1000
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
        max_fulfillment_possibilities = list()
        for template in self.templates:
            max_fulfillment_possibilities.append(get_course_match(template, taken_courses))

        # if template contains wildcards, this is how many templates can result from the wildcard
        bound_array = [len(e) for e in max_fulfillment_possibilities]

        # all possible combinations using all generated templates
        combos = generate_combinatorics(bound_array, 1)

        # we make a list of all the template combinations
        all_template_combinations = list()

        for combo in combos:
            templates_to_use = []

            # generates the combination of templates to use
            for i in range(0, len(combo)):
                # gets the fulfillment status to use based on the number in combo
                fulfillment_status = max_fulfillment_possibilities[i][combo[i] - 1]
                # gets the template we should use
                templates_to_use.append(fulfillment_status.get_template())
            all_template_combinations.append(templates_to_use)
        
        return all_template_combinations


    def fulfillment(self, taken_courses:set) -> dict:
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
                if template.replacement:
                    continue
                all_fulfillment.update({template:self.template_fill(template, all_fulfillment, max_fulfillments)})

            # print('after NR fulfillment: ' + print_fulfillment(all_fulfillment))

            graph = self.generate_graph(all_fulfillment, max_fulfillments)
            for template in template_set:
                self.template_steal(template, all_fulfillment, max_fulfillments, graph)
            
            # print('after steal: ' + print_fulfillment(all_fulfillment))

            for template in template_set:
                if not template.replacement:
                    continue
                all_fulfillment.update({template:self.template_fill(template, all_fulfillment, max_fulfillments)})

            # print('after R fulfillment: ' + print_fulfillment(all_fulfillment))

            for template in template_set:
                self.template_trade(template, all_fulfillment, max_fulfillments)

            # print('after trade: ' + print_fulfillment(all_fulfillment))

            for template in template_set:
                self.template_trade(template, all_fulfillment, max_fulfillments, template.importance)

            potential_fulfillments.append(all_fulfillment)

        # checks all fulfillment sets and return the best one
        best_fulfillment = None
        for fulfillment in potential_fulfillments:
            if best_fulfillment is None or total_unfulfilled_slots(fulfillment) < total_unfulfilled_slots(best_fulfillment):
                best_fulfillment = fulfillment

        end = timeit.default_timer()
        print('\nfulfillment runtime: ', end - start, '\n')
        return best_fulfillment


    def generate_graph(self, all_fulfillment:dict, max_fulfillments:dict):
        bfs_roots = set()
        overlap_calculator = Backwards_Overlap(all_fulfillment, max_fulfillments)
        graph = Graph(set(all_fulfillment.keys()), overlap_calculator)
        
        # generate links between fulfillment statuses
        for fulfillment_status1 in all_fulfillment.values():
            if fulfillment_status1.get_template().replacement:
                continue
            if fulfillment_status1.excess_count() > 0:
                bfs_roots.add(fulfillment_status1.get_template())
            for fulfillment_status2 in all_fulfillment.values():
                if fulfillment_status2.get_template().replacement:
                    continue
                graph.update_connection(fulfillment_status1.get_template(), fulfillment_status2.get_template())
        graph.roots = bfs_roots
        self.DEBUG.print(str(graph))
        return graph


    def course_move(self, giver_fulfillment:Fulfillment_Status, receiver_fulfillment:Fulfillment_Status, course:Course, graph:Graph) -> None:
        '''
        manages the graph such that it remains consistent with course moves. This method must be used
        if you want to be able to modify fulfillment sets without rebuilding the entire graph
        '''
        giver_fulfillment.remove_fulfillment_course(course)
        receiver_fulfillment.add_fulfillment_course(course)

        for out_connection in graph.outbound_connections(giver_fulfillment.get_template()):
            graph.update_connection(giver_fulfillment.get_template(), out_connection)

        for in_connection in graph.inbound_connections(receiver_fulfillment.get_template()):
            graph.update_connection(receiver_fulfillment.get_template(), in_connection)

        graph.update_connection(giver_fulfillment.get_template(), receiver_fulfillment.get_template())
        graph.update_connection(receiver_fulfillment.get_template(), giver_fulfillment.get_template())


    def template_fill(self, template:Template, all_fulfillment:dict, max_fulfillments:dict, importance_level:int=-1) -> Fulfillment_Status:
        '''
        Computes fulfillment status of a single template

        Parameters:
            template (Template): template being fulfilled, must not contain wildcards
            all_fulfillment ({Template:Fulfillment_Status}): all previously fulfilled statuses
            max_fulfillments ({Template:Fulfillment_Status}): all taken courses that can possibilty fulfill this template
            importance level (int): a course will treat all courses under this specified importance level as stealable

        Returns:
            fulfillment (Fulfillment_Status): fulfillment status of the current template
        '''

        requested_courses = max_fulfillments.get(template).get_fulfillment_set()

        # self.DEBUG.print(str(template) + ' requests: ' + str([str(e) for e in requested_courses]))

        if template.replacement:
            requested_courses = sort_by_num_wanted_bindings(all_fulfillment, max_fulfillments, requested_courses, Bind_Type.R)
            requested_courses.reverse()
        this_fulfillment = Fulfillment_Status(template, template.courses_required, set())

        """
        we grab all courses from potential_courses that won't disturb
        the fulfillment of previous templates
        """
        for course in requested_courses:
            # course hasn't been added to any fulfillment sets yet, or if this template is replacement enabled
            # and the course is not in any no replacement templates
            if (not len(course_bindings(all_fulfillment, course))
                    or (template.replacement and not len(course_bindings_with_NR_templates(all_fulfillment, course)))):
                this_fulfillment.add_fulfillment_course(course)
                all_fulfillment.update({template:this_fulfillment})
                continue

            # we are free to remove the course from its original places and add it here
            if not this_fulfillment.fulfilled() and course_has_only_weak_bindings(all_fulfillment, course, importance_level):
                course_bindings_clear(all_fulfillment, course)
                this_fulfillment.add_fulfillment_course(course)
                all_fulfillment.update({template:this_fulfillment})
                continue

        return this_fulfillment


    def course_steal(self, template:Template, course:Course, all_fulfillment:dict, max_fulfillments:dict, graph:Graph, importance_level:int=-1, less_important_templates:set=None) -> bool:
        '''
        try to have template steal the course from aother templates in all_fulfillment, using the graph given and update
        graph appropriately after a successful transfer of courses

        returns whether steal is successful
        '''
        if less_important_templates is None:
            less_important_templates = get_less_important_templates(all_fulfillment, importance_level)
        bfs = graph.bfs(less_important_templates)

        # Optimization: we can leave immediately if BFS doesn't even contain the target at all
        if not bfs.contains_child(template):
            return False

        # the templates containing the requested course, we will BFS search for this template
        target_template = template_containing_course(all_fulfillment, course)
        if target_template is None:
            return False
        
        # the path to move courses, recorded as a list of templates traversed
        path = bfs.get_path(target_template)
        self.DEBUG.print('path: ' + ' -> '.join([str(e) for e in path]) + ' --> ' + str(template))

        # shifts courses along the path such that we obtain a new course
        for i in range(0, len(path) - 1):
            giver = path[i]
            receiver = path[i + 1]
            transferred_courses = graph.edge_data(giver, receiver, False)

            # avoid being greedy and taking courses that fulfill replaceable templates for yourself!
            transferred_course = sort_by_num_bindings(max_fulfillments, transferred_courses, Bind_Type.R)
            transferred_course = transferred_course[0]

            self.DEBUG.print(f'transferring course {transferred_course} from {giver} to {receiver}')
            self.course_move(all_fulfillment.get(giver), all_fulfillment.get(receiver), transferred_course, graph)

        self.DEBUG.print(f'transferring course {course} from {path[-1]} to {all_fulfillment.get(template)}')
        self.course_move(all_fulfillment.get(path[-1]), all_fulfillment.get(template), course, graph)


    def template_steal(self, template:Template, all_fulfillment:dict, max_fulfillments:dict, graph:Graph, importance_level:int=-1) -> None:
        '''
        try to steal any courses it can from other templates
        '''
        if template.replacement:
            return

        this_fulfillment = all_fulfillment.get(template)
        bfs = graph.bfs()
        if not bfs.contains_child(template):
            return

        for course in max_fulfillments.get(template).get_fulfillment_set():
            if this_fulfillment.fulfilled():
                return
            if course in all_fulfillment.get(template).get_fulfillment_set():
                continue
            self.course_steal(template, course, all_fulfillment, max_fulfillments, graph, importance_level)


    def template_trade(self, template:Template, all_fulfillment:dict, max_fulfillments:dict, importance_level=-1) -> None:
        '''
        TEMPLATE MUST BE REPLACEMENT

        try to exchange courses from other replacement templates by receiving
        a course that fulfills both self and the other replacement template
        '''
        this_fulfillment = all_fulfillment.get(template)

        if not template.replacement or this_fulfillment.fulfilled():
            return

        requested_courses = max_fulfillments.get(template).get_fulfillment_set().difference(all_fulfillment.get(template).get_fulfillment_set())
        requested_courses_sorted = sort_by_num_bindings(all_fulfillment, requested_courses, Bind_Type.R)

        for course in requested_courses_sorted:
            if this_fulfillment.fulfilled():
                return

            # we bind the wanted course (which at this point, we know is unbound since the requested courses filtered out already bound courses)
            course_bind_to_R_templates(all_fulfillment, max_fulfillments, course)

            # calculate the donateable courses, which is the weakly bound courses
            donateable_courses = all_weakly_bound_courses(all_fulfillment, Bind_Type.R)

            # run BFS to see if there are a donateable course that allows for the requested course to be taken
            #
            # it's important to make sure dummy is in the name so course steal knows to remove the course
            # it stole from the actual replacement templates in addition to the dummy templates
            less_important_templates = get_less_important_templates(all_fulfillment, importance_level, Bind_Type.NR)
            
            dummy_donor_template = Template('dummy donor', template_course=Course('dummy donor', 'dummy', 'dummy'), courses_required = 0)
            dummy_donor_fulfillment = Fulfillment_Status(dummy_donor_template, fulfillment_set=donateable_courses)
            all_fulfillment.update({dummy_donor_template:dummy_donor_fulfillment})
            max_fulfillments.update({dummy_donor_template:copy.deepcopy(dummy_donor_fulfillment)})

            dummy_receiver_template = Template('dummy receiver', template_course=Course('dummy receiver', 'dummy', 'dummy'), courses_required = 1)
            dummy_receiver_fulfillment = Fulfillment_Status(dummy_receiver_template, fulfillment_set=set())
            dummy_receiver_max_fulfillment = Fulfillment_Status(dummy_receiver_template, fulfillment_set={course})
            all_fulfillment.update({dummy_receiver_template:dummy_receiver_fulfillment})
            max_fulfillments.update({dummy_receiver_template:dummy_receiver_max_fulfillment})

            graph = self.generate_graph(all_fulfillment, max_fulfillments)

            bfs = graph.bfs(less_important_templates)
            template_with_course = template_containing_course(all_fulfillment, course)

            if not bfs.contains_child(template_with_course):
                course_bindings_clear(all_fulfillment, course, Bind_Type.R)
                all_fulfillment.pop(dummy_donor_template)
                max_fulfillments.pop(dummy_donor_template)
                all_fulfillment.pop(dummy_receiver_template)
                max_fulfillments.pop(dummy_receiver_template)
                continue

            self.course_steal(dummy_receiver_template, course, all_fulfillment, max_fulfillments, graph, less_important_templates=less_important_templates)

            traded_course = max_fulfillments.get(dummy_donor_template).get_fulfillment_set() - dummy_donor_fulfillment.get_fulfillment_set()
            if len(traded_course) == 1:
                traded_course = list(traded_course)[0]

            course_bindings_clear(all_fulfillment, traded_course, Bind_Type.R)

            this_fulfillment.add_fulfillment_course(course)
            all_fulfillment.pop(dummy_donor_template)
            max_fulfillments.pop(dummy_donor_template)
            all_fulfillment.pop(dummy_receiver_template)
            max_fulfillments.pop(dummy_receiver_template)
    

    def json(self) -> json:
        degree = dict()
        degree.update({self.name:self.templates})
        return json.dumps(degree)

    def __str__(self):
        return self.name

    def __repr__(self):
        rep = f"{self.name}: \n"
        for template in self.templates:
            rep += str(template)
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
    fulfillments = list(all_fulfillment.values())
    fulfillments.sort()
    for status in fulfillments:
        printout += (f"  Template '{status.template.name}':" + \
            f"\n    replacement: {status.template.replacement}, importance: {status.template.importance}" + \
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


def all_weakly_bound_courses(all_fulfillment:dict, bind_type:Bind_Type=Bind_Type.ALL) -> set:
    loosely_bound = set()
    strongly_bound = set()
    for template, fulfillment in all_fulfillment.items():
        if bind_type != Bind_Type.ALL and template.replacement != bind_type.value:
            continue
        if template.courses_required < fulfillment.get_actual_count():
            loosely_bound.update(fulfillment.get_fulfillment_set())
        else:
            strongly_bound.update(fulfillment.get_fulfillment_set())
    return loosely_bound - strongly_bound


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
            num_appear = len(course_bindings(all_fulfillment, course))
        elif sort_type == Bind_Type.NR:
            num_appear = len(course_bindings_with_NR_templates(all_fulfillment, course))
        elif sort_type == Bind_Type.R:
            num_appear = len(course_bindings_with_R_templates(all_fulfillment, course))
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


def sort_by_num_wanted_bindings(all_fulfillment:dict, max_fulfillments:dict, requested_courses:list, bind_type:Bind_Type=Bind_Type.ALL) -> list:
    '''
    Bucket sort that sorts courses inside requested_courses by the number of bindings they have
    with courses within all_fulfillment, from least to most
    '''
    requested_courses_ordered = list()

    buckets = list()

    for course in requested_courses:
        # determine the appropriate bucket to put each course in
        num_appear = 0
        for template, fulfillment_status in all_fulfillment.items():
            if bind_type != Bind_Type.ALL and template.replacement != bind_type.value:
                continue
            if (not fulfillment_status.fulfilled() and course in max_fulfillments.get(template).get_fulfillment_set()):
                num_appear += 1

        # generate the necessary empty buckets
        for _ in range(0, num_appear - len(buckets) + 1):
            buckets.append(list())

        # append to the appropriate bucket
        buckets[num_appear].append(course)

    # condense the buckets into a single list
    for bucket in buckets:
        requested_courses_ordered.extend(bucket)
    return requested_courses_ordered


def get_less_important_templates(all_fulfillment:dict, importance_level, bind_type:Bind_Type=Bind_Type.ALL) -> set:
    templates = set()
    if importance_level == -1:
        return templates
    for template in all_fulfillment.keys():
        if bind_type != Bind_Type.ALL and template.replacement != bind_type.value:
            continue
        if template.importance < importance_level:
            templates.add(template)
    return templates


def course_has_only_weak_bindings(all_fulfillment:dict, course, importance_level:int=-1) -> bool:
    '''
    true if removing this course from all existing fulfillment sets will not cause a fulfilled
    template to become unfulfilled
    '''
    for fulfillment_status in all_fulfillment.values():
        if course in fulfillment_status.get_fulfillment_set() and fulfillment_status.excess_count() == 0 and fulfillment_status.get_template().importance >= importance_level:
            return False
    return True


def course_bindings_clear(all_fulfillment:dict, course, bind_type:Bind_Type=Bind_Type.ALL) -> None:
    '''
    Removes course from all existing fulfillment sets
    '''
    for template, fulfillment_status in all_fulfillment.items():
        if bind_type != Bind_Type.ALL and template.replacement != bind_type.value:
            continue
        if course in fulfillment_status.get_fulfillment_set():
            fulfillment_status.remove_fulfillment_course(course)


def course_bind_to_R_templates(all_fulfillment:dict, max_fulfillments:dict, course:Course) -> None:
    '''
    add the course to all fulfillment sets that are replacement enabled
    '''
    for fulfillment_status in all_fulfillment.values():
        if (fulfillment_status.get_template().replacement 
                and course in max_fulfillments.get(fulfillment_status.get_template()).get_fulfillment_set()):
            fulfillment_status.add_fulfillment_course(course)


def course_bindings_with_R_templates(all_fulfillment:dict, course:Course) -> list:
    '''
    Total number of appearances of course in fulfillment sets that allow replacement
    '''
    host_fulfillment_statuses = list()
    for fulfillment_status in all_fulfillment.values():
        if fulfillment_status.get_template().replacement and course in fulfillment_status.get_fulfillment_set():
            host_fulfillment_statuses.append(fulfillment_status)
    return host_fulfillment_statuses


def course_bindings_with_NR_templates(all_fulfillment:dict, course) -> list:
    '''
    Total number of appearances of course in fulfillment sets that do not allow replacement
    '''
    host_fulfillment_statuses = list()
    for fulfillment_status in all_fulfillment.values():
        if not fulfillment_status.get_template().replacement and course in fulfillment_status.get_fulfillment_set():
            host_fulfillment_statuses.append(fulfillment_status)
    return host_fulfillment_statuses


def course_bindings(all_fulfillment:dict, course) -> list:
    '''
    Total number of appearances of course in all fulfillment sets
    '''
    host_fulfillment_statuses = list()
    for fulfillment_status in all_fulfillment.values():
        if course in fulfillment_status.get_fulfillment_set():
            host_fulfillment_statuses.append(fulfillment_status)
    return host_fulfillment_statuses


def total_unfulfilled_slots(all_fulfillment:dict) -> int:
    '''
    Total number of unfulfilled courses across all fulfillment sets
    '''
    count = 0
    for fulfillment_status in all_fulfillment.values():
        count += max(0, fulfillment_status.get_required_count() - fulfillment_status.get_actual_count())
    return count


def templates_containing_course(all_fulfillment:dict, course:Course) -> set:
    '''
    returns a set of all templates that contain the specified course
    '''
    templates = set()
    for template, fulfillment_status in all_fulfillment.items():
        if course in fulfillment_status.get_fulfillment_set():
            templates.add(template)
    return templates

def template_containing_course(all_fulfillment:dict, course:Course) -> Template:
    '''
    an optimized version for templates_containg_course when we expect
    the course to not be duplicated, hence returning only first occurance

    returns a set of all templates that contain the specified course
    '''
    for template, fulfillment_status in all_fulfillment.items():
        if course in fulfillment_status.get_fulfillment_set():
            return template
    return None
