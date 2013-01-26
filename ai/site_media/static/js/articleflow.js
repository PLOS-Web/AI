function switch_article_state_ajax(article_pk, requested_transition_pk, error_msg_id, target_url){
    var postData = {
	'article_pk': article_pk,
	'requested_transition_pk': requested_transition_pk,
    };
    
    $.ajax({
	url: target_url,
	type: 'POST',
	datatype: "application/json; charset=utf-8",
	data: postData
    }).done(function (returnedData){
	console.log(returnedData.error);
	
	if (returnedData.error) {
	    alert(returnedData['error']);
	} 
	
	else if (returnedData.open_item_error){
	    alert("Can't do that while there are open items that need action:\n\t" + returnedData.open_item_error.open_issues + " open issues\n\t" + returnedData.open_item_error.open_errors + " open errors." );
	} else {
	    document.location.href = returnedData.redirect_url
	}
	
    });
}

$(document).ready(function(){
    $('#article-note-form').on('hide', function(){
	$('#article-note-collapse-toggle').html('[+]');
    });
    
    $('#article-note-form').on('show', function(){
	$('#article-note-collapse-toggle').html('[-]');
    });
});
