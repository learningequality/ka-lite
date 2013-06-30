(function () {
    var scatterPlot = function(config, element_id, data) {
        this.init(config, element_id, data);
    };

    scatterPlot.prototype.defaultClickFn = function(elem) {
        // provides a default click function (alert the text)
        alert(elem.data('text'));
    };

    scatterPlot.prototype.defaultHoverInFn = function(elem) {
        // provides a default hover function (show the text)
        var x = elem.getBBox().x,
            y = elem.getBBox().y;

        elem.attr('stroke', '#ccc');
        var text = this.r.text(
                elem.getBBox().x,
                elem.getBBox().y - this.config.text_width,
                elem.data('text'));

        if (x + text.getBBox().width < this.config.size) {
            text.attr('x',
                elem.getBBox().x + (text.getBBox().width / 2) - (this.config.text_width * 1));
        } else {
            text.attr('x',
                elem.getBBox().x - (text.getBBox().width / 2) + (this.config.text_width * 1));
        }

        if (y - text.getBBox().height - (this.config.text_width / 2) < 0) {
            text.attr('y',
                elem.getBBox().y + this.config.text_width + (2 * this.config.radius));
        }

        elem.data('hover', [
                this.r.rect(
                    text.getBBox().x - (this.config.text_width / 2),
                    text.getBBox().y - (this.config.text_width / 2),
                    text.getBBox().width + this.config.text_width,
                    text.getBBox().height + this.config.text_width
                ).attr('fill', "#fff").attr('fill-opacity', 0.7),
                text.toFront()
            ]);
    };

    scatterPlot.prototype.defaultHoverOutFn = function(elem) {
        // provides a default hover function (hide the text)
        elem.attr('stroke', '#333');
        var bits = elem.data('hover');
        elem.data('hover', []);
        for (var i = 0; i < bits.length; i++) {
            bits[i].remove();
        }
    };

    var SIZE = 400;
    scatterPlot.prototype.default_config = {
        size: SIZE,  // plot (i.e. plot area) height/width (square!)
        colours: [  // gradient colours
            ['#CF171F', 0],
            ['#F47721', 37.5],
            ['#FFC80B', 62.5],
            ['#C1D72E', 100]
        ],
        series_colours: ['#000', '#fff'],
        ticks: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  //ticks.. obv.
        xticks: [],
        yticks: [],
        x_label: "",  // x axis label
        y_label: "",  // y axis label
        clickFn: scatterPlot.prototype.defaultClickFn,  // click a point and...
        hoverInFn: scatterPlot.prototype.defaultHoverInFn,  // click a point and...
        hoverOutFn: scatterPlot.prototype.defaultHoverOutFn  // click a point and...
    };

    scatterPlot.prototype.getColours = function () {
        // converts our list to an SVG gradient string
        var result = "45-";
        var colours = this.config.colours;
        for (var ci = 0; ci < colours.length; ci++) {
            var datum = colours[ci];
            switch (ci) {
                case 0:
                    result += datum[0];
                    break;
                case colours.length:
                    result += "-" + datum[0];
                    break;
                default:
                    result += "-" + datum[0] + ":" + datum[1];
            }
        }
        return result;
    };

    scatterPlot.prototype.drawGrid = function() {
        // output the gradient and the lines
        var text_width = this.config.text_width,
            padding = this.config.padding,
            size = this.config.size,
            r = this.r;
            xtick_size = this.config.xtick_size,
            xticks = this.config.xticks,
            ytick_size = this.config.ytick_size,
            yticks = this.config.yticks;

        //gradient
        var background = r.rect(padding - text_width, text_width, size, size);
        background.attr('fill', this.getColours());
        var vpad = padding - text_width;
        r.path(  //axes / border
            "M" + (vpad) + "," + (text_width) +  // move to top
            "L" + (vpad) + "," + (size + text_width) +  // line to bottom
            "L" + (vpad + size) + "," + (size + text_width) +  // line to left
            "L" + (vpad + size) + "," + (text_width) +  // line to top
            "L" + (vpad) + "," + (text_width)  // line to right
        );

        // draw the tick lines
        for (var li in xticks) {
            var line = r.path(
                "M" + (vpad) + "," + (text_width + (xtick_size * li)) + 
                "L" + (vpad + size) + "," + (text_width + (xtick_size * li))
            ).attr("stroke-width", 0.5);
        };
        for (var li in yticks) {
            line = r.path(
                "M" + (vpad + (ytick_size * li)) + "," + (text_width) + 
                "L" + (vpad + (ytick_size * li)) + "," + (text_width + size)
            ).attr("stroke-width", 0.5);
        }
    };

    scatterPlot.prototype.drawLabels = function() {
        // add x, y axis labels and tick labels
        var text_width = this.config.text_width,
            padding = this.config.padding,
            size = this.config.size,
            xtick_size = this.config.xtick_size,
            xticks = this.config.xticks,
            ytick_size = this.config.ytick_size,
            yticks = this.config.yticks;
            r = this.r,
            x_label = this.config.x_label,
            y_label = this.config.y_label,
            xlabels = [],
            ylabels = [];

        // labels
        for (var xi in xticks) {
            if (xi > 0.0) {
                xlabels.push(
                    r.text(
                        text_width + padding + (xi * xtick_size) - (2 * text_width),
                        (2 * text_width) + size,
                        xi));
            }
        }
        for (var yi in yticks) {
            if (yi > 0.0) {
                ylabels.push(
                    r.text(
                        padding - (2 * text_width),
                        size - (ytick_size * yi) + text_width,
                        yi));
            }
        }
        console.log(xlabels);
        console.log(ylabels);
        // origin
        r.text(padding - (2 * text_width), size + (2 * text_width), 0)

        // x axis label
        var xl = r.text(
            padding - text_width + (size / 2),
            size + (padding - text_width),
            x_label);
        // y axis label
        var yl = r.text(
            text_width,
            text_width + (size / 2),
            y_label);
        yl.rotate(-90);
    };

    scatterPlot.prototype.makeDots = function (data) {
        // update dots on plot (not massively efficient)
        // data sould be a dict of list of lists:
        // data = {
        //  'series 1': [[x1,y1,t1],...],
        //  ...
        //}
        var text_width = this.config.text_width,
            padding = this.config.padding,
            size = this.config.size,
            xtick_size = this.config.xtick_size,
            xticks = this.config.xticks,
            ytick_size = this.config.ytick_size,
            yticks = this.config.yticks;
            r = this.r,
            radius = this.config.radius,
            clickFn = this.config.clickFn,
            hoverInFn = this.config.hoverInFn,
            hoverOutFn = this.config.hoverOutFn,
            self = this,
            series_colours = this.config.series_colours;

        // remove old ones...
        var len = this.points.length;
        for (var i = 0; i < len; i++) {
            var point = this.points.pop()
            point.remove();
        }
        // add new ones...
        var count = 0;
        for (i in data) {
            var series = data[i];
            for (var j = 0; j < series.length; j++) {
                var datum = series[j];
                var x = datum[0];
                var y = datum[1];
                var t = datum[2];
                var dot = r.circle(
                    padding - text_width + (x * xtick_size),
                    size + text_width - (y * ytick_size),
                    radius)
                    .attr('stroke', '#555')
                    .attr('fill', series_colours[count])
                    .click(function() { clickFn(this) })
                    .hover(
                        function() {hoverInFn.call(self, this)},
                        function() {hoverOutFn.call(self, this)});
                for (key in t) {
                    dot.data(key, t[key]);
                }
                this.points.push(dot);
            }
            count++;
        }
    };

    scatterPlot.prototype.showLegend = function(data) {
        var text_width = this.config.text_width,
            padding = this.config.padding,
            size = this.config.size,
            xtick_size = this.config.xtick_size,
            xticks = this.config.xticks,
            ytick_size = this.config.ytick_size,
            yticks = this.config.yticks;
            r = this.r,
            radius = this.config.radius,
            series_colours = this.config.series_colours;

        var count = 0;
        var last_rhs = 0;
        for (key in data) {
            var dot = r.circle(
                last_rhs + padding + text_width,
                size + (text_width * 4),
                radius)
                .attr('fill', series_colours[count]);
            var text = r.text(dot.getBBox().x, dot.getBBox().y + radius, key);
            text.attr('x', dot.getBBox().x + text.getBBox().width / 2 + (2 * radius) + text_width);
            count++;
            last_rhs = text.getBBox().x + text.getBBox().width + text_width;
        }
    }

    scatterPlot.prototype.init = function(config, element_id, data) {
        var self = this;
        this.points = [];

        // update config with custom config
        this.config = {};
        for (var key in this.default_config) {
            if (config[key] !== undefined) {
                this.config[key] = config[key];
            } else {
                this.config[key] = this.default_config[key];
            }
        }

        var size = this.config.size;
        //how far apart are the ticks?
        console.log(this.config.xticks);
        this.config.xticks = this.config.xticks ? this.config.xticks : this.config.ticks;
        this.config.yticks = this.config.yticks ? this.config.yticks : this.config.ticks;
        this.config.xtick_size = size / ((this.config.xticks[1]-this.config.xticks[0])*(this.config.xticks.length - 1));
        this.config.ytick_size = size / ((this.config.yticks[1]-this.config.yticks[0])*(this.config.yticks.length - 1));
        // how much LHS/Bottom extra do we need for axes etc?
        this.config.padding = size / 10;
        // the dot size
        this.config.radius = size / 100;
        //hm, bit rough, but really height/width of chars.
        this.config.text_width = this.config.padding / 4;
        
        var _getLegendHeight = function() {
            return self.config.text_width * 2;
        }

        var size = this.config.size,
            padding = this.config.padding;

        this.r = Raphael(element_id, size + (2 * padding), size + padding + _getLegendHeight());
        this.drawLabels();
        this.drawGrid();
        this.showLegend(data);
        this.makeDots(data);
    };

    window.scatterPlot = scatterPlot;
})()
