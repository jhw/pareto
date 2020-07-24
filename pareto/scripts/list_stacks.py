#!/usr/bin/env python

from pareto.scripts import *

if __name__=="__main__":
    try:
        stacks=CF.describe_stacks()["Stacks"]
        df=pd.DataFrame([{"name": stack["StackName"],
                          "status": stack["StackStatus"]}
                         for stack in stacks])
        pd.set_option('display.max_rows', df.shape[0]+1)
        print (df)
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
