'''
DEGREE PLANNER MAIN CLASS
'''

from ..io.output import Output
from .catalog import Catalog
from ..user.user import User
from src.io.parse import *
from .degree import *
from .command_handler import command_handler

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

    def __init__(self, io:Output=None, ENABLE_TENSORFLOW=True):
        # each user is assigned a User object and stored in this dictionary
        # Users = <user id, User>
        self.users = dict()
        self.catalog = Catalog(enable_tensorflow=ENABLE_TENSORFLOW)

        self.default_io = io
        if self.default_io is None:
            self.default_io = Output(Output.OUT.CONSOLE, signature='INPUT HANDLER', auto_clear=True)

        self.ENABLE_TENSORFLOW = ENABLE_TENSORFLOW
        self.SEMESTERS_MAX  = 12


    def user_input(self, user:User, input:str, io=None):
        if io is None:
            io = self.default_io
        command_handler.user_input(self, user, input, io)


    def schedule(self, user:User, schedule_name:str, io:Output=None) -> None:
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
            user.new_schedule(schedule_name)
            user.set_active_schedule(schedule_name)
            return
        else:
            io.print(f"Successfully switched to schedule {schedule_name}!")
            user.set_active_schedule(schedule_name)
            return


    def schedules(self, user:User) -> list:
        ''' Get all of user's schedule

        Args:
            user (User): get the active schedule of this user

        Returns:
            list (list(Schedule)): returns a list of all schedule
                objects
        '''
        return user.schedules()


    def degree(self, user:User, degree_name:str, io:Output=None) -> bool:
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
        
        user.get_active_schedule().degree = degree
        io.print(f"set your degree to {degree.name}")
        return True


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


    def add_course(self, user:User, semester, course_name:str, io:Output=None):
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
            return

        # list of courses matching course_name
        semester = int(semester)
        matched_course_names = self.catalog.search(course_name)

        if len(matched_course_names) == 0:
            io.print(f"Course {course_name} not found")
            return
        if len(matched_course_names) > 1:
            io.print(f"Too many options for course {course_name}")
            return

        # at this point, returned_courses have exactly one course, so we can perform the addition immediately
        course = matched_course_names[0]
        user.get_active_schedule().add_course(semester, self.catalog.get_course(course))
        io.print(f"Added course {course} to semester {semester}")


    def remove_course(self, user:User, semester, course_name:str, io:Output=None):
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

        if not semester.isdigit() or int(semester) not in range(0, self.SEMESTERS_MAX):
            io.print(f"Invalid semester {semester}, enter number between 0 and {self.SEMESTERS_MAX}")
            return

        semester = int(semester)
        this_semester_courses = user.get_active_schedule().get_semester(semester)

        matched_course_names = self.catalog.search(course_name, this_semester_courses)

        if len(matched_course_names) == 0:
            io.print(f"Course {course_name} not found")
            return
        if len(matched_course_names) > 1:
            io.print(f"Too many options for course {course_name}")
            return

        course = matched_course_names[0]
        user.get_active_schedule().remove_course(semester, self.catalog.get_course(course))
        io.print(f"Removed course {course} from semester {semester}")


    def find(self, course_name:str) -> None:
        ''' Print list of courses to output that match input entry, searches from entire catalog

        Args:
            course_name (str): search term
            output (Output): user interface output
        '''
        possible_courses = self.catalog.search(course_name)
        possible_courses.sort()
        return possible_courses


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

        parse_degrees(self.catalog, io)
        io.print(f"Sucessfully parsed degree data")

        parse_tags(self.catalog, io)
        io.print(f"parsed tags")

        self.catalog.reindex()


    def cache(self):
        if self.catalog.recommender is not None:
            self.catalog.recommender.recache()
