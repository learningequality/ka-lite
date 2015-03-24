var testCount = 0;

var qunitTest = QUnit.test;

QUnit.test = window.test = function() {
  testCount += 1;
  qunitTest.apply(this, arguments);
};

$(function(){
    QUnit.begin(function(args) {
      args.totalTests = testCount;
    });
});