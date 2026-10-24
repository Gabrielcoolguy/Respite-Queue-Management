import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
from datetime import datetime
import re
import openpyxl
from openpyxl.chart import PieChart, BarChart, Reference
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.chart.label import DataLabelList

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

    def get_time_waited(self):
        return round(time.monotonic() - self.start_of_waiting_time, 1)

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
        now = time.monotonic() 
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
                else:
                    self.total_regular_customers_that_left += 1
                    self.total_customers_that_left += 1
                    del self.queue[customer_index]
                return True
            return False 
        except ValueError:
            return False

    def push_back_to_end(self):
        if not self.queue:
            return False
        
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
        return True

    def admin_dashboard(self, saved):
        if not saved:
            return "Dashboard stats print bypassed in GUI."

        try:
            now = datetime.now()
            date = f"{now.year}-{now.month}-{now.day}"
            
            wb = openpyxl.Workbook()
            sheet = wb['Sheet']
            sheet.title = "Customers"
            
            wb.create_sheet(title="Queue Time")
            column_width = 18

            data = [
                ["Customer Type", "Total Arrivals", "Served Customers", "Abandoned Queue"],
                ["Regular", self.total_regular_customers, self.total_regular_customers - self.total_regular_customers_that_left, f"=B2-C2"],
                ["Priority", self.total_priority_customers, self.total_priority_customers - self.total_priority_customers_that_left, f"=B3-C3"],
                ["Total", f"=SUM(B2:B3)", f"=SUM(C2:C3)", f"=SUM(D2:D3)"]
            ]
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
            bar_chart.legend.position = "b"
            bar_chart.layout = Layout(manualLayout=ManualLayout(x=0, y=0, h=0.65, w=0.9))
            
            sheet.add_chart(bar_chart, "F10")

            avg_wait = self.average_waiting_time()
            avg_serve = self.average_serving_time()
            wait_val = int(avg_wait) if avg_wait else 0
            serve_val = int(avg_serve) if avg_serve else 0

            sheet = wb["Queue Time"]
            
            data2 = [["Average Wait Time", "Average Serve Time", "Total Time"],
                    [wait_val, serve_val, f"=SUM(B1:B2)"]
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
            pie_chart.dataLabels.showVal = True
            pie_chart.dataLabels.showSerName = False
            pie_chart.dataLabels.position = "outEnd"
            
            sheet.add_chart(pie_chart, "F10")

            filename = f'{date}_ADMIN-STATS.xlsx'
            wb.save(filename)
            return filename
        except Exception as e:
            return str(e)

    def average_waiting_time(self):
        if not self.history:
            return 0
        total_waiting_time = sum(customer.waiting_time for customer in self.history)
        return total_waiting_time / len(self.history)

    def average_serving_time(self):
        if not self.history:
            return None

        total_meeting_time = 0
        for customer in self.history:
            total_meeting_time += customer.meeting_time

        total_customers = len(self.history)
        return total_meeting_time / total_customers


class PublicDisplayWindow(tk.Toplevel):
    def __init__(self, parent, system):
        super().__init__(parent)
        self.system = system
        
        self.title("PUBLIC: QUEUE DISPLAY")
        self.geometry("1100x750")
        
        self.BG_WHITE = "#FFFFFF"
        self.BG_LIGHT = "#E2E2E2"
        self.BG_MID = "#D4D4D4"
        self.BG_DARK = "#BCBCBC"
        self.FG_TEXT = "#222222"
        
        self.configure(bg=self.BG_WHITE)
        
        self._build_layout()
        self.update_clock()
        self.refresh_public_timer()

    def _build_layout(self):
        header_frame = tk.Frame(self, bg=self.BG_WHITE)
        header_frame.pack(fill="x", padx=40, pady=(30, 10))
        
        self.lbl_date = tk.Label(header_frame, text="DATE YEAR", font=("Arial", 16), bg=self.BG_WHITE, fg=self.FG_TEXT, justify="left")
        self.lbl_date.pack(side="left", anchor="nw")
        
        self.lbl_time = tk.Label(header_frame, text="00:00:00 PM", font=("Arial", 16), bg=self.BG_WHITE, fg=self.FG_TEXT)
        self.lbl_time.pack(side="right", anchor="ne")
        
        avg_box = tk.Frame(header_frame, bg="#A5A4A4", 
        bd=2, highlightbackground="#000000", highlightthickness=2)
        avg_box.pack(side="top", anchor="center", ipadx=40, ipady=15)
        
        self.lbl_avg_val = tk.Label(avg_box, text="0 MINUTES", font=("Arial", 46), bg="#A5A4A4", fg=self.FG_TEXT)
        self.lbl_avg_val.pack(pady=(10, 0))
        
        tk.Label(avg_box, text="AVERAGE WAITING TIME", font=("Arial", 14), bg="#A5A4A4", fg=self.FG_TEXT).pack(pady=(0, 10))

        main_container = tk.Frame(self, bg=self.BG_LIGHT,
        bd=2, highlightbackground="#000000", highlightthickness=2)
        main_container.pack(fill="both", expand=True, padx=40, pady=(20, 40))
        
        left_frame = tk.Frame(main_container, bg="#A5A4A4", width=400, height=300, 
        bd=2, highlightbackground="#000000", highlightthickness=2)
        left_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        
        serve_box = tk.Frame(left_frame, bg="#A5A4A4", width=450, height=350)
        serve_box.pack_propagate(False)
        serve_box.pack(padx=5, pady=20, anchor="center")
        
        tk.Label(serve_box, text="READY TO BE SERVED", font=("Arial", 20, "bold"), bg="#A5A4A4", fg=self.FG_TEXT).pack(pady=(10, 15))
        
        windows_container = tk.Frame(serve_box, bg="#A5A4A4")
        windows_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Window 1 Box
        win1_frame = tk.Frame(windows_container, bg="#E2E2E2", bd=2, highlightbackground="#000000", highlightthickness=2, width=190, height=200)
        win1_frame.pack_propagate(False)
        win1_frame.pack(side="left", padx=5)
        
        tk.Label(win1_frame, text="WINDOW 1", font=("Arial", 14, "bold"), bg="#E2E2E2", fg=self.FG_TEXT).pack(pady=(10, 5))
        self.lbl_win1_num = tk.Label(win1_frame, text="--", font=("Arial", 40, "bold"), bg="#E2E2E2", fg=self.FG_TEXT)
        self.lbl_win1_num.pack()
        self.lbl_win1_name = tk.Label(win1_frame, text="NONE", font=("Arial", 18), bg="#E2E2E2", fg=self.FG_TEXT)
        self.lbl_win1_name.pack(pady=5)
        
        # Window 2 Box
        win2_frame = tk.Frame(windows_container, bg="#E2E2E2", bd=2, highlightbackground="#000000", highlightthickness=2, width=190, height=200)
        win2_frame.pack_propagate(False)
        win2_frame.pack(side="right", padx=5)
        
        tk.Label(win2_frame, text="WINDOW 2", font=("Arial", 14, "bold"), bg="#E2E2E2", fg=self.FG_TEXT).pack(pady=(10, 5))
        self.lbl_win2_num = tk.Label(win2_frame, text="--", font=("Arial", 40, "bold"), bg="#E2E2E2", fg=self.FG_TEXT)
        self.lbl_win2_num.pack()
        self.lbl_win2_name = tk.Label(win2_frame, text="NONE", font=("Arial", 18), bg="#E2E2E2", fg=self.FG_TEXT)
        self.lbl_win2_name.pack(pady=5)

        right_frame = tk.Frame(main_container, bg="#A5A4A4", bd=2, highlightbackground="#000000", highlightthickness=2, width=600, height=300)
        right_frame.pack_propagate(False)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=40)
        
        in_line = tk.Label(right_frame, text="IN LINE", font=("Arial", 20), bg="#A5A4A4", fg=self.FG_TEXT)
        in_line.pack(pady=(20, 10))

        list_frame = tk.Frame(right_frame, bg="#A5A4A4")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.queue_listbox = tk.Listbox(
            list_frame,
            font=("Arial", 28),
            bg="#A5A4A4",
            fg=self.FG_TEXT,
            bd=0,
            highlightthickness=0,
            selectbackground="#A5A4A4",
            selectforeground=self.FG_TEXT,
            activestyle="none"
        )
        self.queue_listbox.pack(side="left", fill="both", expand=True)

    def update_clock(self):
        now = datetime.now()
        date_str = now.strftime("%B %d, %Y").upper()
        time_str = now.strftime("%H:%M:%S %p")
        
        self.lbl_date.config(text=date_str)
        self.lbl_time.config(text=time_str)
        
        self.after(1000, self.update_clock)

    def format_average(self, seconds):
        if not seconds or seconds == 0:
            return "0 MINUTES"
        if seconds < 60:
            value = int(round(seconds))
            return f"{value} SECONDS"
        else:
            value = int(round(seconds / 60))
            return f"{value} MINUTES"

    def refresh_public_timer(self):
        avg_wait_secs = self.system.average_waiting_time()
        self.lbl_avg_val.config(text=self.format_average(avg_wait_secs))

        all_called = list(self.system.history)
        if self.system.current_customer:
            all_called.append(self.system.current_customer)

        win1_customers = [all_called[i] for i in range(0, len(all_called), 2)]
        win2_customers = [all_called[i] for i in range(1, len(all_called), 2)]

        # Update Window 1
        if win1_customers:
            cust1 = win1_customers[-1]
            self.lbl_win1_num.config(text=str(cust1.number))
            self.lbl_win1_name.config(text=cust1.name)
        else:
            self.lbl_win1_num.config(text="--")
            self.lbl_win1_name.config(text="NONE")

        # Update Window 2
        if win2_customers:
            cust2 = win2_customers[-1]
            self.lbl_win2_num.config(text=str(cust2.number))
            self.lbl_win2_name.config(text=cust2.name)
        else:
            self.lbl_win2_num.config(text="--")
            self.lbl_win2_name.config(text="NONE")

        # Display remaining waiting queue in the IN LINE listbox
        current_queue_texts = [f"  {cust.number}    {cust.name}" for cust in self.system.queue]
        
        if getattr(self, '_last_queue_list', None) != current_queue_texts:
            self.queue_listbox.delete(0, tk.END)
            
            for i, text in enumerate(current_queue_texts):
                self.queue_listbox.insert(tk.END, text)
                row_color = self.BG_DARK if i % 2 == 0 else self.BG_MID
                self.queue_listbox.itemconfig(i, {'bg': row_color})
                
            self._last_queue_list = current_queue_texts

        self.after(1000, self.refresh_public_timer)

