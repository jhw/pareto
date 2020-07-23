from pareto.components import *

from pareto.components.function import *

def synth_action(**kwargs):
    return Template(resources=[Function(**kwargs),
                               FunctionRole(**kwargs),
                               FunctionDeadLetterQueue(**kwargs),
                               FunctionVersion(**kwargs),
                               FunctionEventConfig(**kwargs)],
                    outputs=[FunctionArn(**kwargs)])

if __name__=="__main__":
    pass
