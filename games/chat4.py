#!/usr/bin/python
#
# Simple Socket Server for Flash
#
# Earthman, you were always the more talented one
# when it came to logic...
#
# 30 May 2006
#
print "Chat3.py"
import sys
import datetime
import asyncore, asynchat
import os, socket, string
import re
import time
from creative_chat import ChatBot, nickname, Word
from sqlite3 import dbapi2 as sqlite

db = sqlite.connect('chatbot.db')
c = db.cursor()


ready = None # who is ready to talk?
codeword = re.compile('chatbot, i am (.*)',re.I)
active = dict()  # dict of codewords -> upgraded chatter objs


def delete_timeouts():
    now = datetime.datetime.now()
    diff = datetime.timedelta(0,5*60) #five minutes of inactivity
    timeouts = [c for c in SOCKETChannel.listeners if now-c.chatobj.last_spoken > diff]
    for c in timeouts: c.handle_close()


def is_user(message):
    global codeword
    test = codeword.match(message)
    if not test: return None

    #matched. lets delete old connections, just in case
    delete_timeouts()
    codename = test.group(1)
    print "login attempt: "+codename

    c.execute('SELECT id,code,logins FROM codes WHERE disabled=0')

    for row in c:
        if row[1]==codename:
            print " %s logged in %d times" %(row[1],row[2]+1)
            c.execute('UPDATE codes SET logins=? WHERE id=?',(row[2]+1,row[0]))
            db.commit()
            return True

def not_logged_in(code):
    return True
    if active.has_key(code):
        active[code].upgraded = False
        c.execute('UPDATE codes SET disabled=1 WHERE code=?',code)
        db.commit()
        print "%s logged in twice, deactivating" %(code)
    else: return True




cb = ChatBot()
cb.name = 'ChatBot'
dirties = """fuck
rape
raped
shit
piss
cunt
cock
dick
fag
gay
pussy
vagina
penis
ass
weiner
wiener
sex
fornicate
intercourse
nasty
do it
bang
boob
cyber
tit
ass
nigger
blowjob
bj
bra
boob
handjob
horny
sperm
jizz
cum
cannibis
weed
smoke
knife
gagged
young
tied up
handcuffs
lick
feels good
crack
butt
touch
fat
no friends
duct tape
bondage
bitch"""
dirties = dirties.split('\n')

def is_clean(message):
    message = message.lower()
    for word in dirties:
        if word in message: return False
    return True

def cleanse(message):
    message = message.lower()
    for word in dirties:
        message = message.replace(word,Word.randomPosWord('n'))
    return message

def haveChatBotTalkTo(x,message):
    if x==cb: return
    response = cb.talk(message)
    print cb.name+'(to '+x.name+'): '+response
    x.toUser(response)

def properTime(): ##some good time display
    return datetime.datetime.now().ctime()

def createName(address):
    ##do something with this address and create a unique nickname
    return nickname('an')

def findNewPartner(x):
    global ready
    if x == cb: return
    if x.blocked: return
    if x.partner != cb:
        x.partner.partner = cb
        x.partner = cb
        haveChatBotTalkTo(x,'?')

    if ready and ready!= x:
        x.partner = ready
        ready.partner = x
        ready = None
    else:
        ready = x
        x.partner = cb


