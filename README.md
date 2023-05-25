# degree-planner-api-2.0
A standalone degree planner API that can be used through the command line

# Degree Planning API

This is a tool that stores user schedules of one's curriculum, checking requirements and automatic suggestions based on the user's preferences.


## Using this API:

import dp.degree_planner and dp.user. Create a new Planner object, and generate a new User object for every unique user. To interact with the planner, call Planner.input_handler(User, Input). 

Note that input can be a command or a response to a prompt. A prompt is requested when the user enters an ambiguous command, such as specifying a course name with multiple possible choices. If your use case does not allow responding to such prompts, set the noreply flag to true by inputting the command "noreply, true" through an admin user or by using -nr flag when starting the program


## Commands:

Commands can be chained together (i.e. import, schedule, Alan, degree, computer science, add, 1, data structures, remove, 1, data structures, print)

`schedule, <schedule name>` : changes the active schedule that is being modified

`degree, <degree name>` : assigns the specified degree to the current schedule for requirement checking purposes

`add, <semester #>, <course name>` : add a course to schedule

`remove, <semester #>, <course name>` : remove a course from schedule

`print` : displays the user's current active schedule that lists all selected courses under their semester numbers, and requirement checking reports

`fulfillment` : displays fulfillment status for degree requirements

`test` : runs test suite

`import` : imports json catalog into a Catalog object


## Class Structure:

user 
    - stores user data and user schedules
    
catalog 
    - stores one copy of RPI's course catalog and degree list
    - course_match to find courses that matches with a defined criteria (using course_template)
    
schedule
    - stores courses organized by semester

course
    - all data describing a course, contains an attribute dictionary
    
degree
    - list of rules that describe degree requirements
    - calculates degree requirement fulfillment across all rules

course_template
    - describes criteria for filtering courses
    
rule
    - a set of course templates and the required fulfillment amount
    - calculates fulfillment of templates

