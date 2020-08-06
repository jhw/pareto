import re

class Counter:
    def __init__(self):
        self.counter=0
    def increment(self):
        self.counter+=1

def increment(fn, counter=Counter()):
    def wrapped(match):
        resp=fn(match, counter)
        counter.increment()
        return resp
    return wrapped
        
@increment        
def matcher(match, counter):
    return "hah" if 0==counter.counter % 2 else 'bah'

if __name__=="__main__":
    print (re.sub("XXX",
                  matcher,
                  "abasdasdad XXX asjdasdsd XXX asdasdd XXX ashdahjsadsa XXX asasasas"))
