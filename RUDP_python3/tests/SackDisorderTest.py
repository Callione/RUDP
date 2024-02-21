import random

from tests.BasicTest import BasicTest

"""
This tests disorder of  packets. We randomly decide to shuffle 
packets that go through the forwarder in out_queue.

Note that to implement this we just needed to override the handle_packet()
method -- this gives you an example of how to extend the basic test case to
create your own.
"""
class SackDisorderTest(BasicTest):
    def __init__(self, forwarder, input_file):
        super(SackDisorderTest, self).__init__(forwarder, input_file, sackMode = True)

    def handle_tick(self,tick_interval):
        self.out_queue = random.shuffle(self.forwarder.out_queue)