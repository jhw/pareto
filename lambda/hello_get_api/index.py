import boto3, json, logging

logger=logging.getLogger()
logger.setLevel(logging.INFO)    

logging.getLogger('botocore').setLevel(logging.WARNING)

def handler(event, context):
    logging.info(event)
    return event

if __name__=="__main__":
    print (handler({"hello": "world"}, None))
