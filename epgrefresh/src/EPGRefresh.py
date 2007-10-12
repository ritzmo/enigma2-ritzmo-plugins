from enigma import eServiceCenter, getBestPlayableServiceReference, eServiceReference, eTimer

# Some target which is used nowhere else
UNUSED_TARGET = 2

# Duration to reside on service in s (to be configurable)
DURATION = 120

class EPGRefresh:
    """WIP - Simple Class to refresh EPGData - WIP"""
    def __init__(self):
        # Initialize Timer
        self.timer = eTimer()
        self.timer.timeout.get().append(self.nextService)

        # Initialize
        self.position = -1
        # TODO: make this dynamic
        self.services = [
            "1:0:1:6DCA:44D:1:C00000:0:0:0:",
            "1:0:1:6D66:437:1:C00000:0:0:0:",
            "1:0:1:445C:453:1:C00000:0:0:0:",
            "1:0:1:2EE3:441:1:C00000:0:0:0:"
        ] # List of ServiceRefs

    def refresh(self):
        # Reset Position
        self.position = -1

        # Start polling in 10ms
        self.timer.start(10, True)

    def nextService(self):
        # Increment Position
        self.position += 1

        # DEBUG
        print "TRYING TO POLL NEXT SERVICE", self.position

        # Check if more Services present
        # TODO: cache length?!
        if len(self.services) < self.position:
            # Play next service
            self.playService(self.services[self.position])

            # Start Timer
            self.timer.startLongTimer(DURATION)

        # Just timeout otherwise

    # Modified Version of Screens.PictureInPicture.playService
    def playService(self, service):
        if service and (service.flags & eServiceReference.isGroup):
            ref = getBestPlayableServiceReference(service, eServiceReference())
        else:
            ref = service

        if ref:
            # TODO: do we need to catch tune failed explicitly?
            self.epgservice = eServiceCenter.getInstance().play(ref)
            if self.epgservice and not self.pipservice.setTarget(UNUSED_TARGET):
                # DEBUG
                print "POLLING SERVICE", ref
                self.epgservice.start()
            else:
                # DEBUG
                print "COULD NOT POLL SERVICE", ref

                # Destroy
                self.epgservice = None

                # Poll next service
                self.timer.stop()
                self.nextService()

epgrefresh = EPGRefresh()