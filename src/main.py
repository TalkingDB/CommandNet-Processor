import sys
import socket
import json
import networkx as nx
from networkx.readwrite import json_graph
from Controller import index as Controller
from app import *
from GraphLib.index import *
from NLProcessor.nl_processor import *
from time import sleep

Config = Config()
address = str(Config.get('NER')['address'])
# port = int(Config.get('NER')['port'])
ner = NLProcessor()


def startServer():
    try:
        sok = socket.socket()
        sok.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sok.bind((address, port))
        sok.listen(5)
        
        print 'CommandNet Processor started listning on ' + address + ':' + str(port), '\nPress Ctrl+C to stop the server.'
        
        cnp = Controller.CommandNetProcessor()

        while True:
            conn, addr = sok.accept()
            st_k = conn.recv(1024)
            
            
            if output_type == 'ner':
                output = str(ner.process_string(st_k))
            else:
                # Pass raw user instructions for processing
                graph_obj = cnp.LiteratureToCommandNetGraphBuilder(st_k)
                
                # Conver List into comma separated string
                for n in nx.nodes(graph_obj):
                    if isinstance(graph_obj.node[n]['entity'], list):
                        graph_obj.node[n]['entity'] = ','.join((list(graph_obj.node[n]['entity'])))
                    # print type(graph_obj.node[n]['command']), graph_obj.node[n]['command']
                    if isinstance(graph_obj.node[n]['command'], list):
                        graph_obj.node[n]['command'] = ','.join((list(graph_obj.node[n]['command'])))
                    
                    if isinstance(graph_obj.node[n]['probable_commands'], list):
                        graph_obj.node[n]['probable_commands'] = ','.join((list(graph_obj.node[n]['probable_commands'])))
                
                output = ""
    
                if output_type == 'json':
                    #json output
                    output = json.dumps(json_graph.node_link_data(graph_obj))
                elif output_type =='gml':
                    # GML Output
                    for i in nx.generate_gml(graph_obj):
                        output += i
                elif output_type =='graphml':
                    for i in nx.generate_graphml(graph_obj):
                        output += i
                
            conn.send(output) 
            conn.close()
    except KeyboardInterrupt:
        print '\nGood Bye!'
        exit()
    except socket.error:
        "some process (most probably an another instance of CommandNet Processor) is already listening on the requested port"
        "now we will restart the process"
        import subprocess
        print 'some process is already running on port ' + str(port) + '. Killing it..' 
        subprocess.call('sudo fuser -k ' + str(port) + '/tcp',shell=True) #kill the system process running on requested port
        sleep (1)
        #restart CommandNet Processor now
        startServer()
    except Exception as e:
        import traceback
        print e
        print e.args
        print traceback.print_exc(file=sys.stdout)
        
        
if __name__ == "__main__":

    if len(sys.argv) > 1:
        output_type = sys.argv[1:][0] #output_type can be : gml, json, ner
        
        if sys.argv[1:][1]:
            port = int(sys.argv[1:][1])
            startServer()
