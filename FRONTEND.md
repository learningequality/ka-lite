# Guide to front end development

## Our stack

The current stack uses bootstrap as a front end framework, LESS for the stylesheets (compiled to CSS with grunt.js). Don't worry, we'll explain everything down here.

### Bootstrap

[Bootstrap](http://getbootstrap.com/2.3.2/) is a front end framework that has a [grid system](http://getbootstrap.com/2.3.2/scaffolding.html) and multiple [CSS elements](http://getbootstrap.com/2.3.2/base-css.html)(buttons, forms...) and [advanced components](http://getbootstrap.com/2.3.2/components.html). We'll try to reuse these elements as much as possible. They have already been optimized to run on all the browsers.

### LESS

We're currently using [LESS](http://lesscss.org/) as a CSS preprocessor. LESS is a stylesheet languages that allows us to use variables, mixins (functions that process variables) and operations.
The [documentation](http://lesscss.org/) is short and gives really great examples on these different concepts.

The structure of the code is the following:


- style.less includes:
	- fonts.less: Font dependencies and declarations.
	- mixins.less: Functions in less to simplify the development (button generator...)
	- variables.less: Color of the layout and other variables 
	- style_with_bootstrap.less: Stylesheet of the whole design

Bootstrap also has the same structure, but you don't have to touch it.

### Grunt.js

[Grunt.js](http://gruntjs.com/) is a front-end tool to compile to run task on the terminal. The current tasks include compiling the less files to css and compressing them. 

#### How to install

You have to run these commands in the directory where package.json is.

```
npm install grunt --save-dev
npm install
```

#### Compile with grunt


```
//Compiles everything
grunt

//Compiles style.less
grunt less:compile

//Compiles bootstrap.less+responsive.less
grunt less:bootstrap
```


## Workflow

Now that you understand all the individual components of the stack let's dive into the workflow.

1. The first things to do is to put the local_settings into debug mode. In this mode, the client will compile the LESS files into CSS. 
2. You'll gain a lot of time if you edit the style of an element dynamically. You can use the Debugger Tool of your browser or add `#!watch` to the url and the browser will reload the page each time you save your less files(Oh yeah!).
3. When you're happy with your changes, you can simply paste the CSS code to the style_with_bootstrap.less file. If you're using existing colors you should check the variable.less files, they're already defined there. If the color is new and you're going to use it more than one time, add it to the variable.less file. 

```
//variable.less

@pink: #ff69b4;
```

When you're using borders, transparency and gradients, look at `less/bootstrap/mixins.less` file. This is already coded to work with all the browsers.

```
//style_with_bootstrap.less
.round-border{
	.border-radius(10px);
}
```

When you're happy with your changes, compile them with grunt!

