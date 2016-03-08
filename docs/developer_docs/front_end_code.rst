Front End Code
--------------

All of our front end code is written in Javascript, with much of it using `Backbone.js <http://backbonejs.org>`__ (and its dependencies `jQuery <https://jquery.com/>`_ and `Underscore.js <http://underscorejs.org>`_).

All new code, where possible, should be written using `Backbone.js <http://backbone.js>`__ to modularize functionality, and allow code to be reused across the site.

Inline Javascript (i.e. Javascript directly in the Django templates inside `<script>` tags) should be avoided except where absolutely necessary (such as to initialize some master object on a page).

For templating on the front end, we use `Handlebars.js <http://handlebarsjs.com/>`_ to render templates with a restricted set of statements and access to all variables passed into the template context.

Modularity
----------

In order to maintain modular code and be explicit about our dependencies, we use `Browserify <http://http://browserify.org/>`_ to build Javascript code into bundles for use on the client side.

To specify a bundle to be imported into the page, you need to create a 'bundle module' - this will be automatically detected by our Javascript build script, and be built into a bundle that can then be included as a script tag in a Django template.

'Bundle modules' are specified inside the static/js directory of a Django app - e.g. 'bundle modules' in distributed are under ``kalite/distributed/static/js/distributed/bundle_modules``. Here is a simple example of a bundle_module::

    var $ = require("base/jQuery");
    var TopicChannelRouter = require("topics/router");
    var Backbone = require("base/backbone");

    module.exports = {
        $: $,
        TopicChannelRouter: TopicChannelRouter,
        Backbone: Backbone
    }

This is the 'learn' bundle module (a file called learn.js in the above directory) - all it specifies is a set of top level objects that need to be exposed to be run within the context of the Django template (because we need Django template context variables to be passed into the Javascript) - here are the relevant ``<script>`` tags from the template::

    <script src="{% static 'js/distributed/bundles/bundle_learn.js' %}"></script>
    <script type="text/javascript">
        var bundle = require("learn");
        bundle.$(function() {
            window.channel_router = new bundle.TopicChannelRouter({default_channel: "{{ channel }}"})
            bundle.Backbone.history.start({pushState: true, root: "{% url 'learn' %}"});
        });
    </script>

Here, we ``require`` the learn bundle (all bundles can be referenced by their name in this way), and are then able to access the objects defined in its ``module.exports``.

For more information about using Browserify to handle dependencies, please refer to the `Browserify Handbook <https://github.com/substack/browserify-handbook>`_.

Building Frontend Code
----------------------

The build script uses `node.js <https://nodejs.org/>`_ - to run the build server for production simply run ``node compile_javascript.js``.

Alternatively, for development, running ``bin/kalite start`` with the ``--watch`` flag will automatically run the build process in watch mode, recompiling Javascript as it changes, on the fly.

If you prefer to run the compilation process separately, it has the following flags::

    --watch         Run in watch mode - automatically recompile Javascript when modules imported into bundles are changed (N.B. this will not detect new bundles being created.)
    --debug         Compile in debug mode - do not minify source code, and create source maps for easier client side debugging.
    --staticfiles   Saves built files directly to the static files dir, rather than into the original app directories - useful if collectstatic has already been run.

Implementing with Backbone
--------------------------

Most of our front end code uses only three kinds of objects, Backbone Models, Collections, and Views.

Backbone Models contain data that we use to render the page - in the case of a coach report, for example, this might be data about each student.

Backbone Collections are groups of Models - so you might have a Collection where each model represents the progress data for an individual student.

The Views define how this data is displayed in the browser, and also defines responses to user interaction to the current display.

Most Views also have an associated Handlebars template, which defines the HTML and how the data passed into the template is displayed in the rendered View.

