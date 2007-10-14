#
# Warning: This Plugin is WIP
#
# TODO: Add Configuration (See GraphMultiEPG for Handling Services)
#

# GUI (Screens)
from Screens.MessageBox import MessageBox

# Plugin
from AutoTimer import AutoTimer
from AutoPoller import autopoller

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# ExpatError
from xml.parsers.expat import ExpatError

autotimer = None

# Autostart
def autostart(reason, session, **kwargs):
	global autotimer

	# Initialize AutoTimer
	autotimer = AutoTimer(session)

	# Start Poller
	autopoller.start(autotimer)

# Mainfunction
def main(session, **kwargs):
	global autotimer
	if autotimer is None:
		autotimer = AutoTimer(session)

	# We might re-parse Xml so catch parsing error
	try:
		ret = autotimer.parseEPG()
		session.open(
			MessageBox,
			"Found a total of %d matching Events.\n%d were new and scheduled for recording." % (ret[0] + ret[1], ret[0]),
			type = MessageBox.TYPE_INFO,
			timeout = 5
		)
	except ExpatError, ee:
		session.open(
			MessageBox,
			"Your config file is not well-formed.\nError parsing in line: %s" % (ee.lineno),
			type = MessageBox.TYPE_ERROR,
			timeout = 5
		)

def Plugins(**kwargs):
	return [
		PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart),
		PluginDescriptor(name="AutoTimer", description = "...", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main)
	]
