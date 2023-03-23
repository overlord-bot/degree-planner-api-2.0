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

    graph.update_connection(n1, n2)
    graph.update_connection(n3, n1)
    graph.update_connection(n3, n4)
    graph.update_connection(n3, n5)
    graph.update_connection(n4, n5)
    graph.update_connection(n4, n1)
    graph.update_connection(n4, n3)
    graph.update_connection(n5, n4)

    print(f'added connections: {graph}')

    graph.remove_connection(n3, n4)
    graph.remove_connection(n2, n3)

    print(f'removed connections: {graph}')

    print(f'outbound connections from n5: {graph.outbound_connections(n5)}')
    print(f'inbound connectinos for n5: {graph.inbound_connections(n5)}')

    bfs = graph.bfs({n5})
    print(f'{bfs}')


def test_other():
    planner = Planner('test_planner')
    user = User(1)
    
    catalog = planner.catalog
    degree = Degree("computer science")
    catalog.add_degree(degree)

    course0 = Course('0', 'BINTEST', 0)
    course0.add_attribute('bin.1')
    course0.add_attribute('bin.5')
    catalog.add_course(course0)

    course1 = Course('1', 'BINTEST', 1)
    course1.add_attribute('bin.1')
    course1.add_attribute('bin.2')
    catalog.add_course(course1)

    course2 = Course('2', 'BINTEST', 2)
    course2.add_attribute('bin.2')
    course2.add_attribute('bin.3')
    catalog.add_course(course2)

    course3 = Course('3', 'BINTEST', 3)
    course3.add_attribute('bin.3')
    course3.add_attribute('bin.4')
    catalog.add_course(course3)

    course4 = Course('4', 'BINTEST', 4)
    course4.add_attribute('bin.4')
    course4.add_attribute('bin.5')
    catalog.add_course(course4)

    course5 = Course('5', 'BINTEST', 5)
    course5.add_attribute('bin.4')
    course5.add_attribute('bin.5')
    catalog.add_course(course5)

    planner.course_search.update_items(catalog.get_all_course_names())
    planner.course_search.generate_index()

    testtemplate1 = Template('bin1', Course("ANY", "BINTEST", 'ANY'))
    #testtemplate1.template_course.add_attribute('bin.1')
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

    # run_cmd(planner, user, 'degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4, add, 5, bin 5, print, fulfillment')

    example_attributes = {
        '':True,
        'True':True,
        'True&True':True,
        'True&False':False,
        'bin.1&bin.5':True,
        'bin.1 & bin.5':True,
        ' () & ( bin.1  &  (((( ( bin.5  ))))) )  ':True,
        ' () & ( bin.1  &  (((( ( bin.5':True,
        'bin.1|bin.5':True,
        'bin.1&bin.4':False,
        'bin.1|bin.4':True,
        'bin.2|bin.4':False,
        'bin.1&bin.5&bin.1':True,
        'bin.1&bin.5&bin.2':False,
        'bin.1&(bin.5|bin.4)':True,
        'bin.2&(bin.1|bin.5)':False,
        'bin.*':True,
        'bin.#':True,
    }
    for example, answer in example_attributes.items():
        true_given = dict()
        response = parse_attribute(example, course0, true_given)
        print(f"parse attribute {example} \n  response: {response}\n  correct response: {answer}")
        print(f"  answer is {'correct :)' if str(response).casefold() == str(answer).casefold() else 'INCORRECT INCORRECT INCORRECT!'}")
        print(f"  true given: {true_given}")

    testtemplate1.template_course.add_attribute('bin.*')
    get_course_match(testtemplate1, {course1, course2, course3, course4, course5})



