''' 
DEGREE PLANNER MAIN CLASS
'''

import re
from ..io.output import *
from .course import Course
from .catalog import Catalog
from .schedule import Schedule
from .test_suite import Test1
from .user import User
from .user import Flag
from .search import Search
from .command import *
from .parse import *

VERSION = "API 2.0"
SEMESTERS_MAX = 12

OUTERROR = Output(OUT.ERROR)
OUTWARNING = Output(OUT.WARN)
OUTINFO = Output(OUT.INFO)
OUTDEBUG = Output(OUT.DEBUG)
OUTCONSOLE = Output(OUT.CONSOLE)

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

    def __init__(self, name):
        # each user is assigned a User object and stored in this dictionary
        # Users = <user id, User>
        self.name = name
        self.users = dict()
        self.catalog = Catalog()
        self.course_search = Search()
        self.flags = set()


    async def input_handler(self, user:User, user_input:str, output:Output=None):
        ''' MAIN FUNCTION FOR ACCEPTING COMMAND ENTRIES

        Args:
            user (User): user object containing all user data and unique user ID
            message (str): string to be parsed as command or submitted to a waiting
                active command
            output (Output): user interface output

        Returns:
            bool: whether input was successfully executed
        '''
        if output is None: output = Output(OUT.CONSOLE)
        if Flag.CMD_PAUSED in user.flag:
            user.command_queue_locked = True
            await OUTDEBUG.print(f'user {user.username} locked command queue')
            user.command_decision = user_input.strip().casefold()
            await OUTDEBUG.print(f'passed user {user.username} decision {user_input} to command loop')
        else:
            # if queue is locked, do not proceed
            if user.command_queue_locked:
                await OUTDEBUG.print(f'user {user.username} tried to access busy queue lmao')
                await output.print(f"ERROR{DELIMITER_TITLE}queue busy, please try again later")
                return False
            user.command_queue_locked = True
            await OUTDEBUG.print(f'user {user.username} locked command queue')
            user.command_queue.join()
            commands = await self.parse_command(user_input, output)
            for command in commands:
                user.command_queue.put(command)
        await self.command_handler(user, output)
        user.command_queue_locked = False
        await OUTDEBUG.print(f'user {user.username} unlocked command queue')
        return True


    async def command_handler(self, user:User, output:Output=None) -> None:
        ''' EXECUTES COMMANDS TAKEN FROM USER'S COMMAND QUEUE

        Args:
            user (User): user object containing all user data and unique user ID
            output (Output): user interface output
        '''
        if output is None: output = Output(OUT.CONSOLE)

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
        await OUTDEBUG.print(f'user {user.username} entered command loop')
        while(not user.command_queue.empty() or Flag.CMD_PAUSED in user.flag):
            if Flag.CMD_PAUSED in user.flag:
                command:Command = user.command_paused
            else:
                command:Command = user.command_queue.get()
                await OUTDEBUG.print(f'user {user.username} fetched command {str(command)}')

            if command.command == CMD.NONE:
                await output(f"ERROR{DELIMITER_TITLE}there was an error understanding your command")
                user.command_queue.task_done()
                continue

            if command.command == CMD.TEST:
                await output.print("BEGINNING TEST", output_location=OUT.INFO)
                await output.print(f"ADMIN{DELIMITER_TITLE}Testing Degree Planner {VERSION}")
                await self.test(Output(OUT.DEBUG))
                await output.print("FINISHED TEST", output_location=OUT.INFO)
                await output.print(f"ADMIN{DELIMITER_TITLE}Test completed successfully, all assertions met")
                user.command_queue.task_done()
                continue

            if command.command == CMD.IMPORT:
                await output.print("BEGINNING DATA IMPORTING", output_location=OUT.INFO)
                await output.print(f"ADMIN{DELIMITER_TITLE}begin parsing data")
                await self.parse_data(Output(OUT.DEBUG))
                await output.print("FINISHED DATA IMPORTING", output_location=OUT.INFO)
                await output.print(f"ADMIN{DELIMITER_TITLE}parsing completed")
                user.command_queue.task_done()
                continue

            if command.command == CMD.FIND:
                if len(command.arguments) == 0:
                    await output.print(f"FIND{DELIMITER_TITLE}no arguments found. Use find, [courses] to find courses")
                else:
                    for entry in command.arguments:
                        await self.print_matches(entry, output)
                user.command_queue.task_done()
                continue

            if command.command == CMD.SCHEDULE:
                if not command.arguments:
                    await output.print(f"SCHEDULE{DELIMITER_TITLE}not enough arguments, please specify a schedule name")
                else:
                    await self.set_active_schedule(user, command.arguments[0], output)
                user.command_queue.task_done()
                continue

            # all commands after this requires an active schedule inside User
            schedule = user.get_current_schedule()
            if schedule == None:
                await output.print(f"SCHEDULE{DELIMITER_TITLE}no schedule selected, creating one named {user.username}")
                await self.set_active_schedule(user, user.username, output)
                schedule = user.get_current_schedule()

            if command.command in (CMD.ADD, CMD.REMOVE):
                if Flag.CMD_PAUSED in user.flag:
                    decision = user.command_decision
                    courses = command.data_store
                    if not decision.isdigit() or int(decision) not in range(1, len(courses) + 1):
                        await output.print(f"SCHEDULE{DELIMITER_TITLE}Please enter a valid selection number")
                        break
                    course:Course = courses[int(decision) - 1]
                    command.arguments[1] = course.get_unique_name()
                    user.flag.remove(Flag.CMD_PAUSED)

                semester = command.arguments[0]
                course = command.arguments[1]

                if command.command == CMD.ADD:
                    possible_courses = await self.add_course(user, course, semester, output)
                else:
                    possible_courses = await self.remove_course(user, course, semester, output)

                if possible_courses is not None:
                    await output.print(f"SCHEDULE{DELIMITER_TITLE}entry {course} has multiple choices, please choose from list:")
                    i = 1
                    for c in possible_courses:
                        output.print_hold(f"  {i}: {repr(c)}")
                        i += 1
                    await output.print_cache()
                    # pause command, set temporary variables/storage and break from the loop
                    command.data_store = possible_courses
                    user.command_paused = command
                    user.flag.add(Flag.CMD_PAUSED)
                    break

                user.command_queue.task_done()
                continue

            if command.command == CMD.PRINT:
                await output.print(f"SCHEDULE{DELIMITER_TITLE}{schedule.name}")
                output.print_hold(f"{str(schedule)}")
                await output.print_cache()
                user.command_queue.task_done()
                continue

            if command.command == CMD.DEGREE:
                if not command.arguments:
                    await output.print(f"SCHEDULE{DELIMITER_TITLE}no arguments found. " + \
                        "Use degree, <degree name> to set your schedule's degree")
                else:
                    await self.set_degree(schedule, command.arguments[0], output)
                user.command_queue.task_done()
                continue

            if command.command == CMD.FULFILLMENT:
                if schedule.degree == None:
                    await output.print(f"SCHEDULE{DELIMITER_TITLE}no degree specified")
                else:
                    await output.print(f"SCHEDULE{DELIMITER_TITLE}{schedule.name} Fulfillment")
                    fulfillment = schedule.degree.fulfillment(schedule.get_all_courses())
                    output.print_hold(schedule.degree.print_fulfillment(fulfillment))
                    await output.print_cache()
                user.command_queue.task_done()
                continue

            if command.command == CMD.AUTOCOMPLETE:
                if schedule.degree == None:
                    await output.print(f"SCHEDULE{DELIMITER_TITLE}no degree specified")
                else:
                    await output.print(f"SCHEDULE{DELIMITER_TITLE}{schedule.name} Recommended path of completion:")

                user.command_queue.task_done()
                continue

            if command.command == CMD.DETAILS:
                details = self.details(command.arguments[0])
                if details is None: details = 'please enter valid full name of course'
                await output.print(details)
                user.command_queue.task_done()
                continue

            else:
                await output.print(f"Unimplemented command {command.command} entered")
                user.command_queue.task_done()
                continue


    #--------------------------------------------------------------------------
    # HELPER FUNCTIONS
    #--------------------------------------------------------------------------

    async def parse_command(self, cmd:str, output:Output=None) -> list:
        ''' Parse string into a list of Command objects

        Args:
            cmd (str): input string to be parsed
            output (Output): user interface output

        Returns:
            list[Command]: list of Command objects each containing data
                on command and arguments
        '''
        if output is None: output = Output(OUT.CONSOLE)

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
                    await output.print(f"ERROR{DELIMITER_TITLE}invalid command '{e}'")
        # after exiting the loop, push the last command if it exists into the queue
        if last_command is not None:
            cmd_queue.append(last_command)

        # verify all commands have the required number of arguments
        for e in cmd_queue:
            if not e.valid():
                await output.print(f"ERROR{DELIMITER_TITLE}invalid arguments for command {str(e)}")
        cmd_queue = [e for e in cmd_queue if e.valid()]
        return cmd_queue


    def cleanse(self, msg:str) -> str:
        re.sub(r'\W+', '', msg)
        return msg


    async def test(self, output:Output=None):
        ''' Runs test suite

        Args:
            output (Output): user interface output
        '''
        if output is None: output = Output(output_location=OUT.DEBUG)
        test_suite = Test1()
        await test_suite.test(output)


    async def set_active_schedule(self, user:User, schedule_name:str, output:Output=None) -> None:
        ''' Changes user's active schedule selection and creates new schedule if
            specified schedule is not found

        Args:
            user (User): user to perform the action on
            schedule_name (str): schedule name
            output (Output): user interface output
        '''
        if output is None: output = Output(OUT.CONSOLE)
        schedule = user.get_schedule(schedule_name)
        if schedule == None:
            await output.print(f"SCHEDULE{DELIMITER_TITLE}Schedule {schedule_name} not found, generating new one!")
            user.new_schedule(schedule_name)
            user.curr_schedule = schedule_name
            return
        else:
            await output.print(f"SCHEDULE{DELIMITER_TITLE}Successfully switched to schedule {schedule_name}!")
            user.curr_schedule = schedule_name
            return



    async def get_active_schedule(self, user:User) -> Schedule:
        ''' Gets schedule currently being modified by user

        Args:
            user (User): get the active schedule of this user

        Returns:
            schedule (Schedule): active schedule object
        '''
        return user.get_current_schedule()


    async def get_all_schedules(self, user:User) -> list:
        ''' Get all of user's schedule

        Args:
            user (User): get the active schedule of this user

        Returns:
            list (list(Schedule)): returns a list of all schedule
                objects
        '''
        return user.get_all_schedules()


    async def set_degree(self, schedule:Schedule, degree_name:str, output:Output=None) -> bool:
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
        if output is None: output = Output(OUT.CONSOLE)
        degree = self.catalog.get_degree(degree_name)
        if degree == None:
            await output.print(f"SCHEDULE{DELIMITER_TITLE}invalid degree entered: {degree_name}")
            return False
        else:
            schedule.degree = degree
            await output.print(f"SCHEDULE{DELIMITER_TITLE}set your degree to {degree.name}")
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
            s = f'{repr(course)}{DELIMITER_TITLE}{course.description}'
            return s
        return None


    async def print_matches(self, course_name:str, output:Output=None) -> None:
        ''' Print list of courses to output that match input entry, searches from entire catalog

        Args:
            course_name (str): search term
            output (Output): user interface output
        '''
        if output is None: output = Output(OUT.CONSOLE)
        possible_courses = self.course_search.search(course_name)
        possible_courses.sort()
        await output.print(f"FIND{DELIMITER_TITLE}courses matching {course_name}: ")
        i = 1
        for c in possible_courses:
            course = self.catalog.get_course(c)
            output.print_hold(f"  {i}: {course.subject} {course.course_id} {course.name}")
            i += 1
        await output.print_cache()


    async def add_course(self, user:User, course_name:str, semester, output:Output=None):
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
        if output is None: output = Output(OUT.CONSOLE)

        # sanity checks
        if isinstance(semester, str) and not semester.isdigit():
            await output.print(f"SCHEDULE{DELIMITER_TITLE}semester must be a number")
            return None
        semester = int(semester)
        if semester not in range(0, SEMESTERS_MAX):
            await output.print(f"SCHEDULE{DELIMITER_TITLE}Invalid semester {semester}, enter number between 0 and 11")
            return None
        
        # list of courses matching course_name
        returned_courses = [self.catalog.get_course(c) for c in self.course_search.search(course_name)]

        if len(returned_courses) == 0:
            await output.print(f"SCHEDULE{DELIMITER_TITLE}Course {course_name} not found")
            return None
        if len(returned_courses) > 1:
            return returned_courses
        
        # at this point, returned_courses have exactly one course, so we can perform the addition immediately
        course = returned_courses[0]
        user.get_current_schedule().add_course(course, semester)
        await output.print(f"SCHEDULE{DELIMITER_TITLE}Added course {course.name} to semester {semester}")
        return None


    async def remove_course(self, user:User, course_name:str, semester, output:Output=None):
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
        if output is None: output = Output(OUT.CONSOLE)

        # sanity checks
        if isinstance(semester, str) and not semester.isdigit():
            await output.print(f"SCHEDULE{DELIMITER_TITLE}semester must be a number")
            return None
        semester = int(semester)
        if semester not in range(0, SEMESTERS_MAX):
            await output.print(f"SCHEDULE{DELIMITER_TITLE}Invalid semester {semester}, enter number between 0 and 11")
            return None
        
        this_semester_courses = user.get_current_schedule().get_semester(semester)

        if len(this_semester_courses) == 0:
            await output.print(f"SCHEDULE{DELIMITER_TITLE}No courses in semester {semester}")
            return None
        
        # list of courses matching course_name
        print(str(this_semester_courses))
        returned_courses = [self.catalog.get_course(c) for c in self.search(course_name, this_semester_courses)]

        if len(returned_courses) == 0:
            await output.print(f"SCHEDULE{DELIMITER_TITLE}Course {course_name} not found")
            return None
        if len(returned_courses) > 1:
            return returned_courses
        
        # at this point, returned_courses have exactly one course, so we can perform the removal immediately
        course = returned_courses[0]
        user.get_current_schedule().remove_course(course, semester)
        await output.print(f"SCHEDULE{DELIMITER_TITLE}Removed course {course.name} from semester {semester}")
        return None

    
    async def parse_data(self, output:Output=None) -> Exception:
        ''' Parse json data into a list of courses and degrees inside a catalog

        Args:
            output (Output): user interface output

        Returns:
            Exception: if exception occurs, returns exception, else None
        '''
        if output is None: 
            output = Output(OUT.CONSOLE)

        catalog_file = "catalog_results.json"
        degree_file = "class_results.json"

        #try:
        await parse_courses(catalog_file, self.catalog, output)
        await output.print(f"ADMIN{DELIMITER_TITLE}Sucessfully parsed catalog data")
        
        # set up searcher for finding courses based on incomplete user input
        self.course_search.update_items(self.catalog.get_all_course_names())
        self.course_search.generate_index()

        await parse_degrees(degree_file, self.catalog, output)
        await output.print(f"ADMIN{DELIMITER_TITLE}Sucessfully parsed degree data")
        await output.print(f"ADMIN{DELIMITER_TITLE}Printing catalog:", output_location=OUT.DEBUG)
        output.print_hold(str(self.catalog))
        await output.print_cache(OUT.DEBUG)

        #except Exception as e:
        #    await output.print(f"ERROR{DELIMITER_TITLE}An exception has occurred during parsing: {e}", output_location=OUT.ERROR)
        #    return e

        #else:
        #    return None
