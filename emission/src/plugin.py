# -*- coding: utf-8 -*-

from Plugins.Plugin import PluginDescriptor
import EmissionOverview

def main(session, **kwargs):
	#reload(EmissionOverview)
	session.open(
		EmissionOverview.EmissionOverview
	)

def Plugins(**kwargs):
	return [
		PluginDescriptor(name = "e-mission", description = _("enigma2 frontend to transmission-daemon"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = main)
	]