def test_fulfillment():
    planner = Planner('test_planner')
    user = User(1)
    
    catalog = planner.catalog
    degree = Degree("computer science")
    catalog.add_degree(degree)

    course1 = Course('1', 'BINTEST', 1)
    course1.add_attribute('bin.1')
    course1.add_attribute('bin.5')
    course1.set_credits(4)
    course1.add_attribute('cross_listed.course X')
    course1.add_attribute('cross_listed.course Y')
    catalog.add_course(course1)

    print(repr(course1))

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
    testtemplate2 = Template('bin2', Course("ANY", "BINTEST", 'ANY'))
    testtemplate2.template_course.add_attribute('bin.2')
    testtemplate3 = Template('bin3', Course("ANY", "BINTEST", 'ANY'))
    testtemplate3.template_course.add_attribute('bin.3')
    testtemplate4 = Template('bin4', Course("ANY", "BINTEST", 'ANY'))
    testtemplate4.template_course.add_attribute('bin.4')
    testtemplate5 = Template('bin5', Course("ANY", "BINTEST", 'ANY'), courses_required=1)
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
    testtemplate2 = Template('bin2', Course("ANY", "BINTEST", 'ANY'), courses_required=3)
    testtemplate2.template_course.add_attribute('bin.2')
    testtemplate3 = Template('bin3', Course("ANY", "BINTEST", 'ANY'))
    testtemplate3.template_course.add_attribute('bin.3')
    testtemplate4 = Template('bin4', Course("ANY", "BINTEST", 'ANY'))
    testtemplate4.template_course.add_attribute('bin.4')
    testtemplate5 = Template('bin5', Course("ANY", "BINTEST", 'ANY'), courses_required=2)
    testtemplate5.template_course.add_attribute('bin.5')
    testtemplate1.replacement = False
    testtemplate2.replacement = True
    testtemplate3.replacement = True
    testtemplate4.replacement = False
    testtemplate5.replacement = False

    degree.add_template(testtemplate1)
    degree.add_template(testtemplate2)
    degree.add_template(testtemplate3)
    degree.add_template(testtemplate4)
    degree.add_template(testtemplate5)

    run_cmd(planner, user, 'degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4, add, 5, bin 5, add, 6, bin 6')
    run_cmd(planner, user, 'print, fulfillment')


def test_fulfillment4():
    planner = Planner('test_planner2', 20)
    user = User(1)
    
    catalog = planner.catalog
    degree = Degree("computer science")
    catalog.add_degree(degree)

    course1 = Course('1', 'BINTEST', 1)
    course1.add_attribute('bin.1')
    course1.add_attribute('bin.2')
    course1.add_attribute('bin.3')
    catalog.add_course(course1)

    course2 = Course('2', 'BINTEST', 2)
    course2.add_attribute('bin.1')
    course2.add_attribute('bin.2')
    catalog.add_course(course2)

    planner.course_search.update_items(catalog.get_all_course_names())
    planner.course_search.generate_index()

    testtemplate1 = Template('bin1', Course("ANY", "BINTEST", 'ANY'), courses_required=1)
    testtemplate1.template_course.add_attribute('bin.1')
    testtemplate2 = Template('bin2', Course("ANY", "BINTEST", 'ANY'))
    testtemplate2.template_course.add_attribute('bin.2')
    testtemplate3 = Template('bin3', Course("ANY", "BINTEST", 'ANY'))
    testtemplate3.template_course.add_attribute('bin.3')
    testtemplate1.replacement = False
    testtemplate2.replacement = True
    testtemplate3.replacement = True

    degree.add_template(testtemplate1)
    degree.add_template(testtemplate2)
    degree.add_template(testtemplate3)

    run_cmd(planner, user, 'degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4, add, 5, bin 5, add, 6, bin 6')
    run_cmd(planner, user, 'print, fulfillment')


