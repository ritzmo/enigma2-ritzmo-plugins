#
# Warning: This Plugin is WIP
#
# Later on this is meant to run automatically (in background)
#

# GUI (Screens)
from Screens.MessageBox import MessageBox

# Plugin
from AutoTimer import AutoTimer

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Mainfunction
def main(session, **kwargs):
	autotimer = AutoTimer(session)
	ret = autotimer.parseEPG()
	session.open(
		MessageBox,
		"Found a total of %d matching Events.\n%d were new and scheduled for recording." % (ret[0] + ret[1], ret[0]),
		type = MessageBox.TYPE_INFO,
		timeout = 5
	)

def Plugins(**kwargs):
	return [
        PluginDescriptor(name="AutoTimer", description = "...", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main)
    ]
