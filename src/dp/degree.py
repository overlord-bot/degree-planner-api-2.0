'''
contains degree class and a set of helper functions
'''

import json

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
        self.rules = list() # rules should be inserted in order of importance


    def add_rule(self, rule) -> None:
        '''
        Parameters:
            rule (Rule): rule to add to this degree, duplicates allowed
        '''
        self.rules.append(rule)


    def remove_rule(self, rule) -> None:
        '''
        Parameters:
            rule (Rule): rule to remove to this degree, removes all occurances
        '''
        self.rules = [e for e in self.rules if e != rule]


    def fulfillment_of_rule(self, rule, all_fulfillment:dict, taken_courses:set) -> list:
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
        """
        all courses that can possibily fulfill this rule, we will choose a subset from this list
        that minimally impacts other rules
        """

        requested_statuses_return = rule.fulfillment(taken_courses)
        for requested_status_return in requested_statuses_return:
            """
            we order courses based on how many 'excessively fulfilled' sets it will impact

            an excessively fulfilled set refers to a template in which the fulfilled set
            is larger than required count, and thus can sacrifice a certain amount of courses
            from its fulfillment set without impacting its fulfilled status
            """
            requested_courses_ordered = sort_courses_by_fulfillment_appearances(all_fulfillment, requested_status_return)
            fulfillment_set = set()

            """
            we greedily grab courses from requested_courses_ordered that won't disturb
            the fulfillment of previous rules
            """
            for course in requested_courses_ordered:
                # a non no_replacement rule may share any course with another non no_replacement rule
                if not rule.no_replacement and unbound_course(course, all_fulfillment):
                    fulfillment_set.add(course)
                    continue
                if not can_remove_from_all_fulfillment_sets(all_fulfillment, course):
                    continue
                remove_from_all_fulfillment_sets(all_fulfillment, course)
                fulfillment_set.add(course)

            requested_status_return.set_fulfillment_set(fulfillment_set)
            fulfilled_statuses.append(requested_status_return)
            all_fulfillment.update({rule:fulfilled_statuses})

        return fulfilled_statuses


    def fulfillment(self, taken_courses:set) -> dict:
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
        """
        for i in range(len(self.rules) - 1, 0, -1):
            if self.rules[i].high_priority:
                rule = self.rules.pop(i)
                self.rules.insert(0, rule)

        for rule in self.rules:
            status_return.update({rule:self.fulfillment_of_rule(rule, status_return, taken_courses)})

        return status_return


    def print_fulfillment(self, status_return:dict) -> str:
        """
        Print status_return dictionary in a neat string format
        """
        printout = ''
        for rule, status_list in status_return.items():
            printout += f"Rule '{rule.name}':\n"
            for status in status_list:
                printout += (f"  Template '{status.template.name}':" + \
                    f"\n    required count: {status.get_required_count()}" + \
                    f"\n    actual count: {status.get_actual_count()}\n")
                simplified_fulfillment_set = set()
                for course in status.get_fulfillment_set():
                    simplified_fulfillment_set.add(course.get_unique_name())
                printout += f"    fulfillment set: {simplified_fulfillment_set}\n"
        return printout


    def json(self):
        '''
        Return this class as a json file
        '''
        degree = dict()
        degree.update({self.name:self.rules})
        return json.dumps(degree)


    def __repr__(self):
        rep = f"{self.name}: \n"
        for rule in self.rules:
            rep += f"  Rule: {rule}\n"
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

def unbound_course(course, status:dict):
    '''
    Course is not in any rule with no_replacement, meaning another non no_replacement
    rule may use this rule for its fulfillment
    '''
    for rule, fulfillment_statuses in status.items():
        for fulfillment_status in fulfillment_statuses:
            if course in fulfillment_status.get_fulfillment_set() and rule.no_replacement:
                return False
    return True


def sort_courses_by_fulfillment_appearances(status_return:dict, requested_status_return:list) -> list:
    """
    bucket sort algorithm O(n) time, can be replaced by priority queue
    that runs in O(log(n)) time but I value my sanity
    
    if you wish to implement a priority queue system in this God forsakened chaos
    of a program then knock yourself out
    """
    requested_courses_ordered = list()

    requested_courses_bucket_sort = list()
    for course in requested_status_return.get_fulfillment_set():
        num_appear = appearances_in_fulfillment_sets(status_return, course)
        for _ in range(0, num_appear - len(requested_courses_bucket_sort) + 1):
            requested_courses_bucket_sort.append(list())
        requested_courses_bucket_sort[num_appear].append(course)
    for bucket in requested_courses_bucket_sort:
        requested_courses_ordered.extend(bucket)
    return requested_courses_ordered


def can_remove_from_all_fulfillment_sets(status:dict, course) -> bool:
    """
    Whether removing this course from all existing fulfillment sets will cause a fulfilled
    template to become unfulfilled
    """
    for fulfillment_statuses in status.values():
        for fulfillment_status in fulfillment_statuses:
            if course in fulfillment_status.get_fulfillment_set() and fulfillment_status.excess_count() == 0:
                return False
    return True


def remove_from_all_fulfillment_sets(status:dict, course) -> None:
    """
    Removes course from all existing fulfillment sets
    """
    for fulfillment_statuses in status.values():
        for fulfillment_status in fulfillment_statuses:
            if course in fulfillment_status.get_fulfillment_set():
                fulfillment_status.remove_fulfillment_course(course)


def appearances_in_fulfillment_sets(status:dict, course) -> int:
    """
    Total number of appearances of course in all fulfillment sets
    """
    count = 0
    for fulfillment_statuses in status.values():
        for fulfillment_status in fulfillment_statuses:
            if course in fulfillment_status.get_fulfillment_set():
                count += 1
    return count


def compute_unfulfilled(status:dict) -> int:
    """
    Total number of unfulfilled courses across all fulfillment sets
    """
    count = 0
    for template_dict in status.values():
        for template_status in template_dict.values():
            count += max(0, template_status.get('required') - template_status.get('actual'))
    return count
