class Template(dict):

    def __init__(self, **kwargs):
        dict.__init__(self, kwargs)
        for attr in ["parameters",
                     "resources",
                     "outputs"]:
            self.setdefault(attr, [])

    def update(self, template):
        for attr in self.keys():
            if attr in template:
                self[attr]+=template[attr]

    def render(self):
        """
        - dict() required because values are lists of tuples
        """
        return {k.capitalize():dict(v)
                for k, v in self.items()
                if len(v) > 0}

if __name__=="__main__":
    pass
