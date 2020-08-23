#!/usr/bin/env python

from pareto.scripts import *

from pareto.components.env import synth_env

if __name__=="__main__":
    try:        
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.safe_load("""
        - name: config
          type: file
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        synth_env(config)
    except RuntimeError as error:
        logging.error(error)                      


        
