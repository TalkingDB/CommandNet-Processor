"""
Created on 18-Jul-2014
@author: tushar
@contact: tushar@solutionbeyond.net - +91-998-831-3001
@version: 0.1
@summary: CommandNet Boostrapper parses CommentNet dataset to output CommonSense graph of sentences.  
The graph tells which token (from input) is a command, and which tokens from input are parameters 
to command 

Updated on 08-Oct-2014
@author: Karan S. Sisodia <karansinghsisodia@gmail.com>
"""

import socket
import json
import networkx as nx
from networkx.readwrite import json_graph
from pymongo import MongoClient
import time

from app import *
from GraphLib.index import *
from NLProcessor.nl_processor import *
from commandnet import *
from _line_profiler import label

# Configuration File
Config = Config()

# Connect to MongoDB to query Entity_to_Command
db = MongoClient(str(Config.get('MongoDB')['host']), int(Config.get('MongoDB')['port']))
Entity_to_Command_collection = db[str(Config.get('MongoDB')['database'])].Entity_to_Command

# Initialize NLProcessor (NER)
nlp = NLProcessor()
CommandNet = CommandNet()


class CommandNetProcessor():
    G = nx.DiGraph()
    vertices = []

    def __init__(self):
        pass

    def __queryNER(self, literature):
        """
        Function to get NER Graph of the given user instruction
        """
        start_time = int(round(time.time() * 1000))
        
        # TODO: remove below code when CNP starts handling 's
        literature = literature.replace("'", "")
        
        gl, last_node_id, instructions = nlp.process_user_instructions(literature)
        
        # Prepare combined graph
        node_id = last_node_id
        for instruction in instructions:
            parent_node_id = instruction['parent_id']
            
            nered_output = nlp.process_string(instruction['instruction'])
            
            last = ()
            for token in nered_output['tokens']:
                current = (token['start'], token['end'])
                if last != current:
                    node_id += 1
                    gl.addNode(node_id, {
                        'type': 'token', 
                        'entity': str(token['id']).split(","),
                        'label': token['surface_text'],
                        'command':'',
                        'start': token['start'],
                        'end': token['end']
                    })
                    gl.addRelation((parent_node_id, node_id), {})
                else:
                    gl.G.node[node_id]['entity'].append(token['id'])
                last = current
                
        end_time = int(round(time.time() * 1000))
        
        print "\n*NER Time Profile:*",
        "Start Time: ", start_time, "ms",
        "End Time: ", end_time, "ms",
        "Diff: ", end_time - start_time, "ms", "\n"
        
        # Uncomment below line to check NER Output
        #print json.dumps(gl.jsonOutput())
        return gl.G
    
    """[Psecode]* Literature to CommandNet Graph Builder():"""
    def LiteratureToCommandNetGraphBuilder(self,literature):
        
        start_time = int(round(time.time() * 1000))
        
        """[Psecode] Pass literature to NER, get graph in return"""
        global G
        G = self.__queryNER(literature)
        #NER returns entities separated by comma, we must rather store them as a python List object
        #converting comma separated entities, into a list :
        for n,d in G.nodes_iter(data=True):
            entities = d['entity']
            G.node[n]['entity'] = entities
            
            """[Psecode #1053] Find 'Commands' of each 'Entity'
            by looking up 'Entity_to_Command' collection in mongodo
            """
            Commands = []
            for entity in entities:
                RecordSet = Entity_to_Command_collection.find({'entity_url':entity})
                for Record in RecordSet:
                    Commands.append(Record['command'])
            Unique_Commands = list(set(Commands))
        
            G.node[n]['probable_commands'] = Unique_Commands
            #print "n = " + str(n) + ", entities = " + str(entities) + ", probable_commands = " + str(Unique_Commands)
        # print G.nodes(data=True)
        

        NewHypergraphsToBeInserted = []
                
        """[Psecode] Loop through each NewInstruction.""" 
        newInstructions = list((n for n,d in G.nodes_iter(data=True) if 'CommandNet>NewInstruction' in d['command']))     
        #iterate through each NewInstruction
        for instruction in newInstructions:
            
            # Loop from Priority number 1 to 3 to execute only the highest priority commandnet commands first
            for Priority in xrange(1,4):
                
                while True: #this loop is BROKEN a few lines down if no change in graph is found
                    NewHypergraphsToBeInserted = []
    
                    """[Psecode] note down the state of graph, it is to be compared later to see if a change is made in graph or not"""
                    GraphBeforeCommandNetProcessing = G.nodes(data=True)
                    
                    """[Psecode] for each NewInstruction, Loop backwards through hypergraphs or vertices (if vertex exists outside the hypergraph)"""
                    vertices = G.successors(instruction)
                    vertices.sort(cmp=None, key=None, reverse=True)
                    #vertices.reverse()
                    output = None
                    for vertex in vertices:
                        
                        """[Psecode]--- Pick the entities in each vertex which contain CommandNet functions"""
                        for Command in G.node[vertex]['probable_commands'] :
                            if Command[0:10] =='CommandNet' :
                                Command = Command[11:]
                                """[Psecode] Parse Parameter expression of each CommandNet function saved inside vertex."""
                                """[Psecode] Pass each CommandNet function and the vertex from where it was found to function"""
                                """[Psecode] 'Parses the CommandNet parameter expression'"""
                                # print str(G.node[vertex])
                                output =  self.ParseCommandNetParameterExpression(Command, vertex,Priority)
                                if output is not None:
                                    NewHypergraphsToBeInserted.append(output)
                                    #because if we dont break, same vertices may get chained under multiple hypergraphs. We may want to REMOVE this line of code later when we want 2 commands to compete for parameters. For now the command which gets checked first, and matches, makes the hypergraph
                                    break 
    
                        if output is not None:
                            break #because if we dont break, same vertices may get chained under multiple hypergraphs. We may want to REMOVE this line of code later when we want 2 commands to compete for parameters. For now the command which gets checked first, and matches, makes the hypergraph 
                            
                    #hypergraphs or later words are appearing first, they must be added last, hence reversing the list
                    NewHypergraphsToBeInserted.reverse()
                    
                    for Hypergraph in NewHypergraphsToBeInserted:
                        Command = Hypergraph[0]
                        vertexLabel = Hypergraph[1]
                        probableCommandsOfPotentiallyNewCommandHypergraph = Hypergraph[2]
                        chainOfVerticesToBeEnguledIfCommandIsFound = Hypergraph[3]
                        lastNode = chainOfVerticesToBeEnguledIfCommandIsFound[len(chainOfVerticesToBeEnguledIfCommandIsFound)-1][0]+0.01 #set such a nodeID which is slightly greater than the nodeID of the last vertex being engulfed. This way the hypergraph will rank in serial order (when we sort list of nodes), otherwise it gets added to the last
                        
                        #TODO: change entity from entitiesOfPotentiallyNewCommandHypergraph to []
                        #TODO: set 'probable_commands' to entitiesOfPotentiallyNewCommandHypergraph
                        #TODO: rename entitiesOfPotentiallyNewCommandHypergraph to probableCommandsOfPotentiallyNewCommandHypergraph
                        G.add_node(lastNode, type='hypergraph', command=['CommandNet>' + Command], label=vertexLabel, entity=[], probable_commands=probableCommandsOfPotentiallyNewCommandHypergraph)
        
                        """[Psecode] engulf the range of vertices in a hypergraph. mark the hypergraph as CommandNet function whose parameters matched"""
                        for VertexToBeEnguledInChain,ParamName in chainOfVerticesToBeEnguledIfCommandIsFound:
                            predecessors = G.predecessors(VertexToBeEnguledInChain)
                            predecessor = predecessors[0]
                            G.remove_edge(predecessor, VertexToBeEnguledInChain)
                            """[Psecode] inside each vertex in hypergraph, specify which ones among them is subject param, object param, or other parameter"""
                            G.add_edge(lastNode, VertexToBeEnguledInChain, param=ParamName)
                            # link the newly created hypergraph with original parent of the engulfed vertex
                            G.add_edge(predecessor, lastNode)
                    
                    """[Psecode]-- Loop through all hypergraphs. Treat those hypergraphs as '$noun_phrase' which were created because of"""
                    """[Psecode]   a command of Level3 or greater, AND one of the (deep) child vertex is a noun"""
                    """[Psecode]-- run the above hypergraph-Vertex-loop again if there was a change in graph before and after the hypergraph-vertex-loop above"""
    
                    
                    # print 'G.nodes = ' + str(G.nodes(data=True))
                    # print 'G.edges = ' + str(G.edges(data=True))
                    # print 'GraphBeforeCommandNetProcessing = ' + str(GraphBeforeCommandNetProcessing)
                    if G.nodes(data=True) == GraphBeforeCommandNetProcessing:
                        break
                    """[Psecode]-- (later) after all the commands are finished firing, for each vertex see if it is claimed by multiple hypergraphs which are overlapping but non-concentric. Let the 'strongest hypergraph' claim the vertex. This is similar to finding longest chain in NER"""
                    """[Psecode]- Return the graph data object"""
                
