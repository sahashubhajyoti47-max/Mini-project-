import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
import json
import csv
import os

# -------------------- SETTINGS --------------------

APP_TITLE = "Student Expense Tracker"
DATA_FILE = "expenses_data.json"
CURRENCY = "₹"

BG_COLOR = "#F2F5FA"
CARD_COLOR = "#FFFFFF"
PRIMARY_COLOR = "#2563EB"
DARK_COLOR = "#172554"
TEXT_COLOR = "#334155"
GREEN_COLOR = "#15803D"
RED_COLOR = "#DC2626"

categories = [
    "Food",
    "Travel",
    "Education",
    "Shopping",
    "Bills",
    "Entertainment",
    "Health",
    "Other"
]

expenses = []
budget = 0.0


# -------------------- DATA STORAGE --------------------

def load_data():
    global expenses, budget

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            expenses = data.get("expenses", [])
            budget = float(data.get("budget", 0))

        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            expenses = []
            budget = 0.0
    else:
        expenses = []
        budget = 0.0


def save_data():
    data = {
        "expenses": expenses,
        "budget": budget
    }

    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
    except OSError as error:
        messagebox.showerror(
            "Save Error",
            f"Could not save your data:\n{error}"
        )


# -------------------- MAIN WINDOW --------------------

root = tk.Tk()
root.title(APP_TITLE)
root.geometry("1050x720")
root.minsize(850, 620)
root.configure(bg=BG_COLOR)

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    background="white",
    foreground=TEXT_COLOR,
    rowheight=30,
    fieldbackground="white",
    font=("Arial", 10)
)

style.configure(
    "Treeview.Heading",
    background="#E2E8F0",
    foreground=DARK_COLOR,
    font=("Arial", 10, "bold"),
    padding=8
)

style.map(
    "Treeview",
    background=[("selected", "#BFDBFE")],
    foreground=[("selected", DARK_COLOR)]
)

load_data()


# -------------------- HELPER FUNCTIONS --------------------

def money(amount):
    return f"{CURRENCY}{amount:,.2f}"


def calculate_total():
    return sum(float(item["amount"]) for item in expenses)


def update_summary():
    total = calculate_total()
    remaining = budget - total

    total_label.config(text=money(total))
    budget_label.config(text=money(budget))
    remaining_label.config(text=money(remaining))

    if remaining < 0:
        remaining_label.config(fg=RED_COLOR)
        status_label.config(
            text=f"Budget exceeded by {money(abs(remaining))}",
            fg=RED_COLOR
        )
    elif budget > 0:
        remaining_label.config(fg=GREEN_COLOR)
        status_label.config(
            text=f"You have {money(remaining)} left in your budget.",
            fg=GREEN_COLOR
        )
    else:
        remaining_label.config(fg=TEXT_COLOR)
        status_label.config(
            text="Set a budget to track your spending.",
            fg=TEXT_COLOR
        )


def refresh_table():
    for row in expense_table.get_children():
        expense_table.delete(row)

    # Show newest expenses first
    sorted_expenses = sorted(
        expenses,
        key=lambda item: item.get("id", 0),
        reverse=True
    )

    for item in sorted_expenses:
        expense_table.insert(
            "",
            "end",
            iid=str(item["id"]),
            values=(
                item["date"],
                item["name"],
                item["category"],
                money(float(item["amount"]))
            )
        )

    update_summary()


def clear_form():
    name_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)
    category_box.set(categories[0])
    date_entry.delete(0, tk.END)
    date_entry.insert(0, date.today().isoformat())
    name_entry.focus_set()


# -------------------- ADD EXPENSE --------------------

def add_expense():
    name = name_entry.get().strip()
    amount_text = amount_entry.get().strip()
    category = category_box.get()
    expense_date = date_entry.get().strip()

    if not name:
        messagebox.showwarning(
            "Missing Information",
            "Please enter an expense name."
        )
        name_entry.focus_set()
        return

    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        messagebox.showwarning(
            "Invalid Amount",
            "Please enter a valid amount greater than zero."
        )
        amount_entry.focus_set()
        return

    try:
        date.fromisoformat(expense_date)
    except ValueError:
        messagebox.showwarning(
            "Invalid Date",
            "Enter the date in YYYY-MM-DD format, for example 2026-10-26."
        )
        date_entry.focus_set()
        return

    if category not in categories:
        messagebox.showwarning(
            "Invalid Category",
            "Please select a valid category."
        )
        return

    new_id = max(
        (int(item.get("id", 0)) for item in expenses),
        default=0
    ) + 1

    expenses.append({
        "id": new_id,
        "name": name,
        "amount": round(amount, 2),
        "category": category,
        "date": expense_date
    })

    save_data()
    refresh_table()
    clear_form()

    status_label.config(
        text=f"Expense '{name}' added successfully!",
        fg=GREEN_COLOR
    )


