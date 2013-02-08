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
    'doi': 'pone.0000001'
}
r = requests.put('http://10.135.2.181:8000/api/article/', data=simplejson.dumps(data))
print r.text
