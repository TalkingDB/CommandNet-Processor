__author__="karan S. Sisodia"
__date__ ="$Jun 3, 2014 11:49:49 PM$"

import json
import ner
import re
import codecs
# from stemming.porter2 import stem
from nltk.stem.wordnet import WordNetLemmatizer
lmtzr = WordNetLemmatizer()

#Database
import database
import entity_model

#Libs
from GraphLib import index as GL
from networkx.readwrite import json_graph

Database = database.Database()
Mongodb = Database.connect()
EntityModel = entity_model.EntityModel(Mongodb)

#Initialize NER Data
ner_obj = ner.NER(EntityModel)
ner_obj.load_wikipedia_entities_in_memory()

class NLProcessor():
    
    def __init__(self):
        self.ner = ner_obj
        self.output = ''
        self.EntityModel = EntityModel
    
    def process_string(self, s):
        """
        Function to start process
        """
        separated_joined_words = self.__separate_joined_words(s)
        root_string = self.__get_root_word(separated_joined_words)
        return self.__get_ner_data(root_string)

    def __separate_joined_words(self,strLiterature):
        
        """[Psecode] the aim of regex below is NOT to replace "12,345" with "12 , 345 but replace "12, 345" to "12 , 345" """
        punctuations = [",",".","!"]       
        for punctuation in punctuations:
            strLiterature = re.sub(
            """((?<=[A-Za-z0-9])[\s]*[""" + punctuation + """][\s]*(?=[A-Za-z])        #replaces 'abc,xyz'; 'abc, xyz'; 'abc ,xyz'; '123, xyz' to 'abc , xyz'
            |(?<=[A-Za-z])[\s]*[""" + punctuation + """][\s]*(?=[A-Za-z0-9])           #replaces 'xyz, 123' to 'xyz , 123'
            |(?<=[0-9])[\s]+[""" + punctuation + """][\s]*(?=[0-9])                    #replaces '123 ,456' to '123 , 456'
                |(?<=[0-9])[\s]*[""" + punctuation + """][\s]*(?=[0-9])               #replaces '123, 456' to '123 , 456'
            |[""" + punctuation + """][\s]*$)                                         #replaces '123,'; 'abc.' to '123 , '
            """,                                
            " " + punctuation + " ",                                                 #to be replaced with
            strLiterature,                                                           #search in
            0,                                                                       #count of replacements to be made. 0 probably means infinite
            re.VERBOSE)                                                              #setting to VERBOSE allows us to put comments inside regular expression
            
        """[Psecode] Search for 1 digit, search for 1 alphabet. before the alphabet insert a whitespace"""
        strLiterature = re.sub("(?<=\d)(?=([A-Za-z]{1}))", " ", strLiterature)
        #TODO : above regex succeeds in separating 'abc 20oz' to 'abc 20 oz' but it also separates 'abc20oz' to 'abc20 oz'. it should rather let 'abc20oz' remain 'abc20oz' 
        
        return strLiterature
        
    def __get_root_word(self, s):
        """
        Function to get root word of a given word
        """
        words = s.lower().split()
        i = 0
        for word in words:
            try:
                words[i] = lmtzr.lemmatize(str(word.encode('utf8')))
            except:
                words[i] = codecs.decode(word,"latin-1")
            i += 1

        words = ' '.join(words)
        return words
    
    def __get_ner_data(self, data):
        """
        Function to get ner of a string
        """
        output = self.ner.get_data(data)
        return output
    
    def process_user_instructions(self, raw_instruction):
        """
        Function to process user instructions in new instruction (graph format)
        """
        gl = GL.GraphLib()
        instructions = []
        node_id = 1
        
        gl.addNode(node_id, {
            'type': 'hypergraph', 
            'entity': '',
            'command':'CommandNet>NewInstruction',
            'label': raw_instruction
        })
        
        parent_id = node_id
                
        if "~" in raw_instruction:
            for i in raw_instruction.split('~'):
                node_id += 1
                #TODO : stop removing special characters from here!
                label = i
                
                gl.addNode(node_id, {
                    'type': 'hypergraph', 
                    'entity': '',
                    'command':'CommandNet>NewInstruction',
                    'label': label
                })
                gl.addRelation((parent_id, node_id), {})
                instructions.append({"parent_id":node_id, "instruction":label})
        else:
            node_id += 1
            gl.addNode(node_id, {
                'type': 'hypergraph', 
                'entity': '',
                'command':'CommandNet>NewInstruction',
                'label': raw_instruction
            })
            gl.addRelation((parent_id, node_id), {})
            instructions.append({"parent_id":node_id, "instruction":raw_instruction})
        
        #print json.dumps(gl.jsonOutput())
        return gl, node_id, instructions
