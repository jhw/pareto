#!/usr/bin/env python

from pareto.scripts import *

def refactor_src(pat, rep, root):
    def refactor(tokens):
        path="/".join(tokens)
        for entry in os.listdir(path):
            newtokens=tokens+[entry]
            filename="/".join(newtokens)
            if os.path.isdir(filename):
                if not filename=="__pycache__":
                    refactor(newtokens)
            elif filename.endswith("pyc"):
                pass
            else:
                text=open(filename).read()
                newtext=re.sub(pat, rep, text)
                newfilename=re.sub(pat, rep, filename)
                if (text!=newtext or
                    filename!=newfilename):
                    print (newfilename)
                    dest=open(newfilename, 'w')
                    dest.write(newtext)
                    dest.close()
    refactor(root.split("/"))
                        
if __name__=="__main__":
    try:
        argsconfig=yaml.load("""
        - name: pat
          type: str
        - name: rep
          type: str
        - name: root
          type: str
        """, Loader=yaml.FullLoader)
        args=argsparse(sys.argv[1:], argsconfig)
        refactor_src(**args)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
