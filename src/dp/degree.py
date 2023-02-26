from array import *
import json
import copy
from .fulfillment_status import Fulfillment_Status

class Degree():

    def __init__(self, name):
        self.name = name

        # set of Rules that dictate requirements for this degree
        # rules should be inserted in order of importance
        self.rules = list()

    def add_rule(self, rule):
        self.rules.append(rule)

    def remove_rule(self, rule):
        self.rules.remove(rule)

    def fulfillment(self, taken_courses:set):
        status_return = dict() # {rule : [fulfillment_status]}

        for i in range(0, len(self.rules)):
            if self.rules[i].high_priority:
                rule = self.rules.pop(i)
                self.rules.insert(0, rule)
        
        for rule in self.rules:
            if not rule.no_replacement:
                status_return.update({rule:rule.fulfillment(taken_courses)})
            else:
                fulfilled_statuses = list()
                # all courses that can possibily fulfill this rule, we will choose a subset from this list
                # that minimally impacts other rules
                requested_statuses_return = rule.fulfillment(taken_courses)

                for requested_status_return in requested_statuses_return:

                    # we order courses based on how many 'excessively fulfilled' sets it will impact
                    #
                    # an excessively fulfilled set refers to a template in which the fulfilled course set
                    # is larger than the required count, and thus can sacrifice a certain amount of courses
                    # from its fulfillment set without impacting its fulfilled status
                    requested_courses_ordered = list()

                    # bucket sort algorithm O(n) time, can be replaced by priority queue 
                    # that runs in O(log(n)) time but I value my sanity
                    #
                    # if you wish to implement a priority queue system in this God forsakened chaos 
                    # of a program then knock yourself out
                    requested_courses_bucket_sort = list()
                    for course in requested_status_return.get_fulfillment_set():
                        num_appear = self.appearances_in_fulfillment_sets(status_return, course)
                        for _ in range(0, num_appear - len(requested_courses_bucket_sort) + 1):
                            requested_courses_bucket_sort.append(list())
                        requested_courses_bucket_sort[num_appear].append(course)
                    for bucket in requested_courses_bucket_sort:
                        requested_courses_ordered.extend(bucket)

                    required_count = requested_status_return.get_required_count()
                    actual_count = 0
                    fulfillment_set = set()

                    # we greedily grab courses from requested_courses_ordered that won't disturb
                    # the fulfillment of previous rules until this rule is fulfilled or we run out of courses
                    for course in requested_courses_ordered:
                        if self.can_remove_from_all_fulfillment_sets(status_return, course):
                            actual_count += 1
                            self.remove_from_all_fulfillment_sets(status_return, course)
                            taken_courses.remove(course)
                            fulfillment_set.add(course)
                            if actual_count >= required_count:
                                break
                    
                    requested_status_return.set_fulfillment_set(fulfillment_set)
                    fulfilled_statuses.append(requested_status_return)

                status_return.update({rule:fulfilled_statuses})
        
        return status_return


    '''
    HELPER FUNCTIONS
    '''

    """
    Whether removing this course from all existing fulfillment sets will cause a fulfilled
    template to become unfulfilled
    """
    def can_remove_from_all_fulfillment_sets(self, status:dict, course) -> bool:
        for fulfillment_statuses in status.values():
            for fulfillment_status in fulfillment_statuses:
                if course in fulfillment_status.get_fulfillment_set() and fulfillment_status.excess_count() == 0:
                    return False
        return True
    
    """
    Removes course from all existing fulfillment sets
    """
    def remove_from_all_fulfillment_sets(self, status:dict, course) -> None:
        for fulfillment_statuses in status.values():
            for fulfillment_status in fulfillment_statuses:
                if course in fulfillment_status.get_fulfillment_set():
                    fulfillment_status.remove_fulfillment_course(course)

    """
    Total number of appearances of course in all fulfillment sets
    """
    def appearances_in_fulfillment_sets(self, status:dict, course) -> int:
        count = 0
        for fulfillment_statuses in status.values():
            for fulfillment_status in fulfillment_statuses:
                if course in fulfillment_status.get_fulfillment_set():
                    count += 1
        return count

    """
    Total number of unfulfilled courses
    """
    def compute_unfulfilled(self, status:dict) -> int:
        count = 0
        for template_dict in status.values():
            for template_status in template_dict.values():
                count += max(0, template_status.get('required') - template_status.get('actual'))
        return count

    """
    Print status_return dictionary in a neat string format
    """
    def print_fulfillment(self, status:dict) -> str:
        printout = ''
        for rule, status_list in status.items():
            printout += f"Rule '{rule.name}':\n"
            for status in status_list:
                printout += f"  Template '{status.template.name}':\n    required count: {status.get_required_count()}\n    actual count: {status.get_actual_count()}\n"
                simplified_fulfillment_set = set()
                for course in status.get_fulfillment_set():
                    simplified_fulfillment_set.add(course.get_unique_name())
                printout += f"    fulfillment set: {simplified_fulfillment_set}\n"
        return printout

    """
    Return this class as a json file
    """
    def json(self):
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
        for r in self.rules:
            i += hash(r)
        i += hash(self.name)
        return i