def test_fulfillment5():
    planner = Planner('test_planner2', 10)
    user = User(1)
    
    catalog = planner.catalog
    degree = Degree("computer science")
    catalog.add_degree(degree)

    course1 = Course('1', 'BINTEST', 1)
    course1.add_attribute('bin.1')
    course1.add_attribute('bin.2')
    course1.add_attribute('bin.3')
    course1.add_attribute('bin.4')
    catalog.add_course(course1)

    course2 = Course('2', 'BINTEST', 2)
    course2.add_attribute('bin.2')
    course2.add_attribute('bin.3')
    course2.add_attribute('bin.4')
    catalog.add_course(course2)

    course3 = Course('3', 'BINTEST', 3)
    course3.add_attribute('bin.1')
    course3.add_attribute('bin.2')
    course3.add_attribute('bin.5')
    catalog.add_course(course3)

    course4 = Course('4', 'BINTEST', 4)
    course4.add_attribute('bin.3')
    course4.add_attribute('bin.5')
    catalog.add_course(course4)

    course5 = Course('5', 'BINTEST', 5)
    course5.add_attribute('bin.4')
    course5.add_attribute('bin.5')
    catalog.add_course(course5)

    planner.course_search.update_items(catalog.get_all_course_names())
    planner.course_search.generate_index()

    testtemplate1 = Template('bin1', Course("ANY", "BINTEST", 'ANY'), courses_required=1)
    testtemplate1.template_course.add_attribute('bin.1')
    testtemplate2 = Template('bin2', Course("ANY", "BINTEST", 'ANY'), courses_required=2)
    testtemplate2.template_course.add_attribute('bin.2')
    testtemplate3 = Template('bin3', Course("ANY", "BINTEST", 'ANY'), courses_required=2)
    testtemplate3.template_course.add_attribute('bin.3')
    testtemplate4 = Template('bin4', Course("ANY", "BINTEST", 'ANY'), courses_required=2)
    testtemplate4.template_course.add_attribute('bin.4')
    testtemplate5 = Template('bin5', Course("ANY", "BINTEST", 'ANY'), courses_required=3)
    testtemplate5.template_course.add_attribute('bin.5')
    testtemplate1.replacement = False
    testtemplate2.replacement = True
    testtemplate3.replacement = True
    testtemplate4.replacement = True
    testtemplate5.replacement = True

    degree.add_template(testtemplate1)
    degree.add_template(testtemplate2)
    degree.add_template(testtemplate3)
    degree.add_template(testtemplate4)
    degree.add_template(testtemplate5)

    run_cmd(planner, user, 'degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4, add, 5, bin 5, add, 6, bin 6')
    run_cmd(planner, user, 'print, fulfillment')

