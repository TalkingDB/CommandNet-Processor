__author__="Karan S. Sisodia"
__date__ ="$Jun 4, 2014 12:38:00 AM$"

import json
import time
import datetime
from collections import defaultdict
import re
import sys
from pymongo import MongoClient

EntitiesOfWords = {}
Common_Words=[]
EntityMetaData = []
keywords=[]

class NER():
    def __init__(self, table):
        self.common_words_file_path = '../data/common-words'
        self.EntityModel = table
        
    def get_data(self, data):
        return self.find_named_entities(data, 0)
    
    def load_wikipedia_entities_in_memory(self):
        print 'Initializing NER data...'
        
        # load common words file
#        fileWikiStopWords = open(self.common_words_file_path,'r')
        fileWikiStopWords = []
        for line in fileWikiStopWords:
            Common_Words.append(line[:-1])

        mngClient = MongoClient("127.0.0.1",27017)
        db= mngClient.noisy_NER
        entityCollection = db.entity
        if sys.argv[1:][2] == 'train_UIP_from_learnt_answers': #command line parameter passed to our process
            #this mongo query loads only those surface_texts which have been marked as 'approved' by human trainers
            entities = entityCollection.find({"approved_by_trainer":{"$exists": 1}}) 
        elif sys.argv[1:][2] == 'compute_high_priority_training_questions':
            #this mongo query loads only which have neither approved AND nor disapproved, or the ones which have only approved.
            entities = entityCollection.find({"$or": [{"approved_by_trainer":{"$exists": 1}},{"approved_by_trainer":{"$exists": 0},"disapproved_by_trainer":{"$exists": 0}}]})
        
        for entity in entities:
            keyword = str(entity['surface_text'])
#            if (keyword == "cheese pizza"):
#                print keyword
            if type(keyword) is int:
                keyword = str(keyword)
            keywords.append(keyword)
            EntityMetaData.append([entity['entity_url'], len(keyword.split())]) #[word, word count]
        x=0
        token1=''
        token2=''
        for keyword in keywords:                    
            # loop for each keyword in keyword list
            #assume that 'keyword' is 'league of super humans'

            x = x + 1 #this number will be assigned as EntityID

            words = keyword.split()         #loop for each word in keyword

            wordCount = len(words) 
            for y in range(0,wordCount):
                if words[y] in Common_Words:
                    token1=''
                    if y-1>0: #if current word is NOT the first word of keyword
                        token1 = words[y-1] + ' ' + words[y] #token1 = 'league of'
                    if token1!=token2 and token2!='':
                        self.insert_entities_of_words(token1,x)

                    token2=''
                    try:token2 = words[y] + ' ' + words[y+1] #token2 = 'of super'
                    except:pass
                    self.insert_entities_of_words(token2,x)
                else:
                    self.insert_entities_of_words(words[y],x)
        print "Ner Data Initialized Successfully!"

    def insert_entities_of_words(self, token ='',EntityID = 0):
        if token != '':
            try:
                tmpList = EntitiesOfWords[token]
                tmpList.append(EntityID)
            except:tmpList = [EntityID]
            EntitiesOfWords[token] = tmpList
            

    def find_named_entities(self, strSearch = '', OutputFormat = 0):
        Words_NGram = []
        curNGramID=0
        PreviousTokenStartingWordID = 0
        token1=''
        token2=''
        
        #loop for each word in strSearch, prepare tokens which are to be searched
        words = strSearch.lower().split()         #loop for each word in keyword
        wordsCount = len(words) #-1
        tokens = []
        for x in range(0,wordsCount):
            if words[x] in Common_Words:
                if x-1 >0: #try catching error as previous word might not exist!
                    token1=words[x - 1] + ' ' + words[x]
                    if (token2 != token1 and token2 !=''):
                        tokens.append([token1#previous word concatenated with current common word
                                       ,x-1#current WordID
                                       ,2])#wordCount

                try: #try catching error as next word might not exist!
                    token2=words[x] + ' ' + words[x + 1]
                    tokens.append([token2 #previous word concatenated with current common word 
                                   ,x #current WordID
                                   ,2 #wordCount
                                   ])
                except:
                        pass
            else:
                tokens.append([words[x] #previous word concatenated with current common word 
                               ,x #current WordID
                               ,1 #wordCount
                               ])
            # tokens list may look like this : [['Krrish',0,1],['Krrish is',0,2],['is a',1,2]]

        #search tokens in Entities
        wordCount=0
        for dataitem in tokens:
            token = dataitem[0]
            curWordID =dataitem[1] 
            wordCount = dataitem[2]

            dictEntities = {}

            #form a CHAIN when 2 adjoinings tokens both match with a particular Entity. See wiki article Chain-formation-console-output for details
            try:
                for entity in EntitiesOfWords[token]:

                    if curNGramID == 0:
                        dictEntities[entity] = [curWordID, curWordID+wordCount -1, wordCount,token,curWordID]
