import boto3, json, logging

import pymorphy2 # layer test

logger=logging.getLogger()
logger.setLevel(logging.INFO)    

logging.getLogger('botocore').setLevel(logging.WARNING)

def api_gateway(fn):
    def wrapped(event, context):
        resp=fn(event, context)
        return {"statusCode": 200,
                "headers": {"Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*"},
                "body": json.dumps(resp)}
    return wrapped

@api_gateway
def handler(event, context):
    logging.info(event)
    return event

if __name__=="__main__":
    print (handler({"hello": "world"}, None))

