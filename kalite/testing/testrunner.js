var testCount = 0;

var qunitTest = QUnit.test;

QUnit.test = window.test = function() {
  testCount += 1;
  qunitTest.apply(this, arguments);
  console.log(testCount);
};

QUnit.begin(function(args) {
  args.totalTests = testCount;
});