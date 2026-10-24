# Modules
from datetime import datetime
import time
import re
import openpyxl
from openpyxl.chart import PieChart, BarChart, Reference
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.chart.label import DataLabelList


# TODO: QUEUE SYSTEM
class Customer:
    def __init__(self, customer_name, customer_number, priority_status):
        self.name = customer_name
        self.number = customer_number
        self.priority = priority_status
        self.waiting_time = 0
        self.start_of_waiting_time = time.monotonic()
        self.called_time = None
        self.meeting_time = 0
        self.done = False

    def current_meeting(self):
        if self.called_time is None:
            return 0
        if self.done:
            return self.meeting_time
        return time.monotonic() - self.called_time

    def __repr__(self):
        return f"NAME: {self.name}, TICKET NUMBER: {self.number}, PRIORITY: {self.priority}, TIME WAITED: {self.waiting_time}, TIME MEETING LASTED: {self.meeting_time}"


class QueueSystem:
    def __init__(self):
        self.queue = []
        self.history = []
        self.current_customer = None
        self.ticket_number = 101
        self.total_regular_customers = 0
        self.total_priority_customers = 0
        self.total_regular_customers_that_left = 0
        self.total_priority_customers_that_left = 0
        self.total_customers_that_left = 0

    def add_customer(self, name, is_priority=False):
        new_customer = Customer(name, self.ticket_number, is_priority)
        if is_priority:
            position = len(self.queue)
            for i, customer in enumerate(self.queue):
                if not customer.priority:
                    position = i
                    break

            self.queue.insert(position, new_customer)
            self.total_priority_customers += 1
        else:
            self.queue.append(new_customer)
            self.total_regular_customers += 1

        self.ticket_number += 1
        if self.ticket_number > 999:
            self.ticket_number = 101
        return new_customer

    def call_next(self):
        now = time.monotonic()  # Customer serve time timer will start.

        if self.current_customer is not None:
            self.current_customer.meeting_time = round(now - self.current_customer.called_time, 2)
            self.current_customer.done = True
            self.history.append(self.current_customer)
            self.current_customer = None

        if len(self.queue) > 0:
            next_customer = self.queue.pop(0)
            next_customer.waiting_time = round(now - next_customer.start_of_waiting_time, 2)
            next_customer.called_time = now
            self.current_customer = next_customer

        return self.current_customer

    def remove_from_queue(self, inputted_ticket):
        try:
            customer_to_be_removed = int(inputted_ticket)
            customer_index = None

            for i, customer in enumerate(self.queue):
                if customer.number == customer_to_be_removed:
                    customer_index = i
                    break

            if customer_index is not None:
                if self.queue[customer_index].priority:
                    self.total_priority_customers_that_left += 1
                    self.total_customers_that_left += 1
                    del self.queue[customer_index]
                    print(f"Ticket Number {customer_to_be_removed} has been removed.")
                else:
                    self.total_regular_customers_that_left += 1
                    self.total_customers_that_left += 1
                    del self.queue[customer_index]
                    print(f"Ticket Number {customer_to_be_removed} has been removed.")
            else:
                print(f"Ticket Number {customer_to_be_removed} was not found.")
        except ValueError:
            print("Something went wrong, please input a number.")

    def push_back_to_end(self):
        position = 0
        late_customer = self.queue[0]
        if late_customer.priority:
            for i, customer in enumerate(self.queue):
                if not customer.priority:
                    position = i
                    break
            self.queue.insert(position, late_customer)
            del self.queue[0]
        else:
            self.queue.append(late_customer)
            del self.queue[0]


    def admin_dashboard(self, saved):
        try:
            now = datetime.now()
            date = f"{now.year}-{now.month}-{now.day}"

            # Below not needed for GUI only for terminal
            total_customers = len(self.history)   
            total_queue_time = format_average(self.average_serving_time() + self.average_waiting_time())

            print(f"Total Overall Customers: {total_customers}")
            print(f"Total Regular Customers: {self.total_regular_customers}")
            print(f"Total Priority Customers: {self.total_priority_customers}")
            print(f"Total Customers that left: {self.total_customers_that_left}")
            print(f"Average Meeting Time: {format_average(self.average_serving_time())}")
            print(f"Average Waiting Time: {format_average(self.average_waiting_time())}")
            print(f"Total Queue Time: {total_queue_time}")

        
            if saved:
                wb = openpyxl.Workbook()
                sheet = wb['Sheet']
                sheet.title = "Customers"
                wb.create_sheet(title="Queue Time")
                column_width = 18


                data = [["Customer Type", "Total Arrivals", "Served Customers", "Abandoned Queue"],
                        ["Regular", self.total_regular_customers, self.total_regular_customers - self.total_regular_customers_that_left, f"=B2-C2"],
                        ["Priority", self.total_priority_customers, self.total_priority_customers - self.total_priority_customers_that_left, f"=B3-C3"],
                        ["Total", f"=SUM(B2:B3)", f"=SUM(C2:C3)", f"=SUM(D2:D3)"]]

                for row in data:
                    sheet.append(row)

                for column in ["A", "B", "C", "D"]:
                    sheet.column_dimensions[column].width = column_width

                bar_chart = BarChart()
                data_bar_chart = Reference(sheet, min_col=1, min_row=2, max_col=4, max_row=4)
                bar_chart.add_data(data_bar_chart, titles_from_data=True, from_rows=True)

                categories = Reference(sheet, min_col=2, min_row=1, max_col=4, max_row=1)
                bar_chart.set_categories(categories)

                bar_chart.grouping = "clustered"
                bar_chart.overlap = -10

                bar_chart.y_axis.delete = False
                bar_chart.x_axis.delete = False

                bar_chart.legend.position = "b"

                bar_chart.layout = Layout(
                    manualLayout=ManualLayout(
                        x=0,
                        y=0,
                        h=0.65,
                        w=0.9,
                        ))

                sheet.add_chart(bar_chart, "F10")

                sheet = wb["Queue Time"]

                data2 = [["Average Wait Time", "Average Serve Time", "Total Time"],
                         [int(format_average(self.average_waiting_time())[0]), int(format_average(self.average_serving_time())[0]), f"=SUM(B1:B2)"]    
                ]
                

                for row in data2:
                    sheet.append(row)

                for column in ["A", "B"]:
                    sheet.column_dimensions[column].width = column_width

                pie_chart = PieChart()

                data_pie_chart = Reference(sheet, min_col=1, min_row=2, max_col=3, max_row=2)
                pie_chart.add_data(data_pie_chart, titles_from_data=True)

                categories_pie_chart = Reference(sheet, min_col=1, min_row=1, max_col=3, max_row=1)
                pie_chart.set_categories(categories_pie_chart)

                pie_chart.dataLabels = DataLabelList()

                pie_chart.dataLabels.showPercent = True
                pie_chart.dataLabels.showCatName = False
                pie_chart.dataLabels.showVal = False
                pie_chart.dataLabels.showSerName = False
                pie_chart.dataLabels.position = "outEnd"


                sheet.add_chart(pie_chart, "F10")

                wb.save(f'{date}_ADMIN-STATS.xlsx')
                
            else:
                print("You chose not to save.")
        except TypeError:
                    print("No customers were served yet.")
    

