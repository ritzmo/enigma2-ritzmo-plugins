# -*- coding: utf-8 -*-

from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigText, ConfigNumber
import EmissionOverview

from transmission import transmission

config.plugins.emission = ConfigSubsection()
config.plugins.emission.hostname = ConfigText(default = "localhost", fixed_size = False)
config.plugins.emission.username = ConfigText(default = "", fixed_size = False)
config.plugins.emission.password = ConfigText(default = "", fixed_size = False)
config.plugins.emission.port = ConfigNumber(default = 9091)

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

