import boto3, json, logging

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

if __name__=="__main__":
    pass