# TODO: Average time functions 
    def average_serving_time(self):
        # Total of all serving times divided by the number of customers.
        if not self.history:
            return None

        total_meeting_time = 0
        for customer in self.history:
            total_meeting_time += customer.meeting_time

        total_customers = len(self.history)

        return total_meeting_time / total_customers

    def average_waiting_time(self):
        # Total of all waiting times divided by the number of customers.
        if not self.history:
            return None

        total_waiting_time = 0
        for customer in self.history:
            total_waiting_time += customer.waiting_time

        total_customers = len(self.history)

        return total_waiting_time / total_customers


# TODO: GUI (terminal based for now until code fully done)
def format_hms(seconds):
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_average(seconds):
    if seconds is None:
        return "-- MINUTES"

    if seconds < 60:
        value = int(round(seconds))
        unit = "SECOND"
    else:
        value = int(round(seconds / 60))
        unit = "MINUTE"

    if value != 1:
        unit += "S"

    return f"{value} {unit}"


def tag(customer):
    if customer.priority:
        return "[VIP]"
    return ""


def header(title):
    now = datetime.now()
    date = f"{now.strftime('%B').upper()} {now.day}, {now.year}"
    clock = now.strftime("%I:%M:%S %p")
    print("=" * 40)
    print(f"{date}             {clock}")
    print(title.center(40))
    print("=" * 40)


