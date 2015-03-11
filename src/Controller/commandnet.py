__author__="Karan S. Sisodia"
__date__ ="$Oct 09, 2014 04:03:50 PM$"

class CommandNet():

    def __int__(self):
        pass

    """[Psecode]* Parameter Expressions"""
    def UnitOfMeasurement(self,mode, subject=-1, object=-1):
        if mode=='parameter_expression':
            parameter_expression = {
                "type": "SequenceExpression",
                "sequence": [
                                ['object:$token','subject:DBPedia>Units_of_measurement']
                             ],
                "priority":3
            }
            return parameter_expression
        elif mode=='execute':
            #note the subject's predecessor as (A)
            #remove the linking of subject's predecessor and object's predecessor
            #link subject and object with a new Node. Make this new node as its predecessor. Refer it as (B)
            #Pass the subgraph (B) to QuantityOrSizeOf Command
            return "CommandNet>QuantityOrSizeOf"


    def VagueSizeOf(self,mode, subject=-1, object=-1):
        if mode=='parameter_expression':
            parameter_expression = {
                "type": "SequenceExpression",
                "sequence": [['object:$token','subject:$Noun_phrase'],
                             ['object:$token','subject:CommandNet>Noun']
                             ],
                "priority":3
            }
            return parameter_expression

    def UnitsOfX(self,mode, subject=-1, object=-1):
        if mode=='parameter_expression':
            parameter_expression = {
                "type": "SequenceExpression",
                "sequence": [
                                ['object:$token','subject:$Noun_phrase'],   #[2] [cheese pizza's dipped in chocolate]
                                ['object:$token','subject:CommandNet>Noun'],   #[2] [cheese pizza's dipped in chocolate]
                                ['object:$token','ignore:CommonSense>Of','subject:$Noun_phrase']
                            ],
                "priority":3
            }
            return parameter_expression
        """[Psecode]-- Store parameter expression in a dictionary object."""
        """[Psecode]-- Make the function to return Parameter expression"""

#     def MeasuringUnit(self,mode, subject=-1, object=-1):
#         return [['object:$token']]
#         """[Psecode]-- Store parameter expression in a dictionary object."""
#         """[Psecode]-- Make the function to return Parameter expression"""

    def Container(self,mode, subject=-1, object=-1):
        if mode=='parameter_expression':
            parameterExpression = self.WhatOfWhat('parameter_expression')
            parameterExpression['sequence'] += [
                ['object:$token','containing','subject:$Noun_phrase'],
                ['object:$token','containing','subject:CommandNet>Noun'],
                ['object:$token','having','subject:$Noun_phrase'],
                ['subject:$Noun_phrase','in','object:$token']
            ]
            parameterExpression["priority"] = 3
            return parameterExpression

    def WhatOfWhat(self, mode):
        if mode=='parameter_expression':
            parameter_expression = {
                "type": "SequenceExpression",
                "sequence": [
                                ['subject:CommandNet>Noun','object:$token'],
                                ['object:$token','ignore:CommonSense>Of','subject:$Noun_phrase'],
                                ['object:$token','ignore:CommonSense>Of','subject:CommandNet>Noun'],
                                ['subject:CommandNet>Noun','\'s','object:$token']
                            ],
                "priority":3
                                    
            }
            return parameter_expression
        """[Psecode]-- Store parameter expression in a dictionary object."""
        """[Psecode]-- Make the function to return Parameter expression"""
        
    def QuantityOrSizeOf(self, mode, subject=-1, object=-1):
        if mode=='parameter_expression':
            parameter_expression = {
                "type": "SequenceExpression",
                "sequence": [
                                ['object:$token','subject:CommandNet>Noun'],
                                ['object:$token','ignore:CommonSense>Of','subject:CommandNet>Noun'],
                                ['object:$token','subject:$Noun_phrase'],
                                ['object:$token','ignore:CommonSense>Of','subject:$Noun_phrase']
                            ],
                "priority":3
            }
            return parameter_expression
    
    def LessOf(self, mode, subject=-1, object=-1):
        if mode=='parameter_expression':
            parameter_expression = {
                "type": "SequenceExpression",
                "sequence": [
                                ['object:$token','subject:CommandNet>Noun'],
                                ['object:$token','subject:$Noun_phrase']
                            ],
                "priority":3
            }
            return parameter_expression
    
    def MoreOf(self, mode, subject=-1, object=-1):
        if mode=='parameter_expression':
            parameter_expression = {
                "type": "SequenceExpression",
                "sequence": [
                                ['object:$token','subject:CommandNet>Noun'],
                                ['object:$token','subject:$Noun_phrase']
                            ],
                "priority":3
            }
            return parameter_expression
        
    def AlongWith(self, mode, subject=-1, object=-1):
        if mode=='parameter_expression':
            parameter_expression = {
                "type": "SequenceExpression",
                "sequence": [
                                ["subject:CommandNet>Noun","ignore:$token","object:CommandNet>Noun"],
                                ["subject:$Noun_phrase","ignore:$token","object:CommandNet>Noun"],
                                ["subject:CommandNet>Noun","ignore:$token","object:$Noun_phrase"],
                                ["subject:$Noun_phrase","ignore:$token","object:$Noun_phrase"]
                            ],
                "priority":3
            }
            return parameter_expression

    def MoreObjectInSubject(self, mode, subject=-1, object=-1):
        if mode=='parameter_expression':
            parameter_expression = {
                "type": "SequenceExpression",
                "sequence": [
#                                 ["subject:CommandNet>Noun","$token","object:CommandNet>Noun"],
#                                 ["subject:$Noun_phrase","$token","object:CommandNet>Noun"],
#                                 ["subject:CommandNet>Noun","$token","object:$Noun_phrase"],
#                                 ["subject:$Noun_phrase","$token","object:$Noun_phrase"]
                                ["ignore:$token","object:CommandNet>Noun"],
                                ["ignore:$token","object:$Noun_phrase"]
                            ],
                "priority":3
            }
            return parameter_expression
        
    def NewInstructionOfNouns(self, mode, subject=-1, object=-1):
        if mode=='parameter_expression':
            parameter_expression = {
                "type": 'RepeatingExpression',
                "repeaters":['subject:CommandNet>Noun'],
                "separators":["and", "or", ",", "&"], # List of separator
                "priority":1
            }
            return parameter_expression
        
    def NewInstruction(self, mode, subject=-1, object=-1):
        if mode=='parameter_expression':
            parameter_expression = {
                "type": 'RepeatingExpression',
                "repeaters":['subject:$Noun_phrase'],
                "separators":["and", "or", ",", "&"], # List of separator
                "priority":4
            }
            return parameter_expression
        
    def Noun(self, mode, subject=-1, object=-1):
        if mode=='parameter_expression':
            parameter_expression = {
                "type": 'RepeatingExpression',
                "repeaters":['subject:CommandNet>Noun','subject:$Noun_phrase'],
                "separators":[], # List of separator
                "priority":2
            }
            return parameter_expression
        elif mode == 'execution':
            return "$nounPhrase"