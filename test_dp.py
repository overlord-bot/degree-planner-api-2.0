import timeit
import asyncio
from datetime import datetime
from src.dp.graph import Graph
from src.dp.degree_planner import Planner
from src.dp.course import Course
from src.dp.user import User
from src.dp.degree_template import Template
from src.dp.degree import *

def test_graph():
    n1 = '1'
    n2 = '2'
    n3 = '3'
    n4 = '4'
    n5 = '5'
    graph = Graph([n1, n2, n3, n4, n5])
    print(f'initial graph: {graph}')

    graph.add_connection(n1, n2)
    graph.add_connection(n3, n1)
    graph.add_connection(n3, n4)
    graph.add_connection(n3, n5)
    graph.add_connection(n4, n5)
    graph.add_connection(n4, n1)
    graph.add_connection(n4, n3)
    graph.add_connection(n5, n4)

    print(f'added connections: {graph}')

    graph.remove_connection(n3, n4)
    graph.remove_connection(n2, n3)

    print(f'removed connections: {graph}')

    print(f'outbound connections from n5: {graph.outbound_connections(n5)}')
    print(f'inbound connectinos for n5: {graph.inbound_connections(n5)}')

    bfs = graph.bfs({n5})
    print(f'{bfs}')

def test_fulfillment():
    planner = Planner('test_planner')
    user = User(1)
    
    catalog = planner.catalog
    degree = Degree("computer science")
    catalog.add_degree(degree)

    course1 = Course('1', 'BINTEST', 1)
    course1.add_attribute('bin.1')
    course1.add_attribute('bin.5')
    catalog.add_course(course1)

    course2 = Course('2', 'BINTEST', 2)
    course2.add_attribute('bin.1')
    course2.add_attribute('bin.2')
    catalog.add_course(course2)

    course3 = Course('3', 'BINTEST', 3)
    course3.add_attribute('bin.2')
    course3.add_attribute('bin.3')
    catalog.add_course(course3)

    course4 = Course('4', 'BINTEST', 4)
    course4.add_attribute('bin.3')
    course4.add_attribute('bin.4')
    catalog.add_course(course4)

    course5 = Course('5', 'BINTEST', 5)
    course5.add_attribute('bin.3')
    course5.add_attribute('bin.4')
    catalog.add_course(course5)

    print('course 1 + course 2: ' + repr(course1 + course2))

    planner.course_search.update_items(catalog.get_all_course_names())
    planner.course_search.generate_index()

    testtemplate1 = Template('bin1', Course("ANY", "BINTEST", 'ANY'))
    testtemplate1.template_course.add_attribute('bin.1')
    testtemplate1.courses_required = 1
    testtemplate2 = Template('bin2', Course("ANY", "BINTEST", 'ANY'))
    testtemplate2.template_course.add_attribute('bin.2')
    testtemplate3 = Template('bin3', Course("ANY", "BINTEST", 'ANY'))
    testtemplate3.template_course.add_attribute('bin.3')
    testtemplate4 = Template('bin4', Course("ANY", "BINTEST", 'ANY'))
    testtemplate4.template_course.add_attribute('bin.4')
    testtemplate5 = Template('bin5', Course("ANY", "BINTEST", 'ANY'))
    testtemplate5.template_course.add_attribute('bin.5')
    testtemplate1.replacement = False
    testtemplate2.replacement = False
    testtemplate3.replacement = False
    testtemplate4.replacement = False
    testtemplate5.replacement = False

    degree.add_template(testtemplate1)
    degree.add_template(testtemplate2)
    degree.add_template(testtemplate3)
    degree.add_template(testtemplate4)
    degree.add_template(testtemplate5)

    print('template 1 + template 2: ' + repr(testtemplate1 + testtemplate2))

    run_cmd(planner, user, 'degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4, add, 5, bin 5, print, fulfillment')


