import ConfigParser
import os

class Config():
    
    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read(os.path.dirname(__file__) + '/app.conf')
        
    def get(self, section):
        dict1 = {}
        options = self.config.options(section)
        for option in options:
            try:
                dict1[option] = self.config.get(section, option)
                if dict1[option] == -1:
                    DebugPrint("skip: %s" % option)
            except:
                print("exception on %s!" % option)
                dict1[option] = None
        return dict1