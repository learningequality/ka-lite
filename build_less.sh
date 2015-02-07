#!/bin/sh
# Commented out because original less file isn't there atm?
# lessc -x kalite/static/perseus/lib/katex/katex.less kalite/static/perseus/lib/katex/katex.css

lessc -x kalite/distributed/static/perseus/stylesheets/exercise-content-package/perseus.less kalite/distributed/static/perseus/stylesheets/exercise-content-package/perseus.css
lessc -x kalite/distributed/static/perseus/stylesheets/perseus-admin-package/editor.less kalite/distributed/static/perseus/stylesheets/perseus-admin-package/editor.css