# -------------------- DELETE EXPENSE --------------------

def delete_expense():
    selected = expense_table.selection()

    if not selected:
        messagebox.showwarning(
            "No Selection",
            "Please select an expense from the table first."
        )
        return

    answer = messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to delete the selected expense?"
    )

    if not answer:
        return

    selected_ids = {int(item_id) for item_id in selected}

    expenses[:] = [
        item for item in expenses
        if int(item.get("id", 0)) not in selected_ids
    ]

    save_data()
    refresh_table()

    status_label.config(
        text="Selected expense(s) deleted.",
        fg=GREEN_COLOR
    )


# -------------------- SET BUDGET --------------------

def set_budget():
    global budget

    try:
        new_budget = float(budget_entry.get().strip())

        if new_budget < 0:
            raise ValueError

    except ValueError:
        messagebox.showwarning(
            "Invalid Budget",
            "Please enter a valid budget of zero or more."
        )
        return

    budget = round(new_budget, 2)

    save_data()
    update_summary()

    status_label.config(
        text="Budget saved successfully!",
        fg=GREEN_COLOR
    )


# -------------------- EXPORT CSV --------------------

def export_csv():
    if not expenses:
        messagebox.showinfo(
            "No Expenses",
            "Add some expenses before exporting."
        )
        return

    file_path = filedialog.asksaveasfilename(
        title="Export Expenses",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        initialfile="student_expenses.csv"
    )

    if not file_path:
        return

    try:
        with open(
            file_path, "w", newline="", encoding="utf-8-sig"
        ) as file:
            writer = csv.writer(file)

            writer.writerow([
                "Date",
                "Expense Name",
                "Category",
                "Amount (INR)"
            ])

            for item in sorted(
                expenses, key=lambda entry: entry.get("date", "")
            ):
                writer.writerow([
                    item["date"],
                    item["name"],
                    item["category"],
                    item["amount"]
                ])

        messagebox.showinfo(
            "Export Successful",
            f"Expenses exported successfully!\n\n{file_path}"
        )

    except OSError as error:
        messagebox.showerror(
            "Export Error",
            f"Could not export expenses:\n{error}"
        )


# -------------------- HEADER --------------------

header = tk.Frame(root, bg=DARK_COLOR, padx=25, pady=20)
header.pack(fill="x")

tk.Label(
    header,
    text="Student Expense Tracker",
    font=("Arial", 24, "bold"),
    bg=DARK_COLOR,
    fg="white"
).pack(anchor="w")

tk.Label(
    header,
    text="Manage your daily expenses easily!",
    font=("Arial", 11),
    bg=DARK_COLOR,
    fg="#CBD5E1"
).pack(anchor="w", pady=(5, 0))


# -------------------- SUMMARY CARDS --------------------

summary_frame = tk.Frame(root, bg=BG_COLOR, padx=20, pady=15)
summary_frame.pack(fill="x")

for column in range(3):
    summary_frame.columnconfigure(column, weight=1)


def create_summary_card(parent, column, title, initial, color):
    card = tk.Frame(
        parent,
        bg=CARD_COLOR,
        padx=15,
        pady=12,
        highlightbackground="#E2E8F0",
        highlightthickness=1
    )
    card.grid(
        row=0,
        column=column,
        sticky="nsew",
        padx=5,
        pady=2
    )

    tk.Label(
        card,
        text=title,
        font=("Arial", 10),
        bg=CARD_COLOR,
        fg=TEXT_COLOR
    ).pack(anchor="w")

    label = tk.Label(
        card,
        text=initial,
        font=("Arial", 18, "bold"),
        bg=CARD_COLOR,
        fg=color
    )
    label.pack(anchor="w", pady=(6, 0))

    return label


total_label = create_summary_card(
    summary_frame, 0, "Total Spent", money(0), PRIMARY_COLOR
)

budget_label = create_summary_card(
    summary_frame, 1, "Monthly Budget", money(0), DARK_COLOR
)

remaining_label = create_summary_card(
    summary_frame, 2, "Budget Remaining", money(0), GREEN_COLOR
)


# -------------------- BUDGET SETTING --------------------

budget_frame = tk.Frame(root, bg=BG_COLOR, padx=25)
budget_frame.pack(fill="x", pady=(0, 10))

tk.Label(
    budget_frame,
    text="Set your budget (₹):",
    font=("Arial", 10, "bold"),
    bg=BG_COLOR,
    fg=TEXT_COLOR
).pack(side="left")

