import sys
import getopt

import Checksum
import BasicSender
import time
import threading
import base64


'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False, sackMode=False):
        super(Sender, self).__init__(dest, port, filename, debug)

    #重写send，直接传入字节流并发送
    def send(self, message, address=None):
        if address is None:
            address = (self.dest,self.dport)
        self.sock.sendto(message, address)

    #重写make_packet，返回字节流
    def make_packet(self,msg_type,seqno,msg):
        body = "{}|{}|".format(msg_type,seqno).encode() + msg + "|".encode()
        checksum = Checksum.generate_checksum(body).encode()
        packet = body + checksum
        # print(packet)
        return packet


    # cut file into a sequence of packets
    def cut_packets(self):
        seqno = 0
        MaxPacketLen = 1400  #should be about 1400
        self.packet_seq = []
        self.window_size = 5  # send windows size
        msg = base64.encodebytes(self.infile.read(MaxPacketLen))
        #msg = self.infile.read(MaxPacketLen)
        msg_type = None
        
        while not msg_type == 'end':
            next_msg = base64.encodebytes(self.infile.read(MaxPacketLen))
            #next_msg = self.infile.read(MaxPacketLen)

            msg_type = 'data'
            if seqno == 0:
                msg_type = 'start'
            elif next_msg == b'':
                msg_type = 'end'

            packet = self.make_packet(msg_type,seqno,msg)
            self.packet_seq.append(packet)
            msg = next_msg
            seqno += 1
        self.infile.close()


    # Main sending loop.
    def start(self):
        self.sendBase = 0
        self.next_seq = self.sendBase
        self.window_size = 5  # send windows size
        self.timeout = 0.5
        
        self.cut_packets() # cut file into a sequence of packets
        
        if not sackMode:
            self.timer = None # only one timer for the window
            self.GBN_timer()
            while self.sendBase < len(self.packet_seq):
                if self.next_seq < self.sendBase + self.window_size:
                    for seqno in range(self.next_seq, self.sendBase + self.window_size):
                        if seqno >= len(self.packet_seq):
                            break
                        packet = self.packet_seq[seqno]
                        #print("sent: %s" % packet)
                        self.send(packet)
                    self.next_seq = self.sendBase + self.window_size
        
                response = self.receive()
                response = response.decode()
                self.handle_response(response)
                
            self.timer.cancel()
        
        elif sackMode:
            self.timers = {} # one timer for each packet in window
            while self.sendBase < len(self.packet_seq):
                if self.next_seq < self.sendBase + self.window_size:
                    for seqno in range(self.next_seq, self.sendBase + self.window_size):
                        if seqno >= len(self.packet_seq):
                            break
                        if seqno not in self.timers.keys():
                            packet = self.packet_seq[seqno]
                            #print("sent: %s" % packet)
                            self.send(packet)
                            # set a timer for each packet
                            self.timers[seqno] = threading.Timer(self.timeout, self.resend,args=[seqno])
                            self.timers[seqno].start()
                    
                    self.next_seq = self.sendBase + self.window_size
                    
                response = self.receive()
                response = response.decode()
                self.handle_response(response)
        
    # Handles a response from the receiver.
    def handle_response(self,response_packet):
        if Checksum.validate_checksum(response_packet):
            #print("recv: %s" % response_packet)
            
            msg_type,ackstr,_,_ = self.split_packet(response_packet)
            if msg_type == 'ack':
                ackno = int(ackstr)
                if (ackno <= self.sendBase):
                    pass
                else:
                    self.handle_new_ack(ackno)  
                    
            elif msg_type == 'sack':
                cum_ack = int(ackstr.split(';')[0])
                sack_list = ackstr.split(';')[1].split(',')
                if cum_ack <= self.sendBase:
                    pass
                else:
                    # cancel the timers
                    for seqno in range(self.sendBase,cum_ack):
                        if seqno in self.timers.keys():
                            self.timers[seqno].cancel()
                            del self.timers[seqno]
                    # update the window
                    self.sendBase = cum_ack
                if sack_list[0] != '':
                    # cancel timers for individual acks
                    sacks = [int(seqno) for seqno in sack_list]
                    for seqno in sacks:
                        if seqno in self.timers.keys():
                            self.timers[seqno].cancel()
                            del self.timers[seqno]
                        
        else:
            print("recv: %s <--- CHECKSUM FAILED" % response_packet)
    
    def resend(self,seqno):
        # for sackMode, resend one packet
        packet = self.packet_seq[seqno]
        #print("rsent: %s" % packet)
        self.send(packet)
        if self.sendBase < len(self.packet_seq):
            self.timers[seqno]=threading.Timer(self.timeout, self.resend,args=[seqno])
            self.timers[seqno].start()
        
    def GBN_timer(self):
        self.timer = threading.Timer(self.timeout, self.handle_timeout)
        self.timer.start()
    
    def handle_timeout(self):
        #print('sender time out')
        for seqno in range(self.sendBase,self.sendBase+self.window_size):
            if seqno >= len(self.packet_seq):
                break 
            packet = self.packet_seq[seqno]
            #print("resent: %s" % packet)
            self.send(packet)
        if self.sendBase < len(self.packet_seq):
            self.GBN_timer()

    def handle_new_ack(self, ack):
        self.sendBase = ack
        #print(f'sendBase = {self.sendBase}')
        self.timer.cancel()
        if self.sendBase < len(self.packet_seq):
            self.GBN_timer()

    def handle_dup_ack(self, ack):
        pass

    def log(self, msg):
        if self.debug:
            print(msg)


'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print("RUDP Sender")
        print("-f FILE | --file=FILE The file to transfer; if empty reads from STDIN")
        print("-p PORT | --port=PORT The destination port, defaults to 33122")
        print("-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost")
        print("-d | --debug Print debug messages")
        print("-h | --help Print this usage message")
        print("-k | --sack Enable selective acknowledgement mode")

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:dk", ["file=", "port=", "address=", "debug=", "sack="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False
    sackMode = False

    for o,a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True
        elif o in ("-k", "--sack="):
            sackMode = True

    s = Sender(dest, port, filename, debug, sackMode)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
