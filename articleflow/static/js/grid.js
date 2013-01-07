$(document).ready(function() {
    $('.datepicker').datepicker();

    $('#search-panel').on('hide', function() {;
	$('#search-collapse-toggle').html('[+] search');
    });
    
    $('#search-panel').on('show', function() {
	$('#search-collapse-toggle').html('[-] search');
    });
});