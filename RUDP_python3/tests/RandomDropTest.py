import random

from tests.BasicTest import BasicTest

"""
This tests random packet drops. We randomly decide to drop about half of the
packets that go through the forwarder in either direction.

Note that to implement this we just needed to override the handle_packet()
method -- this gives you an example of how to extend the basic test case to
create your own.
"""
class RandomDropTest(BasicTest):
    def handle_packet(self):
        for p in self.forwarder.in_queue:
            choice = random.choice([True,False])
            if self.forwarder.debug:
                print(choice)
            if choice:
                self.forwarder.out_queue.append(p)
            
            # if random.choice([True, False]):
            #     self.forwarder.out_queue.append(p)
                
            

        # empty out the in_queue
        self.forwarder.in_queue = []
