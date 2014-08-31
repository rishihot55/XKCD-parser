from bs4 import BeautifulSoup
import urllib
import os.path
import time
import re
res = urllib.urlopen('http://xkcd.com')
html = res.read()
soup = BeautifulSoup(html)
urls = soup.find_all('a',{'rel': re.compile('^prev$')})
comic = soup.find('div',id='comic').find('img')
url = comic.get('src')
type = url.split('.')[-1]
ref = urls[0].get('href')
curr = int(ref[1:-1]) + 1
for i in range(curr,0,-1):
	if (os.path.isfile('./'+str(i)+'.png') !=True):
		print "Downloading Comic No: "+str(i)
		res = urllib.urlopen('http://xkcd.com/'+str(i))
		html = res.read()
		soup = BeautifulSoup(html)
		comic = soup.find('div',id='comic').find('img')
		url = comic.get('src')
		type = url.split('.')[-1]
	if (os.path.isfile('./'+str(i)+'.'+type) !=True):
		print "Saved : "+str(i)+" "+url
		urllib.urlretrieve(url,str(i)+'.'+type)
		type = 'png'