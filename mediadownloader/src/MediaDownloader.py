# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Label import Label

# Download
from VariableProgressSource import VariableProgressSource

class MediaDownloader(Screen):
	"""Simple Plugin which downloads a given file. If not targetfile is specified the user will be asked
	for a location (see LocationBox). If doOpen is True the Plugin will try to open it after downloading."""

	skin = """<screen name="MediaDownloader" position="100,150" size="540,60" >
			<widget name="wait" position="20,10" size="500,30" valign="center" font="Regular;23" />
			<widget source="progress" render="Progress" position="2,40" size="536,20" />
		</screen>"""

	def __init__(self, session, file, askOpen = False, downloadTo = None, callback = None):
		Screen.__init__(self, session)

		# Save arguments local
		self.file = file
		self.askOpen = askOpen
		self.filename = downloadTo
		self.callback = callback

		# Inform user about whats currently done
		self["wait"] = Label(_("Downloading..."))
		self["progress"] = VariableProgressSource()

		# Set Limit if we know it already (Server might not tell it)
		if self.file.size:
			self["progress"].writeValues(0, self.file.size*1048576)

		# Call getFilename as soon as we are able to open a new screen
		self.onExecBegin.append(self.getFilename)

	def getFilename(self):
		self.onExecBegin.remove(self.getFilename)

		# If we have a filename (downloadTo provided) start fetching
		if self.filename is not None:
			self.fetchFile()
		# Else open LocationBox to determine where to save
		else:
			# TODO: determine basename without os.path?
			from os import path
			from Screens.LocationBox import LocationBox

			self.session.openWithCallback(
				self.gotFilename,
				LocationBox,
				_("Where to save?"),
				path.basename(self.file.path),
				minFree = self.file.size
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
		from HTTPProgressDownloader import download

		# Fetch file
		download(self.file.path, self.filename, self["progress"].writeValues).addCallback(self.gotFile).addErrback(self.error)

	def openCallback(self, res):
		from Components.Scanner import openFile

		# Try to open file if res was True
		if res and not openFile(self.session, None, self.filename):
			self.session.open(
				MessageBox,
				_("No suitable Viewer found!"),
				type = MessageBox.TYPE_ERROR,
				timeout = 5
			)

		# Calback with Filename on success
		if self.callback is not None:
			self.callback(self.filename)

		self.close()

	def gotFile(self, data = ""):
		# Ask if file should be opened unless told not to
		if self.askOpen:
			self.session.openWithCallback(
				self.openCallback,
				MessageBox,
				_("Do you want to try to open the downloaded file?"),
				type = MessageBox.TYPE_YESNO
			)
		# Otherwise callback and close
		else:
			# Calback with Filename on success
			if self.callback is not None:
				self.callback(self.filename)

				self.close()

	def error(self):
		self.session.open(
			MessageBox,
			_("Error while downloading file %s") % (self.file.path),
			type = MessageBox.TYPE_ERROR,
			timeout = 3
		)

		# Calback with None on failure
		if self.callback is not None:
			self.callback(None)

		self.close()
