import re

class Counter:
    def __init__(self):
        self.counter=0
    def increment(self):
        self.counter+=1

def increment(fn):
    def wrapped(match, counter):
        resp=fn(match, counter)
        counter.increment()
        return resp
    return wrapped
        
@increment        
def matcher(match, counter):
    return "hah" if 0==counter.counter % 2 else 'bah'

if __name__=="__main__":
    counter=Counter()
    print (re.sub("XXX",
                  lambda m: matcher(m, counter),
                  "abasdasdad XXX asjdasdsd XXX asdasdd XXX ashdahjsadsa XXX asasasas"))