#                        dictEntities[entity] = [0 #start wordID of Chain
#                                                , wordCount-1  #end wordID of Chain
#                                                , wordCount  #count of words in Chain
#                                                ,token #the token which is being searched to find surface chains. Note this field is used only for debugging purposes. not requried for production purposes
#                                                ,0] #the wordID from where the token starts. Note this field is used only for debugging purposes. not requried for production purposes
                    else:
                        LastNGram = Words_NGram[curNGramID-1]

                        if entity in LastNGram: #same entity was found in this token & previous token

                            #check whether the order of last token and this token is accurate in probable entity
                            PreviousTokenStartingWordID = LastNGram[entity][0]
                            ThisTokenEndingWordID = curWordID+wordCount - 1
                            surfaceTextMatched = ''
                            for wordID in range(PreviousTokenStartingWordID, ThisTokenEndingWordID+1):
                                surfaceTextMatched = surfaceTextMatched + words[wordID] + ' '
                            surfaceTextMatched = surfaceTextMatched[:-1] #remove the trailing space from the end of surface text string
                            keyword = keywords[entity-1]
                            if keyword.find(surfaceTextMatched) != -1: #so in keyword:'Pirates of the Caribbean' we are trying to search surfaceText:'Pirates of'
                                dictEntities[entity] = [PreviousTokenStartingWordID, ThisTokenEndingWordID, ThisTokenEndingWordID - PreviousTokenStartingWordID + 1,token,curWordID]
                            else:
                                #do same as :elseif entity NOT in LastNGram
                                dictEntities[entity] = [curWordID, curWordID+wordCount -1, wordCount,token,curWordID]
                        else:
                            dictEntities[entity] = [curWordID, curWordID+wordCount -1, wordCount,token,curWordID]

                Words_NGram.append(dictEntities)
                curNGramID = curNGramID + 1
            except:
                pass
            
#        print Words_NGram
    
    #engulf smaller named entities which are overlapped by larger named entities
    # - producing a more finer list of entities

        #init LargestEntityPerWord for all wordIDs
        #LargestEntityPerWord is a LIST of defaultdict. its heirarchy is as follows :
        #LIST
        #    DefaultDict
        #        LIST             
        LargestEntityPerWord = []
        for x in range(0,len(words)+1):
            LargestEntityPerWord.append(defaultdict(list))

        # Surface chains are grouped by WordIDs (For each WordID in input text, Words_NGram contains a dictionary. Each dictionary contains Entities with which WordID matched)
        for word in Words_NGram[::-1]: #when use use -1 here, we are reading the Words_NGram list, but in REVERSE ORDER 

            for Entity in word: #Enumerate through each entity stored inside each WordID

                startingWordID = word[Entity][0]#StartingWordID of current entity
                endingWordID  = word[Entity][1]#EndingWordID of current entity.
                wordCount = word[Entity][2]##WordCount of current entity
                #independentStartingWordID =word[Entity][4]

                if (#wordCount>=4 or #this matching rule may be removed later! It matches any phrase with an entity if 4 words of the phrase match with entity
                    wordCount == int(EntityMetaData[Entity-1][1])): #filters down to only those matches where wordcount of surface-chain matches with wordcount of Entity. This matching rule may be removed/improved later! Hence removing the possibility to match phrase 'Michael Jordan' with Entity 'Michael Jr Jordan'. This rule may be removed when Wikipedia disambiguation is added
                    if wordCount >0:#this matching rule may be removed/improved later! once wordnet sysnets are loaded in Common_Words 

                        #ignore matches where order of words in surface text and entityDb dont match
                        surfaceTextMatched = ''
                        for wordID in range(startingWordID, endingWordID+1):
                            surfaceTextMatched = surfaceTextMatched + words[wordID] + ' '
                        surfaceTextMatched = surfaceTextMatched[:-1]
                        keyword = keywords[Entity-1]
                        if keyword.find(surfaceTextMatched) != -1:
                        # when a surface form matches its entity 100%, insert that EntityID in LargestEntityPerWord in EVERY WORDID as follows
                        # LargestEntityPerWord after its filled:
                        #     wordID:125
                        #         wordCount:4
                        #             Entity:123,startingWordID:125,endingWordID:123
                        #             Entity:123,startingWordID:125,endingWordID:123
                        #         wordCount:3
                        #         wordCount:2
                        #    wordID:126
                        #    ...
                            for wordID in range(startingWordID,endingWordID+1):
                                LargestEntityPerWord[wordID][wordCount].append([Entity,startingWordID,endingWordID])

        NamedEntities_Unsorted = set()
        SmallestEntities = set()
        # scan LargestEntityPerWord for each wordID. AFTER LOOP IN #2 IS FINISHED
        #     Pick the largest wordCount in there, enumerate the Enties in there.
        #         For each entity check the startingWordID and endingWordID
        #             In LargestEntityPerWord[startingWordID] and LargestEntityPerWord[endingWordID] check whether same Entity exists. If it does, declare it as the Winner Entity
        for collidingChain in LargestEntityPerWord:
            if len(collidingChain)>0:
                ProbablyWinningEntities = collidingChain.items()[-1][1] #Described below

    #                SmallestEntities.append(schain)

                #by using [-1] here we are asking for LARGEST wordcount to return the NamedEntityMetaData. see the comment below to understand better
                #if a = {1: [[664456, 15, 15], [904079, 15, 15]], 2: [[664470, 14, 15]]}
                #print a.items()[-1] will return:
                #(2, [[664470, 14, 15]])
                #and print a.items()[-1][1] will return [[664470, 14, 15]]
                #and print a.items()[-1][0] will return 2

                wordCount  = collidingChain.items()[-1][0] 

                for EntityData in ProbablyWinningEntities:
                    Entity = EntityData[0]
                    startingWordID = EntityData[1]
                    endingWordID = EntityData[2]

                    if (Entity in [x[0] for x in LargestEntityPerWord[startingWordID][wordCount]]
                    and Entity in [x[0] for x in LargestEntityPerWord[endingWordID][wordCount]]):
                        NamedEntities_Unsorted.add((startingWordID,endingWordID,Entity,EntityMetaData[Entity-1][0]))

