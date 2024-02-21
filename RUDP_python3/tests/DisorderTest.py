import random

from tests.BasicTest import BasicTest

"""
This tests disorder of  packets. We randomly decide to shuffle 
packets that go through the forwarder in out_queue.

"""
class DisorderTest(BasicTest):
    def handle_tick(self,tick_interval):
        self.out_queue = random.shuffle(self.forwarder.out_queue)