import re

def layer_project_name(config, package):
    return "%s-%s-layer" % (config["globals"]["app"],
                            package["name"])
    
def validate_layer_package(fn):
    def wrapped(packagestr):
        if ("-" in packagestr and
            not re.search("\\-(\\d+\\.)*\\d+$", packagestr)):
            raise RuntimeError("package definition has invalid format")
        return fn(packagestr)
    return wrapped

@validate_layer_package
def parse_layer_package(packagestr):
    tokens=packagestr.split("-")
    package={"name": tokens[0]}
    if len(tokens) > 1:
        package["version"]={"raw": tokens[1],
                            "formatted": tokens[1].replace(".", "-")}
    return package
    
if __name__=="__main__":
    pass
