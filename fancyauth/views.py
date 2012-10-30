from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

def loginajax(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if request.is_ajax():
            if form.is_valid():
                user = authenticate(username = request.POST['username'],password = request.POST['password'])
                if user is not None:
                    login(request, user)
                    return HttpResponse('True')
                else:
                    return HttpResponse('False')      
            else:
                return HttpResponse(form.errors)
        else:
            if form.is_valid():
                user = authenticate(username = request.POST['username'],password = request.POST['password'])
                if user is not None:
                    login(request,user)

    else:
        form = AuthenticationForm(request)

    return render_to_response(
        'fancyauth/login_ajax.html',
        {
            "form": form
            },
        context_instance=RequestContext(request)
        )
        
def logoutajax(request):
    logout(request)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('home')))
    
