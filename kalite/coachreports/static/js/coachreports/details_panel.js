var eventData = { 
	page: 1,
  	totalPages: 2,
	questions: [
	{
		question: "1",
		anchor: "a",
		events: [
			{
				attempt: "1",
				action: "answered '10'",
				duration: "40 sec",			
				status: "incorrect"					
			},
			{
				attempt: "2",
				action: "answered '20'",
				duration: "45 sec",			
				status: "incorrect"
			},
			{
				attempt: "3",
				action: "used hint (3)",
				duration: "30 sec",			
				status: "incorrect"
			}
		]
	},
	{
		question: "2",
		anchor: "b",
		events: [
			{
				attempt: "1",
				action: "answered '5'",
				duration: "30 sec",			
				status: "incorrect"					
			},
			{
				attempt: "2",
				action: "answered '22'",
				duration: "20 sec",			
				status: "incorrect"
			},
			{
				attempt: "3",
				action: "used hint (0)",
				duration: "10 sec",			
				status: "correct"
			}
		]
	},
	{
		question: "3",
		anchor: "c",
		events: [
			{
				attempt: "1",
				action: "answered '25'",
				duration: "30 sec",			
				status: "incorrect"					
			},
			{
				attempt: "2",
				action: "answered '50'",
				duration: "10 sec",			
				status: "incorrect"
			},
			{
				attempt: "3",
				action: "answered '30'",
				duration: "20 sec",			
				status: "correct"
			}
		]
	},
	{
		question: "4",
		anchor: "d",
		events: [
			{
				attempt: "1",
				action: "answered '2'",
				duration: "25 sec",			
				status: "incorrect"					
			},
			{
				attempt: "2",
				action: "answered '0'",
				duration: "20 sec",			
				status: "incorrect"
			},
			{
				attempt: "3",
				action: "answered '4'",
				duration: "15 sec",			
				status: "correct"
			}
		]
	},
	{
		question: "5",
		anchor: "a",
		events: [
			{
				attempt: "1",
				action: "answered '5'",
				duration: "30 sec",			
				status: "incorrect"					
			},
			{
				attempt: "2",
				action: "answered '10'",
				duration: "25 sec",			
				status: "incorrect"
			},
			{
				attempt: "3",
				action: "answered '0'",
				duration: "30 sec",			
				status: "correct"
			}
		]
	},
	{	
		question: "6",
		anchor: "b",
		events: [
			{
				attempt: "1",
				action: "answered '45'",
				duration: "15 sec",			
				status: "incorrect"					
			},
			{
				attempt: "2",
				action: "answered '50'",
				duration: "30 sec",			
				status: "incorrect"
			},
			{
				attempt: "3",
				action: "answered '55'",
				duration: "20 sec",			
				status: "correct"
			}
		]
	},
	{		
		question: "7",
		anchor: "c",
		events: [
			{
				attempt: "1",
				action: "answered '133'",
				duration: "10 sec",			
				status: "incorrect"					
			},
			{
				attempt: "2",
				action: "answered '255'",
				duration: "50 sec",			
				status: "incorrect"
			},
			{
				attempt: "3",
				action: "answered '300'",
				duration: "10 sec",			
				status: "correct"
			}
		]
	},
	{		
		question: "8",
		anchor: "d",
		events: [
			{
				attempt: "1",
				action: "answered '14'",
				duration: "15 sec",			
				status: "incorrect"					
			},
			{
				attempt: "2",
				action: "answered '12'",
				duration: "30 sec",			
				status: "incorrect"
			},
			{
				attempt: "3",
				action: "answered '13'",
				duration: "20 sec",			
				status: "correct"
			}
		]
	}	
]};
		
var detailsPanelView = BaseView.extend({
	
	//Number of items to show from the collection
	limit: 4,
	
	template: HB.template("coach_nav/detailspanel"),
	
	initialize: function () {
		_.bindAll(this);
		eventData["pages"] = [];
		for (var i = 0; i < eventData.totalPages; i++) {
			eventData.pages.push(i+1);
		}; 
		this.render();
	},
	
	render: function() {
		this.$el.html(this.template(eventData));
		this.bodyView = new detailsPanelBodyView ({
			data: { questions: eventData.questions.slice(0, this.limit)},
			el: this.$(".body")
		});
	}
});


var detailsPanelBodyView = BaseView.extend({
	
	template: HB.template("coach_nav/detailspanelbody"),
	
	initialize: function (options) {
		_.bindAll(this);
		this.data = options.data;
		this.render();
	},
	
	render: function() {
		this.$el.html(this.template(this.data));
	}
});






