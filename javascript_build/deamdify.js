/**
 * Module dependencies.
 */
var through = require('through')
  , esprima = require('esprima')
  , estraverse = require('estraverse')
  , path = require('path')
  , escodegen = require('escodegen')
  , util = require('util');


/**
 * Transform AMD to CommonJS.
 *
 * This transform translates AMD modules into CommonJS modules.  AMD modules
 * are defined by calling the `define` function that is available as a free
 * or global variable.  The transform translates that call into traditional
 * CommonJS require statements.  Any value returned from the factory function
 * is assigned to `module.exports`.
 *
 * After the transform is complete, Browserify will be able to parse and
 * bundle the module as if it were a Node.js module.
 *
 * @param {String} file
 * @return {Stream}
 * @api public
 */
module.exports = function (file) {
  var data = '';
  
  var stream = through(write, end);
  var ext = path.extname(file);
  return stream;
  
  function write(buf) { data += buf }
  function end() {
    var ast
      , tast
      , isAMD = false;

    if (ext.toLowerCase() === '.js') {
      try {
        ast = esprima.parse(data)
      } catch (error) {
        throw new Error('Error deamdifying ' + file + ': ' + error);
      }
    
    //console.log('-- ORIGINAL AST --');
    //console.log(util.inspect(ast, false, null));
    //console.log('------------------');
    
    // TODO: Ensure that define is a free variable.
    // TODO: Implement support for amdWeb UMD modules.
    
    estraverse.replace(ast, {
      enter: function(node) {
        if (isDefine(node)) {
          var parents = this.parents();
          
          // Check that this module is an AMD module, as evidenced by invoking
          // `define` at the top-level.  Any CommonJS or UMD modules are pass
          // through unmodified.
          if (parents.length == 2 && parents[0].type == 'Program' && parents[1].type == 'ExpressionStatement') {
            isAMD = true;
          }
        }
      },
      leave: function(node) {
        if (isDefine(node)) {
          if (node.arguments.length == 1 && node.arguments[0].type == 'FunctionExpression') {
            var factory = node.arguments[0];
            
            if (factory.params.length == 0) {
              tast = createProgram(factory.body.body);
              this.break();
            } else if (factory.params.length > 0) {
              // simplified CommonJS wrapper
              tast = createProgram(factory.body.body);
              this.break();
            }
          } else if (node.arguments.length == 1 && node.arguments[0].type == 'ObjectExpression') {
            // object literal
            var obj = node.arguments[0];
            
            tast = createModuleExport(obj);
            this.break();
          } else if (node.arguments.length == 2 && node.arguments[0].type == 'ArrayExpression' && node.arguments[1].type == 'FunctionExpression') {
            var dependencies = node.arguments[0]
              , factory = node.arguments[1];
            
            var ids = dependencies.elements.map(function(el) { return el.value });
            var vars = factory.params.map(function(el) { return el.name });
            var reqs = createRequires(ids, vars);
            if (reqs) {
              tast = createProgram([reqs].concat(factory.body.body));
            } else {
              tast = createProgram(factory.body.body);
            }
            this.break();
          } else if (node.arguments.length == 3 && node.arguments[0].type == 'Literal' && node.arguments[1].type == 'ArrayExpression' && node.arguments[2].type == 'FunctionExpression') {
            var dependencies = node.arguments[1]
              , factory = node.arguments[2];
            
            var ids = dependencies.elements.map(function(el) { return el.value });
            var vars = factory.params.map(function(el) { return el.name });
            var reqs = createRequires(ids, vars);
            if (reqs) {
              tast = createProgram([reqs].concat(factory.body.body));
            } else {
              tast = createProgram(factory.body.body);
            }
            this.break();
          }
        } else if (isReturn(node)) {
          var parents = this.parents();
          
          if (parents.length == 5 && isDefine(parents[2]) && isAMD) {
            return createModuleExport(node.argument);
          }
        }
      }
    });
    }
    
    if (!isAMD) {
      stream.queue(data);
      stream.queue(null);
      return;
    }
    
    tast = tast || ast;
    
    //console.log('-- TRANSFORMED AST --');
    //console.log(util.inspect(tast, false, null));
    //console.log('---------------------');
    
    var out = escodegen.generate(tast);
    stream.queue(out);
    stream.queue(null);
  }
};


function isDefine(node) {
  var callee = node.callee;
  return callee
    && node.type == 'CallExpression'
    && callee.type == 'Identifier'
    && callee.name == 'define'
  ;
}

function isReturn(node) {
  return node.type == 'ReturnStatement';
}

function createProgram(body) {
  return { type: 'Program',
    body: body };
}

function createRequires(ids, vars) {
  var decls = [];
  
  for (var i = 0, len = ids.length; i < len; ++i) {
    if (['require', 'module', 'exports'].indexOf(ids[i]) != -1) { continue; }
    
    decls.push({ type: 'VariableDeclarator',
      id: { type: 'Identifier', name: vars[i] },
      init: 
        { type: 'CallExpression',
          callee: { type: 'Identifier', name: 'require' },
          arguments: [ { type: 'Literal', value: ids[i] } ] } });
  }
  
  if (decls.length == 0) { return null; }
  
  return { type: 'VariableDeclaration',
    declarations: decls,
    kind: 'var' };
}

function createModuleExport(obj) {
  return { type: 'ExpressionStatement',
    expression: 
     { type: 'AssignmentExpression',
       operator: '=',
       left: 
        { type: 'MemberExpression',
          computed: false,
          object: { type: 'Identifier', name: 'module' },
          property: { type: 'Identifier', name: 'exports' } },
       right: obj } };
}
