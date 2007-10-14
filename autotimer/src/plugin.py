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

autotimer = None

# Autostart
def autostart(reason, session, **kwargs):
	global autotimer

	# Don't crash on faulty XML
	try:
		autotimer = AutoTimer(session)
	except ExpatError, ee:
		pass

	autopoller.start(autotimer)

# Mainfunction
def main(session, **kwargs):
	global autotimer
	if autotimer is None:
		autotimer = AutoTimer(session)

	# Re-parse XML
	try:
		autotimer.parseXML()
	except ExpatError, ee:
		session.open(
			MessageBox,
			"Your config file is unparsable.",
			type = MessageBox.TYPE_ERROR,
			timeout = 5
		)
		return
		
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
