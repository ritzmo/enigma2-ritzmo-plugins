#
# This is still WIP (although it works just fine)
# To be used as easy-to-use Downloading Application by other Plugins
#
# WARNING:
# Needs my plugin_viewer-Patch in its most recent version

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import InputBox

from Tools.BoundFunction import boundFunction

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Components.FileList import FileList

from Components.Scanner import Scanner, ScanPath, openFile

from Plugins.Plugin import PluginDescriptor

from twisted.web.client import downloadPage

class LocationBox(Screen):
	"""Simple Class similar to MessageBox / ChoiceBox but used to choose a folder"""

	skin = """<screen name="LocationBox" position="100,130" size="540,340" >
			<widget name="text" position="0,2" size="540,22" font="Regular;22" />
			<widget name="filelist" position="0,25" size="540,235" />
			<widget name="target" position="0,260" size="540,40" valign="center" font="Regular;22" />
			<ePixmap position="260,300" zPosition="1" size="140,40" pixmap="key_yellow-fs8.png" transparent="1" alphatest="on" />
			<widget name="key_yellow" position="260,300" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap position="400,300" zPosition="1" size="140,40" pixmap="key_green-fs8.png" transparent="1" alphatest="on" />
			<widget name="key_green" position="400,300" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, text = "", filename = "", currDir = "/", windowTitle = "Select Location"):
		Screen.__init__(self, session)

		self["text"] = Label(text)
		self.text = text

		self.filename = filename

		self.filelist = FileList(currDir, showDirectories = True, showFiles = False)
		self["filelist"] = self.filelist

		self["key_green"] = Button(_("Confirm"))
		self["key_yellow"] = Button(_("Rename"))

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

		self.onShown.append(boundFunction(self.setTitle, windowTitle))
		self.onShown.append(self.updateTarget)

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

	def select(self):
		if self.filelist.getCurrentDirectory is not None:
			self.close(''.join([self.filelist.getCurrentDirectory(), self.filename]))

	def changeName(self):
		if self.filename == "":
			self.session.open(
				MessageBox,
				"Changing the Filename is currently disabled.",
                                type = MessageBox.TYPE_INFO,
                                timeout = 5
			)
		else:	
			# TODO: Add Information that changing extension is bad?
			# TODO: decide if using an inputbox is ok - we could also keep this in here
			self.session.openWithCallback(
				self.nameChanged,
				InputBox,
				text = self.filename
			)

	def nameChanged(self, res):
		if res is not None:
			self.filename = res
			self.updateTarget()

	def updateTarget(self):
		if self.filelist.getCurrentDirectory is not None:
			self["target"].setText(''.join([self.filelist.getCurrentDirectory(), self.filename]))
		else:
			self["target"].setText("Invalid Location")


	def __repr__(self):
		return str(type(self)) + "(" + self.text + ")"

class MediaDownloader(Screen):
	"""Simple Plugin which downloads a given file. If not targetfile is specified the user will be asked
	for a location (see LocationBox). If doOpen is True the Plugin will try to open it after downloading."""

	skin = """<screen name="MediaDownloader" position="100,150" size="540,40" >
			<widget name="wait" position="20,10" size="500,30" valign="center" font="Regular;23" />
		</screen>"""

	def __init__(self, session, url, doOpen = False, downloadTo = None):
		Screen.__init__(self, session)

		self.url = url
		self.doOpen = doOpen
		self.filename = downloadTo

		self["wait"] = Label("Downloading...")

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
		downloadPage(self.url, self.filename).addCallback(self.gotFile).addErrback(self.error)

	def gotFile(self, data = ""):
		# Just close if we are not supposed to open this file
		if not self.doOpen:
			self.close()
			return None
		# Else try to view
		if not openFile(self.session, None, self.filename):
			self.session.open(
				MessageBox,
				"No suitable Viewer found!",
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
				item[item.rfind("/")+1:].replace('%20', ' ').replace('%5F', '_').replace('%2D', '-'),
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
			openfnc = boundFunction(filescan_open, False),
		),
		RemoteScanner(mimetypes = None,
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
