from twisted.web.client import HTTPDownloader, _parse
from twisted.internet import reactor

class HTTPProgressDownloader(HTTPDownloader): 
    """Download to a file and keep track of progress."""

    def __init__(self, url, fileOrName, writeProgress = None, *args, **kwargs):
        HTTPDownloader.__init__(self, url, fileOrName, *args, **kwargs)

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

def download(url, file, writeProgress=None, contextFactory=None, *args, **kwargs):
    """Download a web page to a file but provide current-/total-length.

    @param file: path to file on filesystem, or file-like object.
    @param writeProgress: function which takes two arguments (pos, length)

    See HTTPDownloader to see what extra args can be passed.
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
