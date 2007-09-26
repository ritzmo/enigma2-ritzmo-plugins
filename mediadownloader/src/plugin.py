#
# This is still WIP (although it works just fine)
# To be used as easy-to-use Downloading Application by other Plugins
#
# WARNING:
# Requires my plugin_viewer-Patch in its most recent version
#

# Needed for minFree
from os import statvfs

# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Screens.ChoiceBox import ChoiceBox

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Button import Button
from Components.FileList import FileList

# Generic
from Tools.BoundFunction import boundFunction

# Scanner-Interface
from Components.Scanner import Scanner, ScanPath, openFile

# Plugin
from Plugins.Plugin import PluginDescriptor

# Download
from HTTPProgressDownloader import HTTPProgressDownloaderSource, download

class LocationBox(Screen):
	"""Simple Class similar to MessageBox / ChoiceBox but used to choose a folder/pathname combination"""

	skin = """<screen name="LocationBox" position="100,130" size="540,340" >
			<widget name="text" position="0,2" size="540,22" font="Regular;22" />
			<widget name="filelist" position="0,25" size="540,235" />
			<widget name="target" position="0,260" size="540,40" valign="center" font="Regular;22" />
			<widget name="yellow" position="260,300" zPosition="1" size="140,40" pixmap="key_yellow-fs8.png" transparent="1" alphatest="on" />
			<widget name="key_yellow" position="260,300" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="green" position="400,300" zPosition="1" size="140,40" pixmap="key_green-fs8.png" transparent="1" alphatest="on" />
			<widget name="key_green" position="400,300" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, text = "", filename = "", currDir = "/", windowTitle = "Select Location", minFree = None):
		Screen.__init__(self, session)

		self["text"] = Label(text)
		self.text = text

		self.filename = filename
		self.minFree = minFree

		self.filelist = FileList(currDir, showDirectories = True, showFiles = False)
		self["filelist"] = self.filelist

		self["key_green"] = Button(_("Confirm"))
		self["key_yellow"] = Button(_("Rename"))

		self["green"] = Pixmap()
		self["yellow"] = Pixmap()

		self["target"] = Label()

		self["actions"] = ActionMap(["OkCancelActions", "DirectionsActions", "ColorActions"],
		{
			"ok": self.ok,
			"cancel": self.cancel,
			"green": self.select,
			"yellow": self.changeName,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
		})

		self.onShown.extend([
			boundFunction(self.setTitle, windowTitle),
			self.updateTarget,
			self.showHideRename
		])

	def showHideRename(self):
		if self.filename == "":
			self["yellow"].hide()
			self["key_yellow"].hide()

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
			self.updateTarget()

	def cancel(self):
		self.close(None)

	def selectConfirmed(self, res):
		if res: 
			self.close(''.join([self.filelist.getCurrentDirectory(), self.filename]))

	def select(self):
		# Do nothing unless current Directory is valid
		if self.filelist.getCurrentDirectory() is not None:
			# Check if we need to have a minimum of free Space available
			if self.minFree is not None:
				# Try to read fs stats
				try:
					s = statvfs(self.filelist.getCurrentDirectory())
					if (s.f_bavail * s.f_bsize) / 1000000 > self.minFree:
						# Automatically confirm if we have enough free disk Space available
						return self.selectConfirmed(True)
				except OSError:
					pass

				# Ask User if he really wants to select this folder
				self.session.openWithCallback(
					self.selectConfirmed,
					MessageBox,
					"There might not be enough Space on the selected Partition.\nDo you really want to continue?",
					type = MessageBox.TYPE_YESNO
				)
			# No minimum free Space means we can safely close
			else:   
				self.selectConfirmed(True)

	def changeName(self):
		if self.filename != "":
			# TODO: Add Information that changing extension is bad? disallow?
			# TODO: decide if using an inputbox is ok - we could also keep this in here
			self.session.openWithCallback(
				self.nameChanged,
				InputBox,
				text = self.filename
			)

	def nameChanged(self, res):
		# TODO: inform user when empty name was rejected?
		if res is not None and len(res):
			self.filename = res
			self.updateTarget()

	def updateTarget(self):
		if self.filelist.getCurrentDirectory() is not None:
			self["target"].setText(''.join([self.filelist.getCurrentDirectory(), self.filename]))
		else:
			self["target"].setText("Invalid Location")

	def __repr__(self):
		return str(type(self)) + "(" + self.text + ")"

class MediaDownloader(Screen):
	"""Simple Plugin which downloads a given file. If not targetfile is specified the user will be asked
	for a location (see LocationBox). If doOpen is True the Plugin will try to open it after downloading."""

	skin = """<screen name="MediaDownloader" position="100,150" size="540,60" >
			<widget name="wait" position="20,10" size="500,30" valign="center" font="Regular;23" />
			<widget source="progress" render="Progress" position="2,40" size="536,20" />
		</screen>"""

	def __init__(self, session, file, doOpen = False, downloadTo = None, callback = None):
		Screen.__init__(self, session)

		# Save arguments local
		self.file = file
		self.doOpen = doOpen
		self.filename = downloadTo
		self.callback = callback

		# Inform user about whats currently done
		self["wait"] = Label("Downloading...")
		self["progress"] = HTTPProgressDownloaderSource()

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

			self.session.openWithCallback(
				self.gotFilename,
				LocationBox,
				"Where to save?",
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
		# Fetch file
		download(self.file.path, self.filename, self["progress"].writeValues).addCallback(self.gotFile).addErrback(self.error)

	def gotFile(self, data = ""):
		# Try to open if we should
		if self.doOpen and not openFile(self.session, None, self.filename):
			self.session.open(
				MessageBox,
				"No suitable Viewer found!",
				type = MessageBox.TYPE_ERROR,
				timeout = 5
			)

		# Calback with Filename on success
		if self.callback is not None:
			self.callback(self.filename)

		self.close()

	def error(self):
		self.session.open(
			MessageBox,
			'\n'.join(["Error while downloading File:", self.file.path]),
			type = MessageBox.TYPE_ERROR,
			timeout = 3
		)

		# Calback with None on failure
		if self.callback is not None:
			self.callback(None)

		self.close()

def download_file(session, url, to = None, doOpen = False, callback = None, **kwargs):
	"""Provides a simple downloader Application"""
	file = ScanFile(url, autodetect = False)
	session.open(MediaDownloader, file, doOpen, to, callbck)

def filescan_chosen(open, session, item):
	if item:
		session.open(MediaDownloader, item[1], doOpen = open)

def filescan_open(open, items, session, **kwargs):
	"""Download a file from a given List"""
	Len = len(items)
	if Len > 1:
		# Create human-readable filenames
		choices = [
			(
				item.path[item.path.rfind("/")+1:].replace('%20', ' ').replace('%5F', '_').replace('%2D', '-'),
				item
			)
				for item in items
		]

		# And let the user choose one
		session.openWithCallback(
			boundFunction(filescan_chosen, open, session),
			ChoiceBox,
			"Which file do you want to download?",
			choices
		)
	elif Len:
		session.open(MediaDownloader, items[0], doOpen = open)

def filescan(**kwargs):
	# Overwrite checkFile to detect remote files
	class RemoteScanner(Scanner):
		def checkFile(self, file):
			return file.path.startswith("http://") or file.path.startswith("https://")

	return [
		RemoteScanner(
			mimetypes = None,
			paths_to_scan = 
				[
					ScanPath(path = "", with_subdirs = False),
				],
			name = "Download",
			description = "Download...",
			openfnc = boundFunction(filescan_open, False),
		),
		RemoteScanner(
			mimetypes = None,
			paths_to_scan =
				[
					ScanPath(path = "", with_subdirs = False),
				],
			name = "Download",
			description = "Download and open...",
			openfnc = boundFunction(filescan_open, True),
		)
	]

def Plugins(**kwargs):
	return [PluginDescriptor(name="MediaDownloader", where = PluginDescriptor.WHERE_FILESCAN, fnc = filescan)]