#         pos = nx.shell_layout(G)
#         node_labels = nx.get_node_attributes(G, 'label')
#         nx.draw_networkx(G)
#         nx.draw_networkx_labels(G, pos, labels=node_labels)
        #plt.show()
        end_time = int(round(time.time() * 1000))
        
#         print "*CP Time Profile:*"
#         print "Start Time: ", start_time, "ms"
#         print "End Time: ", end_time, "ms"
#         print "Diff: ", end_time - start_time, "ms"
#         print "Graph = ", G.nodes(data=True)
        
        
        for n,d in G.nodes_iter(data=True):
            entities = d['entity']
            
            Commands = []
            for entity in entities:
                RecordSet = Entity_to_Command_collection.find({'entity_url':entity})
                for Record in RecordSet:
                    Commands.append(Record['command'])
            Unique_Commands = list(set(Commands))
        
            print "n = " + str(n) + ", entity = " + str(entities) + ", probable_commands = " + str(Unique_Commands)

        
        return G
    
    def ParseCommandNetParameterExpression(self, Command, VertexID, Priority):
        """
        Function to Parse the CommandNet parameter expression
        """
        
        # For debugging purpose 
        print '--------------------COMMAND------------------------'
        print 'Command = ' + Command
        print 'Vertex = ' + str(G.node[VertexID])
        
        """[Psecode] call the CommandNet function requested (A)"""
        ParameterExpressions = eval('CommandNet.' + Command + '(mode=\'parameter_expression\')')
        
        """[Psecode] evaluate priority number. Process command only if it belongs to current priority or HIGHER priority"""
        if Priority >= ParameterExpressions['priority']:
            
            """[Psecode] Check whether ParamExpression is of the type of RepeatingParameter, or SequenceParameter, accordingly send it for parsing"""
            if ParameterExpressions['type']=='SequenceExpression':
                return self.ParseSequentialParameterExpression(Command, VertexID, ParameterExpressions['sequence'])
                
            elif ParameterExpressions['type']=='RepeatingExpression':
                """[Psecode] - parse separator"""
                """[Psecode] - parse repeater"""
                return self.ParseRepeatingParameterExpression(Command, VertexID, ParameterExpressions['repeaters'],ParameterExpressions['separators'])
            

    def ParseSequentialParameterExpression(self,Command, VertexID, ParameterExpressions):
        for ParameterExpression in ParameterExpressions:
            """[Psecode] prepare a sequence of parameters which must be matched with range of graph vertices"""
            """[Psecode] calculate the range of graph vertices which we must try to match with sequence of parameters"""
            #find origin of search by locating '$token'