def test_fulfillment6():
    planner = Planner('test_planner2', 10)
    user = User(1)
    
    catalog = planner.catalog
    degree = Degree("computer science")
    catalog.add_degree(degree)

    course1 = Course('1', 'BINTEST', 1)
    course1.add_attribute('bin.1')
    course1.add_attribute('bin.2')
    course1.add_attribute('bin.3')
    course1.add_attribute('bin.4')
    catalog.add_course(course1)

    course2 = Course('2', 'BINTEST', 2)
    course2.add_attribute('bin.2')
    course2.add_attribute('bin.3')
    course2.add_attribute('bin.4')
    catalog.add_course(course2)

    course3 = Course('3', 'BINTEST', 3)
    course3.add_attribute('bin.1')
    course3.add_attribute('bin.2')
    course3.add_attribute('bin.5')
    catalog.add_course(course3)

    course4 = Course('4', 'BINTEST', 4)
    course4.add_attribute('bin.3')
    course4.add_attribute('bin.5')
    catalog.add_course(course4)

    course5 = Course('5', 'BINTEST', 5)
    course5.add_attribute('bin.4')
    course5.add_attribute('bin.5')
    catalog.add_course(course5)


    course6 = Course('6', 'BINTEST', 6)
    course6.add_attribute('bin.1')
    course6.add_attribute('bin.2')
    course6.add_attribute('bin.3')

    course6.add_attribute('bin.6')
    course6.add_attribute('concentration.AI')
    catalog.add_course(course6)

    course7 = Course('7', 'BINTEST', 7)
    course7.add_attribute('bin.1')
    course7.add_attribute('bin.2')
    course7.add_attribute('bin.3')

    course7.add_attribute('bin.6')
    course7.add_attribute('bin.7')
    catalog.add_course(course7)

    course8 = Course('8', 'BINTEST', 8)
    course8.add_attribute('bin.1')
    course8.add_attribute('bin.2')
    course8.add_attribute('bin.3')

    course8.add_attribute('bin.7')
    course8.add_attribute('bin.8')
    course8.add_attribute('bin.9')
    catalog.add_course(course8)

    course9 = Course('9', 'BINTEST', 9)
    course9.add_attribute('bin.1')
    course9.add_attribute('bin.2')
    course9.add_attribute('bin.3')

    course9.add_attribute('bin.7')
    course9.add_attribute('bin.8')
    course9.add_attribute('bin.9')
    course9.add_attribute('concentration.theory')
    catalog.add_course(course9)

    course10 = Course('one', 'BINTEST', 'one')
    course10.add_attribute('bin.3')
    course10.add_attribute('bin.4')
    course10.add_attribute('bin.5')

    course10.add_attribute('bin.8')
    course10.add_attribute('bin.9')
    course10.add_attribute('concentration.theory')
    catalog.add_course(course10)

    course11 = Course('two', 'BINTEST', 'two')
    course11.add_attribute('bin.3')
    course11.add_attribute('bin.4')
    course11.add_attribute('bin.5')

    course11.add_attribute('bin.8')
    course11.add_attribute('concentration.AI')
    catalog.add_course(course11)

    planner.course_search.update_items(catalog.get_all_course_names())
    planner.course_search.generate_index()

    testtemplate1 = Template('bin1', Course("ANY", "BINTEST", 'ANY'), courses_required=1)
    testtemplate1.template_course.add_attribute('bin.1')
    testtemplate2 = Template('bin2', Course("ANY", "BINTEST", 'ANY'), courses_required=2)
    testtemplate2.template_course.add_attribute('bin.2')
    testtemplate3 = Template('bin3', Course("ANY", "BINTEST", 'ANY'), courses_required=2)
    testtemplate3.template_course.add_attribute('bin.3')
    testtemplate4 = Template('bin4', Course("ANY", "BINTEST", 'ANY'), courses_required=2)
    testtemplate4.template_course.add_attribute('bin.4')
    testtemplate5 = Template('bin5', Course("ANY", "BINTEST", 'ANY'), courses_required=3)
    testtemplate5.template_course.add_attribute('bin.5')

    testtemplate6 = Template('bin6', Course("ANY", "BINTEST", 'ANY'), courses_required=1)
    testtemplate6.template_course.add_attribute('bin.6')
    testtemplate7 = Template('bin7', Course("ANY", "BINTEST", 'ANY'), courses_required=1)
    testtemplate7.template_course.add_attribute('bin.7')
    testtemplate8 = Template('bin8', Course("ANY", "BINTEST", 'ANY'), courses_required=1)
    testtemplate8.template_course.add_attribute('bin.8')
    testtemplate9 = Template('bin9', Course("ANY", "BINTEST", 'ANY'), courses_required=1)
    testtemplate9.template_course.add_attribute('bin.9')
    testtemplate10 = Template('bin10', Course("ANY", "BINTEST", 'ANY'), courses_required=2)
    testtemplate10.template_course.add_attribute('concentration.*')
    
    testtemplate1.replacement = False
    testtemplate2.replacement = True
    testtemplate3.replacement = True
    testtemplate4.replacement = True
    testtemplate5.replacement = True
    
    testtemplate6.replacement = False
    testtemplate7.replacement = False
    testtemplate8.replacement = False
    testtemplate9.replacement = False
    testtemplate10.replacement = False

    templates = list()
    templates.append(testtemplate1)
    templates.append(testtemplate2)
    templates.append(testtemplate3)
    templates.append(testtemplate4)
    templates.append(testtemplate5)

    templates.append(testtemplate6)
    templates.append(testtemplate7)
    templates.append(testtemplate8)
    templates.append(testtemplate9)
    templates.append(testtemplate10)

    # templates.reverse()

    for t in templates:
        degree.add_template(t)

    run_cmd(planner, user, 'degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4, add, 5, bin 5, add, 6, bin 6')
    run_cmd(planner, user, 'add, 7, bin 7, add, 7, bin 8, add, 7, bin 9, add, 7, bin one, add, 7, bin two, add, 8, bin two')
    run_cmd(planner, user, 'print, fulfillment')

def run_cmd(planner, user, string):
    planner.input_handler(user, string)


start = timeit.default_timer()

print(f'beginning test {datetime.now()}')
# logging.getLogger().setLevel(logging.DEBUG)
test_graph()
test_other()
input('press enter to continue')
test_fulfillment()
input('press enter to continue')
test_fulfillment2()
input('press enter to continue')
test_fulfillment3()
input('press enter to continue')
test_fulfillment4()
input('press enter to continue')
test_fulfillment5()
input('press enter to continue')
test_fulfillment6()

stop = timeit.default_timer()
print('\ntime: ', stop - start)