def test_fulfillment2():
    planner = Planner('test_planner2', 12)
    user = User(1)
    
    catalog = planner.catalog
    degree = Degree("computer science")
    catalog.add_degree(degree)

    course1 = Course('1', 'BINTEST', 1)
    course1.add_attribute('bin.1')
    course1.add_attribute('bin.5')
    catalog.add_course(course1)

    course2 = Course('2', 'BINTEST', 2)
    course2.add_attribute('bin.1')
    course2.add_attribute('bin.2')
    catalog.add_course(course2)

    course3 = Course('3', 'BINTEST', 3)
    course3.add_attribute('bin.2')
    course3.add_attribute('bin.3')
    course3.add_attribute('bin.4')
    catalog.add_course(course3)

    course4 = Course('4', 'BINTEST', 4)
    course4.add_attribute('bin.2')
    course4.add_attribute('bin.3')
    course4.add_attribute('bin.4')
    catalog.add_course(course4)

    course5 = Course('5', 'BINTEST', 5)
    course5.add_attribute('bin.3')
    course5.add_attribute('bin.4')
    catalog.add_course(course5)

    course6 = Course('6', 'BINTEST', 6)
    course6.add_attribute('bin.3')
    course6.add_attribute('bin.5')
    catalog.add_course(course6)

    planner.course_search.update_items(catalog.get_all_course_names())
    planner.course_search.generate_index()

    testtemplate1 = Template('bin1', Course("ANY", "BINTEST", 'ANY'))
    testtemplate1.template_course.add_attribute('bin.1')
    testtemplate1.courses_required = 1
    testtemplate2 = Template('bin2', Course("ANY", "BINTEST", 'ANY'))
    testtemplate2.template_course.add_attribute('bin.2')
    testtemplate3 = Template('bin3', Course("ANY", "BINTEST", 'ANY'))
    testtemplate3.template_course.add_attribute('bin.3')
    testtemplate4 = Template('bin4', Course("ANY", "BINTEST", 'ANY'))
    testtemplate4.template_course.add_attribute('bin.4')
    testtemplate5 = Template('bin5', Course("ANY", "BINTEST", 'ANY'), courses_required=2)
    testtemplate5.template_course.add_attribute('bin.5')
    replacement = True
    testtemplate1.replacement = replacement
    testtemplate2.replacement = replacement
    testtemplate3.replacement = replacement
    testtemplate4.replacement = replacement
    testtemplate5.replacement = replacement

    degree.add_template(testtemplate1)
    degree.add_template(testtemplate2)
    degree.add_template(testtemplate3)
    degree.add_template(testtemplate4)
    degree.add_template(testtemplate5)

    run_cmd(planner, user, 'degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4, add, 5, bin 5, add, 6, bin 6, print, fulfillment')

def test_fulfillment3():
    planner = Planner('test_planner2', 20)
    user = User(1)
    
    catalog = planner.catalog
    degree = Degree("computer science")
    catalog.add_degree(degree)

    course1 = Course('1', 'BINTEST', 1)
    course1.add_attribute('bin.1')
    course1.add_attribute('bin.5')
    catalog.add_course(course1)

    course2 = Course('2', 'BINTEST', 2)
    course2.add_attribute('bin.1')
    course2.add_attribute('bin.2')
    catalog.add_course(course2)

    course3 = Course('3', 'BINTEST', 3)
    course3.add_attribute('bin.2')
    course3.add_attribute('bin.3')
    course3.add_attribute('bin.4')
    catalog.add_course(course3)

    course4 = Course('4', 'BINTEST', 4)
    course4.add_attribute('bin.2')
    course4.add_attribute('bin.3')
    course4.add_attribute('bin.4')
    catalog.add_course(course4)

    course5 = Course('5', 'BINTEST', 5)
    course5.add_attribute('bin.3')
    course5.add_attribute('bin.4')
    catalog.add_course(course5)

    course6 = Course('6', 'BINTEST', 6)
    course6.add_attribute('bin.3')
    course6.add_attribute('bin.5')
    catalog.add_course(course6)

    planner.course_search.update_items(catalog.get_all_course_names())
    planner.course_search.generate_index()

    testtemplate1 = Template('bin1', Course("ANY", "BINTEST", 'ANY'), courses_required=1)
    testtemplate1.template_course.add_attribute('bin.1')
    testtemplate2 = Template('bin2', Course("ANY", "BINTEST", 'ANY'))
    testtemplate2.template_course.add_attribute('bin.2')
    testtemplate3 = Template('bin3', Course("ANY", "BINTEST", 'ANY'))
    testtemplate3.template_course.add_attribute('bin.3')
    testtemplate4 = Template('bin4', Course("ANY", "BINTEST", 'ANY'))
    testtemplate4.template_course.add_attribute('bin.4')
    testtemplate5 = Template('bin5', Course("ANY", "BINTEST", 'ANY'), courses_required=2)
    testtemplate5.template_course.add_attribute('bin.5')
    testtemplate1.replacement = False
    testtemplate2.replacement = False
    testtemplate3.replacement = False
    testtemplate4.replacement = False
    testtemplate5.replacement = False

    degree.add_template(testtemplate1)
    degree.add_template(testtemplate2)
    degree.add_template(testtemplate3)
    degree.add_template(testtemplate4)
    degree.add_template(testtemplate5)

    run_cmd(planner, user, 'degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4, add, 5, bin 5, add, 6, bin 6')
    run_cmd(planner, user, 'print, fulfillment')

def run_cmd(planner, user, string):
    planner.input_handler(user, string)


start = timeit.default_timer()

print(f'beginning test {datetime.now()}')
test_graph()
input('press enter to continue')
test_fulfillment()
input('press enter to continue')
test_fulfillment2()
input('press enter to continue')
test_fulfillment3()

stop = timeit.default_timer()
print('\ntime: ', stop - start)
