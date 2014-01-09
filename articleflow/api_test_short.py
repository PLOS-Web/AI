import requests
import simplejson

#host_base = "http://10.135.2.181:8000"
host_base ="http://192.168.2.40:8000"

print "Should create article"
data = {
}
r = requests.put(host_base + '/api/article/pone.0000001', data=simplejson.dumps(data))
print r.text
