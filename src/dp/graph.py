'''
BFS searching functions and classes
'''

import copy
import timeit
import queue

from .fulfillment_status import Fulfillment_Status

class Backwards_Overlap():

    def __init__(self, all_fulfillment:dict, max_fulfillment:dict):
        self.max_fulfillment = max_fulfillment
        self.all_fulfillment = all_fulfillment

    def edge_data(self, node1:Fulfillment_Status, node2:Fulfillment_Status):
        return self.all_fulfillment.get(node1).get_fulfillment_set().intersection(self.max_fulfillment.get(self.all_fulfillment.get(node2).get_template()).get_fulfillment_set())
    
class Forwards_Overlap():

    def __init__(self, all_fulfillment:dict, max_fulfillment:dict):
        self.max_fulfillment = max_fulfillment
        self.all_fulfillment = all_fulfillment

    def edge_data(self, node1:Fulfillment_Status, node2:Fulfillment_Status):
        return self.all_fulfillment.get(node1).get_fulfillment_set().intersection(self.max_fulfillment.get(self.all_fulfillment.get(node2).get_template()).get_fulfillment_set())


class BFS_data():
    '''
    stores shortest paths that traces from any root to that node

    if node isn't found, that means it isn't connected to any roots
    '''

    def __init__(self, start_nodes:set):
        self.paths = dict()
        self.bfs_queue = queue.SimpleQueue()

        for node in start_nodes:
            self.add_path(node, [node])

    def add_path(self, node, path:list):
        self.paths.update({node:path})
        self.bfs_queue.put(node)

    def remove_path(self, node):
        self.paths.pop(node, None)

    def get_path(self, node):
        return self.paths.get(node, None)
    
    def contains_node(self, node):
        return self.paths.get(node, None) is not None
    
    def contains_child(self, node):
        if not self.contains_node(node):
            return False
        return len(self.paths.get(node)) > 1
    
    def next(self):
        return self.bfs_queue.get()
    
    def has_next(self):
        return not self.bfs_queue.empty()
    
    def __len__(self):
        return len(self.paths)
    
    def __repr__(self):
        rstr = f'\nbfs paths:\n'
        for node, path in self.paths.items():
            rstr += f"  {str(node).ljust(10)}: {' -> '.join([str(e) for e in path])}\n"
        return rstr


class Graph():
    '''
    adjacency graph that can store sets as edge data
    '''

    def __init__(self, nodes_set:set, edge_data_gen=None):
        nodes = list(nodes_set)
        self.grid = [[{} for j in range(len(nodes))] for i in range(len(nodes))]
        self.nodes_id = dict()
        self.nodes_name = dict()
        self.edge_data_gen = edge_data_gen
        self.roots = set()
        for i in range(0, len(nodes)):
            self.nodes_id.update({nodes[i]:i})
            self.nodes_name.update({i:nodes[i]})

    
    def compute_overlap(self, node1, node2):
        if self.edge_data_gen is None:
            return {'1'}
        return self.edge_data_gen.edge_data(node1, node2)


    def update_connection(self, node_origin, node_to, data_set:set=None):
        '''
        add a connection from node_origin to node_to
        '''
        if node_origin == node_to:
            return
        if data_set is None:
            data_set = self.compute_overlap(node_origin, node_to)
        self.grid[self.node_id(node_origin)][self.node_id(node_to)] = data_set


    def try_add_connection(self, node_origin, node_to):
        if node_origin == node_to:
            return
        data_set = self.compute_overlap(node_origin, node_to)
        if len(data_set):
            self.grid[self.node_id(node_origin)][self.node_id(node_to)] = data_set
            return True
        return False


    def remove_connection(self, node_origin, node_to):
        '''
        remove a connection from node_origin to node_to
        '''
        if node_origin == node_to:
            return
        self.grid[self.node_id(node_origin)][self.node_id(node_to)] = {}


    def outbound_connections(self, node) -> set:
        '''
        returns set of nodes this node connects to
        '''
        id = self.node_id(node)
        connected_nodes = set()
        for i in range(0, len(self.grid)):
            if len(self.grid[id][i]):
                connected_nodes.add(self.node_object(i))
        return connected_nodes


    def inbound_connections(self, node) -> set:
        '''
        returns set of nodes that connect to this node
        '''
        id = self.node_id(node)
        connected_nodes = set()
        for i in range(0, len(self.grid)):
            if len(self.grid[i][id]):
                connected_nodes.add(self.node_object(i))
        return connected_nodes
    
    
    def edge_data(self, node1, node2, first_element_only:bool=False):
        elements = self.grid[self.node_id(node1)][self.node_id(node2)]
        if first_element_only and len(elements):
            for e in elements:
                return e
        return elements


    def node_id(self, node) -> int:
        '''
        node id of node object
        '''
        return self.nodes_id.get(node)


    def node_object(self, id):
        '''
        node object from node id
        '''
        return self.nodes_name.get(id)


    def bfs(self, start_nodes:set=None) -> BFS_data:
        '''
        find BFS paths from links
        '''
        if start_nodes is None:
            start_nodes = self.roots
            
        bfs = BFS_data(start_nodes)
        while bfs.has_next():
            node_current = bfs.next()
            for node_next in self.outbound_connections(node_current):
                if bfs.contains_node(node_next):
                    continue
                trace = copy.deepcopy(bfs.get_path(node_current))
                trace.append(node_next)
                bfs.add_path(node_next, trace)

        return bfs


    def __repr__(self):
        WIDTH = 16
        rstr = f"\n{'links'.ljust(WIDTH)}{''.join([str(self.node_object(i)).ljust(WIDTH) for i in range(0, len(self))])}\n"
        for i in range(0, len(self.grid)):
            rstr += str(self.node_object(i)).ljust(WIDTH)
            for j in range(0, len(self.grid)):
                data_set = self.grid[i][j]
                if not len(data_set):
                    rstr += '-'.ljust(WIDTH)
                    continue
                rstr += f"{', '.join([str(e) for e in data_set])}".ljust(WIDTH)
            rstr += '\n'
        return rstr
    

    def __eq__(self, other):
        return self.grid == other.grid and self.nodes_id == other.nodes_id
   

    def __len__(self):
        return len(self.grid)
