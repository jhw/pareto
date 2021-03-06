from pareto.helpers.text import hungarorise, text_left

class Outputs(dict):

    @classmethod
    def initialise(self, stackname, cf, filterfn=lambda k, v: True):
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
        return "\n".join(["%s\t%s" % (text_left(k), v)
                          for k, v in self.items()])
    
if __name__=="__main__":
    pass
