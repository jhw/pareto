import re

def titleise(text):
    return " ".join([tok.capitalize()
                     for tok in re.split("\\-|\\_", text)])

def labelise(text):
    return "-".join([tok.lower()
                     for tok in re.split("\\s|\\_", text)])

def hungarorise(text):
    return "".join([tok.capitalize()
                    for tok in re.split("\\-|\\_", text)])    

def underscore(text):
    return text.replace("-", "_")

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
