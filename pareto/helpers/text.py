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
