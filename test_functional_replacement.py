import re

def remap_single_quotes(text):
    class Counter:
        def __init__(self):
            self.value=0
        def increment(self):
            self.value+=1
    def count(fn):
        counter=Counter()
        def wrapped(match):
            resp=fn(match, counter)
            counter.increment()
            return resp
        return wrapped
    @count
    def matcher(match, counter):
        return "\"'" if 0==counter.value % 2 else "'\""
    return re.sub("'''", matcher, text)

if __name__=="__main__":
    print (remap_single_quotes("'''asjdasdsd'''"))
