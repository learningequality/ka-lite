To update this library within the KA Lite repo, we use git subtree.

First add the Learning Equality Perseus repo as a remote to your local git repository:
```
git remote add -f perseus https://github.com/learningequality/perseus.git
```
You can now update the repo with the following command:
```
git subtree pull --squash --prefix=kalite/distributed/static/perseus perseus master
```