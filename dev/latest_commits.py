from git import Repo

import datetime

def latest_commits(repo, roots,                       
                   ignore=["test.py"],
                   window=90):
    def diff_commits(c1, c0):
        modified=[] 
        for diff in c0.diff(c1):
            if (diff.a_blob is not None and
                diff.a_blob.path not in modified):
                modified.append(diff.a_blob.path)        
            if (diff.b_blob is not None and
                diff.b_blob.path not in modified):
                modified.append(diff.b_blob.path)        
        return modified
    class Latest(dict):
        def __init__(self, roots, ignore):
            dict.__init__(self)
            self.roots=roots
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
                if root:
                    self[root]=(commit.hexsha, ts)
        @property
        def complete(self):
            return len(self)==len(self.roots)
    commits=sorted(repo.iter_commits(),
                   key=lambda x: x.committed_datetime)
    latest=Latest(roots=roots,
                  ignore=ignore)
    cutoff=datetime.datetime.today()-datetime.timedelta(days=window)
    for c0, c1 in zip(commits[:-1], commits[1:]):
        if c1.committed_datetime.strftime("%Y-%m-%d") < cutoff.strftime("%Y-%m-%d"):
            break
        diffs=diff_commits(c1, c0)
        latest.update(c1, diffs)
        if latest.complete:
            break
    if not latest.complete:
        raise RuntimeError("latest commit map is incomplete")
    return latest

if __name__=="__main__":
    import os
    roots=["lambda/%s" % path
           for path in os.listdir("lambda")]
    latest=latest_commits(Repo("."), roots)
    print (latest)
            
    
