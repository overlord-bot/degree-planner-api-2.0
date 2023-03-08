import timeit
import asyncio
from datetime import datetime
from src.dp.graph import *
from src.dp.degree_planner import *

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
    run_cmd(planner, user, 'import, degree, computer science, add, 1, bin 1, add, 2, bin 2, add, 3, bin 3, add, 4, bin 4')
    run_cmd(planner, user, 'print, fulfillment')

def run_cmd(planner, user, string):
    asyncio.run(planner.input_handler(user, string))


start = timeit.default_timer()

print(f'beginning test {datetime.now()}')
test_graph()
input('press enter to continue')
test_fulfillment()

stop = timeit.default_timer()
print('\ntime: ', stop - start)