#             print '-----------PARAMETER EXPRESSION----------------'
#             print ParameterExpression
            paramCount = len(ParameterExpression)
            counter = 0
            origin = -1
            chainOfVerticesToBeEnguledIfCommandIsFound = []
            # TODO: rename entitiesOfPotentialNewCommandHypergraph to probableCommandsOfPotentiallyNewCommandHypergraph
            probableCommandsOfPotentiallyNewCommandHypergraph = []
            while (counter<paramCount):
                pos = ParameterExpression[counter].find('$token')
                if pos >-1:
                    origin = counter
                    chainOfVerticesToBeEnguledIfCommandIsFound.append([VertexID,ParameterExpression[counter][0:pos-1]])
                    break
                counter = counter + 1

            if origin>-1: #origin was found (if its not found, there must be some typing mistake in parameterExpression
                if origin == 0:
                    ParamIDsToCheckOnLeftOfOrigin = [-1,-1] #nothing on left is to be checked
                else:
                    ParamIDsToCheckOnLeftOfOrigin = [1, origin+1] #for xrange to work, ending ID must be 1 greater. so it should have been origin but we have purposely used origin+1
                
                if origin < paramCount-1:
                    ParamIDsToCheckOnRightOfOrigin = [origin+1, paramCount] #for xrange to work, ending ID must be 1 greater. so it should have been paramCount, but we have purposely used paramCount+1
                else:
                    ParamIDsToCheckOnRightOfOrigin = [-1, -1] #nothing on right is to be checked
                
