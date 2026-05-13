import tkinter as tk
from tkinter import ttk
import os
import threading
import sys
import subprocess
import pathlib

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
STATUS_CHAR_LIMIT = 40

# CLI Script Filename
CLI_FILENAME = "ytdlp-mp3-downloader-cli.py"

def create_dn_instance():
    url = url_entry.get()
    if url:
        table.insert("", tk.END, values=(url, "Downloading..."))
        url_entry.delete(0, tk.END)
        threading.Thread(target=dn_instance, args=(url,), daemon=True).start()

def dn_instance(url):
    command = [sys.executable, CLI_FILENAME, "--url", url]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    def update_status(text):
        if len(text) > STATUS_CHAR_LIMIT:
            text = text[:STATUS_CHAR_LIMIT - 3] + "..."
        for item in table.get_children():
            if table.item(item, "values")[0] == url:
                table.item(item, values=(url, text))
                break

    latest_line = ""
    for line in process.stdout:
        latest_line = line.strip()
        update_status(latest_line)

    process.wait()
    if process.returncode == 0:
        update_status(f"Completed: {pathlib.Path(latest_line).name}")
    elif process.returncode == 1:
        update_status("Invalid URL")
    elif process.returncode == 2:
        update_status("Download Error")
    else:
        update_status("Error")

# Root Window Configuration
root = tk.Tk()
root.title(WIN_TITLE)
root.geometry("400x450")
root.minsize(375, 350)
root.configure(bg=BG_COLOR)

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
input_frame.pack(pady=10)

# Label & Entry for URL Input
tk.Label(input_frame, text="URL:", font=FONT_NORMAL, bg=BG_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, padx=5, pady=5, sticky="e")
url_entry = tk.Entry(input_frame, font=FONT_NORMAL, bg=FIELD_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, relief="flat", bd=5, width=32)
url_entry.grid(row=0, column=1, padx=5, pady=5)

# Download Button
dn_button = tk.Button(root, text="Start Download", font=FONT_NORMAL, bg=ACCENT_COLOR, fg=TEXT_COLOR, activebackground="#357abd", activeforeground=TEXT_COLOR, relief="flat", padx=5, pady=5, command=create_dn_instance)
dn_button.pack(pady=10)

# Table Layout
columns = ("name", "status")
table = ttk.Treeview(root, columns=columns, show="headings")
table.heading("name", text="Name")
table.heading("status", text="Status")
table.column("name", width=150, anchor="w")
table.column("status", width=100, anchor="w")
table.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)

root.mainloop()
