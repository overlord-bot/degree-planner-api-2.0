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
    ALL = 2 # must be distinct in value since False gets converted to 1 in some instances

class Degree():
    '''
    Stores a list of rules, inserted in order of importance

    Rules will be computed sequentially for fulfillment. A rule computed first will
    be guaranteed the fact that subsequential rules cannot remove courses from its
    fulfillment set if it does not have any excess.

    rules can additionally be marked as high priority to compute its fulfillment first
    '''

    def __init__(self, name, catalog=None):
        self.name = name
        self.templates = list()
        self.catalog = catalog
        self.DEBUG = Output(OUT.DEBUG, signature='DEGREE')

        self.MAX_IMPORTANCE = 1000 # essentially the maximum number of templates possible

    def add_template(self, template:Template):
        '''
        templates should be inserted in order of importance
        '''
        if not len(self.templates):
            template.importance = self.MAX_IMPORTANCE
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


    ##############################################################################################
    # MAIN FULFILLMENT FUNCTION
    ##############################################################################################

    def fulfillment(self, taken_courses:set) -> dict:
        '''
        Generates the best fulfillment set by assigning courses to the templates stored along with
        each degree.

        If a wildcard is encountered, all possible values of that wildcard will be attempted and the
        best one in the end applied and stored in the return dictionary. (For example, suppose
        Template1 has attribute [concentration.*]. This means all courses must be within the same
        concentration, not mattering which one in particular. The return we receive would describe
        the concentration that provided the best fulfillment, and would have an attribute such as
        [concentration.ai].)

        parameters:
            taken_courses (set): all courses that is to be used to generate the fulfillment sets

        returns:
            all_fulfillment (dict): {template : Fulfillment_set}
                template is the template evaluated, with all wildcard tokens replaced by the best token
                fulfillment_set objects contain the courses that fulfill that template
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

            '''
            NR TEMPLATE FIRST COME FIRST SERVE FILL
            '''
            for template in template_set:
                if template.replacement:
                    continue
                all_fulfillment.update({template:self.template_fill(template, all_fulfillment, max_fulfillments)})

            self.DEBUG.print(f'after NR fulfillment: {print_fulfillment(all_fulfillment)}')

            '''
            NR TEMPLATE STEAL
            '''
            graph = self.generate_graph(all_fulfillment, max_fulfillments)
            for template in template_set:
                self.template_steal(template, all_fulfillment, max_fulfillments, graph)
            
            self.DEBUG.print(f'after NR steal: {print_fulfillment(all_fulfillment)}')

            '''
            R TEMPLATE FIRST COME FIRST SERVE FILL
            '''
            for template in template_set:
                if not template.replacement:
                    continue
                all_fulfillment.update({template:self.template_fill(template, all_fulfillment, max_fulfillments)})

            self.DEBUG.print(f'after R fulfillment: {print_fulfillment(all_fulfillment)}')

            '''
            R TEMPLATE STEAL/TRADE
            '''
            for template in template_set:
                #continue
                self.replacement_template_steal(template, all_fulfillment, max_fulfillments)

            self.DEBUG.print(f'after R steal: {print_fulfillment(all_fulfillment)}')

            '''
            R TEMPLATE FORCE STEAL/TRADE
            '''
            for template in template_set:
                self.replacement_template_steal(template, all_fulfillment, max_fulfillments, template.importance)

            potential_fulfillments.append(all_fulfillment)

        # checks all fulfillment sets and return the best one
        best_fulfillment = None
        for fulfillment in potential_fulfillments:
            if best_fulfillment is None or total_unfulfilled_slots(fulfillment) < total_unfulfilled_slots(best_fulfillment):
                best_fulfillment = fulfillment
            elif total_unfulfilled_slots(fulfillment) == total_unfulfilled_slots(best_fulfillment) and total_filled_slots(fulfillment) > total_filled_slots(best_fulfillment):
                best_fulfillment = fulfillment

        end = timeit.default_timer()
        self.DEBUG.print(f'\nfulfillment runtime: {end - start}\n', OUT.INFO)
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
        fills in each template with available courses in order in which the templates appear.
        
        Note that the goal is not to produce an optimal solution just yet, but rather to guarantee that ALL courses that
        can be assigned to a template is assigned to some template. (any template for now, doesn't matter which one in particular.)
        Optimizing the assignments occurs in the next steps.

        Parameters:
            template (Template): template being fulfilled, must not contain wildcards
            all_fulfillment ({Template:Fulfillment_Status}): all previously fulfilled statuses
            max_fulfillments ({Template:Fulfillment_Status}): all taken courses that can possibilty fulfill this template
            importance level (int): a course will treat all courses under this specified importance level as stealable

        Returns:
            fulfillment (Fulfillment_Status): fulfillment status of the current template
        '''

        requested_courses = max_fulfillments.get(template).get_fulfillment_set()

        self.DEBUG.print(f"template {template} requests: {[str(e) for e in requested_courses]}")

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
            if not this_fulfillment.fulfilled() and course_has_only_weak_bindings(all_fulfillment, course, importance_level) and not template.replacement:
                course_bindings_clear(all_fulfillment, course)
                this_fulfillment.add_fulfillment_course(course)
                all_fulfillment.update({template:this_fulfillment})
                continue

        return this_fulfillment


    def course_steal(self, template:Template, course:Course, all_fulfillment:dict, max_fulfillments:dict, graph:Graph, importance_level:int=-1, less_important_templates:set=None) -> bool:
        '''
        The optimization step for course assignment to templates.

        There can be scenarios where a course may take a course from another template's fulfillment set without negatively
        impacting them. This occurs when the template being stolen from has excess (fulfillment courses > required courses).

        This method uses a BFS search tree to locate all the different paths we can shuffle courses around (say template1
        needs a course template2 has. Template2 may not have excess, but Template3 does and can offer Template2 a course, so
        we transfer a course from Template3 to Template2, then the wanted course from Template2 to Template1.)

        The BFS tree has the excessly filled templates as roots and the template we want to receive a course as the target
        for search. If less_important_templates is not None, then we also add them as the roots, essentially saying that
        we can take courses from this template without compensation. This step is used as a final optimization step when
        interacting between replacement and non replacement templates due to the fact that all non replacement templates
        get computed first, even the ones that are of lower importance than existing replacement templates, so we need a way
        for the replacement templates to recapture their deserved courses.

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


    def replacement_template_steal(self, template:Template, all_fulfillment:dict, max_fulfillments:dict, importance_level=-1) -> None:
        '''
        We now introduce templates with replacement. (note this computation should occur after non-replacement
        templates are fully optimized.) This is essentially a version of the course stealing method but used for
        replacement templates, since replacement templates have the unique property of allowing multiple templates
        to simulatenously posess the same course.

        Note that this method employs the stealing method as a sub-routine, so it is not a replacement for the course
        steal method but rather an extension of it.

        
        There are senarios where if the replacement templates give up a course, they will be able to in turn receive
        an otherwise 'locked' course that can more optimally fulfill them.

        For example, suppose the following scenario:
            Template 1 (no-replacement): wants course1 or course2
            Template 2 (replacement): wants course1
            Template 3 (replacement): wants course1 or course2

        If we gave course1 to template 1 and the course2 to template 2/3, only two of them (template 1 and template 3) are
        fulfilled. To remedy this, this method functions as follows:

            1) identify the courses we want that can fulfill a maximum number of replacement templates. In this case, there
            exists one such course: course1.

            2) identify the courses that, should we obtain the wanted course, we will be able to free up and give away.
            In this case, if we obtain course1, we will be able to release course2. This method does this by temporarily
            giving the templates the wanted course and generating the list of courses that can be subsequently removed
            without affecting any fulfillment sets that doesn't have excess. (NOTE a proof is still needed to demonstrate that,
            because we originally filled the templates with there are no scenarios exist in which we can give up a course that
            breaks a fulfillment set but results in more fulfillment sets being fulfilled)

            3) see if giving those courses out to the replacement templates will allow the course we want to take to be taken.
            We do this by creating two 'dummy templates', one receiver and one giver, with the receiver essentially telling
            the course stealing algorithm that we want that course in particular, and the giver containing all the donor courses
            we can offer.

            4) we will know whether this worked or not by seeing if the donor fulfillment set has had courses taken from it. If it
            did, then this trade was a success. If not, we revert everything back to how it was originally
            
            5) repeat until we go through all wanted courses or this template becomes fulfilled.
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
            
            dummy_donor_template = Template('dummy donor', courses_required = 0)
            dummy_donor_fulfillment = Fulfillment_Status(dummy_donor_template, fulfillment_set=donateable_courses)
            all_fulfillment.update({dummy_donor_template:dummy_donor_fulfillment})
            max_fulfillments.update({dummy_donor_template:copy.deepcopy(dummy_donor_fulfillment)})

            dummy_receiver_template = Template('dummy receiver', courses_required = 999)
            dummy_receiver_fulfillment = Fulfillment_Status(dummy_receiver_template, fulfillment_set=set())
            dummy_receiver_max_fulfillment = Fulfillment_Status(dummy_receiver_template, fulfillment_set={course})
            all_fulfillment.update({dummy_receiver_template:dummy_receiver_fulfillment})
            max_fulfillments.update({dummy_receiver_template:dummy_receiver_max_fulfillment})

            graph = self.generate_graph(all_fulfillment, max_fulfillments)

            bfs = graph.bfs(less_important_templates)
            template_with_course = template_containing_course(all_fulfillment, course)

            if not bfs.contains_node(template_with_course):
                self.DEBUG.print(f'R template attempting to steal course {course} failed, not found in bfs tree {bfs}')
                course_bindings_clear(all_fulfillment, course, Bind_Type.R)
                all_fulfillment.pop(dummy_donor_template)
                max_fulfillments.pop(dummy_donor_template)
                all_fulfillment.pop(dummy_receiver_template)
                max_fulfillments.pop(dummy_receiver_template)
                continue
            self.DEBUG.print(f'R template stealing course {course}')
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


    ##############################################################################################
    # fulfillment recommendation
    ##############################################################################################

    def recommend(self, taken_courses) -> dict:
        '''
        gives possible courses to take
        '''
        best_fulfillments = self.fulfillment(taken_courses)

        recommender = dict() # {best template : {alternative template : fulfillment list}}
        # note that best template == alternative template if best template does not contain wildcards

        for best_template, best_fulfillment in best_fulfillments.items():

            original_spec = best_template.original_specifications
            # remaking the original template
            best_template_original = Template(best_template.name + ' original', specifications=original_spec, replacement=best_template.replacement, courses_required=1)

            # here we receive the list of fulfillment sets from get course match
            matches = get_course_match(best_template_original, self.catalog.get_all_courses())
            matches_dict = {}

            for matched_fulfillment in matches:
                self.DEBUG.print(f'max match for template {best_template_original}: {matches}')
                # remove the courses already taken
                recommended_courses = matched_fulfillment.get_fulfillment_set()
                for course in best_fulfillment.get_fulfillment_set():
                    recommended_courses.discard(course)

                recommended_courses = sort_by_num_bindings(best_fulfillments, recommended_courses, Bind_Type.R)
                recommended_courses = self.sort_by_preference()
                if best_template.replacement:
                    recommended_courses.reverse()

                matches_dict.update({matched_fulfillment.get_template():recommended_courses})
                self.DEBUG.print(f'max sorted match for template {str(matched_fulfillment.get_template())}: {[str(e) for e in recommended_courses]}')

            recommender.update({best_template:matches_dict})
       
        return recommender
    

    def sort_by_preference(self, all_fulfillment, user, taken_courses):
        return 
    # TODO ACTUALLY, WE CAN MAKE A GENERIC SORTER WITH CUSTOM COMPARIOSN FUNCTION

    

    def display_agent(self, best_fulfillment, recommender):
        pass


    

    def json(self) -> json:
        degree = dict()
        degree.update({self.name:self.templates})
        return json.dumps(degree)

    def __str__(self):
        return self.name

    def __repr__(self):
        rep = f"degree: {self.name} \n"
        for template in self.templates:
            rep += repr(template) + '\n'
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
            f"\n    actual count: {status.get_actual_count()}" + \
            f"\n    specifications: {status.template.specifications}" + \
            f"\n    original specifications: {status.template.original_specifications}\n")
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


def total_filled_slots(all_fulfillment:dict) -> int:
    count = 0
    for fulfillment_status in all_fulfillment.values():
        count += fulfillment_status.get_actual_count()
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
