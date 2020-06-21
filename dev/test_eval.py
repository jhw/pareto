def identify(item):
    def is_apple(item):
        return item["colour"] in ["red", "green"]
    def is_banana(item):
        return item["colour"]=="yellow"
    for fruit in ["apple", "banana"]:
        matcher=eval("is_%s" % fruit)
        if matcher(item):
            return fruit
    return None

if __name__=="__main__":
    print (identify({"colour": "yellow"}))
