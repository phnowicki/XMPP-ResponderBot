#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
import getpass
import sleekxmpp
import threading
import MySQLdb
import smtplib
# Import the email modules we'll need
from email.mime.text import MIMEText
from datetime import datetime
from daemon import runner


class EchoBot(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)

        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.
        self.add_event_handler("ssl_invalid_cert", self.ssl_invalid_cert)
        self.add_event_handler("message", self.message)
		
    def get_data_from_db(self, jid):
        db = MySQLdb.connect(host="localhost", # your host, usually localhost
                     user="root", # your username
                     passwd="P@ssw0rd", # your password
                     db="xmppautobot") # name of the data base

        # you must create a Cursor object. It will let
        #  you execute all the query you need
        cursor = db.cursor()

        # Use all the SQL you like
        cursor.execute("SELECT message, email, presence, status FROM userdata WHERE jid='" + self.boundjid.bare + "'")
        row = cursor.fetchone()
        local_list = [row[0], row[1], row[2], row[3]]
        return local_list

    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        responsedata = self.get_data_from_db(self.boundjid.bare)
        self.send_presence(responsedata[2],responsedata[3])
        self.get_roster()

    def message(self, msg):
        """
        Process incoming message stanzas. Be aware that this also
        includes MUC messages and error messages. It is usually
        a good idea to check the messages's type before processing
        or sending replies.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        fromperson = str(msg['from'])
        msgbody = str(msg['body'])
        responsedata = self.get_data_from_db(self.boundjid.bare)
		
        if msg['type'] in ('chat', 'normal'):
            msg.reply(responsedata[0]).send()
			
		    #### Send an email to let the user know
            msg1 = MIMEText("Your contact " + fromperson + " sent you the following message to you at " + self.boundjid.bare + "\n\n" + msgbody)
            me = 'moderator@collaborationasylum.com'
            you = responsedata[1]
            msg1['Subject'] = 'You were sent a message to ' + self.boundjid.bare
            msg1['From'] = me
            msg1['To'] = you

            # Send the message via our own SMTP server, but don't include the
            # envelope header.
            s = smtplib.SMTP('192.168.1.50')
            s.sendmail(me, [you], msg1.as_string())
            s.quit()
			
    def ssl_invalid_cert(self, cert_module):
        print("")
		
class myThread (threading.Thread):
    def __init__(self, threadID, name, counter, id, pwd):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.id = id
        self.pwd = pwd
    def run(self):
        print "Starting " + self.name
        logging.basicConfig(format='%(levelname)-8s %(message)s')
        xmpp = EchoBot(self.id, self.pwd)
        xmpp.register_plugin('xep_0030') # Service Discovery
        xmpp.register_plugin('xep_0004') # Data Forms
        xmpp.register_plugin('xep_0060') # PubSub
        xmpp.register_plugin('xep_0199') # XMPP Ping
        if xmpp.connect(('192.168.1.15', 5222)):
			# If you do not have the dnspython library installed, you will need
			# to manually specify the name of the server if it does not match
			# the one in the JID. For example, to use Google Talk you would
			# need to use:
			#
			# if xmpp.connect(('talk.google.com', 5222)):
			#     ...
			xmpp.process(block=True)
			print("Done")
        else:
			print("Unable to connect.")
        print "Exiting " + self.name		
		
class App():

    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = '/var/run/mydaemon.pid'
        self.pidfile_timeout = 5

    def run(self):
        exitFlag = 0

        # Python versions before 3.0 do not use UTF-8 encoding
        # by default. To ensure that Unicode is handled properly
        # throughout SleekXMPP, we will set the default encoding
        # ourselves to UTF-8.
        if sys.version_info < (3, 0):
            reload(sys)
            sys.setdefaultencoding('utf8')
        else:
            raw_input = input
        db = MySQLdb.connect(host="localhost", # your host, usually localhost
                     user="root", # your username
                      passwd="P@ssw0rd", # your password
                      db="xmppautobot") # name of the data base

        # you must create a Cursor object. It will let
        #  you execute all the query you need
        cursor = db.cursor()

        # Use all the SQL you like
        cursor.execute("SELECT jid, password FROM userdata WHERE enabled=1")

        # get the number of rows in the resultset
        numrows = int(cursor.rowcount)

        thread1 = []

        # get and display one row at a time.
        for x in range(0,numrows):
            row = cursor.fetchone()
            thread1.append(myThread(1, "Thread-" + row[0], 1, row[0], row[1]))

        for x in range(0,numrows):	
            # Start new Threads
            thread1[x].start()

        print "Exiting Main Thread"
		
    def close(self):
        sys.exit()


app = App()
daemon_runner = runner.DaemonRunner(app)
daemon_runner.do_action()