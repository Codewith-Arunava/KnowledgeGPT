import urllib.request
import json
import urllib.error

data = json.dumps({'name':'Test User 8000', 'email':'test8000@example.com', 'password':'password123'}).encode('utf-8')
req = urllib.request.Request('http://localhost:8000/api/v1/auth/register', data=data, headers={'Content-Type': 'application/json'})

try:
    print(urllib.request.urlopen(req).read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.read().decode('utf-8'))