#                 print ('ParamIDsToCheckOnLeftOfOrigin = ' + str(ParamIDsToCheckOnLeftOfOrigin))
#                 print ('ParamIDsToCheckOnRightOfOrigin = ' + str(ParamIDsToCheckOnRightOfOrigin))
            
                """[Psecode]-- match whether sequence of parameters exactly match with range of graph vertices."""
                sequenceMatched = True
                paramOffset=0
                siblings = G.successors(G.predecessors(VertexID)[0])
                siblings.sort(cmp=None, key=None, reverse=False) #after sorting, the hypergraphs which were added during CP will get placed in serial order, otherwise all hypergraphs used to get pushed to the end of graph which resulted in error while sequence matchin

                paramID = ParamIDsToCheckOnLeftOfOrigin[0]
                while paramID < ParamIDsToCheckOnLeftOfOrigin[1]:
#                 for paramID in xrange(ParamIDsToCheckOnLeftOfOrigin[0],ParamIDsToCheckOnLeftOfOrigin[1]):
                    paramOffset = paramOffset - 1
                    try:
                        GraphVertexToBeMatched = siblings[[i for i,x in enumerate(siblings) if x == VertexID][0]+paramOffset]
                        #vertexToMatch = G.node[GraphVertexToBeMatched-1]
                        vertexToMatch = G.node[GraphVertexToBeMatched]
                        parameterToMatch = ParameterExpression[paramID - 1]
                        paramID = paramID + 1
                        
                        pos = parameterToMatch.find(":")
                        if pos > -1 :
                            parameterCommandOrString = parameterToMatch[pos+1:]
                            chainOfVerticesToBeEnguledIfCommandIsFound.append([GraphVertexToBeMatched,parameterToMatch[0:pos]])
                        else:
                            parameterCommandOrString = parameterToMatch
                            chainOfVerticesToBeEnguledIfCommandIsFound.append([GraphVertexToBeMatched,""]) 
                        
                        #find out whether the hypergraph must be made a $noun_phrase or $verb_phrase if some of its child vertex is a $noun_phrase or $verb_phrase 
                        if parameterCommandOrString.find("Noun") > -1: probableCommandsOfPotentiallyNewCommandHypergraph.append("$Noun_phrase")

