#!/usr/bin/env python3
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk


class KernelModuleGUI:

  def __init__(self, root):
    self.root = root
    self.root.title("Linux Kernel Module Inspector")
    self.root.geometry("950x600")
    self.root.minsize(700, 400)

    self.dark_mode = False
    self.modules_data = []

    self.setup_ui()
    self.setup_styles()
    self.load_modules()

  def setup_ui(self):
    # Main container
    main_frame = ttk.Frame(self.root, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # --- Top Toolbar ---
    top_bar = ttk.Frame(main_frame)
    top_bar.pack(fill=tk.X, pady=(0, 8))

    # Search Bar
    ttk.Label(top_bar, text="🔍 Search:").pack(side=tk.LEFT, padx=(0, 5))
    self.search_var = tk.StringVar()
    self.search_var.trace_add("write", self.filter_modules)
    self.search_entry = ttk.Entry(
        top_bar, textvariable=self.search_var, width=25
    )
    self.search_entry.pack(side=tk.LEFT, padx=(0, 15))

    # Refresh Button
    self.refresh_btn = ttk.Button(
        top_bar, text="🔄 Refresh", command=self.load_modules
    )
    self.refresh_btn.pack(side=tk.LEFT, padx=5)

    # Theme Toggle
    self.theme_btn = ttk.Button(
        top_bar, text="🌙 Dark Mode", command=self.toggle_theme
    )
    self.theme_btn.pack(side=tk.RIGHT)

    # --- Main Split Window (Resizable List + Details) ---
    self.paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
    self.paned_window.pack(fill=tk.BOTH, expand=True)

    # Left Pane: Module Table (Treeview)
    left_frame = ttk.Frame(self.paned_window)
    self.paned_window.add(left_frame, weight=1)

    columns = ("name", "size", "used_by")
    self.tree = ttk.Treeview(
        left_frame, columns=columns, show="headings", selectmode="browse"
    )

    self.tree.heading("name", text="Module Name", command=lambda: self.sort_by("name"))
    self.tree.heading("size", text="Size (Bytes)", command=lambda: self.sort_by("size"))
    self.tree.heading("used_by", text="Used By", command=lambda: self.sort_by("used_by"))

    self.tree.column("name", width=180, anchor=tk.W)
    self.tree.column("size", width=90, anchor=tk.E)
    self.tree.column("used_by", width=100, anchor=tk.W)

    tree_scroll = ttk.Scrollbar(
        left_frame, orient=tk.VERTICAL, command=self.tree.yview
    )
    self.tree.configure(yscroll=tree_scroll.set)

    self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    self.tree.bind("<<TreeviewSelect>>", self.on_module_select)

    # Right Pane: Module Metadata (modinfo)
    right_frame = ttk.Frame(self.paned_window)
    self.paned_window.add(right_frame, weight=2)

    ttk.Label(
        right_frame, text="Module Details (modinfo)", font=("Segoe UI", 10, "bold")
    ).pack(anchor=tk.W, pady=(0, 4))

    self.info_text = scrolledtext.ScrolledText(
        right_frame, wrap=tk.WORD, font=("Monospace", 9)
    )
    self.info_text.pack(fill=tk.BOTH, expand=True)

    # --- Bottom Status Bar ---
    self.status_var = tk.StringVar(value="Ready")
    status_lbl = ttk.Label(
        main_frame,
        textvariable=self.status_var,
        relief=tk.SUNKEN,
        anchor=tk.W,
        padding=2,
    )
    status_lbl.pack(fill=tk.X, pady=(8, 0))

  def setup_styles(self):
    self.style = ttk.Style()
    if "clam" in self.style.theme_names():
      self.style.theme_use("clam")

  def toggle_theme(self):
    self.dark_mode = not self.dark_mode
    if self.dark_mode:
      bg_color = "#1e1e1e"
      fg_color = "#e0e0e0"
      field_bg = "#252526"
      accent = "#005fb8"

      self.theme_btn.config(text="☀️ Light Mode")
      self.style.configure(
          ".", background=bg_color, foreground=fg_color, fieldbackground=field_bg
      )
      self.style.configure(
          "TFrame", background=bg_color, foreground=fg_color
      )
      self.style.configure(
          "TLabel", background=bg_color, foreground=fg_color
      )
      self.style.configure(
          "TEntry", background=field_bg, foreground=fg_color
      )
      self.style.configure(
          "TButton",
          background="#333333",
          foreground=fg_color,
          bordercolor="#555555",
      )
      self.style.map(
          "TButton",
          background=[("active", "#0078d7")],
          foreground=[("active", "#ffffff")],
      )
      self.style.configure(
          "Treeview",
          background=field_bg,
          foreground=fg_color,
          fieldbackground=field_bg,
          borderwidth=0,
      )
      self.style.configure(
          "Treeview.Heading", background="#2d2d2d", foreground=fg_color
      )
      self.style.map(
          "Treeview",
          background=[("selected", accent)],
          foreground=[("selected", "#ffffff")],
      )

      self.info_text.config(
          bg=field_bg, fg=fg_color, insertbackground=fg_color
      )
      self.root.configure(bg=bg_color)
    else:
      self.style.theme_use("clam")
      self.theme_btn.config(text="🌙 Dark Mode")

      bg_color = "#f0f0f0"
      fg_color = "#000000"

      self.style.configure(
          ".", background=bg_color, foreground=fg_color, fieldbackground="#ffffff"
      )
      self.style.configure(
          "TFrame", background=bg_color, foreground=fg_color
      )
      self.style.configure(
          "TLabel", background=bg_color, foreground=fg_color
      )
      self.style.configure(
          "TButton", background="#e0e0e0", foreground=fg_color
      )
      self.style.configure(
          "Treeview",
          background="#ffffff",
          foreground=fg_color,
          fieldbackground="#ffffff",
          borderwidth=1,
      )
      self.style.configure(
          "Treeview.Heading", background="#e0e0e0", foreground=fg_color
      )
      self.style.map(
          "Treeview",
          background=[("selected", "#0078d7")],
          foreground=[("selected", "#ffffff")],
      )

      self.info_text.config(bg="#ffffff", fg="#000000", insertbackground="#000000")
      self.root.configure(bg=bg_color)

  def load_modules(self):
    self.modules_data.clear()
    try:
      with open("/proc/modules", "r") as f:
        for line in f:
          parts = line.split()
          if parts:
            name = parts[0]
            size = int(parts[1])
            used_by = parts[3] if len(parts) > 3 else "-"
            self.modules_data.append(
                {"name": name, "size": size, "used_by": used_by}
            )

      self.filter_modules()
      self.status_var.set(
          f"Loaded {len(self.modules_data)} kernel modules successfully."
      )
    except Exception as e:
      messagebox.showerror("Error", f"Failed to read /proc/modules:\n{e}")

  def filter_modules(self, *args):
    query = self.search_var.get().strip().lower()

    # Clear tree
    for item in self.tree.get_children():
      self.tree.delete(item)

    # Insert filtered
    count = 0
    for mod in self.modules_data:
      if query in mod["name"].lower() or query in mod["used_by"].lower():
        self.tree.insert(
            "",
            tk.END,
            values=(mod["name"], f"{mod['size']:,}", mod["used_by"]),
        )
        count += 1

    self.status_var.set(f"Showing {count} of {len(self.modules_data)} modules.")

  def on_module_select(self, event):
    selected_item = self.tree.selection()
    if not selected_item:
      return

    item_values = self.tree.item(selected_item[0])["values"]
    mod_name = item_values[0]

    # Fetch modinfo
    self.info_text.config(state=tk.NORMAL)
    self.info_text.delete("1.0", tk.END)

    try:
      result = subprocess.run(
          ["modinfo", mod_name], capture_output=True, text=True, check=True
      )
      self.info_text.insert(tk.END, result.stdout)
    except subprocess.CalledProcessError as e:
      self.info_text.insert(
          tk.END, f"Error getting metadata for '{mod_name}':\n{e.stderr}"
      )
    except Exception as e:
      self.info_text.insert(tk.END, f"Unexpected error: {str(e)}")

  def sort_by(self, col):
    reverse = getattr(self, f"_sort_{col}_reverse", False)

    if col == "size":
      self.modules_data.sort(key=lambda x: x["size"], reverse=reverse)
    else:
      self.modules_data.sort(key=lambda x: x[col].lower(), reverse=reverse)

    setattr(self, f"_sort_{col}_reverse", not reverse)
    self.filter_modules()


if __name__ == "__main__":
  root = tk.Tk()
  app = KernelModuleGUI(root)
  root.mainloop()