# Plugin
from Plugins.Plugin import PluginDescriptor

# GUI (Screen)
from MountManager import MountManager

# Mounts
from Mounts import mounts

# Autostart
def autostart(reason, **kwargs):
	# Automount on start
	if reason == 0:
		mounts.mount()
	# We could umount on shutdown, but this is done by the system anyway

# Mainfunction
def main(session, **kwargs):
	session.open(MountManager)

# Menu
def menu(menuid, **kwargs):
	if menuid == "network":
		return [("Mount Manager", main, "mount_manager", None)]
	return []

# Plugin definitions
def Plugins(**kwargs):
	return [
			PluginDescriptor(name="Mount Manager", where = PluginDescriptor.WHERE_AUTOSTART, fnc=autostart),
			PluginDescriptor(name="Mount Manager", description="Manage your network mounts", where = PluginDescriptor.WHERE_MENU, fnc=menu)
	]
