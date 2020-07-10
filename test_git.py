from git import Repo

def get_latest_commits(repo, roots):
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
        def __init__(self, roots):
            dict.__init__(self)
            self.roots=roots
        def is_valid(self, diff):
            for root in self.roots:
                if diff.startswith(root):
                    return True
            return False
        def update(self, commit, diffs):
            for diff in diffs:
                if self.is_valid(diff):
                    self[str(diff)]=str(commit.hexsha)
    commits=sorted(repo.iter_commits(),
                   key=lambda x: x.committed_datetime)
    latest=Latest(roots)
    for c0, c1 in zip(commits[:-1], commits[1:]):
        diffs=diff_commits(c1, c0)
        """
        print ("%s [%s] -> %s" % (c1.hexsha,
                                  c1.committed_datetime,
                                  diffs))
        """
        latest.update(c1, diffs)
    return latest

if __name__=="__main__":
    latest=get_latest_commits(Repo("."),
                              roots=["lambda"])
    print (latest)
            
    