#                         print 'Match vertex = ' + str(vertexToMatch)
#                         print 'with parameter = ' + parameterEntityOrString
                        commandOrLabelMatched = False
                        labelMatched = vertexToMatch['label'] == parameterCommandOrString 
                        commandMatched = False
                        if (labelMatched == False):
                            commandMatched = parameterCommandOrString in vertexToMatch['probable_commands']
                            IgnoreTokenFound = "CommonSense>IgnoreToken" in vertexToMatch['probable_commands'] \
                                            or ((vertexToMatch['entity'] == [] or ('~NoTag' in vertexToMatch['entity'])) and vertexToMatch['probable_commands'] == []) 
                            if IgnoreTokenFound == True:
                                commandMatched = True
                                paramID = paramID - 1
                                
#                             for command in vertexToMatch['probable_commands']:
#                                 commandMatched = command == parameterCommandOrString
#                                 if ( commandMatched == True ) :
#                                     break

                        if ( commandMatched or labelMatched ) :
                            commandOrLabelMatched = True
                        
                        if commandOrLabelMatched == False:
                            sequenceMatched = False
                            break

                    except (KeyError,IndexError) as e:
                        sequenceMatched = False
                        break
                        pass
                
                if sequenceMatched == True:
                    paramOffset=0
                    siblings = G.successors(G.predecessors(VertexID)[0])
                    siblings.sort(cmp=None, key=None, reverse=False) #after sorting, the hypergraphs which were added during CP will get placed in serial order, otherwise all hypergraphs used to get pushed to the end of graph which resulted in error while sequence matchin
                    paramID = ParamIDsToCheckOnRightOfOrigin[0]
                    while paramID <ParamIDsToCheckOnRightOfOrigin[1] :
#                     for paramID in xrange(ParamIDsToCheckOnRightOfOrigin[0],ParamIDsToCheckOnRightOfOrigin[1]):
                        paramOffset = paramOffset + 1
                        
                        try:
                            GraphVertexToBeMatched = siblings[[i for i,x in enumerate(siblings) if x == VertexID][0]+paramOffset]
                            vertexToMatch =  G.node[GraphVertexToBeMatched]
                            parameterToMatch = ParameterExpression[paramID]
                            paramID = paramID + 1

                            pos = parameterToMatch.find(":")
                            if pos > -1 :
                                parameterCommandOrString = parameterToMatch[pos+1:]
                                chainOfVerticesToBeEnguledIfCommandIsFound.append([GraphVertexToBeMatched,parameterToMatch[0:pos]])
                            else:
                                parameterCommandOrString = parameterToMatch
                                chainOfVerticesToBeEnguledIfCommandIsFound.append([GraphVertexToBeMatched,""]) 

                            #find out whether the hypergraph must be made a $noun_phrase or $verb_phrase if some of its child vertex is a $noun_phrase or $verb_phrase 
                            if parameterCommandOrString.find("Noun") > -1: probableCommandsOfPotentiallyNewCommandHypergraph.append("$Noun_phrase")
                            
#                             print 'Match vertex = ' + str(vertexToMatch)
#                             print 'with parameter = ' + parameterCommandOrString
                            commandOrLabelMatched = False
                            commandMatched = False
                            labelMatched = vertexToMatch['label'] == parameterCommandOrString
                             
                            if (labelMatched == False):
                                commandMatched = parameterCommandOrString in vertexToMatch['probable_commands']
                                IgnoreTokenFound = "CommonSense>IgnoreToken" in vertexToMatch['probable_commands'] \
                                            or ((vertexToMatch['entity'] == [] or ('~NoTag' in vertexToMatch['entity'])) and vertexToMatch['probable_commands'] == []) 
                                if IgnoreTokenFound == True:
                                    commandMatched = True
                                    chainOfVerticesToBeEnguledIfCommandIsFound.pop(len(chainOfVerticesToBeEnguledIfCommandIsFound)-1)
                                    paramID = paramID - 1