class QueueGUI(tk.Tk):
    def __init__(self, system):
        super().__init__()
        self.system = system
        self.title("ADMIN: QUEUE CONTROLLER")
        self.geometry("860x600")
        self.configure(bg="#000000")

        self.BG_BLACK = "#000000"
        self.BG_CARD = "#121212"
        self.BG_INPUT = "#1E1E1E"
        self.FG_WHITE = "#FFFFFF"
        self.FG_MUTED = "#AAAAAA"
        self.BORDER_GRAY = "#333333"
        self.ACCENT_BLUE = "#38bdf8"
        self.ACCENT_RED = "#ef4444"

        self._init_styles()
        self._build_layout()
        
        self.public_display = PublicDisplayWindow(self, self.system)
        
        self.refresh_timer()
        
    def _init_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview", background=self.BG_CARD, foreground=self.FG_WHITE,
            fieldbackground=self.BG_CARD, rowheight=32, font=("Segoe UI", 10), borderwidth=0,
        )
        style.configure(
            "Treeview.Heading", background="#222222", foreground=self.FG_WHITE,
            font=("Segoe UI", 10, "bold"), relief="flat",
        )
        style.map("Treeview", background=[("selected", "#333333")], foreground=[("selected", "#FFFFFF")])

    def _build_layout(self):
        header_frame = tk.Frame(self, bg=self.BG_BLACK)
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        tk.Label(
            header_frame, text="RESPITE QUEUE MANAGEMENT SYSTEM",
            font=("Segoe UI", 16, "bold"), bg=self.BG_BLACK, fg=self.FG_WHITE,
        ).pack(side="left")

        body_frame = tk.Frame(self, bg=self.BG_BLACK)
        body_frame.pack(fill="both", expand=True, padx=20, pady=10)

        left_panel = tk.Frame(body_frame, bg=self.BG_BLACK, width=320)
        left_panel.pack(side="left", fill="y", padx=(0, 15))

        right_panel = tk.Frame(body_frame, bg=self.BG_BLACK)
        right_panel.pack(side="right", fill="both", expand=True)
        
        add_card = tk.LabelFrame(
            left_panel, text=" INPUT ", font=("Segoe UI", 9, "bold"),
            bg=self.BG_CARD, fg=self.FG_WHITE, bd=1, relief="solid", highlightbackground=self.BORDER_GRAY,
        )
        add_card.pack(fill="x", pady=(0, 15), ipady=10, ipadx=10)

        tk.Label(add_card, text="Customer Name:", bg=self.BG_CARD, fg=self.FG_MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=10)
        self.entry_name = tk.Entry(add_card, bg=self.BG_INPUT, fg=self.FG_WHITE, insertbackground="white", bd=1, relief="solid", font=("Segoe UI", 10))
        self.entry_name.pack(fill="x", padx=10, pady=(2, 10))
        self.entry_name.bind("<Return>", lambda event: self.add_customer_action())
        
        self.var_vip = tk.BooleanVar()
        tk.Checkbutton(
            add_card, text="Priority", variable=self.var_vip, bg=self.BG_CARD, fg=self.FG_WHITE,
            selectcolor=self.BG_BLACK, activebackground=self.BG_CARD, activeforeground=self.FG_WHITE, font=("Segoe UI", 9),
        ).pack(anchor="w", padx=10, pady=(0, 10))

        tk.Button(
            add_card, text="ADD TO QUEUE", bg=self.FG_WHITE, fg=self.BG_BLACK, font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2", command=self.add_customer_action
        ).pack(fill="x", padx=10, pady=(10, 5), ipady=5)

        tk.Button(
            add_card, text="CALL NEXT CUSTOMER", bg=self.ACCENT_BLUE, fg=self.BG_BLACK, font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2", command=self.call_next_action
        ).pack(fill="x", padx=10, pady=(5, 5), ipady=5)

        extra_card = tk.LabelFrame(
            left_panel, text=" MANAGEMENT ", font=("Segoe UI", 9, "bold"),
            bg=self.BG_CARD, fg=self.FG_WHITE, bd=1, relief="solid", highlightbackground=self.BORDER_GRAY,
        )
        extra_card.pack(fill="x", ipady=10, ipadx=10)

        tk.Button(
            extra_card, text="Push Top Customer to End", bg=self.BG_INPUT, fg=self.FG_WHITE, font=("Segoe UI", 9),
            relief="solid", bd=1, cursor="hand2", command=self.push_to_end_action
        ).pack(fill="x", padx=10, pady=5, ipady=3)

        tk.Button(
            extra_card, text="Remove Ticket", bg=self.BG_INPUT, fg=self.ACCENT_RED, font=("Segoe UI", 9),
            relief="solid", bd=1, cursor="hand2", command=self.remove_ticket_action
        ).pack(fill="x", padx=10, pady=5, ipady=3)
        
        tk.Button(
            extra_card, text="Export Stats (Excel)", bg="#22c55e", fg="white", font=("Segoe UI", 9, "bold"),
            relief="flat", bd=1, cursor="hand2", command=self.export_excel_action
        ).pack(fill="x", padx=10, pady=(15,5), ipady=5)
        
        table_card = tk.LabelFrame(
            right_panel, text=" LIVE QUEUE ", font=("Segoe UI", 9, "bold"), bg=self.BG_CARD, fg=self.FG_WHITE,
            bd=1, relief="solid", highlightbackground=self.BORDER_GRAY
        )
        table_card.pack(fill="both", expand=True)

        columns = ("Ticket", "Name", "Status", "Wait Time")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def add_customer_action(self):
        name = self.entry_name.get().strip()
        if not bool(re.match(r"^[a-zA-Z\s]+$", name)):
            messagebox.showwarning("Input Error", "Please enter alphabetical letters only.")
            return
            
        if not name:
            messagebox.showwarning("Input Error", "Name cannot be empty.")
            return
            
        self.system.add_customer(name, self.var_vip.get())
        self.entry_name.delete(0, tk.END)
        self.var_vip.set(False)
        self.update_display()

    def call_next_action(self):
        served_customer = self.system.call_next()
        if not served_customer:
            messagebox.showinfo("Queue Empty", "No customers waiting.")
        self.update_display()

    def push_to_end_action(self):
        success = self.system.push_back_to_end()
        if not success:
            messagebox.showinfo("Action Failed", "Queue is empty, nothing to push back.")
        self.update_display()

    def remove_ticket_action(self):
        ticket_str = simpledialog.askstring("Remove Ticket", "Enter the Ticket Number to remove:")
        if ticket_str:
            success = self.system.remove_from_queue(ticket_str)
            if success:
                messagebox.showinfo("Success", f"Ticket {ticket_str} removed successfully.")
            else:
                messagebox.showerror("Error", f"Ticket {ticket_str} not found or invalid.")
        self.update_display()

    def export_excel_action(self):
        result = self.system.admin_dashboard(saved=True)
        if ".xlsx" in result:
            messagebox.showinfo("Export Successful", f"Stats exported to Excel file:\n{result}")
        else:
            messagebox.showerror("Export Failed", f"An error occurred:\n{result}")

    def update_display(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for customer in self.system.queue:
            status_text = "VIP" if customer.priority else "Regular"
            self.tree.insert("", "end", values=(f"{customer.number}", customer.name, status_text, f"{customer.get_time_waited()}s"))

    def refresh_timer(self):
        self.update_display()
        self.after(1000, self.refresh_timer)

if __name__ == "__main__":
    system = QueueSystem()
    app = QueueGUI(system)
    app.mainloop()