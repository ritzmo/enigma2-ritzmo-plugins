from twisted.web.client import HTTPDownloader
from twisted.internet import reactor

from urlparse import urlparse, urlunparse
from base64 import encodestring

class HTTPProgressDownloader(HTTPDownloader): 
	"""Download to a file and keep track of progress."""

	def __init__(self, url, fileOrName, writeProgress = None, *args, **kwargs):
		HTTPDownloader.__init__(self, url, fileOrName, *args, **kwargs)

		# Save callback locally
		self.writeProgress = writeProgress

		# Initialize
		self.currentlength = 0
		self.totallength = None

	def gotHeaders(self, headers):
		# If we have a callback and 'OK' from Server try to get length
		if self.writeProgress and self.status == '200':
			if headers.has_key('content-length'):
				self.totallength = int(headers['content-length'][0])
				self.writeProgress(0, self.totallength)

		return HTTPDownloader.gotHeaders(self, headers)

	def pagePart(self, data):
		# If we have a callback and 'OK' from server increment pos
		if self.writeProgress and self.status == '200':
			self.currentlength += len(data)
			self.writeProgress(self.currentlength, self.totallength)

		return HTTPDownloader.pagePart(self, data)

def _parse(url, defaultPort=None):
	url = url.strip()
	parsed = urlparse(url)
	scheme = parsed[0]
	path = urlunparse(('','')+parsed[2:])
	if defaultPort is None:
		if scheme == 'https':
			defaultPort = 443
		elif scheme == 'ftp':
			defaultPort = 21
		else:
			defaultPort = 80
	host, port = parsed[1], defaultPort
	if '@' in host:
		username, host = host.split('@')
		if ':' in username:
			username, password = username.split(':')
		else:
			password = ""
	else:
		username = ""
		password = ""
	if ':' in host:
		host, port = host.split(':')
		port = int(port)
	if path == "":
		path = "/"
	return scheme, host, port, path, username, password

def download(url, file, writeProgress=None, contextFactory=None, *args, **kwargs):
	"""Download a web page to a file but provide current-/total-length.

	@param file: path to file on filesystem, or file-like object.
	@param writeProgress: function which takes two arguments (pos, length)

	See HTTPDownloader to see what extra args can be passed.
	"""

	scheme, host, port, path, username, password = _parse(url)	

	if scheme == 'ftp':
		from FTPProgressDownloader import FTPProgressDownloader

		if not (username and password):
			username = 'anonymous'
			password = 'my@email.com'

		client = FTPProgressDownloader(host, port, path, file, username, password, writeProgress, *args, **kwargs)
		return client.deferred

	if username and password:
		# twisted will crash if we don't rewrite this ;-)
		url = scheme + '://' + host + ':' + str(port) + path

		basicAuth = encodestring("%s:%s" % (username, password))
		authHeader = "Basic " + basicAuth.strip()
		AuthHeaders = {"Authorization": authHeader}

		if kwargs.has_key("headers"):
			kwargs["headers"].update(AuthHeaders)
		else:
			kwargs["headers"] = AuthHeaders

	factory = HTTPProgressDownloader(url, file, writeProgress, *args, **kwargs)
	if scheme == 'https':
		from twisted.internet import ssl
		if contextFactory == None :
			contextFactory = ssl.ClientContextFactory()
		reactor.connectSSL(host, port, factory, contextFactory)
	else:
		reactor.connectTCP(host, port, factory)

	return factory.deferred
