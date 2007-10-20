#
# Warning: This Plugin is WIP
#


# Plugin
from EPGRefresh import epgrefresh

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Mainfunction
def main(session, **kwargs):
	epgrefresh.refresh()

def Plugins(**kwargs):
	return [
		PluginDescriptor(name="EPGRefresh", description = "...", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main)
	]
