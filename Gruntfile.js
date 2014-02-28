module.exports = function(grunt) {

  // Project configuration.
	grunt.initConfig({
		pkg: grunt.file.readJSON('package.json'), //To read the values of the package.json file
		
		less: {
			compile: {
				options: {
					paths:["./kalite/static/less"], //Directory to check for @imports
					yuicompress: true,
					strictImports: true //Force evaluation of imports.
				},
				files: {
					"./kalite/static/css/style.css": "./kalite/static/less/style.less",
				},

			},
			
			bootstrap: {
				options: {
					paths:["./kalite/static/less/bootstrap"],
					yuicompress: true,
					strictImports: true //Force evaluation of imports.
				},
				files: {
					"./kalite/static/css/bootstrap/bootstrap.css": "./kalite/static/less/bootstrap/bootstrap.less",
					"./kalite/static/css/bootstrap/responsive.css": "./kalite/static/less/bootstrap/responsive.less"
				},
			}
		},
		jshint: {
			files: [
				'Gruntfile.js',
				'kalite/static/js/coachreports/',
				'kalite/static/js/securesync/',
				'kalite/static/js/updates/',
				'kalite/static/js/exercises.js',
				'kalite/static/js/khan-lite.js',
				'kalite/static/js/kmap-editor.js',
				'kalite/static/js/search_autocomplete.js',
				'kalite/static/js/videoplayer.js'
			],
			// http://www.jshint.com/docs/options/
			options: {
				"-W018": false, // Confusing use of '!'.
				"-W032": false, // Unnecessary semicolon.
				"-W038": false, // 'variable' used out of scope.
				"-W041": false, // Use '===' to compare with ''.
				"-W047": false, // A trailing decimal point can be confused with a dot
				"-W065": false, // Missing radix parameter.
				"-W070": false, // Extra comma. (it breaks older versions of IE)
				"-W088": false, // Creating global 'for' variable.

				// Enforcing options
				bitwise: true, // Unexpected use of '&'.
				//curly: true, // Expected '{' and instead saw 'variable'.
				//eqeqeq: true, // Expected '===' and instead saw '=='.
				es3: true, // 'feature' is available in ECMAScript > 3
				//forin: true, // The body of a for in should be wrapped in an if statement to filter unwanted properties from the prototype.
				freeze: true, // Extending prototype of native object: 'Object'.
				immed: true, // Function declarations are not invocable. Wrap the whole function invocation in parens.
				//latedef: 'nofunc', // 'variable' was used before it was defined.
				noarg: true, // Avoid arguments.callee.
				noempty: true, // Empty block.
				nonbsp: true, // "non-breaking whitespace" character
				nonew: true, // Do not use 'new' for side effects.
				//undef: true, // 'variable' is not defined.
				//unused: true, // 'variable' is defined but never used.
				//strict: true, // Missing "use strict" statement.
				//trailing: true, // Trailing whitespace.

				// Relaxing options
				asi: true, // Missing semicolon.
				shadow: true, // 'variable' is already defined.
				sub: true, // ['property'] is better written in dot notation.

				// Environments
				browser: true,
				jquery: true,
				globals: {
					'_': true,
					Exercises: true,
					Khan: true,
					gettext: true,
					sprintf: true
				}
			}
		}
	});

	// Load the plugin that provides the "less" task.
	grunt.loadNpmTasks('grunt-contrib-less');

	// Load the plugin that provides the "jshint" task.
	grunt.loadNpmTasks('grunt-contrib-jshint');

	// Default task(s).
	grunt.registerTask('default', ['less']);

};
