#
# Warning: This Plugin is WIP
#
# Later on this is meant to run automatically (in background)
#

# Plugin
from AutoTimer import AutoTimer

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Mainfunction
def main(session, **kwargs):
	AutoTimer(session)

def Plugins(**kwargs):
	return [
        PluginDescriptor(name="AutoTimer", description = "...", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main)
    ]
