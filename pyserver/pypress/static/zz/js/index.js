

var IndexFunUtil = {};

IndexFunUtil.init = function() {
	this.init_data();
	this.init_event();
}

IndexFunUtil.init_event = function()  {
	$.afui.actionsheet(
	    [{
	        text: 'roger',
	        cssClasses: 'red',
	        click: function () {
	            alert("Clicked Back")
	        }
	    }, {
	        text: 'Alert Hi',
	        cssClasses: 'blue',
	        click: function () {
	            alert("Hi");
	        }
	    }, {
	        text: 'Alert Goodbye',
	        cssClasses: '',
	        click: function () {
	            alert("Goodbye");
	        }
	    }]
	);
}
IndexFunUtil.init_event = function() {
	//for tab click
	$('.tab').on('click', 'li', function(event) {
		event.preventDefault();

		var $that = $(this);

		$that.parent().find('.active').removeClass('active').end().end().addClass('active');
		$that.parent().next('.tab-content').find('.in').removeClass('in');
		$($that.children('a').data('href')).addClass('in');
	});
	
}
$(document).ready(function() {
	IndexFunUtil.init();
})