# WIP Target
#from FakeTarget import FakeTarget

# Testing
from Screens.PictureInPicture import PictureInPicture

from enigma import eTimer, eServiceReference

# Duration to reside on service in s (to be configurable)
DURATION = 12

class EPGRefresh:
    """WIP - Simple Class to refresh EPGData - WIP"""
    def __init__(self):
        # Initialize Timer
        self.timer = eTimer()
        self.timer.timeout.get().append(self.nextService)

        # Initialize Fake Target
        self.target = None

        # Initialize
        self.position = -1
        # TODO: make this dynamic
        self.services = [
            eServiceReference(x)
              for x in [
                  "1:0:1:6DCA:44D:1:C00000:0:0:0:",
                  "1:0:1:6D66:437:1:C00000:0:0:0:",
                  "1:0:1:445C:453:1:C00000:0:0:0:",
                  "1:0:1:2EE3:441:1:C00000:0:0:0:"
              ]
        ]

    def refresh(self, session = None):
        if self.target is None:
            if session is not None:
                self.target = session.instantiateDialog(PictureInPicture)
                self.target.show()
            else:
                return
            
        # Reset Position
        self.position = -1

        # Start polling in 100ms
        self.timer.start(100, True)

    def nextService(self):
        # Increment Position
        self.position += 1

        # DEBUG
        print "TRYING TO POLL NEXT SERVICE", self.position

        # Check if more Services present
        # TODO: cache length?!
        if len(self.services) > self.position:
            # Play next service
            if self.target.playService(self.services[self.position]):
                # Start Timer
                self.timer.startLongTimer(DURATION)
            else:
                # Skip service if play failed
                self.nextService()
        else:
            # Destroy service
            self.target.hide()
            #self.target.stop()
            pass

epgrefresh = EPGRefresh()