# Modules
from collections import deque
import time

# TODO: QUEUE SYSTEM
class Customer:
    def __init__(self, customer_name, customer_number, priority_status, waiting_time):
        self.name = customer_name
        self.number = customer_number
        self.priority = priority_status
        self.waiting_time = waiting_time
        self.start_of_waiting_time = time.time() 


    def __repr__(self):
        return f'NAME: {self.name}, TICKET NUMBER: {self.number}, PRIORITY: {self.priority}, TIME: {self.waiting_time}'


class Queue_system:
    def __init__(self):
        #self.queue = []
        self.queue = deque()
        self.ticket_number = 1

    def add_customer(self, name, is_priority = False):
        new_customer = Customer(name, self.ticket_number, is_priority, waiting_time=0)
        if is_priority == True:
            #self.queue.insert(0, new_customer)
            self.queue.appendleft(new_customer)
        else:
            self.queue.append(new_customer)

        self.ticket_number += 1
        if self.ticket_number == 100:
            self.ticket_number = 1

    def remove_customer(self):
        #print(self.queue[0].start_of_waiting_time)
        
        time_waited = time.time() - self.queue[0].start_of_waiting_time # Start minus time as of removal from queue.
        self.queue[0].waiting_time = round(float(time_waited), 2)
        #print(system.queue)
        
        self.queue.popleft()
        
        

system = Queue_system()

name = input('ur name')
vip = input('vip? Y/N')
if vip.upper() =='Y':
    system.add_customer(name, is_priority=True)
if vip.upper() =='N':
    system.add_customer(name, is_priority=False)

customer_finished = input('Is customer done? Y/N')
if customer_finished.upper() == 'Y':
    system.remove_customer()
else:
    pass

print(list(system.queue))



# TODO: DATABASE (Use arraylist instead)



# TODO: GUI



# TODO: QUEUE TICKET DISPLAY



# TODO: DISPLAY OF AVERAGE TIME A MEETING LASTS