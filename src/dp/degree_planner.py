''' 
DEGREE PLANNER MAIN CLASS
'''

import re
from ..io.output import *
from .course import Course
from .catalog import Catalog
from .schedule import Schedule
from .old_test_suite import Test1
from .user import User
from .user import Flag
from .search import Search
from .command import *
from .parse import *
from .degree import *

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
            test
                - run test_suite.py
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

    def __init__(self, name, SEMESTERS_MAX:int=10):
        # each user is assigned a User object and stored in this dictionary
        # Users = <user id, User>
        self.name = name
        self.users = dict()
        self.catalog = Catalog()
        self.course_search = Search()
        self.flags = set()

        self.default_io = Output(OUT.CONSOLE, signature='INPUT HANDLER', auto_clear=True)

        self.SEMESTERS_MAX = SEMESTERS_MAX


    def input_handler(self, user:User, user_input:str, io:Output=None) -> bool:
        ''' MAIN FUNCTION FOR ACCEPTING COMMAND ENTRIES

        Args:
            user (User): user object containing all user data and unique user ID
            message (str): string to be parsed as command or submitted to a waiting
                active command
            output (Output): user interface output

        Returns:
            bool: whether input was successfully executed
        '''
        if io is None:
            io = self.default_io

        if Flag.CMD_PAUSED in user.flag:
            user.command_queue_locked = True
            io.debug(f'user {user.username} locked command queue')
            user.command_decision = user_input.strip().casefold()
        
        else:
            # if queue is locked, do not proceed
            if user.command_queue_locked:
                io.print(f'queue busy, please try again later')
                return False
            
            user.command_queue_locked = True
            io.debug(f'user {user.username} locked command queue')
            user.command_queue.join()
            commands = self.parse_command(user_input, io)

            for command in commands:
                user.command_queue.put(command)

        self.command_handler(user, io)
        user.command_queue_locked = False
        io.debug(f'user {user.username} unlocked command queue')
        return True


    def command_handler(self, user:User, io:Output=None) -> None:
        ''' EXECUTES COMMANDS TAKEN FROM USER'S COMMAND QUEUE

        Args:
            user (User): user object containing all user data and unique user ID
            output (Output): user interface output
        '''
        if io is None:
            io = self.default_io
            self.default_io.user = user

        """
        This while loop will keep running until all commands are executed with
        one exception: if user input is requested to finish running a command.
        
        If that is the case, this loop will break, the current command will be
        stored in User, and further user input will run this loop again where
        it first executes the stored command, and then continue as normal.
        
        NOTE: Use break to stop this loop only when awaiting user input
        and add Flag.CMD_PAUSED in user.flag, otherwise the loop can never
        be entered again.
        """
        io.debug(f'user {user.username} entered command loop')
        while(not user.command_queue.empty() or Flag.CMD_PAUSED in user.flag):
            if Flag.CMD_PAUSED in user.flag:
                command:Command = user.command_paused
            else:
                command:Command = user.command_queue.get()
                io.debug(f'user {user.username} fetched command {command}')

            if command.command == CMD.NONE:
                io.print(f"there was an error understanding your command")
                user.command_queue.task_done()
                continue

            if command.command == CMD.TEST:
                io.print(f"Testing Degree Planner {VERSION}")
                self.test(io)
                io.print(f"Test completed successfully, all assertions met")
                user.command_queue.task_done()
                continue

            if command.command == CMD.IMPORT:
                io.info("BEGINNING DATA IMPORTING")
                io.print("begin parsing data")
                self.parse_data(io)
                io.info("FINISHED DATA IMPORTING")
                io.print("parsing completed")
                user.command_queue.task_done()
                continue

            if command.command == CMD.FIND:
                if len(command.arguments) == 0:
                    io.print(f"no arguments found. Use find, [courses] to find courses")
                else:
                    for entry in command.arguments:
                        self.print_matches(entry, io)
                user.command_queue.task_done()
                continue

            if command.command == CMD.SCHEDULE:
                if not command.arguments:
                    io.print(f"not enough arguments, please specify a schedule name")
                else:
                    self.set_active_schedule(user, command.arguments[0], io)
                user.command_queue.task_done()
                continue

            # all commands after this requires an active schedule inside User
            schedule = user.get_current_schedule()
            if schedule == None:
                io.print(f"no schedule selected, creating one named {user.username}")
                self.set_active_schedule(user, user.username, io)
                schedule = user.get_current_schedule()

            if command.command in (CMD.ADD, CMD.REMOVE):
                if Flag.CMD_PAUSED in user.flag:
                    decision = user.command_decision
                    courses = command.data_store
                    if not decision.isdigit() or int(decision) not in range(1, len(courses) + 1):
                        io.print(f"Please enter a valid selection number")
                        break
                    course:Course = courses[int(decision) - 1]
                    command.arguments[1] = course.get_unique_name()
                    user.flag.remove(Flag.CMD_PAUSED)

                semester = command.arguments[0]
                course = command.arguments[1]

                if command.command == CMD.ADD:
                    possible_courses = self.add_course(user, course, semester, io)
                else:
                    possible_courses = self.remove_course(user, course, semester, io)

                if possible_courses is not None:
                    io.print(f"entry {course} has multiple choices, please choose from list:")
                    i = 1
                    for c in possible_courses:
                        io.store(f"  {i}: {c.subject} {c.course_id} {c.name}")
                        i += 1
                    io.view_cache()
                    # pause command, set temporary variables/storage and break from the loop
                    command.data_store = possible_courses
                    user.command_paused = command
                    user.flag.add(Flag.CMD_PAUSED)
                    break

                user.command_queue.task_done()
                continue

            if command.command == CMD.PRINT:
                io.store(f"{str(schedule)}")
                io.view_cache()
                user.command_queue.task_done()
                continue

            if command.command == CMD.DEGREE:
                if not command.arguments:
                    io.print(f"no arguments found. " + \
                        "Use degree, <degree name> to set your schedule's degree")
                else:
                    self.set_degree(schedule, command.arguments[0], io)
                user.command_queue.task_done()
                continue

            if command.command == CMD.FULFILLMENT:
                if schedule.degree == None:
                    io.print(f"no degree specified")
                else:
                    io.store(f"{schedule.name} Fulfillment")
                    io.store(f"  taken courses: {[str(e) for e in schedule.get_all_courses()]}")
                    fulfillment = schedule.degree.fulfillment(schedule.get_all_courses())
                    io.store(print_fulfillment(fulfillment))
                    io.view_cache()
                user.command_queue.task_done()
                continue

            if command.command == CMD.AUTOCOMPLETE:
                if schedule.degree == None:
                    io.print(f"no degree specified")
                else:
                    io.store(f"{schedule.name} Recommended path of completion:")
                    io.view_cache()

                user.command_queue.task_done()
                continue

            if command.command == CMD.DETAILS:
                details = self.details(command.arguments[0])
                if details is None: details = 'please enter valid full name of course'
                io.store(details)
                io.view_cache()
                user.command_queue.task_done()
                continue

            else:
                io.print(f"Unimplemented command {command.command} entered")
                user.command_queue.task_done()
                continue


    #--------------------------------------------------------------------------
    # HELPER FUNCTIONS
    #--------------------------------------------------------------------------

    def parse_command(self, cmd:str, io:Output=None) -> list:
        ''' Parse string into a list of Command objects

        Args:
            cmd (str): input string to be parsed
            output (Output): user interface output

        Returns:
            list[Command]: list of Command objects each containing data
                on command and arguments
        '''
        if io is None:
            io = self.default_io

        arg_list = [self.cleanse(e.strip().casefold()) for e in cmd.split(",") if e.strip()]
        cmd_queue = []
        last_command = None

        for e in arg_list:
            # if we find a command, push the last command to the queue and create new command
            if CMD.get(e) != CMD.NONE:
                if last_command is not None:
                    cmd_queue.append(last_command)
                last_command = Command(e)
            # otherwise, add this as an argument to the last command
            else:
                if last_command is not None:
                    last_command.arguments.append(e)
                else:
                    io.print(f"ERROR: invalid command '{e}'")
        # after exiting the loop, push the last command if it exists into the queue
        if last_command is not None:
            cmd_queue.append(last_command)

        # verify all commands have the required number of arguments
        for e in cmd_queue:
            if not e.valid():
                io.print(f"ERROR: invalid arguments for command {str(e)}")
        cmd_queue = [e for e in cmd_queue if e.valid()]
        return cmd_queue


    def cleanse(self, msg:str) -> str:
        re.sub(r'\W+', '', msg)
        return msg


    def test(self, io:Output=None):
        ''' Runs test suite

        Args:
            output (Output): user interface output
        '''
        test_suite = Test1()
        test_suite.test(io)


    def set_active_schedule(self, user:User, schedule_name:str, io:Output=None) -> None:
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
        if schedule == None:
            io.print(f"Schedule {schedule_name} not found, generating new one!")
            user.new_schedule(schedule_name, self.SEMESTERS_MAX)
            user.curr_schedule = schedule_name
            return
        else:
            io.print(f"Successfully switched to schedule {schedule_name}!")
            user.curr_schedule = schedule_name
            return



    def get_active_schedule(self, user:User) -> Schedule:
        ''' Gets schedule currently being modified by user

        Args:
            user (User): get the active schedule of this user

        Returns:
            schedule (Schedule): active schedule object
        '''
        return user.get_current_schedule()


    def get_all_schedules(self, user:User) -> list:
        ''' Get all of user's schedule

        Args:
            user (User): get the active schedule of this user

        Returns:
            list (list(Schedule)): returns a list of all schedule
                objects
        '''
        return user.get_all_schedules()


    def set_degree(self, schedule:Schedule, degree_name:str, io:Output=None) -> bool:
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
        if degree == None:
            io.print(f"invalid degree entered: {degree_name}")
            return False
        else:
            schedule.degree = degree
            io.print(f"set your degree to {degree.name}")
            return True

    
    def search(self, course_name:str, course_pool:set=None) -> list:
        ''' Returns list of courses to output that match input entry

        Args:
            course_name (str): search for courses that contains this string in its name
            course_pool (set): pool of courses to search from
        '''
        possible_courses = self.course_search.search(course_name)
        if course_pool is not None:
            possible_courses = [e for e in possible_courses if self.catalog.get_course(e) in course_pool]
        """ 
        Note that while it is possible to use 
        search = Search(course_pool)
        possible_courses = search.search(course_name)
        doing so means we're constructing a new search object and generating its index
        everytime we do a search, drastically slowing down the program and defeating
        the whole point of the searcher.
        """
        return possible_courses


    def details(self, course_name:str) -> str:
        ''' Returns:
            description (string): the course description. Returns None if invalid name
        '''
        courses = self.search(course_name)
        if len(courses) == 0:
            return 'Course not found'
        if len(courses) == 1:
            course = self.catalog.get_course(courses[0])
            s = f'{repr(course)}: {course.description}'
            return s
        return None


    def print_matches(self, course_name:str, io:Output=None) -> None:
        ''' Print list of courses to output that match input entry, searches from entire catalog

        Args:
            course_name (str): search term
            output (Output): user interface output
        '''
        if io is None:
            io = self.default_io

        possible_courses = self.course_search.search(course_name)
        possible_courses.sort()
        io.print(f"courses matching {course_name}: ")
        i = 1
        for c in possible_courses:
            course = self.catalog.get_course(c)
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
            io.print(f"Invalid semester {semester}, enter number between 0 and 11")
            return None
        
        # list of courses matching course_name
        semester = int(semester)
        returned_courses = [self.catalog.get_course(c) for c in self.course_search.search(course_name)]

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
            io.print(f"Invalid semester {semester}, enter number between 0 and 11")
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

    
    def parse_data(self, io:Output=None) -> Exception:
        ''' Parse json data into a list of courses and degrees inside a catalog

        Args:
            output (Output): user interface output

        Returns:
            Exception: if exception occurs, returns exception, else None
        '''
        if io is None:
            io = self.default_io

        catalog_file = "catalog.json"
        degree_file = "degrees.json"

        parse_courses(catalog_file, self.catalog, io)
        io.print(f"Sucessfully parsed catalog data")
        
        # set up searcher for finding courses based on incomplete user input
        self.course_search.update_items(self.catalog.get_all_course_names())
        self.course_search.generate_index()

        parse_degrees(degree_file, self.catalog, io)
        io.print(f"Sucessfully parsed degree data")
        io.debug(f"Printing catalog:")
        io.debug(str(self.catalog))
