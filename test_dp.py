import timeit
import asyncio
import sys
from datetime import datetime
from src.math.graph import *
from src.dp.command_handler import Planner
from src.dp.course import Course
from src.user.user import User
from src.dp.template import Template
from src.dp.degree import *

class Test_Graph_Edge_Data_Gen(Edge_Generator):

    def __init__(self) -> None:
        pass

    def edge_data(self, node1, node2):
        return 'CON' if (int(node1) < int(node2) or (int(node1) + int(node2)) % 2 == 0) else None
    

def test_graph():
    n1 = '1'
    n2 = '2'
    n3 = '3'
    n4 = '4'
    n5 = '5'

    n6 = '6'
    n7 = '7'
    n8 = '8'
    graph_empty = Graph()
    print('empty graph: ' + str(graph_empty))
    graph_empty.add_node('t1')
    print('empty graph with one node added: ' + str(graph_empty))
    graph = Graph([n1, n2, n3, n4, n5], Test_Graph_Edge_Data_Gen())
    graph.update_all_connections()

    graph.remove_connection(n1, n2)
    print('removed connection n1 to n2: ' + str(graph_empty))
    graph.update_connection(n1, n2)

    print(f'added connections (connection if n1 < n2, or if n1 + n2 is even): {graph}')

    print(f'outbound connections from n5: {graph.outbound_connections(n5)}')
    print(f'inbound connectinos for n5: {graph.inbound_connections(n5)}')

    bfs = graph.bfs({n5})
    print(f'{bfs}')

    print(f'adding nodes via add')
    graph.add_node(n6)
    graph.add_node(n7)
    graph.add_node(n8)
    graph.add_node(n8)

    print(f'added connections 6, 7, 8: {graph}')
    print(f'removing nodes via remove')

    graph.remove_node(n2)
    print(f'removed connection 2: {graph}')
    graph.remove_node(n4)
    graph.remove_node(n8)
    graph.remove_node(n8)
    print(f'removed connection 4, 8, 8 (again): {graph}')

    graph.add_node(n2)
    graph.add_node(n4)
    graph.remove_node(n6)
    graph.remove_node(n7)
    print(f'reverted everything back: {graph}')
    bfs = graph.bfs({n5})
    print(f'{bfs}')

    print(f'testing graph iterator: getting all nodes: {[str(e) for e in graph]}')
    print(f'testing graph iterator: getting all edge values: {[str(e) for e in graph.edge_values()]}')
    print(f'testing graph iterator: getting all edge endpoints id: {[str(e) for e in graph._edge_endpoints_id()]}')
    print(f'testing graph iterator: getting all edge endpoints: {[str(e) for e in graph.edge_endpoints()]}')
    print(f'testing graph iterator: getting all items endpoints: {[str(e) for e in graph.edge_items()]}')

    print(f'sorting:')
    print(str(dictionary_sort({'machine learning':1, 'robotics':2, 'animation':3, 'computer vision':4, 'banana':10, 'oranges':9, 'apple':8, 'tesla':7,'citrus':2.5}, True)))
    print(str(bucket_sort({'machine learning':1, 'robotics':2, 'animation':3, 'computer vision':4, 'banana':10, 'oranges':9, 'apple':8, 'tesla':7,'citrus':2.5})))


def test_other():
    planner = Planner()
    
    catalog = planner.catalog
    degree = Degree("computer science", catalog)
    catalog.add_degree(degree)

    course0 = Course('0', 'BINTEST', 0)
    course0.add_attribute('bin.1')
    course0.add_attribute('bin.5')
    course0.add_attribute('credits.3')
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

    testtemplate1 = Template('bin1', 'bin.1')
    testtemplate2 = Template('bin2', 'bin.2')
    testtemplate3 = Template('bin3', 'bin.3')
    testtemplate4 = Template('bin4', 'bin.4')
    testtemplate5 = Template('bin5', 'bin.5')
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

    catalog.reindex(False)

    print(f'course0 credits: {course0.get_credits()}')

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

    testtemplate1.add_specification('bin.*')
    # get_course_match(testtemplate1, {course1, course2, course3, course4, course5})

    #print('\ntesting fulfillment recommendations: \n')
    #degree.recommend({course0, course1, course2, course3, course4, course5})



def test_fulfillment():
    planner = Planner()
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

    catalog.reindex(False)

    testtemplate1 = Template('bin1', 'bin.1')
    testtemplate2 = Template('bin2', 'bin.2')
    testtemplate3 = Template('bin3', 'bin.3')
    testtemplate4 = Template('bin4', 'bin.4')
    testtemplate5 = Template('bin5', 'bin.5')
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
    planner = Planner(12)
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

    testtemplate1 = Template('bin1', 'bin.1')
    testtemplate2 = Template('bin2', 'bin.2')
    testtemplate3 = Template('bin3', 'bin.3')
    testtemplate4 = Template('bin4', 'bin.4')
    testtemplate5 = Template('bin5', 'bin.5')
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

    catalog.reindex(False)

    run_cmd(planner, user, 'degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4, add, 5, bin 5, add, 6, bin 6, print, fulfillment')

