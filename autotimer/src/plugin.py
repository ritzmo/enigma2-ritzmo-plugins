#
# Warning: This Plugin is WIP
#
# Later on this is meant to run automatically (in background)
#

# GUI (Screens)
from Screens.MessageBox import MessageBox

# Plugin
from AutoTimer import AutoTimer
from AutoPoller import autopoller

# Plugin definition
from Plugins.Plugin import PluginDescriptor

autotimer = None

# Autostart
def autostart(reason, session, **kwargs):
	global autotimer
	autotimer = AutoTimer(session)
	autopoller.start(autotimer)

# Mainfunction
def main(session, **kwargs):
	global autotimer
	if autotimer is None:
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
		PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart),
		PluginDescriptor(name="AutoTimer", description = "...", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main)
	]