#                                 for command in vertexToMatch['probable_commands']:
#                                     commandMatched = command == parameterCommandOrString
#                                     if ( commandMatched == True ) :
#                                         break

                            if ( commandMatched or labelMatched ) :
                                commandOrLabelMatched = True
                            
                            if commandOrLabelMatched == False:
                                sequenceMatched = False
                                break
                            
                        except (KeyError,IndexError) as e:
                            sequenceMatched = False
                            break
                            pass
                        
                # print 'sequence Matched = ' + str(sequenceMatched), "\n"
                """[Psecode] if match is successful, or no parameters were required to be matched :"""
                if sequenceMatched == True:
                    vertexLabel = Command #G.node[VertexID]['label']

                    """[Psecode] pass the hypergraph to a new CommandNet function (B) which the CommandNet command (A) was requesting"""
                    IfNewHypergraph = eval('CommandNet.' + Command + '(mode=\'execute\')')
                    if IfNewHypergraph is not None :probableCommandsOfPotentiallyNewCommandHypergraph.append(IfNewHypergraph)
                    
                    #take note of the hypergraph that must be inserted. this hypergraph node must be inserted after 1 cycle of evaluation of all commands is complete
                    return [Command,vertexLabel,probableCommandsOfPotentiallyNewCommandHypergraph,chainOfVerticesToBeEnguledIfCommandIsFound]
                    """[Psecode] inside hypergraph vertex, claim that the vertex is the CommandNet function"""

                    #Parameter Expression successfully has found one Command, no need to check rest of the parameter expressions
                    break
        
    def ParseRepeatingParameterExpression(self,Command, VertexID, Repeaters, Separators):
        chainOfVerticesToBeEnguledIfCommandIsFound = []
        probableCommandsOfPotentiallyNewCommandHypergraph = []
        parameterCommandsOrStrings = []
        
        """[Psecode] - find sibling nodes. sort them in ascending order"""
        siblings = G.successors(G.predecessors(VertexID)[0])
        siblings.sort(cmp=None, key=None, reverse=False) #after sorting, the hypergraphs which were added during CP will get placed in serial order, otherwise all hypergraphs used to get pushed to the end of graph which resulted in error while sequence matchin

        pos = Repeaters[0].find(":")
        if pos > -1 :
            for Repeater in Repeaters:
                parameterCommandsOrStrings.append (Repeater[pos+1:])
            parameterType = Repeaters[0][:pos]
        else:
            for Repeater in Repeaters:
                parameterCommandsOrStrings.append (Repeater)
            

        
        
        """[Psecode] - start looping from the RIGHT of vertexID, till the beginning of siblings"""       
        """[Psecode] - keep looping while we continue to find alternating sequence of separator and repeator, break once we find a discontinuation of repetition - break the loop """
        """[Psecode] - engulf all 'repeator nodes with subject parameter' & 'separtor nodes without parameter' in chainOfVerticesToBeEngulfed until the loop continues"""        
        origin = siblings.index(VertexID) #find the itemID of VertexID node. this origin is requried so that RIGHT node of origin (VertexID) can be found from siblings list
        if len(Separators)>0:#rightNode must be identified because most probably the command got triggered on detection of a separator, rather than repeator. We are wanting to run a loop from node on right so that a repeator gets enclosed in our probable chain of hypergraph
            if origin + 1 > len(siblings) - 1:
                return #stop matching the parameters & return nothing - because the repeators weren't repeating in right node, infact the right node is not present!
            else:
