from twisted.internet import reactor, defer
from twisted.internet.protocol import Protocol, ClientCreator
from twisted.protocols.ftp import FTPClient, FTPFileListProtocol

class FTPProgressDownloader(Protocol):
	"""Download to a file from FTP and keep track of progress."""

	def __init__(self, host, port, path, fileOrName, username = 'anonymous', \
		password = 'my@email.com', writeProgress = None, *args, **kwargs):

		# TODO: fix forcing passv here
		passive_ftp = True
		timeout = 30

		# We need this later
		self.path = path

		# Initialize
		self.currentlength = 0
		self.totallength = None
		self.writeProgress = writeProgress

		# Output
		if isinstance(fileOrName, str):
			self.filename = fileOrName
			self.file = None
		else:
			self.file = fileOrName

		creator = ClientCreator(reactor, FTPClient, username, password, passive = passive_ftp)

		creator.connectTCP(host, port, timeout).addCallback(self.controlConnectionMade).addErrback(self.connectionFailed)

		self.deferred = defer.Deferred()

	def controlConnectionMade(self, ftpclient):
		# We need the client locally
		self.ftpclient = ftpclient

		# Try to fetch filesize
		self.ftpFetchSize()

	# Handle recieved msg
	def sizeRcvd(self, msgs):
		# Split up return
		code, msg = msgs[0].split()
		if code == '213':
			self.totallength = int(msg)
			if self.writeProgress is not None:
				self.writeProgress(0, self.totallength)

			# We know the size, so start fetching
			self.ftpFetchFile()
		else:
			# Error while reading size, try to list it
			self.ftpFetchList()

	def ftpFetchSize(self):
		d = self.ftpclient.queueStringCommand('SIZE ' + self.path)
		d.addCallback(self.sizeRcvd).addErrback(self.ftpFetchList)
		#d.arm()

	# Handle recieved msg
	def listRcvd(self):
		# Quit if file not found
		if not len(self.filelist.files):
				self.connectionFailed()
				return

		self.totallength = self.filelist.files[0]['size']
		if self.writeProgress is not None:
			self.writeProgress(0, self.totallength)

		# Invalidate list
		self.filelist = None

		# We know the size, so start fetching
		self.ftpFetchFile()

	def ftpFetchList(self):
		self.filelist = FTPFileListProtocol()
		d = self.ftpclient.list(self.path, self.filelist)
		d.addCallback(self.listRcvd).addErrback(self.connectionFailed)
		#d.arm()

	def openFile(self):
		# TODO: implement offset/resume
		return open(self.filename, 'w')

	def ftpFetchFile(self):
		# Finally open file
		if self.file is None:
			try:
				self.file = self.openFile()
			except IOError, ie:
				# TODO: handle exception
				raise ie

		d = self.ftpclient.retrieveFile(self.path, self)
		d.addCallback(self.ftpFinish).addErrback(self.connectionFailed)
		#d.arm()

	def dataReceived(self, data):
		if not self.file:
			return

		if self.writeProgress is not None:
			self.currentlength += len(data)
			self.writeProgress(self.currentlength, self.totallength)
		try:
			self.file.write(data)
		except IOError, ie:
			# TODO: handle exception
			self.file = None
			raise ie

	def ftpFinish(self, code = 0, message = None):
		self.ftpclient.quit()
		if self.file is not None:
			self.file.close()
		self.deferred.callback(code)

	def connectionFailed(self, reason = None):
		if self.file is not None:
			self.file.close()
		self.deferred.errback(reason)
