# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button
from AutoTimerList import AutoTimerPreviewList

class AutoTimerPreview(Screen):
	"""Preview Timers which would be set"""

	skin = """<screen name="AutoTimerPreview" title="Preview AutoTimer" position="75,155" size="565,265">
		<widget name="timerlist" position="5,5" size="555,210" scrollbarMode="showOnDemand" />
		<ePixmap position="0,220" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,220" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,220" zPosition="4" size="140,40" pixmap="skin_default/key-yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,220" zPosition="4" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,220" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,220" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="280,220" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="420,220" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, timers):
		Screen.__init__(self, session)

		self.timers = timers

		self["timerlist"] = AutoTimerPreviewList(self.timers)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("???"))
		self["key_yellow"] = Button(_("???"))
 		self["key_blue"] = Button(_("???"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.yellow,
				"blue": self.blue
			}
		)

	def yellow(self):
		pass

	def blue(self):
		pass

	def cancel(self):
		self.close(None)

	def save(self):
		self.close(True)
