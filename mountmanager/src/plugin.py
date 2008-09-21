# Autostart
def autostart(reason, **kwargs):
	from Mounts import mounts

	# Automount on start
	if reason == 0:
		mounts.mount()
	else:
		mounts.umount()

# Mainfunction
def main(session, **kwargs):
	from MountManager import MountManager
	session.open(MountManager)

# Menu
def menu(menuid, **kwargs):
	if menuid == "network":
		return [("Mount Manager", main, "mount_manager", None)]
	return []

# Plugin definitions
def Plugins(**kwargs):
	from Plugins.Plugin import PluginDescriptor
	return [
			PluginDescriptor(name="Mount Manager", where = PluginDescriptor.WHERE_AUTOSTART, fnc=autostart),
			PluginDescriptor(name="Mount Manager", description="Manage your network mounts", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main)
	]
