# Guide to front end development

## Our stack

The current stack uses bootstrap as a front end framework, LESS for the stylesheets (compiled to CSS with grunt.js). Don't worry, we'll explain everything down here.

### Bootstrap

[Bootstrap](http://getbootstrap.com/2.3.2/) is a front end framework that has a [grid system](http://getbootstrap.com/2.3.2/scaffolding.html) and multiple [CSS elements](http://getbootstrap.com/2.3.2/base-css.html)(buttons, forms...) and [advanced components](http://getbootstrap.com/2.3.2/components.html). We'll try to reuse these elements as much as possible. They have already been optimized to run on all the browsers.


### LESS

We're currently using [LESS](http://lesscss.org/) as a CSS preprocessor. LESS is a stylesheet languages that allows us to use variables, mixins (functions that process variables) and operations.
The [documentation](http://lesscss.org/) is short and gives really great examples on these different concepts.

The structure of the code is the following:

- `style.less` includes:
	- `fonts.less`: Font dependencies and declarations.
	- `mixins.less`: Functions in less to simplify the development (button generator...)
	- `variables.less`: Colors of the layout and other variables 
	- `style_with_bootstrap.less`: Stylesheet of the whole design (except landing page). It contains a lot of reusable parts like buttons, lists and tables.
	- `landing_page.less`: Stylesheet of the landing page


`style_with_bootstrap.less` is the page where you put your changes. `mixins.less` and `variables.less` are helpers to make the code cleaner and create reusable part(Don't Repeat Yourself).

## Workflow

### Development

Now that you understand all the individual components of the stack let's dive into the workflow.

1. The first things to do is to put the `local_settings.py` in debug mode (`DEBUG=True`). In this mode, the browser (client-side with less.js) will compile the LESS files into CSS. 

2. Edit the the HTML/LESS files. You can directly edit the less files. Indeed, I have added `less.watch();` in the base.html, the browser will reload the page each time you save your less files(Oh yeah!).

3. When you're happy with your changes, don't forget to check if existing colors (check the `variable.less` file) or parts (buttons, lists, tables...) exit. If you're using a method/variable more than 2 times, please add a variable or a mixin.

```
//variable.less

@pink: #ff69b4;
```
```
//mixins.less

.content-tree-background (@url) {
  margin-top: 2px;
  background: url(@url) no-repeat;
}
```

When you're using borders, transparency and gradients, look at `less/bootstrap/mixins.less` file. This is already coded to work with all the browsers.

```
//style_with_bootstrap.less

.round-border{
	.border-radius(10px);
}
```


### Production with Grunt.js

[Grunt.js](http://gruntjs.com/) is a tool to run tasks on the terminal. The current default task includes compiling the less files to css and compressing them. 

#### How to install

First, install the [Node.js package manager (npm)](http://nodejs.org/download/).


Then, you have to run these commands in the directory where package.json is.

```
npm install
npm install -g grunt-cli
```

#### Compile with grunt


```
grunt #Compiles everything
grunt less:compile #Compiles style.less
grunt less:bootstrap #Compiles bootstrap.less+responsive.less
```

The CSS is compiled in the `static/css` folder. If you want to make those changes available to production, you need to commit them.
