To update this library within the KA Lite repo, we use git subtree.

First add the Learning Equality Perseus repo as a remote to your local git repository:
```
git remote add -f perseus https://github.com/learningequality/perseus.git
```
You can now update the repo with the following command:
```
git subtree pull --squash --prefix=kalite/distributed/static/js/distributed/perseus perseus master
```

To rebuild Perseus, you need to create a .gitmodules file in the root of the project and add these items:
[submodule "react-components"]
    path = kalite/distributed/static/js/distributed/perseus/react-components
    url = https://github.com/Khan/react-components.git
[submodule "kmath"]
    path = kalite/distributed/static/js/distributed/perseus/kmath
    url = git@github.com:Khan/kmath.git
[submodule "simple-markdown"]
    path = kalite/distributed/static/js/distributed/perseus/simple-markdown
    url = git@github.com:Khan/simple-markdown.git
[submodule "hubble"]
    path = kalite/distributed/static/js/distributed/perseus/hubble
    url = https://github.com/joelburget/hubble.git
[submodule "qunit"]
    path = kalite/distributed/static/js/distributed/perseus/ke/test/qunit
    url = https://github.com/jquery/qunit

Then run make build from within the Perseus directory.