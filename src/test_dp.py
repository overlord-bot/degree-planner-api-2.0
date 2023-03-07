import timeit
from dp.search_tree import *

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

    bfs = graph.build_bfs({n5})
    print(f'{bfs}')

start = timeit.default_timer()

test_graph()

stop = timeit.default_timer()
print('\ntime: ', stop - start)