class chatter(object):
    """
    chatters are people playing the game
    """

    def __init__(self,channel):
        self.name = createName(channel.iport)
        self.channel = channel ## the socket object
        self.partner = cb ## who this user is talking with
        self.unanswered = 0 ## the number of times the user has said something without hearing anything back
        self.upgraded = '' #if upgraded, this will be the secret code
        self.announce("joined")
        self.clean = True
        self.ts = []
        ip = channel.iport[0]
        if ip == '184.76.25.154':
            self.blocked = True
        else:
            self.blocked = False
        self.last_spoken = datetime.datetime.now()

    def toUser(self, message):
        """
        push a message to this user
        """
        self.unanswered = 0  ## the user has received a message
        #clear the count

        if self.upgraded: source = self.partner.name
        else: source = 'chatbot'

        if self.clean and not is_clean(message):
            message = cleanse(message)
            print "cleaner: "+message

        channel = self.channel
        if channel is None: return
        channel.push(source+': '+message+'\0')
        channel.push(emotion(message)+'\0')

    def fromUser(self,message):
        """
        user has sent in a message
        """
        self.last_spoken = datetime.datetime.now()
        
        
        if not self.blocked:
            self.ts.append(time.time())
            if len(self.ts) >= 5:
                # check the first time stamp
                dt = self.ts[-1] - self.ts[0]
                self.ts = self.ts[1:]  # rolling buffer
                print dt
                if dt < 30:
                    self.blocked = True
                    print 'blocking %s' % self.name

        print self.name+" (to "+self.partner.name+"):"+message
        if self.clean:
            self.clean = (self.clean and is_clean(message))
        if self.partner == cb: ##if the user is talking to the chatbot
            haveChatBotTalkTo(self,message)
            findNewPartner(self) ## and try to find a real partner for the user
        else:
            if message!='switch me': self.partner.toUser(message) ## send the message to the users real partner
            self.unanswered+=1 ## increment the count
            if (message=='switch me' and self.upgraded) \
               or (self.unanswered>2 and not (self.upgraded or self.partner.upgraded)):
                findNewPartner(self) ## if the partner hasnt responded, find a new one if both unupgraded

    def announce(self, logmessage):
	channel = self.channel
	if not channel: return
        print self.name+channel.iport+" has "+logmessage+" at "+properTime()

    def close(self):
        global ready
        if ready == self: ready = None
        findNewPartner(self.partner)
        self.announce("left")
        if active.has_key(self.upgraded): del active[self.upgraded]
        self.channel = None
	print 'goodbye', self.name

PORT = 43143

class SOCKETChannel(asynchat.async_chat):
    listeners = []

    def __init__(self, server, sock, addr):
        self.iport = str(addr)
        self.chatobj = chatter(self)
        asynchat.async_chat.__init__(self, sock)
        self.set_terminator("\n")
        self.data = ""
        SOCKETChannel.listeners.append(self)

    def handle_close(self) :
        self.chatobj.close()
        xs = SOCKETChannel.listeners
        if self in xs:
            xs.remove(self)
        asynchat.async_chat.handle_close(self)
        print "Connections remaining:"+str(len(xs))

    def handle_error(self):
        asynchat.async_chat.handle_error(self)
        self.handle_close()

    def __del__(self):
        pass

    def collect_incoming_data(self, data):
        self.data = self.data + data

    def found_terminator(self):
        data = self.data.strip('\n').strip('\0')
        self.data=""
        if data=='': return ##dont do anything with blank data

        secretcode = is_user(data)
        if secretcode is None or self.chatobj.upgraded:
            self.chatobj.fromUser(data)
            return

        #this is a real secret code.
        if not_logged_in(secretcode): #not_logged_in has sideeffects
            active[secretcode] = self.chatobj
            self.chatobj.upgraded = secretcode
            self.push("Secret Mode Activated\0")


def emotion(line):
    if happy(line): return '[smile]'
    if wink(line): return'[wink]'
    if confused(line): return '[question]'
    if swearing(line): return '[snarl]'
    if allcaps(line): return '[snarl]'
    if sad(line): return '[droop]'
    return '[normal]'


def happy(line):
    return re.compile(r'(yay|thanks)').match(line.lower())!=None

def confused(line):
    return re.compile(r'(wh(at|o|y|ere)|how|do|is|can).*\?').match(line.lower())!=None

def swearing(line):
    return re.compile(r'.* (fuck|shit|cunt).*').match(line.lower())!=None

def allcaps(line):
    return line.upper()==line

def wink(line):
    return re.compile(r'lol\!?').match(line.lower())!=None

def sad(line):
    return re.compile(r'(^|.* )(im?|my|me)( |$)').match(line.lower())!=None


class SOCKETServer(asyncore.dispatcher):

    def __init__(self, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind(("", port))
        self.listen(5)

    def handle_accept(self):
        conn, addr = self.accept()
        SOCKETChannel(self, conn, addr)


s = SOCKETServer(PORT)
print "Listening on port", PORT, "..."
try:
    asyncore.loop()
except KeyboardInterrupt:
    
    print 'messaging %s users' % len(SOCKETChannel.listeners)
    for l in SOCKETChannel.listeners:
        l.chatobj.toUser('I am rebooting. Give me a few seconds and refresh.')
    print 'shutting down'
    time.sleep(3)
    s.close()
