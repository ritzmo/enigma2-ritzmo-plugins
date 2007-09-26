# GUI (Screens)
from Screens.Screen import Screen
from MountEdit import MountEdit

# GUI (Components)
from Components.Button import Button
from Components.ActionMap import ActionMap
from MountList import MountList

# Mounts
from Mounts import mounts

class MountManager(Screen):
	"""Main Screen of MountManager."""

	skin = """
		<screen name="MountManager" position="140,148" size="420,250" title="Mount manager">
			<widget name="entries" position="5,0" size="410,200" scrollbarMode="showOnDemand" />
			<ePixmap position="0,205" zPosition="1" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
			<ePixmap position="140,205" zPosition="1" size="140,40" pixmap="skin_default/key-yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="280,205" zPosition="1" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
			<widget name="key_green" position="0,205" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="140,205" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="280,205" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Button Labels
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_("Delete"))
		self["key_blue"] = Button(_("Add"))

		# Refresh mounts
		mounts.reload()

		# Create List of Mounts
		self["entries"] = MountList(mounts.getExtendedList())

		# Define Actions
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"ok": self.ok,
				"cancel": self.close,
				"green": self.save,
				"yellow": self.remove,
				"blue": self.add
			}
		)

	def refresh(self):
		# Set new List of Mounts
		self["entries"].l.setList(mounts.getExtendedList())

	def ok(self):
		# Edit selected Mount
		current = self["entries"].getCurrent()
		if current is not None:
			self.session.openWithCallback(self.refresh, MountEdit, mounts, org_mp = current[0])

	def save(self):
		# Save XML
		mounts.save()

		# Mount
		# TODO: fetch output?
		# Possible: Use eAppContainer (e.g. via Screens.Console), add possibility to use eAppContailer::kill
		# This would force us to show manual mount commands. wanted?
		mounts.mount()
		self.close()

	def add(self):
		# Add a new Mount
		self.session.openWithCallback(self.refresh, MountEdit, mounts)

	def remove(self):
		# Remove selected Mount
		current = self["entries"].getCurrent()
		if current is not None:
			mounts.remove(current[0])
			self.refresh()
