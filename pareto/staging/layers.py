class Layers(dict):

    def __init__(self, config, s3):
        dict.__init__(self)
        paginator=s3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=config["globals"]["bucket"],
                                 Prefix="%s/layers" % config["globals"]["app"])
        def filter_name(key):
            return key.split("/")[-1].split(".")[0]        
        for struct in pages:
            if "Contents" in struct:
                self.update({filter_name(obj["Key"]):obj["Key"]
                             for obj in struct["Contents"]})

if __name__=="__main__":
    pass

