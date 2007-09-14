from Plugins.Plugin import PluginDescriptor

from MountManager import MountManager
from Mounts import mounts

def autostart(reason, **kwargs):
	# Automount on start
	if reason == 0:
		mounts.mount()
	# We could umount on shutdown, but this is done by the system anyway

def main(session, **kwargs):
	session.open(MountManager)

def menu(menuid, **kwargs):
	if menuid == "network":
		return [("Mount Manager", main)]
	return [ ]

def Plugins(**kwargs):
	return [PluginDescriptor(name="Mount Manager", where = PluginDescriptor.WHERE_AUTOSTART, fnc=autostart),
		PluginDescriptor(name="Mount Manager", description="Manage your network mounts", where = PluginDescriptor.WHERE_SETUP, fnc=menu)]
