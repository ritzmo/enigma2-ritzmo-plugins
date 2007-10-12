#
# Warning: This Plugin is WIP
#
# Actually I wanted to implemented this as scheduled task
# but unfortunately I'm unable to zap non-mainwindow from outside
# enigma2 and eTimer's can't be run with dynamic length
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
