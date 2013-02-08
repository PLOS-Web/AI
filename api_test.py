import requests
import simplejson


print "should give invalid data"
data = {
    'test': 'this is a test'
}
r = requests.put('http://10.135.2.181:8000/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text


print "should give unable to parse"
r = requests.put('http://10.135.2.181:8000/api/article/pone.9999999', data='hahaha}')
print r.text


print "echo"
data = {
}
r = requests.put('http://10.135.2.181:8000/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "update pubdate: invalid date format"
data = {
    'pubdate': '2013-12-31 00:00:00'
}
r = requests.put('http://10.135.2.181:8000/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "update pubdate: success"
data = {
    'pubdate': '2013-12-31'
}
r = requests.put('http://10.135.2.181:8000/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "update state: nonexistant state"
data = {
    'state': 'lala',
}
r = requests.put('http://10.135.2.181:8000/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "update state: nonexistant state"
data = {
    'state': 'lala',
}
r = requests.put('http://10.135.2.181:8000/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "update state: success"
data = {
    'state': 'Ingested',
}
r = requests.put('http://10.135.2.181:8000/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "Shouldn't do anything"
data = {
}
r = requests.put('http://10.135.2.181:8000/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text

print "Shouldn't do anything"
data = {
    'state': 'New'
}
r = requests.put('http://10.135.2.181:8000/api/article/pone.9999999', data=simplejson.dumps(data))
print r.text
