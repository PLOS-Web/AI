$(document).ready(function() {
    $('.datepicker').datepicker();

    $('#search-panel').on('hide', function() {;
	$('#search-collapse-toggle').html('[+] search');
    });
    
    $('#search-panel').on('show', function() {
	$('#search-collapse-toggle').html('[-] search');
    });

    $('.grid-header').hover(
	function() {
	    $(this).find(".order-arrow-inactive").fadeIn();
	},
	function() {
	    $(this).find(".order-arrow-inactive").fadeOut();
	}
    );
});
