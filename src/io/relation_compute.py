import logging
import asyncio
from ..math.graph import Graph

def initialize_relations(text_title, text_body, graph:Graph=None) -> Graph:
    '''
    takes in article title and body text

    Returns:
        graph: a relational graph of each keyword with each other
    '''
    if graph is None:
        graph = Graph()

    strengthen(graph, 'n1', 'n2', 5.3)
    strengthen(graph, 'n1', 'n2', 5.3)
    strengthen(graph, 'n3', 'n2', 1)
    strengthen(graph, 'n5', 'n6', 1)
    print(f'graph: {graph}')
    scale(graph, 2, 3)
    print(f'graph: {graph}')


def strengthen(graph:Graph, element1, element2, num:float):
    if element1 not in graph:
        graph.add_node(element1, True, 0)
    if element2 not in graph:
        graph.add_node(element2, True, 0)

    curr_num = graph.edge_data(element1, element2)
    curr_num += num

    graph.update_connection(element1, element2, curr_num)
    graph.update_connection(element2, element1, curr_num)


def scale(graph:Graph, multiplicative, additive):
    for n1, n2, num in graph.edge_items():
        num *= multiplicative
        num += additive
        graph.update_connection(n1, n2, num)
