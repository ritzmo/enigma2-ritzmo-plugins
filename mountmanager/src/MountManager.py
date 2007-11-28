# GUI (Screens)
from Screens.Screen import Screen
from MountEdit import MountEdit

# GUI (Components)
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.SelectionList import SelectionList, SelectionEntryComponent
from MountList import MountList

# Mounts
from Mounts import mounts

# Timer
from enigma import eTimer

class MountProcess(Screen):
	"""Displays process of mounting."""
	
	skin = """<screen position="100,100" size="550,360" title="Mounting in progress..." >
			<widget name="list" position="0,0" size="550,360" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self.timer = eTimer()
		self.timer.timeout.get().append(self.timerTick)
		self.timeout = 6

		list = []
		mountlist = mounts.getExtendedList()
		for listindex in range(len(mountlist)):
			if mountlist[listindex][1] == "1":
				list.append(SelectionEntryComponent(
						mountlist[listindex][0].encode("UTF-8"),
						mountlist[listindex][0],
						listindex,
						False
				))

		self["list"] = SelectionList(list)

		if len(list):
			# Define Actions
			self["actions"] = ActionMap(["OkCancelActions"],
				{
					"cancel": self.cancel,
				}
			)
			self.onLayoutFinish.append(self.startMount)
		else:
			self.onLayoutFinish.append(self.close)

	def startMount(self):
		mounts.mount(self.updateList)

	def cancel(self):
		mounts.callback = None
		self.timer.stop()
		self.timer = None
		self.close()

	def updateList(self, mountpoint = None, retval = False):
		if mountpoint is not None:
			idx = 0
			for item in self["list"].list:
				if item[0][1] == mountpoint:
					self["list"].list[idx] = SelectionEntryComponent(item[0][0], item[0][1], item[0][2], retval)
					break
				idx += 1

			self["list"].setList(self["list"].list)
		else:
			self.origTitle = _("Done mounting...")
			self.timerTick() # tick once before actually starting the timer
			self.timer.start(1000)

	def timerTick(self):
		self.timeout -= 1
		self.setTitle(self.origTitle + " (" + str(self.timeout) + ")")
		if self.timeout == 0:
			self.timer.stop()
			self.cancel()

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

		# Mount with process shown
		self.session.openWithCallback(
			self.close,
			MountProcess
		)

	def add(self):
		# Add a new Mount
		self.session.openWithCallback(self.refresh, MountEdit, mounts)

	def remove(self):
		# Remove selected Mount
		current = self["entries"].getCurrent()
		if current is not None:
			mounts.remove(current[0])
			self.refresh()
