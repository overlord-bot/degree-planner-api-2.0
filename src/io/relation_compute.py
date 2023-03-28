import logging
import asyncio
from ..math.graph import Graph

def calculate_relations(text_title, text_body) -> Graph:
    '''
    takes in article title and body text

    Returns:
        graph: a relational graph of each keyword with each other
    '''

    graph = Graph()
