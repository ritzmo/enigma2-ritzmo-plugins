# Config
from xml.dom.minidom import parse as minidom_parse
from Tools.Directories import fileExists

# Timer
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry, parseEvent

# Timespan
from time import localtime

# EPGCache & Event
from enigma import eEPGCache, eServiceReference

XML_CONFIG = "/etc/enigma2/autotimer.xml"

class AutoTimer:
    def __init__(self, session):
        # Save session (somehow NavigationInstance.instance is None ?!)
        self.session = session

        # Initialize Timers
        self.timers = []

        # Parse config
        self.readXml()
        print "[AutoTimer] Generated List", self.timers
        
        # Parse EPG & Add Events
        self.parseEPG()

    def getValue(self, definitions, default, isList = True):
        # Initialize Output
        ret = ""

        # How many definitions are present
        if isList:
            Len = len(definitions)
            if Len > 0:
                childNodes = definitions[Len-1].childNodes
            else:
                childNodes = []
        else:
            childNodes = definitions.childNodes

        # Iterate through nodes of last one
        for node in childNodes:
            # Append text if we have a text node
            if node.nodeType == node.TEXT_NODE:
                ret = ret + node.data

        # If output is still empty return default
        if not len(ret):
            return default

        # Otherwise return output
        return ret

    def readXml(self):
        # Empty out timers
        self.timers[:]

        # Abort if no config found
        if not fileExists(XML_CONFIG):
            return

        # Parse Config
        dom = minidom_parse(XML_CONFIG)
        
        # Get Config Element
        for config in dom.getElementsByTagName("autotimer"):
            # Iterate Timers
            for timer in config.getElementsByTagName("timer"):
                # Timers are saved as tuple (name, allowedtime (from, to) or None, list of services or None)
                
                # Read out name
                name = self.getValue(timer.getElementsByTagName("name"), None)
                if name is None:
                    print "[AutoTimer] Erroneous config, skipping entry"
                    continue
                
                # Guess allowedtime
                allowed = timer.getElementsByTagName("timespan")
                if len(allowed):
                    # We only support 1 Timespan so far
                    start = self.getValue(allowed[0].getElementsByTagName("from"), None)
                    end = self.getValue(allowed[0].getElementsByTagName("to"), None)
                    if start and end:
                        timetuple = (start, end)
                    else:
                        timetuple = None
                else:
                    timetuple = None

                # Read out allowed services
                allowed = timer.getElementsByTagName("serviceref")
                if len(allowed):
                    servicelist = []
                    for service in allowed:
                        value = self.getValue(service, None, False)
                        if value:
                            servicelist.append(value)
                    if not len(servicelist):
                        servicelist = None
                else:
                    servicelist = None

                # Finally append tuple
                self.timers.append((
                        name,
                        timetuple,
                        servicelist
                ))

    def parseEPG(self):
        epgcache = eEPGCache.getInstance()

        # Iterate Timer
        for timer in self.timers:
            name = str(timer[0])
            print "[AutoTimer] Searching for:", name
            try:
                # Search EPG
                ret = epgcache.search(('RIB', 100, eEPGCache.PARTIAL_TITLE_SEARCH, name, eEPGCache.NO_CASE_CHECK))

                # Continue on empty result
                if ret is None:
                    print "[AutoTimer] Got empty result"
                    continue

                for event in ret:
                    # Format is (ServiceRef, EventId, BeginTime)
                    # Example: ('1:0:1:445D:453:1:C00000:0:0:0:', 25971L, 1192287455L)
                    print "[AutoTimer] Checking Tuple:", event

                    # Check if we have Timelimit
                    timeValid = False
                    if timer[1] is not None:
                        # Parse Time
                        t = localtime(event[2]) # H is t[3], M is t[4]

                        # From
                        tuple = timer[1][0].split(':')
                        h = int(tuple[0])
                        m = int(tuple[1])
                        if h < t[3] or (h == t[3] and m <= t[4]):
                            # To
                            tuple = timer[1][1].split(':')
                            h = int(tuple[0])
                            m = int(tuple[1])
                            if h > t[3] or (h == t[3] and m >= t[4]):
                                timeValid = True
                    else:
                        timeValid = True
                    
                    # Check if we have Servicelimit
                    serviceValid = False
                    if timer[2] is not None:
                        if event[0] in timer[2]:
                            serviceValid = True
                    else:
                        serviceValid = True

                    # If Time & Service valid add Timer
                    if timeValid and serviceValid:
                        print "[AutoTimer] Would add timer for this event"
                        ref = eServiceReference(event[0])
                        evt = epgcache.lookupEventId(ref, event[1])
                        if evt:                            
                            # Check for double Timers
                            double = False
                            for rtimer in self.session.nav.RecordTimer.timer_list:
                                # Serviceref equals and begin is only 10min different
                                # TODO: improve check (eventId would be handy)
                                if str(rtimer.service_ref) == event[0] and abs(rtimer.begin - event[2]) < 600:
                                    print "[AutoTimer] Double timer found!!!!"
                                    double = True
                                    break

                            # If timer is "unique"
                            if not double:
                                print "[AutoTimer] Timer is unique. Adding now!"
                                newEntry = RecordTimerEntry(ServiceReference(ref), *parseEvent(evt))
                                self.session.nav.RecordTimer.record(newEntry)
                        else:
                            print "[AutoTimer] Could not create Event!"

            except StandardError, se:
                print "[AutoTimer] Error occured:", se
