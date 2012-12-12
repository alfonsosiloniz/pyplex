import urllib2, re, xml.etree.cElementTree as et
from pyomxplayer import OMXPlayer
from urlparse import urlparse
import avahi, dbus, sys, platform
from pprint import pprint
import socket, subprocess, signal, os, logging
from threading import Thread
import Queue
import udplistener
import httplistener
from plexInterface import PlexInterface

__all__ = ["ZeroconfService"]
class ZeroconfService:
    """A simple class to publish a network service with zeroconf using
    avahi.

    """

    def __init__(self, name, port, stype="_plexclient._tcp",
                 domain="", host="", text=""):
        self.name = name
        self.stype = stype
        self.domain = domain
        self.host = host
        self.port = port
        self.text = text

    def publish(self):
        bus = dbus.SystemBus()
        server = dbus.Interface(
                         bus.get_object(
                                 avahi.DBUS_NAME,
                                 avahi.DBUS_PATH_SERVER),
                        avahi.DBUS_INTERFACE_SERVER)

        g = dbus.Interface(
                    bus.get_object(avahi.DBUS_NAME,
                                   server.EntryGroupNew()),
                    avahi.DBUS_INTERFACE_ENTRY_GROUP)

        g.AddService(avahi.IF_UNSPEC, avahi.PROTO_UNSPEC,dbus.UInt32(0),
                     self.name, self.stype, self.domain, self.host,
                     dbus.UInt16(self.port), self.text)

        g.Commit()
        self.group = g
        print 'Service published'

    def unpublish(self):
        self.group.Reset()
        
urls = (
    '/xbmcCmds/xbmcHttp','xbmcCmdsXbmcHttp',
    '/(.*)', 'stop', 'hello'
)

def string_to_lines(string):
    return string.strip().replace('\r\n', '\n').split('\n')


class hello:        
    def GET(self, message):
        return 'Hello, World'

class CGCommands:
    def SendCmd (self, command, attributes):
        try:
          sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
          sys.stderr.write("[ERROR] %s\n" % msg[1])
          sys.exit(1)
               
        try:
          sock.connect(("localhost", 9010))
        except socket.error, msg:
          sys.stderr.write("[ERROR] %s\n" % msg[1])
          sys.exit(2)
                      
        sock.send("%s|%s\r\n" % (command , attributes))

    def SendCommand(self, message = None):
        self.SendCmd("K",message)

    def SendPlay(self, url = None):
        self.SendCmd("V",url)
        


class xbmcCommands:
    def __init__(self, omxArgs):
        self.media = None
        self.plex = PlexInterface()
        self.omx = None
        self.omxArgs = omxArgs
        self.cgcmd = CGCommands();


    def PlayMedia(self, fullpath, tag, unknown1, unknown2, unknown3):
        global parsed_path
        global media_key
        global duration

        parsed_path = urlparse(fullpath)
        media_path = parsed_path.scheme + "://" + parsed_path.netloc + tag
        self.media = self.plex.getMedia(media_path)
        
        print 'mediapath', media_path
        if(self.omx):
            self.Stop()
        transcodeURL = self.media.getTranscodeURL()
        
        f = urllib2.urlopen(transcodeURL)
        rawXML = f.read()

        f.close()
		
        for line in string_to_lines(rawXML):
             line = line.strip()
             if line.startswith("#"):
                 sessionURL = ""
             else:
             	sessionURL = self.media.getTranscodeSessionURL() + line

        self.cgcmd.SendPlay(sessionURL)                  
        

    def Pause(self, message):
        self.cgcmd.SendCommand(40);

    def Play(self, message):
        self.cgcmd.SendCommand(39);

    def Stop(self, message):
        self.cgcmd.SendCommand(41);

    def Up(self, message):
        self.cgcmd.SendCommand(19);

    def Down(self, message):
        self.cgcmd.SendCommand(20);

    def Left(self, message):
        self.cgcmd.SendCommand(21);

    def Right(self, message):
        self.cgcmd.SendCommand(22);
        
    def ContextMenu(self, message):
        self.cgcmd.SendCommand(17);

    def ParentDir(self, message):
        self.cgcmd.SendCommand(24);

    def Select(self, message):
        self.cgcmd.SendCommand(23);

    def OSD(self, message):
        self.cgcmd.SendCommand(2);
        
    def getMilliseconds(self,s):
        hours, minutes, seconds = (["0", "0"] + ("%s" % s).split(":"))[-3:]
        hours = int(hours)
        minutes = int(minutes)
        seconds = float(seconds)
        miliseconds = int(3600000 * hours + 60000 * minutes + 1000 * seconds)
        return miliseconds

    def getPosMilli(self):
        return self.getMilliseconds(self.omx.position)
    
    def setPlayed(self):
        self.media.setPlayed()

    def isFinished(self):
        if(self.omx):
            finished = self.omx.finished
        else:
            finished = True
        return finished
    
    def isRunning(self):
        if(self.omx):
            return True
        return False

    def updatePosition(self):
        if self.isFinished():
            if (self.getPosMilli() > (self.media.duration * .95)):
                self.setPlayed()
            self.Stop()
        else:
            self.media.updatePosition(self.getPosMilli())
        

http = None
udp = None

if __name__ == "__main__":
    hostname = platform.uname()[1]
    try:
        print "starting, please wait..."
        global service
        global queue
        global parsed_path
        global media_key
        global duration
        duration = 0
        args = len(sys.argv)
        if args > 1: 
            if sys.argv[1] == "hdmi":
                omxCommand = '-o hdmi'
                print "Audo output over HDMI"
        else:
            omxCommand = ''
            print "Audio output over 3,5mm jack"
        xbmcCmmd = xbmcCommands(omxCommand)

        media_key = None
        parsed_path = None
        queue = Queue.Queue()
        service = ZeroconfService(name= "MC-4GS-HD", port=3000, text=["machineIdentifier=" + hostname,"version=2.0"])
        service.publish()
        udp = udplistener.udplistener(queue)
        udp.start()
        http = httplistener.httplistener(queue)
        http.start()
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        while True:
            try:
                command, args = queue.get(True, 2)
                print "Got command: %s, args: %s" %(command, args)
                if not hasattr(xbmcCmmd, command):
                    print "Command %s not implemented yet" % command
                else:
                    func = getattr(xbmcCmmd, command)
                    func(*args)
                
                # service.unpublish()
            except Queue.Empty:
                pass
            if(xbmcCmmd.isRunning()):
                # print omx.position
                xbmcCmmd.updatePosition()
    except:
        print "Caught exception"
        if(xbmcCmmd):
            xbmcCmmd.Stop("")
        if(udp):
            udp.stop()
            udp.join()
        if(http):
            http.stop()
            http.join()
        raise

