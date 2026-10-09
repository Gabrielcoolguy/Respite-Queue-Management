# Modules
from collections import deque
from datetime import datetime
import time

#TODO: QUEUE_SYSTEM
class Customer:
    def __init__(self, customer_name, customer_number, priority_status, waiting_time):
        self.name = customer_name
        self.number = customer_number
        self.priority = priority_status
        self.waiting_time = waiting_time
        self.start_of_waiting_time = time.time()
        self.called_time = None
        self.meeting_time = 0
        self.done = False

    def current_meeting(self):
        if self.called_time is None:
            return 0
        if self.done:
            return self.meeting_time
        return time.time() - self.called_time

    def __repr__(self):
        return f'NAME: {self.name}, TICKET NUMBER: {self.number}, PRIORITY: {self.priority}, TIME: {self.waiting_time}'


class Queue_system:
    def __init__(self):
        self.queue = deque()
        self.history = []
        self.current = None
        self.ticket_number = 101

    def add_customer(self, name, is_priority=False):
        new_customer = Customer(name, self.ticket_number, is_priority, waiting_time=0)
        if is_priority:
            position = sum(1 for c in self.queue if c.priority)
            self.queue.insert(position, new_customer)
        else:
            self.queue.append(new_customer)

        self.ticket_number += 1
        if self.ticket_number > 999:
            self.ticket_number = 101
        return new_customer

    def call_next(self):
        now = time.time()

        if self.current is not None:
            self.current.meeting_time = round(now - self.current.called_time, 2)
            self.current.done = True
            self.history.append(self.current)
            self.current = None

        if self.queue:
            nxt = self.queue.popleft()
            nxt.waiting_time = round(now - nxt.start_of_waiting_time, 2)
            nxt.called_time = now
            self.current = nxt

        return self.current

    def average_meeting_time(self):
        """Total of all meeting times divided by the number of customers."""
        if not self.history:
            return None
        return sum(c.meeting_time for c in self.history) / len(self.history)

    def average_waiting_time(self):
        """Total of all waiting times divided by the number of customers."""
        if not self.history:
            return None
        return sum(c.waiting_time for c in self.history) / len(self.history)


def format_hms(seconds):
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_average(seconds):
    if seconds is None:
        return "-- MINUTES"
    if seconds < 60:
        n = int(round(seconds))
        return f"{n} SECOND" + ("" if n == 1 else "S")
    n = int(round(seconds / 60))
    return f"{n} MINUTE" + ("" if n == 1 else "S")


def tag(customer):
    return " [VIP]" if customer.priority else ""


def header(title):
    now = datetime.now()
    date = f"{now.strftime('%B').upper()} {now.day}, {now.year}"
    clock = now.strftime("%I:%M:%S %p")
    print("\n" + "=" * 44)
    print(f"{date}{clock:>{44 - len(date)}}")
    print(title.center(44))
    print("=" * 44)


def customer_view(system):
    header("CUSTOMER VIEW")
    print(f"AVERAGE MEETING TIME: {format_average(system.average_meeting_time())}")
    print()
    if system.current:
        print(f"READY TO BE SERVED: {system.current.number}  {system.current.name}{tag(system.current)}")
    else:
        print("READY TO BE SERVED: ---")
    print()
    print("NEXT IN LINE:")
    next_five = list(system.queue)[:5]
    if not next_five:
        print("  (nobody waiting)")
    for c in next_five:
        print(f"  {c.number}  {c.name}{tag(c)}")


def control_view(system):
    header("USER CONTROL VIEW")
    print("CURRENT CUSTOMER")
    if system.current:
        c = system.current
        print(f"  {c.number}  {c.name}{tag(c)}")
        print(f"  Time served: {format_hms(c.current_meeting())}")
    else:
        print("  ---")
    print()
    print("WAITING QUEUE")
    if not system.queue:
        print("  (empty)")
    for c in system.queue:
        print(f"  {c.number}  {c.name}{tag(c)}  (waiting {format_hms(time.time() - c.start_of_waiting_time)})")


if __name__ == "__main__":
    system = Queue_system()

    while True:
        print("\n1. Enter customer's name  2. NEXT  3. Control view  4. Customer view  5. CLOSE")
        choice = input("Choose: ").strip()

        if choice == "1":
            name = input("Enter customer's name: ").strip()
            if name == "":
                print("Name cannot be empty.")
                continue
            vip = input("VIP/Priority? Y/N: ").strip().upper()
            while vip not in ("Y", "N"):
                vip = input("Please type Y or N: ").strip().upper()

            customer = system.add_customer(name, is_priority=(vip == "Y"))
            kind = "VIP" if customer.priority else "Regular"
            print(f"{customer.name} ({kind}) - ticket number {customer.number} (timer started)")

        elif choice == "2":
            current = system.call_next()
            if current:
                print(f"Now serving {current.number} - {current.name}{tag(current)}")
            else:
                print("No customers waiting.")

        elif choice == "3":
            control_view(system)

        elif choice == "4":
            customer_view(system)

        elif choice == "5":
            break

        else:
            print("Invalid choice.")