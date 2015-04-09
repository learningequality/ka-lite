Front End Code
--------------

All of our front end code is written in Javascript, with much of it using `Backbone.js <http://backbonejs.org>`_ (and its dependencies `jQuery <https://jquery.com/>`_ and `Underscore.js <http://underscorejs.org>`_).

All new code, where possible, should be written using `Backbone.js <http://backbone.js>`_ to modularize functionality, and allow code to be reused across the site.

Inline Javascript (i.e. Javascript directly in the Django templates inside `<script>` tags) should be avoided except where absolutely necessary (such as to initialize some master object on a page).

For templating on the front end, we use `Handlebars.js <http://handlebarsjs.com/>`_ to render templates with a restricted set of statements and access to all variables passed into the template context.

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

Note that for the Handlebars importing, only the folder name is necessary to be imported, not each individual template.

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