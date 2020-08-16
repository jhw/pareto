from pareto.helpers.text import hungarorise

def format_text(text, n=32):
    return text+"".join([' ' for i in range(n-len(text))]) if len(text) < n else text[:n]            

class Outputs(dict):

    @classmethod
    def initialise(self, stackname, cf, filterfn=lambda k: True):
        outputs=Outputs()
        for stack in cf.describe_stacks()["Stacks"]:
            if (stack["StackName"].startswith(stackname) and
                "Outputs" in stack):
                for output in stack["Outputs"]:
                    if filterfn(output["OutputKey"],
                                output["OutputValue"]):
                        outputs[output["OutputKey"]]=output["OutputValue"]
        return outputs

    def __init__(self):
        dict.__init__(self)

    def lookup(self, _key):
        key=hungarorise(_key)
        if key not in self:
            raise RuntimeError("%s not found" * key)
        return self[key]

    @property
    def table_repr(self):
        return "\n".join(["%s\t%s" % (format_text(k), v)
                          for k, v in self.items()])
    
if __name__=="__main__":
    pass
