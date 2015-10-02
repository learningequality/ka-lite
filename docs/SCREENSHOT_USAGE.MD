WARNING: Read the following, but then read the section called "The thing about `click`" before using the screenshot directive.

Check out the ss_examples.rst file for some examples. The idea is to have a directive for specifying screenshots of the ka-lite web app that can be automagically updated in the case of UI changes or for building docs in different languages.

A screenshot directive has a number of required options
* `:user-role:` which can be one of `guest`, `learner`, `coach`, or `admin`, and determines what kind of user is logged in for the screenshot.
* `:url:` which is the relative URL to take the screenshot at (or start a sequence of navigation actions to get to the page to take the screenshot at). Don't use urls with UUIDs, as those are dependent on the database and we can't guarantee what will be in the database for screenshot purposes.
* `:navigation-steps:` which is a sequence of steps that needs to be taken.
   See the docstring of _parse_nav_steps in screenshot.py file for specification.
   If you find yourself writing the same sequence of nav steps over and over again, possibly with minor variations, then we can write an alias for it as for LOGIN.
* `:focus:` which will highlight an element specified by jQuery-style selector (by giving it a nice red border) and optionally add a floating annotation box. Works like this:
    :focus: the_selector | A nice little message that follows.
Just use arbitrary selection a la jQuery (so put a hash in front of IDs, etc). Whitespace can be included, e.g. `li a.classname`. Use the separator for annotations!


The thing about `click`
=======================
The :navigation-steps: option is meant to simulate user interaction for screenshots. Unfortunately, it can be dangerous!
Basically, if you use `click` on an element and want to use the *result* of the click, you can get into trouble if the result takes a long time.
For example, something like `#link_to_another_page click` that causes a page load is probably a mistake -- the directive doesn't know how long to wait for the page to load, and will probably throw an error.
Using `click` to interact with UI elements *on the same page* should be ok, as long as the result of interacting with the UI element happens really, really fast.
The rule of thumb is, if a `click` loads a page or waits for an AJAX result, think twice about using it.