#                 rightNodeToOrigin = origin + 1
                for x in xrange(origin+1,len(siblings)):
                    vertexToMatch = G.node[siblings[x]] 
                    if not (vertexToMatch['probable_commands'] == [] and (vertexToMatch['entity'] == [] or ('~NoTag' in vertexToMatch['entity']))):break
                rightNodeToOrigin = x
        else:
            rightNodeToOrigin= origin
        
        repeaterToBeChecked = True
        separatorToBeChecked = False
        
        for x in range(rightNodeToOrigin,-1,-1):
            print G.edges(nbunch=None, data=False)
            vertexToMatch = G.node[siblings[x]]
            commandOrLabelMatched = False
            
            if repeaterToBeChecked == True:
                
                """Try to check Separator even when its time to check repeater, because sometimes humans including multiple separators together after finally mentioning a repeater"""                           
                labelMatched = False
                labelMatched = vertexToMatch['label'] in Separators  
                
                if labelMatched == True :
                    chainOfVerticesToBeEnguledIfCommandIsFound.append([siblings[x],""])
                else:
                    """Check for repeaters now"""
                    labelMatched = vertexToMatch['label'] in parameterCommandsOrStrings 
                    commandMatched = False
                    if (labelMatched == False):
                        for parameterCommandOrString in parameterCommandsOrStrings:
                            commandMatched = parameterCommandOrString in vertexToMatch['probable_commands']
                            if commandMatched == True:break
        
                    if ( commandMatched or labelMatched ) :
                        #find out whether the hypergraph must be made a $noun_phrase or $verb_phrase if some of its child vertex is a $noun_phrase or $verb_phrase 
                        if parameterCommandOrString.find("Noun") > -1: probableCommandsOfPotentiallyNewCommandHypergraph.append("$Noun_phrase")
                        
                        commandOrLabelMatched = True
                        chainOfVerticesToBeEnguledIfCommandIsFound.append([siblings[x],parameterType])
                    #if vertex was 'Not tagged' by NER, keep looking for for next vertex - it might have a repeater
                    NoTagFound = ((vertexToMatch['entity'] == [] or ('~NoTag' in vertexToMatch['entity'])) and vertexToMatch['probable_commands'] == [])
                    if commandOrLabelMatched == False and not NoTagFound:
                        break
                    
                    #Coz there may be some repeaters which are not separated by any separators
                    if len(Separators)>0 and not NoTagFound:
                        repeaterToBeChecked = False
                        separatorToBeChecked = True
                
            elif separatorToBeChecked == True:
                labelMatched = False
                labelMatched = vertexToMatch['label'] in Separators  
                
                if labelMatched == True : chainOfVerticesToBeEnguledIfCommandIsFound.append([siblings[x],""])
                
                if labelMatched == False \
                and not ((vertexToMatch['entity'] == [] or ('~NoTag' in vertexToMatch['entity'])) and vertexToMatch['probable_commands'] == []) : #if vertex was 'Not tagged' by NER, keep looking for for next vertex - it might have a repeater
                    break
                 
                repeaterToBeChecked = True
                separatorToBeChecked = False
       
        if (len(chainOfVerticesToBeEnguledIfCommandIsFound) >= 3) or (len(Separators)==0 and len(chainOfVerticesToBeEnguledIfCommandIsFound) >=2) : #because if length of sequence is less than 3, the the seperator wasnt separating even 2 repeators, it was a fake separator

            vertexLabel = Command

            """[Psecode] pass the hypergraph to a new CommandNet function (B) which the CommandNet command (A) was requesting"""
            IfNewHypergraph = eval('CommandNet.' + Command + '(mode=\'execute\')')
            if IfNewHypergraph is not None :probableCommandsOfPotentiallyNewCommandHypergraph.append(IfNewHypergraph)
            
            #take note of the hypergraph that must be inserted. this hypergraph node must be inserted after 1 cycle of evaluation of all commands is complete
            return [Command,vertexLabel,probableCommandsOfPotentiallyNewCommandHypergraph,chainOfVerticesToBeEnguledIfCommandIsFound]
            """[Psecode] inside hypergraph vertex, claim that the vertex is the CommandNet function"""
        
# """[Psecode] call CommandNetProcessor class, pass it NERed text, display results"""
# x = CommandNetProcessor()
# print (x.LiteratureToCommandNetGraphBuilder('2 20 oz bottles of Pepsi').nodes(data=True))