import requests
import simplejson


print "should give invalid data"
data = {
    'test': 'this is a test'
}
r = requests.put('http://10.135.2.181:8000/api/article/', data=simplejson.dumps(data))
print r.text


print "should give unable to parse"
r = requests.put('http://10.135.2.181:8000/api/article/', data='hahaha}')
print r.text


print "echo"
data = {
    'doi': 'pone.9999999'
}
r = requests.put('http://10.135.2.181:8000/api/article/', data=simplejson.dumps(data))
print r.text

print "update pubdate: invalid date format"
data = {
    'doi': 'pone.9999999',
    'pubdate': '2013-12-31 00:00:00'
}
r = requests.put('http://10.135.2.181:8000/api/article/', data=simplejson.dumps(data))
print r.text

print "update pubdate: success"
data = {
    'doi': 'pone.9999999',
    'pubdate': '2013-12-31'
}
r = requests.put('http://10.135.2.181:8000/api/article/', data=simplejson.dumps(data))
print r.text

print "update state: nonexistant state"
data = {
    'doi': 'pone.9999999',
    'state': 'lala',
}
r = requests.put('http://10.135.2.181:8000/api/article/', data=simplejson.dumps(data))
print r.text

print "update state: nonexistant state"
data = {
    'doi': 'pone.9999999',
    'state': 'lala',
}
r = requests.put('http://10.135.2.181:8000/api/article/', data=simplejson.dumps(data))
print r.text

print "update state: success"
data = {
    'doi': 'pone.9999999',
    'state': 'Ingested',
}
r = requests.put('http://10.135.2.181:8000/api/article/', data=simplejson.dumps(data))
print r.text

print "Shouldn't do anything"
data = {
    'doi': 'pone.9999999',
}
r = requests.put('http://10.135.2.181:8000/api/article/', data=simplejson.dumps(data))
print r.text

print "Shouldn't do anything"
data = {
    'doi': 'pone.9999999',
    'state': 'New'
}
r = requests.put('http://10.135.2.181:8000/api/article/', data=simplejson.dumps(data))
print r.text
