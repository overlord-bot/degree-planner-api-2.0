'''
DEGREE PLANNER MAIN CLASS
'''

from ..io.output import *
from .course import Course
from .catalog import Catalog
from ..user.schedule import Schedule
from ..user.user import User
from ..user.user import Flag
from .command import *
from src.io.parse import *
from .degree import *
from .command_handler import *

VERSION = "API 2.0"

class Planner():
    '''
    All interaction with a Planner is with this class using input_handler

    One catalog shared within a Planner, with distinct users containing their
    own schedules, eligible classes and degree selection

    input_handler function receives commands and arguments separated by
    commas in a string. Multiple commands allowed within one entry.

    Valid commands are:
        (developer only)
            import
                - parse course and degree information from json

        (general use)
            schedule, <schedule name>
                - set active schedule. New schedule will be created if
                specified schedule does not exist
            degree, <degree name>
                - set degree of active schedule
            add, <semester>, <course name>
                - add course to active schedule, courses may not duplicate
                within the same semester but may duplicate accross semesters
            remove, <semester>, <course name>
                - remove course from active schedule in specified semester
            print
                - print schedule
            fulfillment
                - print degree requirement fulfillment status
            find, <course>* (may list any number of courses)
                - find courses that match with the inputted string. Useful
                for browsing courses that contain certain keywords.
            details, <course>
                - course description

    NOTE: This class is created once and is not instigated for each user.
    It is essential to keep all user specific data inside the User class.
    '''

    def __init__(self, SEMESTERS_MAX:int=10, io:Output=None, enable_tensorflow=True):
        # each user is assigned a User object and stored in this dictionary
        # Users = <user id, User>
        self.users = dict()
        self.catalog = Catalog(enable_tensorflow=enable_tensorflow)

        self.default_io = io
        if self.default_io is None:
            self.default_io = Output(OUT.CONSOLE, signature='INPUT HANDLER', auto_clear=True)

        self.SEMESTERS_MAX = SEMESTERS_MAX
        self.ENABLE_TENSORFLOW = enable_tensorflow

    
    def user_input(self, user:User, input:str, io=None):
        if io is None:
            io = self.default_io
        user_input(self, user, input, io)


    def user_set_active_schedule(self, user:User, schedule_name:str, io:Output=None) -> None:
        ''' Changes user's active schedule selection and creates new schedule if
            specified schedule is not found

        Args:
            user (User): user to perform the action on
            schedule_name (str): schedule name
            output (Output): user interface output
        '''
        if io is None:
            io = self.default_io

        schedule = user.get_schedule(schedule_name)
        if schedule is None:
            io.print(f"Schedule {schedule_name} not found, generating new one!")
            user.new_schedule(schedule_name, self.SEMESTERS_MAX)
            user.curr_schedule = schedule_name
            return
        else:
            io.print(f"Successfully switched to schedule {schedule_name}!")
            user.curr_schedule = schedule_name
            return


    def user_get_active_schedule(self, user:User) -> Schedule:
        ''' Gets schedule currently being modified by user

        Args:
            user (User): get the active schedule of this user

        Returns:
            schedule (Schedule): active schedule object
        '''
        return user.get_current_schedule()


    def user_get_all_schedules(self, user:User) -> list:
        ''' Get all of user's schedule

        Args:
            user (User): get the active schedule of this user

        Returns:
            list (list(Schedule)): returns a list of all schedule
                objects
        '''
        return user.schedules()


    def user_set_degree(self, user:User, degree_name:str, io:Output=None) -> bool:
        ''' Changes user's active schedule's degree

        Args:
            user (User): user to perform the action on
            schedule (Schedule): schedule to change degree on
            degree_name (str): degree name
            output (Output): user interface output

        Returns:
            bool: if degree was successfully changed.
                False usually means specified degree was not found
        '''
        if io is None:
            io = self.default_io

        degree = self.catalog.get_degree(degree_name)

        if degree is None:
            io.print(f"invalid degree entered: {degree_name}")
            return False
        
        user.get_current_schedule().degree = degree
        io.print(f"set your degree to {degree.name}")
        return True


    def search(self, course_name:str, course_pool:set=None) -> list:
        ''' Returns list of courses to output that match input entry

        Args:
            course_name (str): search for courses that contains this string in its name
            course_pool (set): pool of courses to search from
        '''
        possible_courses = self.catalog.search(course_name)
        if course_pool is not None:
            possible_courses = [e for e in possible_courses if self.catalog.get_course(e) in course_pool]
        return possible_courses


    def details(self, course_name:str) -> str:
        ''' Returns:
            description (string): the course description. Returns None if invalid name
        '''
        courses = self.catalog.search(course_name)
        if len(courses) == 1:
            course = self.catalog.get_course(courses[0])
            description = f'{repr(course)}: {course.description}'
            return description
        return None


    def print_matches(self, course_name:str, io:Output=None) -> None:
        ''' Print list of courses to output that match input entry, searches from entire catalog

        Args:
            course_name (str): search term
            output (Output): user interface output
        '''
        if io is None:
            io = self.default_io

        possible_courses = self.catalog.search(course_name)
        possible_courses.sort()
        io.print(f"courses matching {course_name}: ")
        i = 1
        for course_name in possible_courses:
            course = self.catalog.get_course(course_name)
            io.store(f"  {i}: {course.subject} {course.course_id} {course.name}")
            i += 1
        io.view_cache()


    def add_course(self, user:User, course_name:str, semester, io:Output=None):
        ''' Add course to user's schedule

        Args:
            user (User): user to perform the action on
            course_name (str): course name
            semester (int or str): semester to add course into
            output (Output): user interface output

        Returns:
            returned_courses (list): If there are multiple courses that match course_name, 
                then this list will be returned in the form of a list of Courses.
        '''
        if io is None:
            io = self.default_io

        # sanity checks
        if not semester.isdigit() or int(semester) not in range(0, self.SEMESTERS_MAX):
            io.print(f"Invalid semester {semester}, enter number between 0 and {self.SEMESTERS_MAX}")
            return None
        
        # list of courses matching course_name
        semester = int(semester)
        returned_courses = [self.catalog.get_course(c) for c in self.catalog.search(course_name)]

        if len(returned_courses) == 0:
            io.print(f"Course {course_name} not found")
            return None
        if len(returned_courses) > 1:
            return returned_courses
        
        # at this point, returned_courses have exactly one course, so we can perform the addition immediately
        course = returned_courses[0]
        user.get_current_schedule().add_course(course, semester)
        io.print(f"Added course {course.name} to semester {semester}")
        return None


    def remove_course(self, user:User, course_name:str, semester, io:Output=None):
        ''' Remove course from user's schedule

        Args:
            user (User): user to perform the action on
            course_name (str): course name
            semester (int or str): semester to remove course from
            output (Output): user interface output

        Returns:
            returned_courses (list): If there are multiple courses that match course_name, 
                then this list will be returned in the form of a list of Courses.
        '''
        if io is None:
            io = self.default_io

        # sanity checks
        if not semester.isdigit() or int(semester) not in range(0, self.SEMESTERS_MAX):
            io.print(f"Invalid semester {semester}, enter number between 0 and {self.SEMESTERS_MAX}")
            return None
        
        semester = int(semester)
        this_semester_courses = user.get_current_schedule().get_semester(semester)
        
        # list of courses matching course_name
        returned_courses = [self.catalog.get_course(c) for c in self.search(course_name, this_semester_courses)]

        if len(returned_courses) == 0:
            io.print(f"Course {course_name} not found")
            return None
        if len(returned_courses) > 1:
            return returned_courses
        
        # at this point, returned_courses have exactly one course, so we can perform the removal immediately
        course = returned_courses[0]
        user.get_current_schedule().remove_course(course, semester)
        io.print(f"Removed course {course.name} from semester {semester}")
        return None

    
    def import_data(self, io:Output=None) -> Exception:
        ''' Parse json data into a list of courses and degrees inside a catalog

        Args:
            output (Output): user interface output

        Returns:
            Exception: if exception occurs, returns exception, else None
        '''
        if io is None:
            io = self.default_io

        parse_courses(self.catalog, io)
        io.print(f"Sucessfully parsed catalog data")
        
        # set up searcher for finding courses based on incomplete user input
        io.print(f"generated search index")

        parse_degrees(self.catalog, io)
        io.print(f"Sucessfully parsed degree data")
        io.debug(f"Printing catalog:")
        io.debug(str(self.catalog))

        parse_tags(self.catalog, io)
        io.print(f"parsed tags")
        
        self.catalog.reindex()


    def recompute_cache(self):
        if self.catalog.recommender is not None:
            self.catalog.recommender.reindex()
