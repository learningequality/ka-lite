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
				yuicompress: true,
				strictImports: true
			}
		}
	});

	// Load the plugin that provides the "less" task.
	grunt.loadNpmTasks('grunt-contrib-less');

	// Default task(s).
	grunt.registerTask('default', ['less']);

};