def test_fulfillment3():
    planner = Planner(20)
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

    testtemplate1 = Template('bin1', 'bin.1') # 6
    testtemplate2 = Template('bin2', 'bin.2', courses_required=3) # 2, 3, 4
    testtemplate3 = Template('bin3', 'bin.3') # 3, 4
    testtemplate4 = Template('bin4', 'bin.4') # 5
    testtemplate5 = Template('bin5', 'bin.5', courses_required=2) # 1
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

    catalog.reindex(False)

    run_cmd(planner, user, 'degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4, add, 5, bin 5, add, 6, bin 6')
    run_cmd(planner, user, 'print, fulfillment')


def test_fulfillment4():
    planner = Planner(20)
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

    testtemplate1 = Template('bin1', 'bin.1', courses_required=1)
    testtemplate2 = Template('bin2', 'bin.2')
    testtemplate3 = Template('bin3', 'bin.3')
    testtemplate1.replacement = False
    testtemplate2.replacement = True
    testtemplate3.replacement = True

    degree.add_template(testtemplate1)
    degree.add_template(testtemplate2)
    degree.add_template(testtemplate3)

    catalog.reindex(False)

    run_cmd(planner, user, 'degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4, add, 5, bin 5, add, 6, bin 6')
    run_cmd(planner, user, 'print, fulfillment')


def test_fulfillment5():
    planner = Planner(10)
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

    testtemplate1 = Template('bin1', 'bin.1')
    testtemplate2 = Template('bin2', 'bin.2', courses_required=2)
    testtemplate3 = Template('bin3', 'bin.3', courses_required=2)
    testtemplate4 = Template('bin4', 'bin.4', courses_required=2)
    testtemplate5 = Template('bin5', 'bin.5', courses_required=3)
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

    catalog.reindex(False)

    run_cmd(planner, user, 'degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4, add, 5, bin 5, add, 6, bin 6')
    run_cmd(planner, user, 'print, fulfillment')

def test_fulfillment6():
    planner = Planner(10)
    user = User(1)
    
    catalog = planner.catalog
    degree = Degree("computer science", catalog)
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

    testtemplate1 = Template('bin1', 'bin.1')
    testtemplate2 = Template('bin2', 'bin.2', courses_required=2)
    testtemplate3 = Template('bin3', 'bin.3', courses_required=2)
    testtemplate4 = Template('bin4', 'bin.4', courses_required=2)
    testtemplate5 = Template('bin5', 'bin.5', courses_required=3)

    testtemplate6 = Template('bin6', 'bin.6')
    testtemplate7 = Template('bin7', 'bin.7', courses_required=1)
    testtemplate8 = Template('bin8', 'bin.8', courses_required=1)
    testtemplate9 = Template('bin9', 'bin.9', courses_required=1)
    testtemplate10 = Template('bin10', 'concentration.*', courses_required=2)
    
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

    catalog.reindex(False)

    # templates.reverse()

    for t in templates:
        degree.add_template(t)

    run_cmd(planner, user, 'degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4, add, 5, bin 5, add, 6, bin 6')
    run_cmd(planner, user, 'add, 7, bin 7, add, 7, bin 8, add, 7, bin 9, add, 7, bin one, add, 7, bin two, add, 8, bin two')
    run_cmd(planner, user, 'print, fulfillment')

    
    #print('\ntesting fulfillment recommendations: \n')
    #degree.recommend(catalog.get_all_courses())

def test_recommender():

    planner = Planner(10)
    user1 = User(1)
    user2 = User(2)
    user3 = User(3)

    run_cmd(planner, user1, 'import, schedule, user1, degree, computer science, add, 1, mac learn 4100, add, 1, deep learn 4, add, 1, 4270 csci vision, add, 1, reinforcement, add, 1, data sci 4350 csci, add, 2, math 2400')
    run_cmd(planner, user1, 'print, fulfillment, recommend')

    print('\n\n\n\n\n\n')
    print('BEGINNING TEST WITH USER 2 WITH IDENTICAL COURSES (but different schedule) FOR TESTING OF CACHING SYSTEM')
    run_cmd(planner, user2, 'schedule, user2, degree, computer science, add, 5, mac learn 4100, add, 6, deep learn 4, add, 7, 4270 csci vision, add, 7, reinforcement, add, 7, data sci 4350 csci, add, 7, math 2400')
    run_cmd(planner, user2, 'print, fulfillment, recommend')

    print('\n\n\n\n\n\n')
    print('BEGINNING TEST WITH USER 3 WITH DIFFERENT SCHEDULE, REIMPORTING AND CUSTOM TAGS')
    run_cmd(planner, user3, 'import, schedule, user3, degree, computer science, add, 1, csci 4380, add, 1, math 4120 geometry, add, 1, math 4040, add, 1, csci 4560, add, 1, csci 4440, add, 2, ecse 4750')
    run_cmd(planner, user3, 'add, 2, graph story, add, 2, 3d animation 4090, add, 2, 3d visual effect, add, 2, 3d modelling, add, 2, art history 1050')
    run_cmd(planner, user3, 'print, fulfillment, recommend, machine learning, music, motor control')
    print('\n')


def run_cmd(planner, user, string):
    planner.input_handler(user, string)


start = timeit.default_timer()

print(f'beginning test {datetime.now()}')

if len(sys.argv) > 1 and '-d' in sys.argv:
    logging.getLogger().setLevel(logging.DEBUG)
    print('DEBUG MODE ON, PRINTING ALL DEBUGGING INFORMATION!')
else:
    logging.getLogger().setLevel(logging.INFO)
test_graph()
input('press enter to continue')
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
input('press enter to continue')
test_recommender()

stop = timeit.default_timer()
print('\ntime: ', stop - start)
