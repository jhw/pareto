from demo import *

import lxml, pymorphy2  # layer test

@api_gateway
def handler(event, context):
    logging.info(event)
    return event

if __name__=="__main__":
    pass
