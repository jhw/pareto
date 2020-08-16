from pareto.helpers.text import hungarorise

class Outputs(dict):

    @classmethod
    def initialise(self, stackname, cf):
        outputs=Outputs()
        for stack in cf.describe_stacks()["Stacks"]:
            if (stack["StackName"].startswith(stackname) and
                "Outputs" in stack):
                for output in stack["Outputs"]:
                    outputs[output["OutputKey"]]=output["OutputValue"]
        return outputs

    def __init__(self):
        dict.__init__(self)

    def lookup(self, _key):
        key=hungarorise(_key)
        if key not in self:
            raise RuntimeError("%s not found" * key)
        return self[key]
        
if __name__=="__main__":
    pass
