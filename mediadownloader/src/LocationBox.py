# Needed for minFree
from os import statvfs

# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox

# Generic
from Tools.BoundFunction import boundFunction

# Quickselect
from Tools.NumericalTextInput import NumericalTextInput

# GUI (Components)
from Components.ActionMap import NumberActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Button import Button
from Components.FileList import FileList

# Timer
from enigma import eTimer

class LocationBox(Screen, NumericalTextInput):
    """Simple Class similar to MessageBox / ChoiceBox but used to choose a folder/pathname combination"""

    skin = """<screen name="LocationBox" position="100,130" size="540,340" >
            <widget name="text" position="0,2" size="540,22" font="Regular;22" />
            <widget name="filelist" position="0,25" size="540,235" />
            <widget name="target" position="0,260" size="540,40" valign="center" font="Regular;22" />
            <widget name="yellow" position="260,300" zPosition="1" size="140,40" pixmap="key_yellow-fs8.png" transparent="1" alphatest="on" />
            <widget name="key_yellow" position="260,300" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
            <widget name="green" position="400,300" zPosition="1" size="140,40" pixmap="key_green-fs8.png" transparent="1" alphatest="on" />
            <widget name="key_green" position="400,300" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;22" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
        </screen>"""

    def __init__(self, session, text = "", filename = "", currDir = None, windowTitle = "Select Location", minFree = None):
        Screen.__init__(self, session)
        NumericalTextInput.__init__(self, nextFunc = self.key_next)

        # Quickselect Timer
        self.key_timer = eTimer()
        self.key_timer.timeout.get().append(self.key_reset)

        # Initialize Quickselect
        self.lastNumber = -1
        self.curr_pos = -1
        self.key_select = ""

        self["text"] = Label(text)
        self.text = text

        self.filename = filename
        self.minFree = minFree

        self["filelist"] = FileList(currDir, showDirectories = True, showFiles = False)

        self["key_green"] = Button(_("Confirm"))
        self["key_yellow"] = Button(_("Rename"))

        self["green"] = Pixmap()
        self["yellow"] = Pixmap()

        self["target"] = Label()

        self["actions"] = NumberActionMap(["OkCancelActions", "DirectionsActions", "ColorActions", "NumberActions"],
        {
            "ok": self.ok,
            "cancel": self.cancel,
            "green": self.select,
            "yellow": self.changeName,
            "left": self.left,
            "right": self.right,
            "up": self.up,
            "down": self.down,
            "1": self.keyNumberGlobal,
            "2": self.keyNumberGlobal,
            "3": self.keyNumberGlobal,
            "4": self.keyNumberGlobal,
            "5": self.keyNumberGlobal,
            "6": self.keyNumberGlobal,
            "7": self.keyNumberGlobal,
            "8": self.keyNumberGlobal,
            "9": self.keyNumberGlobal,
            "0": self.keyNumberGlobal
        })

        self.onShown.extend([
            boundFunction(self.setTitle, windowTitle),
            self.updateTarget,
            self.showHideRename
        ])

    def showHideRename(self):
        if self.filename == "":
            self["yellow"].hide()
            self["key_yellow"].hide()

    def up(self):
        # Reset Quickselect
        self.key_reset()

        self["filelist"].up()

    def down(self):
        # Reset Quickselect
        self.key_reset()

        self["filelist"].down()

    def left(self):
        # Reset Quickselect
        self.key_reset()

        self["filelist"].pageUp()

    def right(self):
        # Reset Quickselect
        self.key_reset()

        self["filelist"].pageDown()

    def ok(self):
        # Reset Quickselect
        self.key_reset()

        if self["filelist"].canDescent():
            self["filelist"].descent()
            self["filelist"].instance.moveSelectionTo(0)
            self.updateTarget()

    def cancel(self):
        self.close(None)

    def selectConfirmed(self, res):
        if res: 
            self.close(''.join([self["filelist"].getCurrentDirectory(), self.filename]))

    def select(self):
        # Reset Quickselect
        self.key_reset()

        # Do nothing unless current Directory is valid
        if self["filelist"].getCurrentDirectory() is not None:
            # Check if we need to have a minimum of free Space available
            if self.minFree is not None:
                # Try to read fs stats
                try:
                    s = statvfs(self["filelist"].getCurrentDirectory())
                    if (s.f_bavail * s.f_bsize) / 1000000 > self.minFree:
                        # Automatically confirm if we have enough free disk Space available
                        return self.selectConfirmed(True)
                except OSError:
                    pass

                # Ask User if he really wants to select this folder
                self.session.openWithCallback(
                    self.selectConfirmed,
                    MessageBox,
                    "There might not be enough Space on the selected Partition.\nDo you really want to continue?",
                    type = MessageBox.TYPE_YESNO
                )
            # No minimum free Space means we can safely close
            else:   
                self.selectConfirmed(True)

    def changeName(self):
        # Reset Quickselect
        self.key_reset()

        if self.filename != "":
            # TODO: Add Information that changing extension is bad? disallow?
            # TODO: decide if using an inputbox is ok - we could also keep this in here
            self.session.openWithCallback(
                self.nameChanged,
                InputBox,
                title = "Please enter a new filename",
                text = self.filename
            )

    def nameChanged(self, res):
        if res is not None:
            if len(res):
                self.filename = res
                self.updateTarget()
            else:
                self.session.open(
                    MessageBox,
                    "An empty filename is illegal.",
                    type = MessageBox.TYPE_ERROR,
                    timeout = 5
                )

    def updateTarget(self):
        if self["filelist"].getCurrentDirectory() is not None:
            self["target"].setText(''.join([self["filelist"].getCurrentDirectory(), self.filename]))
        else:
            self["target"].setText("Invalid Location")

    def keyNumberGlobal(self, number):
        # Cancel Timeout
        self.key_timer.stop()

        # See if another key was pressed before
        if number != self.lastNumber:
            self.nextKey()
            self.lastNumber = number

            # Try to select what was typed
            self.selectByStart()

            # Increment position
            self.curr_pos += 1

        # Get char and append to text
        char = self.getKey(number)
        self.key_select = self.key_select[:self.curr_pos] + unicode(char)

    def selectByStart(self):
        # Don't do anything on initial call
        if not len(self.key_select):
            return
        
        # Don't select if no dir
        if self["filelist"].getCurrentDirectory():
            # TODO: implement proper method in Components.FileList
            files = self["filelist"].getFileList()

            # Initialize index
            idx = 0

            # We select by filename which is absolute
            lookfor = self["filelist"].getCurrentDirectory() + self.key_select

            # Select file starting with generated text
            for file in files:
                if file[0][0] and file[0][0].startswith(lookfor):
                    self["filelist"].instance.moveSelectionTo(idx)
                    break
                idx += 1

    def key_next(self):
        # Invalidate Key
        self.lastNumber = -1

        # Try to select what was typed
        self.selectByStart()

        # Start timeout
        self.key_timer.start(1000, 1)

    def key_reset(self):
        # Eventually stop Timer
        self.key_timer.stop()

        # Invalidate
        self.lastNumber = -1
        self.curr_pos = -1
        self.key_select = ""

    def __repr__(self):
        return str(type(self)) + "(" + self.text + ")"