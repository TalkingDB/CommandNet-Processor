__author__="Karan S. Sisodia"
__email__="karansinghsisodia@gmail.com"
__date__ ="$Sep 12, 2014 12:13:52 PM$"

import networkx as nx
from networkx.readwrite import json_graph

class GraphLib():
    
    def __init__(self):
        self.G = nx.DiGraph()
        
    def addNode(self, name, properties):
        """
        Function to add new node in network
        """
        
        if name:
            self.G.add_node(name)
            if properties:
                self.addNodeProperty(name, properties)
        else:
            raise ValueError("Name must have some value!")
    
    def addNodeProperty(self, node, properties):
        """
        Function to add property/attributes in a node, it supportes multiple
        properties at a time
        """
        if node and properties:
                for key, value in properties.items():
                    self.G.node[node][key] = value
        else:
            raise ValueError("Node and Properties must have some value!")
                
    def addRelation(self, nodes, properties):
        """
        Function to add relation between two nodes
        """
        
        if nodes:
            if isinstance(nodes, tuple):
                self.G.add_edge(*nodes)
                if properties:
                    self.addRelationProperty(nodes, properties)
            else:
                raise ValueError("Nodes must be a pair of two nodes in a tuple! \n eg. (node1, node2)")
        else:
            raise ValueError("Name must have some value!")
    
    def addRelationProperty(self, nodes, properties):
        """
        Function to add property/attributes in a relation/edge
        """
        if nodes and properties:
            if properties:
                out = []
                for key, value in properties.items():
                    self.G.edge[nodes[0]][nodes[1]][key] = value
        else:
            raise ValueError("Nodes and Properties must have some value!")
        

    def updateNodeProperty(self):
        """
        Function to update a property of a node
        """
        pass
    
    def updateRelationProperty(self):
        """
        Function to update property of a relation
        """
        pass
    
    def searchNode(self):
        """
        Function to find a node in a network
        """
        pass
    
    def drawGraph(self):
        #draw graph
        pos = nx.spring_layout(self.G)
        nx.draw_networkx(self.G, pos, with_labels=True)

        node_labels = nx.get_node_attributes(self.G, 'entity')
#        nx.draw_networkx_labels(self.G, pos, labels=node_labels)

        edge_labels = nx.get_edge_attributes(self.G, 'param')
        nx.draw_networkx_edge_labels(self.G, pos, edge_labels=edge_labels)

#        plt.show()
        plt.savefig("/home/sb/Desktop/graph.png", dpi=500) 
        
    def jsonOutput(self):
        """
        Function to get graph data serilized json format
        """
        return json_graph.node_link_data(self.G)
        
    def gmlOutput(self):
        """
        Function to convert NetworkX graph in GML string
        """
        out = ''
        for i in nx.generate_gml(self.G):
            out = out + i
        
        return out
    
    def parseGML(self, lines):
        """
        Function to parse GML string data in NetworkX Object
        """
        return nx.parse_gml(lines,relabel=False)
    
    def getSubjectLeaves(self):
        for n, d in self.G.in_degree().items():
            if d == 0:
                subject_node = self.G.node[self.__findSubject(n)]['resolvedCommand']
        return subject_node.split(',')
    
    def __findSubject(self, n):
        """
        Recursive function to get main subject node
        """
        if self.G.edge[n]:
            for node, properties in self.G.edge[n].items():
                if properties['param'] == 'subject':
                    return self.__findSubject(node)
        else:
            return n
        
    def getAllLeafNodes(self):
        """
        Function to get all leaf nodes from the graph
        """
        leaves=[self.G.node[n]['resolvedCommand'] for n,d in self.G.out_degree().items() if d==0]
        return leaves
    
    def getInstructions(self):
        """
        Function to get first node of the graph, and returns its connected nodes
        """
        out = {}
        for n, d in self.G.in_degree().items():
            if d == 0:
                out = self.__getNeighbors(n)
        return out
    
    def getLeafNodesByCommand(self, node_id, command=None):
        """
        Function to get leaf nodes of a instruction or connected from given node
        """
        leaves = []
        nodes = list(set(self.__findLeaf(node_id)))
        for i in nodes:
            if (self.G.node[i]['entity']).split(':')[0] == command:
                leaves.append({
                    i: self.G.node[i]
                })
        return leaves
                
    def __findLeaf(self, n, li=[]):
        """
        Recursive function to get leaf nodes
        """
        for node in self.G.neighbors(n):
            if not self.G.out_degree(node) and node not in li:
                li += [node]
            else:
                 li += self.__findLeaf(node, li)
        return li
    
    def getChildNodes(self, node_id, edge_relation=None, field=None):
        """
        Function to get child nodes and its property. It can return child node by
        relation or return all nodes.
        
        ## params:
        _node_id:_ Integer
        _edge_relation:_ String `param:subject`
        _field:_ String
        """
        if not edge_relation:
            neighbors = self.__getNeighbors(node_id)
            return neighbors
        else:
            key, value = edge_relation.split(':')
            relation = (key, value)
            return (self.__getNeighbors(node_id, relation)).values()[0]
            
    
    def __getNeighbors(self, node_id, relation=None):
        """
        Function to get neighbors of a node
        """
        out = {}
        for i in self.G.neighbors(node_id):
            if relation:
                if self.G[node_id][i][relation[0]] == relation[1]:
                    out[i] = self.G.node[i]
            else:
                out[i] = self.G.node[i]
        return out

    def searchNode(self, node_id, property):
        """
        Function to get leaf node by its property
        """
        output = []
        nodes = self.__findLeaf(node_id)
        for node in list(set(nodes)):
            if ((self.G.node[node][property[0]]).find(property[1])) > -1:
                output.append(self.G.node[node])

        return output