budget_entry = tk.Entry(
    budget_frame,
    font=("Arial", 11),
    width=15,
    relief="solid",
    bd=1
)
budget_entry.pack(side="left", padx=10, ipady=4)

budget_entry.insert(0, str(budget))


def make_button(parent, text, command, color=PRIMARY_COLOR):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=color,
        fg="white",
        activebackground=color,
        activeforeground="white",
        font=("Arial", 10, "bold"),
        relief="flat",
        cursor="hand2",
        padx=12,
        pady=7
    )


make_button(
    budget_frame, "Save Budget", set_budget, DARK_COLOR
).pack(side="left")


# -------------------- EXPENSE FORM --------------------

form = tk.LabelFrame(
    root,
    text="  Add New Expense  ",
    font=("Arial", 12, "bold"),
    bg=CARD_COLOR,
    fg=DARK_COLOR,
    padx=15,
    pady=12
)
form.pack(fill="x", padx=25, pady=5)

form.columnconfigure(1, weight=1)
form.columnconfigure(3, weight=1)


def form_label(text, row, column):
    tk.Label(
        form,
        text=text,
        font=("Arial", 10),
        bg=CARD_COLOR,
        fg=TEXT_COLOR
    ).grid(
        row=row,
        column=column,
        sticky="w",
        padx=6,
        pady=7
    )


form_label("Expense Name:", 0, 0)

name_entry = tk.Entry(form, font=("Arial", 10), relief="solid", bd=1)
name_entry.grid(
    row=0, column=1, sticky="ew", padx=6, pady=7, ipady=5
)

form_label("Amount (₹):", 0, 2)

amount_entry = tk.Entry(
    form, font=("Arial", 10), relief="solid", bd=1
)
amount_entry.grid(
    row=0, column=3, sticky="ew", padx=6, pady=7, ipady=5
)

form_label("Category:", 1, 0)

category_box = ttk.Combobox(
    form,
    values=categories,
    state="readonly",
    font=("Arial", 10)
)
category_box.grid(
    row=1, column=1, sticky="ew", padx=6, pady=7, ipady=3
)
category_box.set(categories[0])

form_label("Date (YYYY-MM-DD):", 1, 2)

date_entry = tk.Entry(
    form, font=("Arial", 10), relief="solid", bd=1
)
date_entry.grid(
    row=1, column=3, sticky="ew", padx=6, pady=7, ipady=5
)
date_entry.insert(0, date.today().isoformat())

form_buttons = tk.Frame(form, bg=CARD_COLOR)
form_buttons.grid(
    row=2, column=0, columnspan=4, sticky="w", pady=(10, 0)
)

make_button(
    form_buttons, "Add Expense", add_expense, PRIMARY_COLOR
).pack(side="left", padx=(5, 8))

make_button(
    form_buttons, "Clear Form", clear_form, "#64748B"
).pack(side="left")


# -------------------- EXPENSE TABLE --------------------

table_frame = tk.LabelFrame(
    root,
    text="  Expense History  ",
    font=("Arial", 12, "bold"),
    bg=CARD_COLOR,
    fg=DARK_COLOR,
    padx=10,
    pady=10
)
table_frame.pack(
    fill="both", expand=True, padx=25, pady=(10, 5)
)

columns = ("date", "name", "category", "amount")

expense_table = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings",
    selectmode="extended"
)

expense_table.heading("date", text="Date")
expense_table.heading("name", text="Expense Name")
expense_table.heading("category", text="Category")
expense_table.heading("amount", text="Amount (₹)")

expense_table.column("date", width=115, anchor="center")
expense_table.column("name", width=240, anchor="w")
expense_table.column("category", width=160, anchor="center")
expense_table.column("amount", width=150, anchor="e")

scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=expense_table.yview
)

expense_table.configure(yscrollcommand=scrollbar.set)

expense_table.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")


# -------------------- TABLE ACTIONS --------------------

actions = tk.Frame(root, bg=BG_COLOR, padx=25, pady=10)
actions.pack(fill="x")

make_button(
    actions, "Delete Selected", delete_expense, RED_COLOR
).pack(side="left", padx=(0, 10))

make_button(
    actions, "Export to CSV", export_csv, GREEN_COLOR
).pack(side="left")


# -------------------- STATUS BAR --------------------

status_label = tk.Label(
    root,
    text="Welcome! Add your first expense to get started.",
    font=("Arial", 10),
    bg=BG_COLOR,
    fg=TEXT_COLOR,
    anchor="w",
    padx=25,
    pady=8
)
status_label.pack(fill="x")


# -------------------- START APPLICATION --------------------

refresh_table()

root.mainloop()