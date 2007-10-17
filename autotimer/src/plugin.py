#
# Warning: This Plugin is WIP
#
# TODO: Add Configuration (See GraphMultiEPG for Handling Services)
#

# GUI (Screens)
from Screens.MessageBox import MessageBox
from AutoScreens import AutoTimerOverview

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

	# Do not run in background while editing, this might screw things up
	if autopoller.shouldRun:
		autopoller.stop()

	session.openWithCallback(
		editCallback,
		AutoTimerOverview,
		autotimer
	)

def editCallback(session):
	global autotimer

	if autopoller.shouldRun:
		autopoller.start(autotimer, initial = False)

	# Don't do anything when editing was canceled
	if session is None:
		return

	# We might re-parse Xml so catch parsing error
	try:
		ret = autotimer.parseEPG()
		session.open(
			MessageBox,
			"Found a total of %d matching Events.\n%d were new and scheduled for recording." % (ret[0] + ret[1], ret[0]),
			type = MessageBox.TYPE_INFO,
			timeout = 10
		)
	except ExpatError, ee:
		session.open(
			MessageBox,
			"Your config file is not well-formed.\nError parsing in line: %s" % (ee.lineno),
			type = MessageBox.TYPE_ERROR,
			timeout = 10
		)
	except:
		# Don't crash during development
		import traceback, sys
		traceback.print_exc(file=sys.stdout)

def Plugins(**kwargs):
	return [
		PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart),
		PluginDescriptor(name="AutoTimer", description = "Edit Timers and scan for new Events", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main)
	]
