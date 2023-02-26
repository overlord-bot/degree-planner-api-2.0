from array import *
import json
import copy
from .fulfillment_status import Fulfillment_Status

class Degree():

    def __init__(self, name):
        self.name = name # name of the degree program
        self.rules = list() # set of Rules that dictate requirements for this degree

    def get_core(self):
        pass

    def get_pathways(self):
        pass

    def get_concentrations(self):
        pass

    def get_electives(self):
        pass

    def add_rule(self, rule):
        self.rules.append(rule)

    def remove_rule(self, rule):
        self.rules.remove(rule)

        # rules already inserted in order

    def fulfillment(self, taken_courses:set):
        status_return = dict() # {rule : [fulfillment_status]}

        print('rules before reordering: ' + str([e.name for e in self.rules]))
        for i in range(0, len(self.rules)):
            if self.rules[i].high_priority:
                rule = self.rules.pop(i)
                self.rules.insert(0, rule)
        print('rules after reordering: ' + str([e.name for e in self.rules]))
        
        for rule in self.rules:
            if not rule.no_replacement:
                status_return.update({rule:rule.fulfillment(taken_courses)})
            else:
                requested_status_return = rule.fulfillment(taken_courses)[0]
                requested_courses_ordered = list()

                # bucket sort algorithm O(n) time, can be replaced by priority queue that runs in O(log(n)) time but I value my sanity
                # if you wish to implement a priority queue system in this God forsakened chaos of a program then knock yourself out
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
                # the fulfillment of previous rules until this rule is fulfilled or we run out of courses.
                for course in requested_courses_ordered:
                    if self.can_remove_from_all_fulfillment_sets(status_return, course):
                        actual_count += 1
                        self.remove_from_all_fulfillment_sets(status_return, course)
                        taken_courses.remove(course)
                        fulfillment_set.add(course)
                        if actual_count >= required_count:
                            break
                
                requested_status_return.set_fulfillment_set(fulfillment_set)
                status_return.update({rule:[requested_status_return]})
        
        return status_return


    def can_remove_from_all_fulfillment_sets(self, status:dict, course) -> bool:
        for fulfillment_statuses in status.values():
            for fulfillment_status in fulfillment_statuses:
                if course in fulfillment_status.get_fulfillment_set() and fulfillment_status.excess_count() == 0:
                    return False
        return True
    
    def remove_from_all_fulfillment_sets(self, status:dict, course):
        for fulfillment_statuses in status.values():
            for fulfillment_status in fulfillment_statuses:
                if course in fulfillment_status.get_fulfillment_set():
                    fulfillment_status.remove_fulfillment_course(course)

    def appearances_in_fulfillment_sets(self, status:dict, course) -> int:
        count = 0
        for fulfillment_statuses in status.values():
            for fulfillment_status in fulfillment_statuses:
                if course in fulfillment_status.get_fulfillment_set():
                    count += 1
        return count

    def compute_unfulfilled(self, fulfillment:dict) -> int:
        count = 0
        for template_dict in fulfillment.values():
            for template_status in template_dict.values():
                count += max(0, template_status.get('required') - template_status.get('actual'))
        return count


    # returns a list of sets
    def get_combinations(self, course_list:list) -> list:
        combos = list()
        for selected_indices in range(0, pow(2, len(course_list))):
            combo = set()
            for mask in range(0, len(course_list)):
                if pow(2, mask) & selected_indices:
                    combo.add(course_list[mask])
            combos.append(set(combo))
        return combos

    def print_fulfillment(self, status:dict):
        printout = ''
        for rule, status_list in status.items():
            printout += f"Rule '{rule.name}':\n"
            for status in status_list:
                printout += f"  Template '{status.template.name}':\n    required count: {status.get_required_count()}\n    actual count: {status.get_actual_count()}\n"
                printout += f"    fulfillment set: {status.get_fulfillment_set()}\n"

        return printout

    def json(self):
        degree = dict()
        rules = list()
        for r in self.rules:
            rules.append(r)
        degree.update({self.name:r})
        return json.dumps(degree)


    def __repr__(self):
        return f"{self.name}: \n{repr(self.rules)}"

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