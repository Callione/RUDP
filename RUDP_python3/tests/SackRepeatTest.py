import random

from tests.BasicTest import BasicTest

"""
This tests random packet repeats. We randomly decide to repeat about half of the
packets that go through the forwarder in either direction.

Note that to implement this we just needed to override the handle_packet()
method -- this gives you an example of how to extend the basic test case to
create your own.
"""
class SackRepeatTest(BasicTest):
    def __init__(self, forwarder, input_file):
        super(SackRepeatTest, self).__init__(forwarder, input_file, sackMode = True)

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
