# Needed for minFree
from os import statvfs

# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Button import Button
from Components.FileList import FileList

class LocationBox(Screen):
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

    def __init__(self, session, text = "", filename = "", currDir = "/", windowTitle = "Select Location", minFree = None):
        Screen.__init__(self, session)

        self["text"] = Label(text)
        self.text = text

        self.filename = filename
        self.minFree = minFree

        self.filelist = FileList(currDir, showDirectories = True, showFiles = False)
        self["filelist"] = self.filelist

        self["key_green"] = Button(_("Confirm"))
        self["key_yellow"] = Button(_("Rename"))

        self["green"] = Pixmap()
        self["yellow"] = Pixmap()

        self["target"] = Label()

        self["actions"] = ActionMap(["OkCancelActions", "DirectionsActions", "ColorActions"],
        {
            "ok": self.ok,
            "cancel": self.cancel,
            "green": self.select,
            "yellow": self.changeName,
            "left": self.left,
            "right": self.right,
            "up": self.up,
            "down": self.down,
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
        self["filelist"].up()

    def down(self):
        self["filelist"].down()

    def left(self):
        self["filelist"].pageUp()

    def right(self):
        self["filelist"].pageDown()

    def ok(self):
        if self.filelist.canDescent():
            self.filelist.descent()
            self.updateTarget()

    def cancel(self):
        self.close(None)

    def selectConfirmed(self, res):
        if res: 
            self.close(''.join([self.filelist.getCurrentDirectory(), self.filename]))

    def select(self):
        # Do nothing unless current Directory is valid
        if self.filelist.getCurrentDirectory() is not None:
            # Check if we need to have a minimum of free Space available
            if self.minFree is not None:
                # Try to read fs stats
                try:
                    s = statvfs(self.filelist.getCurrentDirectory())
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
        if self.filelist.getCurrentDirectory() is not None:
            self["target"].setText(''.join([self.filelist.getCurrentDirectory(), self.filename]))
        else:
            self["target"].setText("Invalid Location")

    def __repr__(self):
        return str(type(self)) + "(" + self.text + ")"