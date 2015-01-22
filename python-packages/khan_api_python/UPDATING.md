To update this library within the KA Lite repo, we use git subtree.

First add the Khan Python API repo as a remote to your local git repository:
```
git remote add -f ka-api-py https://github.com/learningequality/khan-api-python.git
```
You can now update the repo with the following command:
```
git subtree pull --prefix=python-packages/khan_api_python ka-api-py master
```