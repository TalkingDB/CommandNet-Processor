'''
Created on 18-Mar-2015

@author: Tushar@solutionbeyond.net

@summary: Calls CommandNet Processor 1000 times. And shows the # of seconds the result was given
Helps measure the improvement of speed
'''
import socket
import time

def commandProcessorHit(arg):
    """
    Function to hit command processor socket
    to fetch NER response as JSON
    
    Input : string name
    Output: dict buf of type
        {
            'links':{},
            'nodes':{}
        }
    """
    try:
        s = socket.socket()
        s.connect(("127.0.0.1", 5012))
        s.send(arg)
        buf = ''
        #Iterator applied to receive chunks of data over socket
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            else:
                buf += chunk
                
        return buf
    except UnicodeDecodeError:
        print arg + ' is a unicode string'
    except Exception as e:
        print e

t1 = time.time()
for i in range(1000):
    reply = commandProcessorHit('large cheese pizza')
t2 = time.time()
print str(t2-t1)