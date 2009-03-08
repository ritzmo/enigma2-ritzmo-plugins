# -*- coding: utf-8 -*-

from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigText, ConfigNumber
import EmissionOverview

config.plugins.emission = ConfigSubsection()
config.plugins.emission.hostname = ConfigText(default = "localhost", fixed_size = False)
config.plugins.emission.username = ConfigText(default = "", fixed_size = False)
config.plugins.emission.password = ConfigText(default = "", fixed_size = False)
config.plugins.emission.port = ConfigNumber(default = 9091)

def main(session, **kwargs):
	#reload(EmissionOverview)
	session.open(
		EmissionOverview.EmissionOverview
	)

def Plugins(**kwargs):
	return [
		PluginDescriptor(name = "e-mission", description = _("enigma2 frontend to transmission-daemon"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = main)
	]

