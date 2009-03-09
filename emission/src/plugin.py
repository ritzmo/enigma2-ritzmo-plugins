# -*- coding: utf-8 -*-

from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigText, \
	ConfigNumber, ConfigYesNo
import EmissionOverview

from transmission import transmission

config.plugins.emission = ConfigSubsection()
config.plugins.emission.hostname = ConfigText(default = "localhost", fixed_size = False)
config.plugins.emission.username = ConfigText(default = "", fixed_size = False)
config.plugins.emission.password = ConfigText(default = "", fixed_size = False)
config.plugins.emission.port = ConfigNumber(default = 9091)
config.plugins.emission.autodownload_from_simplerss = ConfigYesNo(default = False)

def simplerss_update_callback(id = None):
	try:
		from Plugins.Extensions.SimpleRSS.plugin import rssPoller
	except ImportError:
		pass # should not happen since the poller has to be active for us to be called :-)
	else:
		# we only check the "new items" feed currently since we do not keep track of the files we downloaded
		if id is None:
			client = None
			for item in rssPoller.newItemFeed.history:
				for file in item[3]:
					if file.mimetype == "application/x-bittorrent":
						if client is None:
							client = transmission.Client(
								address = config.plugins.emission.hostname.value,
								port = config.plugins.emission.port.value,
								user = config.plugins.emission.username.value,
								password = config.plugins.emission.password.value
							)
						# XXX: we might want to run this in the background cause this might block...
						client.add_url(file.path)

def simplerss_handle_callback(el):
	try:
		from Plugins.Extensions.SimpleRSS.RSSPoller import update_callbacks
	except ImportError:
		# XXX: we might want to handle this better than just ignoring it
		pass
	else:
		if el.value and simplerss_update_callback not in update_callbacks:
			update_callbacks.append(simplerss_update_callback)
		elif not el.value and simplerss_update_callback in update_callbacks:
			update_callbacks.remove(simplerss_update_callback)

config.plugins.emission.autodownload_from_simplerss.addNotifier(simplerss_handle_callback, immediate_feedback = False)

def main(session, **kwargs):
	reload(EmissionOverview)
	session.open(
		EmissionOverview.EmissionOverview
	)

def filescan_open(item, session, **kwargs):
	from Tools.Directories import fileExists

	transmission = transmission.Client(
		address = config.plugins.emission.hostname.value,
		port = config.plugins.emission.port.value,
		user = config.plugins.emission.username.value,
		password = config.plugins.emission.password.value
	)

	added = 0

	# XXX: keep track of erroneous torrents?
	for each in item:
		try:
			if transmission.add_url(each):
				added += 1
		except transmission.TransmissionError:
			pass

	from Screens.MessageBox import MessageBox

	session.open(
		MessageBox,
		_("%d Torrents(s) were scheduled for download.") % (added),
		type = MessageBox.TYPE_INFO,
		timeout = 5
	)

from mimetypes import add_type
add_type("application/x-bittorrent", ".tor")
add_type("application/x-bittorrent", ".torrent")

def filescan(**kwargs):
	from Components.Scanner import Scanner, ScanPath

	return [
		Scanner(
			mimetypes = ("application/x-bittorrent",),
			paths_to_scan =
				(
					ScanPath(path = "", with_subdirs = False),
				),
			name = "BitTorrrent Download",
			description = _("Download torrent..."),
			openfnc = filescan_open,
		)
	]

def Plugins(**kwargs):
	return [
		PluginDescriptor(name = "eMission", description = _("enigma2 frontend to transmission-daemon"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main),
		PluginDescriptor(name = "eMission...", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = main),
		PluginDescriptor(where = PluginDescriptor.WHERE_FILESCAN, fnc = filescan),
	]

