import requests
import simplejson

#host_base = "http://10.135.2.181:8000"
host_base ="http://192.168.2.40:8000"

print "should give invalid data"
data = {
    'test': 'this is a test'
}
r = requests.put(host_base + '/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text


print "should give unable to parse"
r = requests.put(host_base + '/api/article/pone.9999999', data='hahaha}')
print r.text


print "echo"
data = {
    'si_guid': '4AQlP4lP0xGaDAMF6CwzAQ',
    'md5': '79054025255fb1a26e4bc422aef54eb4'
}
r = requests.put(host_base + '/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "update pubdate: invalid date format"
data = {
    'pubdate': '2013-12-31 00:00:00'
}
r = requests.put(host_base + '/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "update pubdate: success"
data = {
    'pubdate': '2013-12-31'
}
r = requests.put(host_base + '/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "update state: nonexistant state"
data = {
    'state': 'lala',
}
r = requests.put(host_base + '/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "update state: nonexistant state"
data = {
    'state': 'lala',
}
r = requests.put(host_base + '/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "update state: success"
data = {
    'state': 'Ingested',
}
r = requests.put(host_base + '/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "Shouldn't do anything"
data = {
}
r = requests.put(host_base + '/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "Should complain about a fake user"
data = {
    'state': 'Delivered',
    'state_change_user': 'fake_user',
}
r = requests.put(host_base + '/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "Should reset article to new effected by jlabarba"
data = {
    'state': 'New',
    'state_change_user': 'jlabarba',
}
r = requests.put(host_base + '/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text


##### PUT errorset tests #####
print "Errorset PUT"
data = {
    'source': 'ariesPull',
    'errors': 'error: stuff\nerror: other stuff\nwarning: a warning'
}

r = requests.put(host_base + '/api/article/pone.9999999/errorset/', data=simplejson.dumps(data))
print r.text


##### POST transition tests #####
print "Put article into transitionable state"
data = {
    'state': 'Delivered',
}
r = requests.put(host_base + '/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "transition POST: fake transition name"
data = {
    'name': 'not a transition',
    'transition_user': 'jlabarba',
}
r = requests.post(host_base + '/api/article/pone.9999999/transition/', data=simplejson.dumps(data))
print r.text

print "transition POST: fake user name"
data = {
    'name': 'not a transition',
    'transition_user': 'not a user',
}
r = requests.post(host_base + '/api/article/pone.9999999/transition/', data=simplejson.dumps(data))
print r.text

print "transition GET: ingest"
r = requests.get(host_base + '/api/article/pone.9999999/transition/')
print r.text

print "transition POST: ingest"
data = {
    'name': 'Ingest',
    'transition_user': 'jlabarba',
}

r = requests.post(host_base + '/api/article/pone.9999999/transition/', data=simplejson.dumps(data))
print r.text
