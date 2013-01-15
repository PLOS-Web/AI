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
	if returnedData.error{
	    error_msg_obj.html(returnedData.error);
	} else if returnedData.open_item_error{
	    error_msg_obj.html("Can't advance state, theres still " + returnedData.open_item_error.open_issues + " open issues and " + returnedData.open_item_error.open_errors + " open errors." );
	} else {
	    document.location.href = returnedData.redirect_url
	}
    });
}
