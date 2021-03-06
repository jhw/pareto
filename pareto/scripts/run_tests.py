#!/usr/bin/env python

from pareto.scripts import *

from pareto.helpers.text import underscore

def assert_actions(fn):
    def wrapped(config):
        if "actions" not in config["components"]:
            raise RuntimeError("no actions found")
        return fn(config)
    return wrapped

@assert_actions
def run_tests(config):
    logging.info("running tests")
    def index_test(config, action, klassname="IndexTest"):    
        modname="%s.%s.test" % (config["globals"]["app"],
                                underscore(action["name"]))
        try:
            mod=__import__(modname, fromlist=[klassname])
        except ModuleNotFoundError:
            raise RuntimeError("%s does not exist" % modname)
        klass=getattr(mod, klassname)
        if not klass:
            raise RuntimeError("%s does not exist in %s" % (klassname,
                                                            modname))
        return klass
    klasses=[index_test(config, action)
             for action in config["components"]["actions"]]
    suite=unittest.TestSuite()
    for klass in klasses:
        suite.addTest(unittest.makeSuite(klass))
    runner=unittest.TextTestRunner()
    results=runner.run(suite)
    nfailures, nerrors = len(results.failures), len(results.errors)
    if (nfailures > 0 or nerrors > 0):
        raise RuntimeError("Tests failed with %i failures / %i errors" % (nfailures, nerrors))        
    return results

if __name__=="__main__":
    try:        
        init_stdout_logger(logging.INFO)
        argsconfig=yaml.safe_load("""
        - name: config
          type: file
        """)
        args=argsparse(sys.argv[1:], argsconfig)
        config=args.pop("config")
        run_tests(config)
    except ClientError as error:
        logging.error(error)                      
    except WaiterError as error:
        logging.error(error)                      
    except RuntimeError as error:
        logging.error(error)                      


        
