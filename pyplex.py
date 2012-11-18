import web, urllib2, re, xml.etree.cElementTree as et
from urlparse import urlparse
import avahi, dbus, sys
from pprint import pprint
import socket,  subprocess, signal, os, logging
from threading import Thread
import Queue
import udplistener
import httplistener

logger = logging.getLogger('myapp')
hdlr = logging.FileHandler('/var/log/pyplex.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

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
        logger.info( 'Service published' )

    def unpublish(self):
        self.group.Reset()


        
urls = (
    '/xbmcCmds/xbmcHttp','xbmcCmdsXbmcHttp',
    '/(.*)', 'stop', 'hello'
)
app = web.application(urls, globals())

class hello:        
    def GET(self, message):
        return 'Hello, World'

class xbmcCommands:
    def PlayMedia(self, fullpath, tag, unknown1, unknown2, unknown3):
        global omx
        global parsed_path
        global omxCommand
        global media_key
        global duration
        logger.info ( '---')
        logger.info ( fullpath)
        logger.info ( tag)
        f = urllib2.urlopen(fullpath)
        s = f.read()
        f.close()
        logger.info( s)
        tree = et.fromstring(s)
        #get video
        el = tree.find('./Video/Media/Part')
        key = tree.find('./Video')
        key = key.attrib['ratingKey']
        logger.info( key)
        #print el.attrib['key']
        logger.info(fullpath)
        #Construct the path to the media.
        parsed_path = urlparse(fullpath)
        media_key = key
        duration = int(el.attrib['duration'])
        mediapath = parsed_path.scheme + "://" + parsed_path.netloc + el.attrib['key'] 
        logger.info( mediapath)
        #if(omx):
        #    self.stop()
        #omx = OMXPlayer(mediapath, args=omxCommand, start_playback=True)
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
                      
        sock.send("V|%s\r\n" % (mediapath))
                       

    def Pause(self, message):
        global omx
        if(omx):
            omx.set_speed(1)
            omx.toggle_pause()

    def Play(self, message):
        global omx
        if(omx):
            ret = omx.set_speed(1)
            if(ret == 0):
                omx.toggle_pause()

    def Stop(self, message):
        global omx
        logger.info("Han mandado STOP")
        if(omx):
            omx.stop()

    def stopPyplex(self, message):
        self.stop()
        global service
        exit()

    def SkipNext(self, message = None):
        if(omx):
            omx.increase_speed()

    def SkipPrevious(self, message = None):
        if(omx):
            omx.decrease_speed()

    def StepForward(self, message = None):
        if(omx):
            omx.increase_speed()

    def StepBack(self, message = None):
        if(omx):
            omx.decrease_speed()

    def BigStepForward(self, message = None):
        if(omx):
            omx.jump_fwd_600()

    def BigStepBack(self, message = None):
        if(omx):
            omx.jump_rev_600()
        
def OMXRunning():
    global pid
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    omxRunning = False
    for line in out.splitlines():
        if 'omxplayer' in line:
            pid = int(line.split(None, 1)[0])
            omxRunning = True
    return omxRunning

def getMiliseconds(s):
    hours, minutes, seconds = (["0", "0"] + s.split(":"))[-3:]
    hours = int(hours)
    minutes = int(minutes)
    seconds = float(seconds)
    miliseconds = int(3600000 * hours + 60000 * minutes + 1000 * seconds)
    return miliseconds

xbmcCmmd = xbmcCommands()
omx = None
http = None
udp = None
pid = -1

if __name__ == "__main__":
    try:
        logger.info( "starting, please wait...")
        global service
        global queue
        global parsed_path
        global media_key
        global omxCommand
        global duration
        duration = 0
        args = len(sys.argv)
        if args > 1: 
            if sys.argv[1] == "hdmi":
                omxCommand = '-o hdmi'
                logger.info( "Audo output over HDMI")
        else:
            omxCommand = ''
            logger.info( "Audio output over 3,5mm jack")
        media_key = None
        parsed_path = None
        queue = Queue.Queue()
        service = ZeroconfService(name="MC-4GS-HD", port=3000, text=["machineIdentifier=pi","version=2.0"])
        service.publish()
        udp = udplistener.udplistener(queue)
        udp.start()
        http = httplistener.httplistener(queue)
        http.start()
        while True:
            try:
                command, args = queue.get(True, 2)
                print "Got command: %s, args: %s" %(command, args)
                logger.info(command)
                if not hasattr(xbmcCmmd, command):
                    print "Command %s not implemented yet" % command
                else:
                    func = getattr(xbmcCmmd, command)
                    func(*args)
                
                # service.unpublish()
            except Queue.Empty:
                pass
            if(omx):
                # print omx.position
                if omx.finished:
                    if (getMiliseconds(str(omx.position)) > (duration * .95)):
                        setPlayed = parsed_path.scheme + "://" + parsed_path.netloc + "/:/scrobble?key=" + str(media_key) + "&identifier=com.plexapp.plugins.library"
                        try:
                            f = urllib2.urlopen(setPlayed)
                        except urllib2.HTTPError:
                            print "Failed to update plex that item was played: %s" % setPlayPos
                            pass
                    omx.stop()
                    omx = None
                    continue
                pos = getMiliseconds(str(omx.position))
                #TODO: make setPlayPos a function
                setPlayPos =  parsed_path.scheme + "://" + parsed_path.netloc + '/:/progress?key=' + str(media_key) + '&identifier=com.plexapp.plugins.library&time=' + str(pos) + "&state=playing" 
                try:
                    f = urllib2.urlopen(setPlayPos)
                except urllib2.HTTPError:
                    print "Failed to update plex play time, url: %s" % setPlayPos
                    pass
    except:
        print "Caught exception"
        if(omx):
            omx.stop()
        if(udp):
            udp.stop()
            udp.join()
        if(http):
            http.stop()
            http.join()
        raise

