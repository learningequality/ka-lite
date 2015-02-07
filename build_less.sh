#!/bin/sh

lessc -x kalite/static/perseus/lib/katex/katex.less kalite/static/perseus/lib/katex/katex.css

# TODO: 2 lines of same stuff in different locations
lessc -x kalite/distributed/static/perseus/stylesheets/exercise-content-package/perseus.less kalite/distributed/static/perseus/stylesheets/exercise-content-package/perseus.css
lessc -x kalite/static/perseus/stylesheets/exercise-content-package/perseus.less kalite/static/perseus/stylesheets/exercise-content-package/perseus.css

# TODO: 2 lines of same stuff in different locations
lessc -x kalite/distributed/static/perseus/stylesheets/perseus-admin-package/editor.less kalite/distributed/static/perseus/stylesheets/perseus-admin-package/editor.css
lessc -x kalite/static/perseus/stylesheets/perseus-admin-package/editor.less kalite/static/perseus/stylesheets/perseus-admin-package/editor.css
