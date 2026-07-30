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
    self.root.geometry("1000x650")
    self.root.minsize(750, 450)

    self.dark_mode = False
    self.modules_data = []

    self.setup_styles()
    self.setup_ui()
    self.load_modules()

  def setup_styles(self):
    self.style = ttk.Style()
    if "clam" in self.style.theme_names():
      self.style.theme_use("clam")

  def setup_ui(self):
    # Main container with a sleek gradient feel using padding
    self.main_frame = ttk.Frame(self.root, padding=12)
    self.main_frame.pack(fill=tk.BOTH, expand=True)

    # --- Top Toolbar ---
    top_bar = ttk.Frame(self.main_frame)
    top_bar.pack(fill=tk.X, pady=(0, 10))

    # Search Bar with styled container look
    ttk.Label(top_bar, text="🔍 Search:", font=("Segoe UI", 10, "bold")).pack(
        side=tk.LEFT, padx=(0, 6)
    )
    self.search_var = tk.StringVar()
    self.search_var.trace_add("write", self.filter_modules)
    self.search_entry = ttk.Entry(
        top_bar, textvariable=self.search_var, width=28, font=("Segoe UI", 10)
    )
    self.search_entry.pack(side=tk.LEFT, padx=(0, 15))

    # Refresh Button with accent appearance
    self.refresh_btn = ttk.Button(
        top_bar, text="🔄 Refresh List", command=self.load_modules
    )
    self.refresh_btn.pack(side=tk.LEFT, padx=5)

    # Theme Toggle Button
    self.theme_btn = ttk.Button(
        top_bar, text="🌙 Dark Mode", command=self.toggle_theme
    )
    self.theme_btn.pack(side=tk.RIGHT)

    # --- Main Split Window (Resizable List + Details) ---
    self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
    self.paned_window.pack(fill=tk.BOTH, expand=True)

    # Left Pane: Module Table (Treeview)
    left_frame = ttk.Frame(self.paned_window)
    self.paned_window.add(left_frame, weight=1)

    columns = ("name", "size", "used_by")
    self.tree = ttk.Treeview(
        left_frame, columns=columns, show="headings", selectmode="browse"
    )

    self.tree.heading(
        "name", text="Module Name", command=lambda: self.sort_by("name")
    )
    self.tree.heading(
        "size", text="Size (Bytes)", command=lambda: self.sort_by("size")
    )
    self.tree.heading(
        "used_by", text="Used By", command=lambda: self.sort_by("used_by")
    )

    self.tree.column("name", width=190, anchor=tk.W)
    self.tree.column("size", width=100, anchor=tk.E)
    self.tree.column("used_by", width=110, anchor=tk.W)

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

    self.detail_label = ttk.Label(
        right_frame,
        text="📌 Module Details (modinfo)",
        font=("Segoe UI", 11, "bold"),
    )
    self.detail_label.pack(anchor=tk.W, pady=(0, 6))

    # ScrolledText with Syntax-like Tag Highlights for modinfo labels
    self.info_text = scrolledtext.ScrolledText(
        right_frame, wrap=tk.WORD, font=("Consolas", 10), bd=1, relief=tk.SOLID
    )
    self.info_text.pack(fill=tk.BOTH, expand=True)

    # Configure tag colors for text color flair inside modinfo
    self.info_text.tag_config("key", foreground="#005fb8", font=("Consolas", 10, "bold"))
    self.info_text.tag_config("value", foreground="#222222")

    # --- Bottom Status Bar ---
    self.status_var = tk.StringVar(value="Ready — Select a module to inspect properties.")
    self.status_lbl = ttk.Label(
        self.main_frame,
        textvariable=self.status_var,
        relief=tk.FLAT,
        anchor=tk.W,
        padding=4,
        font=("Segoe UI", 9, "italic"),
    )
    self.status_lbl.pack(fill=tk.X, pady=(8, 0))

    # Apply initial theme configuration
    self.apply_theme()

  def toggle_theme(self):
    self.dark_mode = not self.dark_mode
    self.apply_theme()

  def apply_theme(self):
    if self.dark_mode:
      # Vibrant Modern Dark Palette (Deep Charcoal + Neon Cyan/Electric Blue accents)
      bg_color = "#181818"
      panel_bg = "#222222"
      fg_color = "#f0f0f0"
      accent_color = "#007acc"
      select_bg = "#004885"
      text_bg = "#1e1e1e"
      text_fg = "#d4d4d4"
      status_bg = "#252526"

      self.theme_btn.config(text="☀️ Light Mode")
      self.style.configure(
          ".", background=bg_color, foreground=fg_color, fieldbackground=text_bg
      )
      self.style.configure("TFrame", background=bg_color, foreground=fg_color)
      self.style.configure("TLabel", background=bg_color, foreground=fg_color)
      self.style.configure("TEntry", background=text_bg, foreground=fg_color)
      self.style.configure(
          "TButton",
          background="#333333",
          foreground=fg_color,
          bordercolor="#555555",
      )
      self.style.map(
          "TButton",
          background=[("active", accent_color)],
          foreground=[("active", "#ffffff")],
      )

      self.style.configure(
          "Treeview",
          background=text_bg,
          foreground=fg_color,
          fieldbackground=text_bg,
          borderwidth=0,
          rowheight=24,
      )
      self.style.configure(
          "Treeview.Heading",
          background="#2d2d2d",
          foreground="#ffffff",
          font=("Segoe UI", 9, "bold"),
      )
      self.style.map(
          "Treeview",
          background=[("selected", select_bg)],
          foreground=[("selected", "#ffffff")],
      )

      self.info_text.config(
          bg=text_bg, fg="#9cdcfe", insertbackground="#ffffff"
      )
      self.info_text.tag_config("key", foreground="#4ec9b0", font=("Consolas", 10, "bold"))
      self.info_text.tag_config("value", foreground="#ce9178")

      self.status_lbl.config(background=status_bg, foreground="#b5cea8")
      self.root.configure(bg=bg_color)
    else:
      # Vibrant Crisp Light Palette (Soft Slate + Cobalt Blue Accents)
      bg_color = "#f5f6f8"
      fg_color = "#111111"
      accent_color = "#0066cc"
      select_bg = "#0066cc"
      text_bg = "#ffffff"
      status_bg = "#e4e7eb"

      self.theme_btn.config(text="🌙 Dark Mode")
      self.style.configure(
          ".", background=bg_color, foreground=fg_color, fieldbackground=text_bg
      )
      self.style.configure("TFrame", background=bg_color, foreground=fg_color)
      self.style.configure("TLabel", background=bg_color, foreground=fg_color)
      self.style.configure(
          "TButton", background="#e2e8f0", foreground=fg_color
      )
      self.style.map(
          "TButton",
          background=[("active", accent_color)],
          foreground=[("active", "#ffffff")],
      )

      self.style.configure(
          "Treeview",
          background=text_bg,
          foreground=fg_color,
          fieldbackground=text_bg,
          borderwidth=1,
          rowheight=24,
      )
      self.style.configure(
          "Treeview.Heading",
          background="#e2e8f0",
          foreground="#1a202c",
          font=("Segoe UI", 9, "bold"),
      )
      self.style.map(
          "Treeview",
          background=[("selected", select_bg)],
          foreground=[("selected", "#ffffff")],
      )

      self.info_text.config(
          bg=text_bg, fg="#1f2937", insertbackground="#000000"
      )
      self.info_text.tag_config("key", foreground="#005fb8", font=("Consolas", 10, "bold"))
      self.info_text.tag_config("value", foreground="#222222")

      self.status_lbl.config(background=status_bg, foreground="#2d3748")
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
          f"✨ Loaded {len(self.modules_data)} active kernel modules successfully."
      )
    except Exception as e:
      messagebox.showerror("Error", f"Failed to read /proc/modules:\n{e}")

  def filter_modules(self, *args):
    query = self.search_var.get().strip().lower()

    # Clear tree
    for item in self.tree.get_children():
      self.tree.delete(item)

    # Insert filtered with zebra striping tags if desired
    count = 0
    for mod in self.modules_data:
      if query in mod["name"].lower() or query in mod["used_by"].lower():
        self.tree.insert(
            "",
            tk.END,
            values=(mod["name"], f"{mod['size']:,}", mod["used_by"]),
        )
        count += 1

    if query:
      self.status_var.set(
          f"🔍 Filter match: Showing {count} of {len(self.modules_data)} modules."
      )

  def on_module_select(self, event):
    selected_item = self.tree.selection()
    if not selected_item:
      return

    item_values = self.tree.item(selected_item[0])["values"]
    mod_name = item_values[0]

    # Fetch modinfo with colored layout formatting
    self.info_text.config(state=tk.NORMAL)
    self.info_text.delete("1.0", tk.END)

    try:
      result = subprocess.run(
          ["modinfo", mod_name], capture_output=True, text=True, check=True
      )
      
      # Process lines to add colorful tag emphasis for keys vs values
      for line in result.stdout.splitlines():
        if ":" in line:
          key, val = line.split(":", 1)
          self.info_text.insert(tk.END, key + ":", "key")
          self.info_text.insert(tk.END, val + "\n", "value")
        else:
          self.info_text.insert(tk.END, line + "\n", "value")

      self.status_var.set(f"📌 Auditing metadata for module: [{mod_name}]")
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
