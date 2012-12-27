function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


function switch_status_ajax(issue_pk, issue_id_base, new_status, target_url){
    var status_icon = $('#' + issue_id_base + issue_pk);
    var status_control = $('#' + 'issue-status-control-' + issue_pk);

    console.log('status_icon: ' + status_icon);
    var postData = {
	'issue_pk': issue_pk,
	'status': new_status
    };
    console.log(postData);
    $.ajax({
	url: target_url,
	type: 'POST',
	datatype: "application/json; charset=utf-8",
	data: postData
    }).done(function (returnedData){
	var valid_statuses = [1,2,3];
        if (valid_statuses.indexOf(returnedData['status']) >= 0){
	    console.log("valid status: " + returnedData['status']);
	    for (i in valid_statuses){
                console.log('issue-status-' + valid_statuses[i]);
                status_icon.removeClass('issue-status-' + valid_statuses[i]);
	    }
	    status_icon.addClass('issue-status-' + returnedData.status);
	    status_control.html(returnedData['issue-status-control']);
        }
    }).error(function (errorMsg){
        console.log(errorMsg);
    });
}

