import re

class Counter:

    def __init__(self):
        self.counter=0

    def increment(self):
        self.counter+=1

def matcher(match, counter):
    resp="hah" if 0==counter.counter % 2 else 'bah'
    counter.increment()
    return resp

if __name__=="__main__":
    counter=Counter()
    print (re.sub("XXX",
                  lambda m: matcher(m, counter),
                  "abasdasdad XXX asjdasdsd XXX asdasdd XXX ashdahjsadsa XXX asasasas"))
