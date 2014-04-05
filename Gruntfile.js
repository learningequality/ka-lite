module.exports = function(grunt) {

  // Project configuration.
	grunt.initConfig({
		pkg: grunt.file.readJSON('package.json'), //To read the values of the package.json file

		jshint: {
			files: [
				'Gruntfile.js',
				'kalite/coachreports/static/js/coachreports/',
				'kalite/control_panel/static/js/control_panel/',
				'kalite/distributed/static/js/distributed/',
				'kalite/updates/static/js/updates/',
				'python-packages/securesync/static/js/securesync/'
			],
			// http://www.jshint.com/docs/options/
			options: {
				"-W038": false, // 'variable' used out of scope.
				"-W041": false, // Use '===' to compare with ''.
				"-W047": false, // A trailing decimal point can be confused with a dot
				"-W065": false, // Missing radix parameter.
				"-W088": false, // Creating global 'for' variable.
				"-W107": false, // Script URL.

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
				trailing: true, // Trailing whitespace.

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

	// Load the plugin that provides the "jshint" task.
	grunt.loadNpmTasks('grunt-contrib-jshint');

	// Default task(s).
	grunt.registerTask('default', ['jshint']);

};
