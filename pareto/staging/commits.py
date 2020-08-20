from git import Repo

"""
- Symlinks/Remapper is an opportunity to override default paths for (eg) situations where you may be using symlinks (eg) in a gist (where directory structure not permitted, but pareto project structure requires lambdas to be in a (symlinked) directory
- not ideal as currently requires u to clone push_lambdas.py but better than nothing 
"""

Symlinks={}

def Remapper(path, symlinks=Symlinks):
    return symlinks[path] if path in symlinks else path

def validate_commits(fn):
    def wrapped(*args, **kwargs):
        commits=fn(*args, **kwargs)
        if not commits.complete:
            raise RuntimeError("latest commit map is incomplete (if you've moved lambdas to new directory, have changes been committed ?)")
        return commits
    return wrapped

class CommitMap(dict):

    @classmethod
    @validate_commits
    def create(self,
               roots,
               repo=Repo("."),
               mapfn=Remapper,
               ignore=["test.py"]):
        commits=CommitMap(roots=roots,
                          mapfn=mapfn,
                          ignore=ignore)
        commits.populate(repo.iter_commits(repo.active_branch))
        return commits
    
    def __init__(self, roots, mapfn, ignore):
        dict.__init__(self)
        self.roots=roots
        self.mapfn=mapfn
        self.ignore=ignore

    def find_root(self, diff):
        for root in self.roots:
            if diff.startswith(root):
                return root
        return None

    def is_valid(self, diff):
        for suffix in self.ignore:
            if diff.endswith(suffix):
                return False
        return True

    def update(self, commit, diffs):
        ts=commit.committed_datetime.strftime("%Y-%m-%d %H:%M:%S")
        for diff in diffs:
            if not self.is_valid(diff):
                continue
            root=self.find_root(diff)
            if (root and
                root not in self):
                self[root]={"hexsha": commit.hexsha,
                            "timestamp": ts}
        return self

    @property
    def complete(self):
        return len(self)==len(self.roots)

    def latest_first(fn):
        def wrapped(self, commits):
            return fn(self, list(reversed(sorted(commits,
                                                 key=lambda x: x.committed_datetime))))
        return wrapped

    def diff_commits(self, c1, c0):
        modified=[] 
        for diff in c0.diff(c1):
            if (diff.a_blob is not None and
                diff.a_blob.path not in modified):
                modified.append(self.mapfn(diff.a_blob.path))
            if (diff.b_blob is not None and
                diff.b_blob.path not in modified):
                modified.append(self.mapfn(diff.b_blob.path))
        return modified
    
    @latest_first
    def populate(self, commits):
        for c0, c1 in zip(commits[:-1], commits[1:]):
            diffs=self.diff_commits(c1, c0)
            self.update(c1, diffs)
            if self.complete:
                break
            
if __name__=="__main__":
    pass
