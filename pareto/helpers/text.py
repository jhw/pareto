import re

def titleise(text):
    return " ".join([tok.capitalize()
                     for tok in re.split("\\-|\\_", text)
                     if tok!=''])

def labelise(text):
    return "-".join([tok.lower()
                     for tok in re.split("\\s|\\_", text)
                     if tok!=''])

def hungarorise(text):
    return "".join([tok.capitalize()
                    for tok in re.split("\\-|\\_", text)
                    if tok!=''])

def underscore(text):
    return "_".join([tok for tok in re.split("\\s|\\-", text)
                     if tok!=''])
                                    
def hyphenate(text):
    return "-".join([tok for tok in re.split("\\s|\\_", text)
                     if tok!=''])

def singularise(text):
    if text.endswith("ies"):
        return "%sy" % text[:-3]
    elif text.endswith("s"):
        return text[:-1]
    else:
        return text

def pluralise(text):
    if text.endswith("y"):
        return "%sies" % text[:-1]
    else:
        return "%ss" % text

def stringify(fn):
    def wrapped(text, **kwargs):
        return fn(str(text), **kwargs)
    return wrapped

@stringify
def text_left(text, n=32):
    return text+"".join([' ' for i in range(n-len(text))]) if len(text) < n else text[:n]            

@stringify
def text_right(text, n=32):
    return ("".join([' ' for i in range(n-len(text))]))+text if len(text) < n else text[:n]            