def customer_view(system):
    header("CUSTOMER VIEW")
    print(f"AVERAGE MEETING TIME: {format_average(system.average_serving_time())}")
    print(f"AVERAGE WAITING TIME: {format_average(system.average_waiting_time())}")
    print()

    if system.current_customer is not None:
        print(f"READY TO BE SERVED: {system.current_customer.number}  {system.current_customer.name} {tag(system.current_customer)}")
    else:
        print("READY TO BE SERVED: ---")
    print()
    print("NEXT IN LINE:")
    next_customers = system.queue

    if not next_customers:
        print("(Nobody is waiting)")
    for customer in next_customers:
        print(f"{customer.number}  {customer.name} {tag(customer)}")


def control_view(system):
    header("USER CONTROL VIEW")
    print("CURRENT CUSTOMER")

    if system.current_customer:
        customer = system.current_customer
        print(f"{customer.number}  {customer.name} {tag(customer)}")
        print(f"Time served: {format_hms(customer.current_meeting())}")
    else:
        print("---")
    print()
    print("WAITING QUEUE")

    if not system.queue:
        print("(empty)")
    for customer in system.queue:
        print(f"{customer.number}  {customer.name} {tag(customer)}  (waiting {format_hms(time.monotonic() - customer.start_of_waiting_time)})")


if __name__ == "__main__":
    system = QueueSystem()

    while True:
        print()
        print("1. Enter customer's name  2. Call next customer  3. Remove a customer 4. Push Customer to End 5. Control view  6. Customer view 7. Admin Dashboard 8. Close")
        choice = input("Choose: ").strip()

        if choice == "1":
            name = input("Enter customer's name: ").strip()
            while bool(re.match(r"^[a-zA-Z\s]+$", name)) != True:
                print("Please use alphabetical letters only.")
                name = input("Enter customer's name: ").strip()
            else:
                pass

            while name == "":
                print("Name cannot be empty.")
                name = input("Enter customer's name: ").strip()
            vip = input("VIP/Priority? Y/N: ").strip().upper()
            while vip not in ("Y", "N"):
                vip = input("Please type Y or N: ").strip().upper()

            customer = system.add_customer(name, is_priority=(vip == "Y"))
            kind = "VIP" if customer.priority else "Regular"
            print(f"{customer.name} ({kind}) - ticket number {customer.number} (timer started)")

        elif choice == "2":
            current_customer = system.call_next()
            if current_customer is not None:
                print(f"Now serving {current_customer.number} - {current_customer.name} {tag(current_customer)}")
            else:
                print("No customers waiting.")


        elif choice == "3":
            inputted_ticket = input("Input the ticket of a customer to remove them:")
            system.remove_from_queue(inputted_ticket)

        elif choice == "4":
            system.push_back_to_end()
        
        elif choice == "5":
            control_view(system)

        elif choice == "6":
            customer_view(system)

        elif choice == "7":
            saved = input("Do you want to save the admin dashboard stats as an excel file? Y/N").strip().upper()
            while saved not in ("Y", "N"):
                saved = input("Do you want to save the admin dashboard stats as an excel file? Y/N")
            system.admin_dashboard(saved=(saved == "Y"))

        elif choice == "8":
            break

        else:
            print("Invalid choice.")
