import random

from tests.BasicTest import BasicTest

"""
This tests random packet repeats. We randomly decide to repeat about half of the
packets that go through the forwarder in either direction.

"""
class RepeatTest(BasicTest):
    def handle_packet(self):
        for p in self.forwarder.in_queue:
            choice = random.choice([True,False])
            if self.forwarder.debug and choice:
                print('repeat')
            if choice:
                self.forwarder.out_queue.append(p)  #if chosen, repeat it
            self.forwarder.out_queue.append(p)            

        # empty out the in_queue
        self.forwarder.in_queue = []