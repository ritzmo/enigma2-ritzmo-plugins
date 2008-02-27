from twisted.web.client import HTTPDownloader

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
