'''
BFS searching functions and classes
'''

import copy
import timeit
import queue

class BFS_data():

    def __init__(self, start_nodes:set=None):
        if start_nodes is None:
            start_nodes = set()

        self.paths = dict()
        self.bfs_queue = queue.SimpleQueue()

        for node in start_nodes:
            self.add_node(node, [node])

    def add_node(self, node, path:list):
        self.paths.update({node:path})
        self.bfs_queue.put(node)

    def remove_node(self, node):
        self.paths.pop(node, None)

    def get_path(self, node):
        return self.paths.get(node, None)
    
    def contains_node(self, node):
        return self.paths.get(node, None) is not None
    
    def next(self):
        return self.bfs_queue.get()
    
    def has_next(self):
        return not self.bfs_queue.empty()
    
    def __len__(self):
        return len(self.paths)
    
    def __repr__(self):
        rstr = f'\nbfs paths:\n'
        for node, path in self.paths.items():
            rstr += f"  {str(node).ljust(5)}: {' -> '.join(path)}\n"
        return rstr


class Graph():

    def __init__(self, nodes:list):
        self.grid = [[False for j in range(len(nodes))] for i in range(len(nodes))]
        self.nodes_id = dict()
        self.nodes_name = dict()
        for i in range(0, len(nodes)):
            self.nodes_id.update({nodes[i]:i})
            self.nodes_name.update({i:nodes[i]})


    def add_connection(self, node_origin, node_to):
        '''
        add a connection from node_origin to node_to
        '''
        if node_origin == node_to:
            return
        self.grid[self.node_id(node_origin)][self.node_id(node_to)] = True


    def remove_connection(self, node_origin, node_to):
        '''
        remove a connection from node_origin to node_to
        '''
        if node_origin == node_to:
            return
        self.grid[self.node_id(node_origin)][self.node_id(node_to)] = False


    def outbound_connections(self, node) -> set:
        '''
        returns set of nodes this node connects to
        '''
        id = self.node_id(node)
        connected_nodes = set()
        for i in range(0, len(self.grid)):
            if self.grid[id][i]:
                connected_nodes.add(self.node_name(i))
        return connected_nodes


    def inbound_connections(self, node) -> set:
        '''
        returns set of nodes that connect to this node
        '''
        id = self.node_id(node)
        connected_nodes = set()
        for i in range(0, len(self.grid)):
            if self.grid[i][id]:
                connected_nodes.add(self.node_name(i))
        return connected_nodes


    def node_id(self, node) -> int:
        '''
        node id of node object
        '''
        return self.nodes_id.get(node)


    def node_name(self, id):
        '''
        node object from node id
        '''
        return self.nodes_name.get(id)


    def bfs(self, start_nodes:set) -> BFS_data:
        '''
        find BFS paths from links
        '''
        bfs = BFS_data(start_nodes)
        while bfs.has_next():
            node_current = bfs.next()
            for node_next in self.outbound_connections(node_current):
                if bfs.contains_node(node_next):
                    continue
                trace = copy.deepcopy(bfs.get_path(node_current))
                trace.append(node_next)
                bfs.add_node(node_next, trace)

        return bfs


    def __repr__(self):
        WIDTH = 8
        rstr = f"\n{'links'.ljust(WIDTH)}{''.join([str(self.node_name(i)).ljust(WIDTH) for i in range(0, len(self))])}\n"
        for i in range(0, len(self.grid)):
            node_name = str(self.node_name(i)).ljust(WIDTH)
            rstr += f"{node_name}{''.join(['False'.ljust(WIDTH) if e == False else 'True'.ljust(WIDTH) for e in self.grid[i]])}\n"
        return rstr
    

    def __eq__(self, other):
        return self.grid == other.grid and self.nodes_id == other.nodes_id
    
    def __len__(self):
        return len(self.grid)