Often the data contained in a Backbone Model can change while the user is still on the same page (for example, a student's total points can change while they are interacting with an exercise, so we want their displayed points to update whenever the 'points' attribute of the model updates too).

Here is an example of a Backbone View in KA Lite that does just that::

    var TotalPointView = Backbone.View.extend({

        initialize: function() {
            _.bindAll(this);
            this.listenTo(this.model, "change:points", this.render);
            this.render();
        },

        render: function() {

            var points = this.model.get("points");
            var message = null;

            // only display the points if they are greater than zero, and the user is logged in
            if (!this.model.get("is_logged_in")) {
                return;
            }

            message = sprintf(gettext("Points: %(points)d "), { points : points });

            this.$el.html(message);
            this.$el.show();
        }

    });

The ``initialize`` method is called whenever a new instance of ``TotalPointView`` is instantiated (by calling e.g. ``my_total_point_view = new TotalPointView({model: model})``). There are several arguments that will automatically get set on the view if passed in to the constructor, model is one of them. See the `Backbone.js <http://backbone.js>`_ for more details.

``_.bindAll(this);`` is included in many ``initialize`` methods we use, this helps to ensure that whenever a View method is called, then the ``this`` variable inside each method always refers to the view itself - without this, especially when methods are called due to being bound to events, the ``this`` variable can refer to something completely different.

``this.listenTo(this.model, "change:points", this.render);`` is an example of such an event binding. Here, the view is being told that whenever its model fires the event "change:points", then it should call its own render method (``this.render``). Backbone models fire "change" events whenever one of their attributes changes, and also a specific event like "change:points", which would only fire when the 'points' attribute of the model changes.

Finally ``this.render();`` calls the render method of the view. This method is generally reserved for creating and modifying DOM elements that we will insert into the page.

Inside the render function ``var points = this.model.get("points");`` locally defines the points - as you can see from this example, to access the attributes of a Backbone Model, the ``get("<attribute>")`` method is used.

The content to be rendered into the DOM in this instance is so simple that a Handlebars template is not used. Rather ``message = sprintf(gettext("Points: %(points)d "), { points : points });`` simply fills in the ``%(points)d`` with the 'points' attribute of the second argument of ``sprintf``. See the `sprintf docs <https://www.npmjs.com/package/sprintf-js>`_ for more information.

The part of the page that the view is scoped to can be refered to by ``this.$el`` - this is a jQuery object for the subsection of the DOM of the view, so any whole view operations (such as ``this.$el.html(message);`` or ``this.$el.show();``) will change the entire subsection of the DOM for that view (but will normally only be a subset of the DOM of the entire page). ``this.$el.html(message);`` sets the entire HTML content of the view DOM subsection to the content of the ``message`` variable, and ``this.$el.show();`` makes the DOM subsection visible.

Creating Your Own Backbone View
-------------------------------

To create a new Backbone View, you will either add to an existing Javascript file in the project, or create a new file. For example if you were to add a new View to the coachreports app you could create a file under ``kalite/coachreports/static/js/coachreports/hexagon_report.js``. Some boilerplate to start off with might look something like this::

    var HexagonReportView = BaseView.extend({

        template: HB.template("reports/hexagon-counting")

        initialize: function() {
            _.bindAll(this);
            this.listenTo(this.model, "change:number_of_hexagons", this.render);
            this.render();
        },

        render: function() {
            this.$el.html(this.template(this.model.attributes));
        }

    });

``this.$el.html(this.template(this.model.attributes));`` this line will insert all the attributes of the model into the template for rendering, and then set the HTML of the subsection of the DOM for the view to the resulting HTML.

For this to work, there must be a file ``kalite/coachreports/hbtemplates/reports/hexagon-counting.handlebars`` that contains the Handlebars.js template for this view. For a simple report, the template might look something like this::

    <div class="hexagon-report">
        <h3>{{_ "Hexagon Report" }}</h3>
        <p>{{_ "Current number of hexagons:" }}{{number_of_hexagons}}</p>
    </div>

To have this render in a particular Django template, both of the above files would need to be imported through ``<script>`` tags in the Django template. The relevant tags to add in this case would be::

    <script src="{% url 'handlebars_templates' module_name='reports' %}"></script>
    <script type="text/javascript" src="{% static 'js/coachreports/hexagon_report.js' %}"></script>

Note that for the Handlebars importing, only the folder name is necessary to be imported, not each individual template. It is also important that you do not place this script tag inside a Django-Compressor compress block.

Finally, to actually have this render on the page, we would need to have a Backbone Model that is able to fetch the data from an API endpoint on the server, and when the fetch is successfully completed, prompt the view to be created. Assuming we have a HexagonReportModel already defined, we could insert the following code into the template to initialize this report::

    <script>
        $(function(){
            window.hexagonReportModel = new window.HexagonReportModel();
            hexagonReportModel.fetch().then(function(){
                window.hexagonView = new HexagonReportView({
                    el: $("#student-report-container"),
                    model: hexagonReportModel
                });
            });
        });
    </script>

Line by line this means - ``$(function(){<code here>});`` wait for the browser to finish rendering the HTML before executing the code inside this function.
``window.hexagonReportModel = new window.HexagonReportModel();`` make a new instance of the HexagonReportModel.
``hexagonReportModel.fetch().then(function(){<code here>});`` get the data for this particular model from the server, and when that has finished, then execute the code inside the function.

::

    window.hexagonView = new HexagonReportView({
        el: $("#student-report-container"),
        model: hexagonReportModel
    });

make a new instance of the HexagonReportView. This will automatically call initialize and so the view will render. In addition, ``el: $("#student-report-container"),`` tells the view that it should set its subsection of the DOM to be the DOM element selected by ``$("#student-report-container")`` (i.e. the element with the id 'student-report-container'), and ``model: hexagonReportModel`` tells it to set its 'model' attribute to the hexagonReportModel we instantiated and fetch before.

TL;DR (or 7 quick steps to creating a Backbone View in KA Lite)
---------------------------------------------------------------

#. Find the appropriate app folder inside KA Lite - inside <folder>/static/js/<folder>/ either create a folder for your Backbone files, or find an existing one with a name that fits.
#. Inside this folder either create or open views.js.
#. To start creating a view, type: ``var MyViewNameView = BaseView.extend({});``
#. Define at least an ``initialize`` method, and a ``render`` method.
#. If you want a Handlebars template for your View, look inside <folder>/hbtemplates/ and either create a folder for your Handlebars templates, or find an existing one with a name that fits.
#. Inside this folder create a new file for your handlebars template ``mytemplatename.handlebars``.
#. Add this to your View definition code (inside the curly braces and don't forget commas to separate key/value pairs!): ``template: HB.template("<templatefolder>/mytemplatename")``.
