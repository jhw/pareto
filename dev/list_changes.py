from git import Repo

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

if __name__=="__main__":
    repo=Repo(".")
    commits=list(repo.iter_commits(repo.active_branch))
    for c0, c1 in zip(commits[:-1], commits[1:]):
        diffs=[diff
               for diff in diff_commits(c1, c0)
               if diff.startswith("lambda")]
        if diffs!=[]:
            print ("%s [%s] -> %s" % (c1.hexsha,
                                      c1.committed_datetime,
                                      ", ".join(diffs)))

