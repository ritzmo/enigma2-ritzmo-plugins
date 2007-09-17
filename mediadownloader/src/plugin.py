from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.FileList import FileList

from mimetypes import guess_type

from Plugins.Plugin import PluginDescriptor

class LocationBox(Screen):
	"""Simple Class similar to MessageBox / ChoiceBox but used to choose a folder"""

	# TODO: add usage
	skin = """<screen name="LocationBox" position="100,150" size="540,260" >
			<widget name="text" position="0,2" size="540,22" font="Regular;22" />
			<widget name="filelist" position="0,25" size="540,235" />
		</screen>"""

	def __init__(self, session, text, filename, currDir = "/"):
		Screen.__init__(self, session)

		self["text"] = Label(text)
		self.text = text

		self.filename = filename

		self.filelist = FileList(currDir, showDirectories = True, showFiles = False)
		self["filelist"] = self.filelist

		self["actions"] = ActionMap(["OkCancelActions", "DirectionsActions", "ColorActions"],
		{
			"ok": self.ok,
			"cancel": self.cancel,
			"green": self.select,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
		})

	def up(self):
		self["filelist"].up()

	def down(self):
		self["filelist"].down()

	def left(self):
		self["filelist"].pageUp()

	def right(self):
		self["filelist"].pageDown()

	def ok(self):
		if self.filelist.canDescent():
			self.filelist.descent()

	def cancel(self):
		self.close(None)

	def select(self):
		self.close('/'.join([self.filelist.getCurrentDirectory(), self.filename]))

	def __repr__(self):
		return str(type(self)) + "(" + self.text + ")"

class MediaDownloader(Screen):
	"""Simple Plugin which downloads a given file. If not targetfile is specified the user will be asked
	for a location (see LocationBox). If doOpen is True the Plugin will try to open it after downloading."""

	skin = """<screen name="MediaDownloader" position="100,150" size="540,60" >
			<widget name="wait" position="20,10" size="500,25" font="Regular;23" />
		</screen>"""

	def __init__(self, session, url, doOpen = False, downloadTo = None):
		Screen.__init__(self, session)

		self.url = url
		(self.mimetype, _) = guess_type(url)
		self.doOpen = doOpen
		self.filename = downloadTo

		self["wait"] = Label(_("Downloading..."))

		# Call getFilename as soon as we are able to open a new screen
		self.onExecBegin.append(self.getFilename)

	def getFilename(self):
		self.onExecBegin.remove(self.getFilename)

		# If we have a filename (downloadTo provided) start fetching
		if self.filename is not None:
			self.fetchFile()
		# Else open LocationBox to determine where to save
		else:
			from os import path

			self.session.openWithCallback(
				self.gotFilename,
				LocationBox,
				"Where to save?",
				path.basename(self.url)
			)

	def gotFilename(self, res):
		# If we got a filename try to fetch file
		if res is not None:
			self.filename = res
			self.fetchFile()
		# Else close
		else:
			self.close()

	def fetchFile(self):
		# Fetch file
		from twisted.web.client import downloadPage
		downloadPage(self.url, self.filename).addCallback(self.gotFile).addErrback(self.error)

	def gotFile(self, data = ""):
		# Just close if we are not supposed to open this file
		if not self.doOpen:
			self.close()
			return None
		# Else try to view
		try:
			from Plugins.Extensions.MediaScanner.plugin import openFile
			if not openFile(self.session, self.mimetype, self.filename):
				self.session.open(
					MessageBox,
					"No suitable Viewer found!",
					type = MessageBox.TYPE_ERROR,
					timeout = 5
				)
		except ImportError, ie:
			self.session.open(
				MessageBox,
				"Please install MediaScanner Plugin to view Enclosures!",
				type = MessageBox.TYPE_ERROR,
				timeout = 5
			)
		except Exception, e:
			print e
			self.session.open(
				MessageBox,
				"An unexcpected Error occured.",
				type = MessageBox.TYPE_ERROR,
				timeout = 5
			)
		self.close()

	def error(self):
		self.session.open(
			MessageBox,
			' '.join(["Error while downloading File:", self.url]),
			type = MessageBox.TYPE_ERROR,
			timeout = 3
		)
		self.close()

def download_file(session, url, to = None, doOpen = False, **kwargs):
	"""Provides a simple downloader Application"""
	session.open(MediaDownloader, url, doOpen, to)

def filescan_open(list, session, **kwargs):
	"""Download a file and open it afterwards"""
	session.open(MediaDownloader, list[0], doOpen = True)

def filescan_save(list, session, **kwargs):
	"""Download a file"""
	session.open(MediaDownloader, list[0], doOpen = False)

def filescan(**kwargs):
	# we expect not to be called if the MediaScanner plugin is not available,
	# thus we don't catch an ImportError exception here
	from Plugins.Extensions.MediaScanner.plugin import Scanner, ScanPath

	# Overwrite checkFile to detect remote files
	class RemoteScanner(Scanner):
		def checkFile(self, filename):
			return filename.startswith("http://") or filename.startswith("https://")

	return [
		RemoteScanner(mimetypes = None,
			paths_to_scan = 
				[
					ScanPath(path = "", with_subdirs = False),
				],
			name = "Download",
			description = "Download...",
			openfnc = filescan_save,
		),
		RemoteScanner(mimetypes = None,
			paths_to_scan =
				[
					ScanPath(path = "", with_subdirs = False),
				],
			name = "Download",
			description = "Download and open...",
			openfnc = filescan_open,
		)
	]

def Plugins(**kwargs):
	return [PluginDescriptor(name="MediaDownloader", where = PluginDescriptor.WHERE_FILESCAN, fnc = filescan)]
