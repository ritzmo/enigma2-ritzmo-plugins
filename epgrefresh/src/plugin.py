#
# Warning: This Plugin is WIP
#

# Plugin
from EPGRefresh import epgrefresh
from EPGRefreshConfiguration import EPGRefreshConfiguration

# Plugin definition
from Plugins.Plugin import PluginDescriptor

from time import localtime, mktime

# Config
from Components.config import config, ConfigEnableDisable, ConfigInteger, ConfigSubsection, ConfigClock

now = [x for x in localtime()]
now[3] = 20
now[4] = 15
begin = mktime(now)
now[3] = 23
now[4] = 15
end = mktime(now)

config.plugins.epgrefresh = ConfigSubsection()
config.plugins.epgrefresh.enabled = ConfigEnableDisable(default = False)
config.plugins.epgrefresh.begin = ConfigClock(default = begin)
config.plugins.epgrefresh.end = ConfigClock(default = end)
config.plugins.epgrefresh.interval = ConfigInteger(default = 2, limits=(1, 10))
config.plugins.epgrefresh.inherit_autotimer = ConfigEnableDisable(default = False)

# Autostart
def autostart(reason, **kwargs):
	if config.plugins.epgrefresh.enabled.value and reason == 0:
		epgrefresh.start()
	elif reason == 1:
		epgrefresh.stop()

# Mainfunction
def main(session, **kwargs):
	epgrefresh.stop()
	session.openWithCallback(
		doneConfiguring,
		EPGRefreshConfiguration
	)

def doneConfiguring(**kwargs):
	if config.plugins.epgrefresh.enabled.value:
		epgrefresh.start()

def Plugins(**kwargs):
	return [
		PluginDescriptor(name="EPGRefresh", description = "Automated EPGRefresher", where = PluginDescriptor.WHERE_AUTOSTART, fnc = autostart),
		PluginDescriptor(name="EPGRefresh", description = "Automated EPGRefresher", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main)
	]