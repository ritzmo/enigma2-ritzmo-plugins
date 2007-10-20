#
# Warning: This Plugin is WIP
#

# Plugin
from EPGRefresh import epgrefresh

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Config
from Components.config import config, ConfigEnableDisable, ConfigInteger, ConfigSubsection

config.plugins.epgrefresh = ConfigSubsection()
config.plugins.epgrefresh.enabled = ConfigEnableDisable(default = False)
config.plugins.epgrefresh.interval = ConfigInteger(default = 2, limits=(1, 10))
config.plugins.epgrefresh.inherit_autotimer = ConfigEnableDisable(default = False)

# Mainfunction
def main(session, **kwargs):
	epgrefresh.refresh()

def Plugins(**kwargs):
	return [
		PluginDescriptor(name="EPGRefresh", description = "Automated EPGRefresher", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main)
	]