#
# To be used as easy-to-use Downloading Application by other Plugins
#
# WARNING:
# Requires my plugin_viewer-Patch in its most recent version
#

# GUI (Screens)
from Screens.ChoiceBox import ChoiceBox
from MediaDownloader import MediaDownloader

# Generic
from Tools.BoundFunction import boundFunction

# Scanner-Interface
from Components.Scanner import Scanner, ScanPath

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Download a single File
def download_file(session, url, to = None, askOpen = False, callback = None, **kwargs):
	"""Provides a simple downloader Application"""
	file = ScanFile(url, autodetect = False)
	session.open(MediaDownloader, file, askOpen, to, callbck)

# Item chosen
def filescan_chosen(session, item):
	if item:
		session.open(MediaDownloader, item[1], askOpen = True)

# Open as FileScanner
def filescan_open(items, session, **kwargs):
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
			boundFunction(filescan_chosen, session),
			ChoiceBox,
			"Which file do you want to download?",
			choices
		)
	elif Len:
		session.open(MediaDownloader, items[0], doOpen = open)

# Return Scanner provided by this Plugin
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
			openfnc = filescan_open,
		)
	]

def Plugins(**kwargs):
	return [PluginDescriptor(name="MediaDownloader", where = PluginDescriptor.WHERE_FILESCAN, fnc = filescan)]
