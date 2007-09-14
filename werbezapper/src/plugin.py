from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Plugins.Plugin import PluginDescriptor
from enigma import eTimer

class WerbeZapper:
	def __init__(self, session, servicelist):
		# Save Session&Servicelist
		self.session = session
		self.servicelist = servicelist

		# Create Timer
		self.zap_timer = eTimer()
		self.zap_timer.timeout.get().append(self.zap)

		# Initialize services
		self.zap_service = None
		self.move_service = None

	def showSelection(self):
		if self.zap_timer.isActive():
			# Disable Timer?
			self.session.openWithCallback(self.confirmStop, MessageBox, "Timer already running.\nStop it?")
		else:
			# Select Timer Length
			self.session.openWithCallback(self.conditionalConfirm, ChoiceBox, "When to Zap back?", [(' '.join([str(x), "Min"]), x) for x in range(1,10)])

	def confirmStop(self, result):
		if result:
			# Stop Timer
			self.zap_timer.stop()

			# Reset Vars
			self.zap_service = None
			self.move_service = None

	def conditionalConfirm(self, result):
		if result is not None:
			# Show Information to User, Save Service, Start Timer
			self.session.open(MessageBox, ' '.join(["Zapping back in", str(result[1]), "Minutes"]), type = MessageBox.TYPE_INFO, timeout = 3)

			# Keep playing and selected service as we might be playing a service not in servicelist
			self.zap_service = self.session.nav.getCurrentlyPlayingServiceReference()
			self.move_service = self.servicelist.getCurrentSelection()

			# Start Timer
			self.zap_timer.startLongTimer(result[1]*60)

	def zap(self):
		if self.zap_service is not None:
			# Check if we know where to move in Servicelist
			if self.move_service is not None:
				self.servicelist.setCurrentSelection(self.move_service)
				self.servicelist.zap()

			# Play zap_service if it is different from move_service
			if self.zap_service != self.move_service:
				# Play Service
				self.session.nav.playService(self.zap_service)

			# Reset services
			self.zap_service = None
			self.move_service = None

zapperInstance = None

def main(session, servicelist, **kwargs):
	# Create Instance if none present, show Dialog afterwards
	# TODO: do we really need to keep this instance?
	global zapperInstance
	if zapperInstance is None:
		zapperInstance = WerbeZapper(session, servicelist)
	zapperInstance.showSelection()

def Plugins(**kwargs):
 	return [ PluginDescriptor(name="Werbezapper", description="Automatically zaps back to current service after given Time", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main ) ]
