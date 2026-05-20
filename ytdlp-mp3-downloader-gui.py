import tkinter as tk
from tkinter import ttk
import os
import threading
import sys
import subprocess
import pathlib
from internal.log_time import logTime

# Delete previous session cookie file if it exists to ensure fresh authentication
cookie_file = "youtube_cookies.txt"
if os.path.exists(cookie_file):
    try:
        os.remove(cookie_file)
    except Exception:
        logTime("Failed to remove existing cookie file. Continuing with potential stale session.", level="WRN")

# Hex Colors for Dark Mode
BG_COLOR = "#2e2e2e"       # Window & Frame Background
TEXT_COLOR = "#ffffff"     # Main Text Color
FIELD_BG = "#404040"       # Input Box & Table Rows Background
ACCENT_COLOR = "#4a90e2"   # Button Accent Color

# UI Constants
WIN_TITLE = "YTDLP MP3 Downloader"
FONT_NORMAL = ("Arial", 11)
FONT_BOLD = ("Arial", 11, "bold")
FONT_TITLE = ("Arial", 14, "bold")

# CLI Script Filename
CLI_FILENAME = "ytdlp-mp3-downloader-cli.py"

def create_dn_instance():
    url = url_entry.get()
    if url:
        row_num = len(table.get_children()) + 1
        item = table.insert("", tk.END, values=(row_num, url, "Downloading..."))
        url_entry.delete(0, tk.END)
        threading.Thread(target=dn_instance, args=(url, item), daemon=True).start()

def dn_instance(url, item):
    command = [sys.executable, CLI_FILENAME, "--url", url]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )
    def update_status(text):
        current_vals = table.item(item, "values")
        if current_vals and len(current_vals) >= 3:
            table.item(item, values=(current_vals[0], current_vals[1], text))

    latest_line = ""
    for line in process.stdout:
        latest_line = line.strip()
        update_status(latest_line)

    process.wait()
    if process.returncode == 0:
        completed_name = latest_line.rsplit(": ", 1)[-1].strip()
        completed_name = pathlib.Path(completed_name).name
        update_status(f"Completed: {completed_name}")
    elif process.returncode == 1:
        update_status("Invalid URL")
    elif process.returncode == 2:
        update_status(f"Download Error: {latest_line}")
    else:
        update_status("Error")

# Root Window Configuration
root = tk.Tk()
root.title(WIN_TITLE)
root.geometry("400x650")
root.minsize(375, 350)
root.configure(bg=BG_COLOR)
root.columnconfigure(0, weight=1)

# Set Window Icon
icon_path = os.path.join("internal", "icon.png")
icon_pi = tk.PhotoImage(file=icon_path).subsample(7)
root.iconphoto(False, icon_pi)

# TTK Styling for Table & Custom Elements
style = ttk.Style()
style.theme_use("default")

# Configure the Table (Treeview) colors
style.configure("Treeview", 
                background=FIELD_BG, 
                foreground=TEXT_COLOR, 
                fieldbackground=FIELD_BG, 
                rowheight=25,
                font=FONT_NORMAL)
style.map("Treeview", background=[("selected", ACCENT_COLOR)])

# Configure Table Headers
style.configure("Treeview.Heading", 
                background="#1e1e1e", 
                foreground=TEXT_COLOR, 
                relief="flat",
                borderwidth=5,
                font=FONT_BOLD)
style.map("Treeview.Heading", background=[("active", FIELD_BG)])

# Header with Text and Image
text_img_label = tk.Label(root, text=f" {WIN_TITLE}", font=FONT_TITLE, image=icon_pi, compound="left", bg=BG_COLOR, fg=TEXT_COLOR)
text_img_label.pack(pady=10)

# Input Fields Frame
input_frame = tk.Frame(root, bg=BG_COLOR)
input_frame.pack(fill="x", pady=10, padx=10)
input_frame.columnconfigure(1, weight=1)

# Label & Entry for URL Input
tk.Label(input_frame, text="URL:", font=FONT_NORMAL, bg=BG_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, padx=5, pady=5, sticky="e")
url_entry = tk.Entry(input_frame, font=FONT_NORMAL, bg=FIELD_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, relief="flat", bd=5)
url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

# Download Button
dn_button = tk.Button(root, text="Start Download", font=FONT_NORMAL, bg=ACCENT_COLOR, fg=TEXT_COLOR, activebackground="#357abd", activeforeground=TEXT_COLOR, relief="flat", padx=5, pady=5, command=create_dn_instance)
dn_button.pack(fill="x", padx=10, pady=(0, 10))

# Table Layout
columns = ("no", "name", "status")
# Allow a single row to be selected so selection events fire
table = ttk.Treeview(root, columns=columns, show="headings", selectmode='browse')
table.heading("no", text="No.")
table.heading("name", text="URL")
table.heading("status", text="Status")

table.column("no", width=40, anchor="center", stretch=False)
table.column("name", width=200, anchor="w", stretch=True)
table.column("status", width=150, anchor="w", stretch=True)
table.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)

def clear_completed():
    # Remove rows whose status (column 2) begins with 'Completed'
    for item in table.get_children():
        vals = table.item(item, "values")
        if not vals or len(vals) < 3:
            continue
        status = vals[2]
        try:
            if isinstance(status, str) and status.strip().startswith("Completed"):
                table.delete(item)
        except Exception:
            continue

clear_button = tk.Button(root, text="Clear Completed", font=FONT_NORMAL, bg=ACCENT_COLOR, fg=TEXT_COLOR, activebackground="#357abd", activeforeground=TEXT_COLOR, relief="flat", padx=5, pady=0, command=clear_completed)
clear_button.pack(fill="x", padx=10, pady=(0, 10))

# Readonly selection widgets for copying partial text from a row
selection_frame = tk.Frame(root, bg=BG_COLOR)
selection_frame.pack(fill="x", padx=10, pady=(0,10))

tk.Label(selection_frame, text="URL:", font=FONT_NORMAL, bg=BG_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, sticky="w")
name_var = tk.StringVar()
name_entry = ttk.Entry(selection_frame, textvariable=name_var, font=FONT_NORMAL, state='readonly')
name_entry.grid(row=0, column=1, sticky="ew", padx=6)

tk.Label(selection_frame, text="Status:", font=FONT_NORMAL, bg=BG_COLOR, fg=TEXT_COLOR).grid(row=1, column=0, sticky="w")
status_var = tk.StringVar()
status_entry = ttk.Entry(selection_frame, textvariable=status_var, font=FONT_NORMAL, state='readonly')
status_entry.grid(row=1, column=1, sticky="ew", padx=6, pady=(4,0))

selection_frame.columnconfigure(1, weight=1)

def on_row_select(event):
    sel = table.selection()
    if not sel:
        name_var.set("")
        status_var.set("")
        return
    item_id = sel[0]
    vals = table.item(item_id, "values")
    # Defensive: ensure three columns (no, name, status)
    if vals:
        name_var.set(vals[1] if len(vals) > 1 else "")  # URL column
        status_var.set(vals[2] if len(vals) > 2 else "")  # Status column

table.bind("<<TreeviewSelect>>", on_row_select)

def on_window_close():
    # Delete cookie file on exit
    if os.path.exists(cookie_file):
        try:
            os.remove(cookie_file)
            logTime("Cookie file cleaned up on exit.", level="INF", print_this=False)
        except Exception:
            logTime("Failed to remove cookie file on exit.", level="WRN", print_this=False)
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_window_close)

root.mainloop()
