"""
This is the future main module for kalite settings, where all fundamental and
common django setttings should go.

However, since we are still supporting an old location of settings, we have not
put anything here.


...yet
"""
import warnings

# We do not care about the deprecation warning when this module has been
# imported because then people are probably doing things correctly

warnings.filterwarnings('ignore', message=r'.*Wrong settings module imported.*', append=True)

from kalite.settings import *  # @UnusedWildImport

SOUTH_MIGRATION_MODULES = {
    'tastypie': 'tastypie.south_migrations',
}

# Default welcome message
KALITE_WELCOME_MESSAGE = """
<h2>Need help?</h2>
<p>KA Lite is community-driven and relies on help and experience which you can both share and receive in our community.</p>
<br>
<h4>Offline help: </h4>
<ul>
  <li>Use the "Docs" button in the top menu to get help.</li>
</ul>
<h4>Online help: </h4>
<ul>
  <li>Share your implementation of KA Lite on the map and find other KA Lite users in your country
  <a href='https://learningequality.org/ka-lite/map/' target='_blank'>https://learningequality.org/ka-lite/map/</a>
  (Click on "Add your story!")</li>
  <li>Give and receive KA Lite support in the Learning Equality community 
  <a href='http://community.learningequality.org/' target='_blank'>http://community.learningequality.org/</a></li>
  <li>Help program KA Lite at GitHub 
  <a href='http://github.com/learningequality/ka-lite/' target='_blank'>http://github.com/learningequality/ka-lite/</a></li>
  <li>Sign up for emails about new releases <a href='https://groups.google.com/a/learningequality.org/forum/#!forum/dev' target='_blank'>
  https://groups.google.com/a/learningequality.org/forum/#!forum/dev</a></li>
</ul>
"""