#                 for schain in collidingChain.items()[:-1]:
#                     wordCount  = schain[0]
#                     for sw in schain[1]:
#                         Entity = sw[0]
#                         startingWordID = sw[1]
#                         endingWordID = sw[2]
#                         SmallestEntities.add((startingWordID,endingWordID,Entity))

        NamedEntities_Sorted = sorted(list(NamedEntities_Unsorted),key=lambda x:x[0])
#        SmallestEntities_Sorted = sorted(list(SmallestEntities),key=lambda x:x[0])
    #    print SmallestEntities_Sorted
    #    print NamedEntities_Sorted

            #TODO: the code below must be changed. Instead of accepting anything like NamedEntities.[startingWordID,endingWordID,Entities]
            # it should rather accept : NamedEntities.[EntityID, startingWordID,endingWordID] 
        if OutputFormat==0:
            k = 0
            htmlHightedWords = list(words)
            output = {
                'string' : strSearch.replace('\n', ''),
            }
            contains = set(range(0, len(htmlHightedWords) - 1))

            output['tokens'] = self.prepOutTokens(NamedEntities_Sorted, htmlHightedWords,words)['tokens']
            # print output
            return output


    def prepOutTokens(self, NamedEntities_Sorted, htmlHightedWords,words):
        output = {}
        tokens = []
        prev = ''
        x = 0
        found = set()
        go = False
        
        lastWordIDAdded = 0
        
        for nerTags in NamedEntities_Sorted:
            x = x + 1
            startingWordID = nerTags[0]
            endingWordID = nerTags[1]
            
            """[Psecode] insert tokens with ~NoTag"""
            for i in xrange(lastWordIDAdded,startingWordID):
                obj = {
                    'id' : '~NoTag',
                    'surface_text' : words[i],
                    'start' : i,
                    'end': i
                }
                tokens.append(obj)

            lastWordIDAdded = endingWordID+1
            
            """Comment the portion below. Ask Karan@solutionbeyond.net on what it does"""
            Entity = nerTags[2]
            rdfURL = EntityMetaData[Entity-1][0]
            surface_text = ''
            if((endingWordID - startingWordID) > 0):
                go = True
                for j in range(startingWordID,endingWordID+1):
                    surface_text = surface_text + ' ' + htmlHightedWords[j]
                    found.add(j)
            else: 
                surface_text = htmlHightedWords[startingWordID]
                found.add(startingWordID)

            if (prev != rdfURL or go):
                go = False
                obj = {
                    'id' : rdfURL,
                    'surface_text' : surface_text.strip(),
                    'start' : startingWordID,
                    'end': endingWordID
                }
                if obj not in tokens:
                    tokens.append(obj)
            prev = rdfURL
            
        #Insert ~NoTag after the last surface_text which was found
        for i in xrange(lastWordIDAdded,len(words)):
            obj = {
                'id' : '~NoTag',
                'surface_text' : words[i],
                'start' : i,
                'end': i
            }
            tokens.append(obj)


        output = {
            'tokens':tokens,
            'found':found
        }
        return output


    def escape(self, html):
        return mark_safe(force_unicode(html).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;'))


#if __name__ == "__main__":
#    app = NER()
#    app.load_wikipedia_entities_in_memory()
