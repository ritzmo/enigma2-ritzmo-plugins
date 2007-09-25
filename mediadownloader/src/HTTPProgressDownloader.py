from twisted.web.client import HTTPDownloader, _parse
from twisted.internet import reactor
from Components.Sources.Source import Source

class HTTPProgressDownloaderSource(Source):
    """Source to feed Progress Renderer from HTTPProgressDownloader"""

    def __init__(self):
        # Initialize and invalidate
        Source.__init__(self)
        self.invalidate()

    def invalidate(self):
        # Invalidate
        self.range = None
        self.value = 0
        self.factor = 1
        self.changed((self.CHANGED_CLEAR, ))

    def writeValues(self, pos, max):
        # Only save range if not None
        if max is not None:
            self.range = max / self.factor

        # Save pos
        self.value = pos / self.factor

        # Increase Factor as long as range is too big
        if self.range > 5000000:
            self.factor *= 500

        # Trigger change
        self.changed((self.CHANGED_ALL, ))
    

class HTTPProgressDownloader(HTTPDownloader): 
    """Download to a file and keep track of progress."""

    def __init__(self, url, fileOrName, writeProgress, method='GET', headers=None, agent="Twisted client"):
        HTTPDownloader.__init__(self, url, fileOrName, method=method, headers=headers, agent=agent)

        # Save callback locally
        self.writeProgress = writeProgress

        # Initialize
        self.currentlength = 0
        self.totallength = None

    def gotHeaders(self, headers):
        # If we have a callback and 'OK' from Server try to get length
        if self.writeProgress and self.status == '200':
            if headers.has_key('content-length'):
                self.totallength = int(headers['content-length'][0])
                self.writeProgress(0, self.totallength)

        return HTTPDownloader.gotHeaders(self, headers)

    def pagePart(self, data):
        # If we have a callback and 'OK' from server increment pos
        if self.writeProgress and self.status == '200':
            self.currentlength += len(data)
            self.writeProgress(self.currentlength, self.totallength)

        return HTTPDownloader.pagePart(self, data)

def download(url, file, writeProgress, contextFactory=None, *args, **kwargs):
    """Download a web page to a file but provide current-/total-length.

    @param file: path to file on filesystem, or file-like object.
    @param writeProgress: function which takes two arguments (pos, length)

    See HTTP(Progress)Downloader to see what extra args can be passed.
    """
    scheme, host, port, path = _parse(url)
    factory = HTTPProgressDownloader(url, file, writeProgress, *args, **kwargs)
    if scheme == 'https':
        from twisted.internet import ssl
        if contextFactory == None :
            contextFactory = ssl.ClientContextFactory()
        reactor.connectSSL(host, port, factory, contextFactory)
    else:
        reactor.connectTCP(host, port, factory)

    return factory.deferred
