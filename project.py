import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import subprocess
import os
import json
import sys

from tkinter.font import Font


QEMU_IMG_PATH = "C:/msys64/ucrt64/bin/qemu-img.exe"
QEMU_SYSTEM_PATH = "C:/msys64/ucrt64/bin/qemu-system-x86_64.exe"





VM_PROJECTS_DIR = "D:/VMs/projects/"
os.makedirs(VM_PROJECTS_DIR, exist_ok=True)  # Create folder if not exists



save_path = ""
disk_path = ""
iso_path = ""

# --- Color Theme ---
COLORS = {
    "bg_dark": "#f0f4f8",
    "bg_medium": "#e1e8ef",
    "bg_light": "#d0dae7",
    "accent_blue": "#3b82f6",
    "accent_green": "#10b981",
    "accent_orange": "#f59e0b",
    "accent_purple": "#8b5cf6",
    "accent_red": "#ef4444",
    "text_light": "#1e293b",
    "text_muted": "#64748b",
    "border": "#cbd5e1"
}




# --- Functions ---
def toggle_theme():
    global COLORS
    COLORS.clear()
    if theme_var.get() == "Dark":
        COLORS.update(DARK_THEME)
    else:
        COLORS.update(LIGHT_THEME)
    root.destroy()
    os.execl(sys.executable, sys.executable, *sys.argv)

def select_save_folder():
    global save_path
    selected_path = filedialog.askdirectory()
    if selected_path:
        save_path = selected_path
        entry_save_path.config(state="normal")
        entry_save_path.delete(0, tk.END)
        entry_save_path.insert(0, save_path)
        entry_save_path.config(state="readonly")

def create_disk():
    global save_path
    disk_name = entry_name.get()
    disk_size = entry_size.get().strip().upper()
    disk_format = var_format.get()

    if not disk_name or not disk_size or not save_path:
        messagebox.showerror("Error", "Please fill in all fields!")
        return

    if not disk_size[-1] in ("G", "M", "K"):
        messagebox.showerror("Error", "Disk size must end with G, M, or K!")
        return

    try:
        size_value = float(disk_size[:-1])
        unit = disk_size[-1]

        max_allowed = {"K": 1024 * 1024, "M": 1024 * 10, "G": 100}  # e.g. max 100G
        if size_value > max_allowed[unit]:
            messagebox.showerror("Error", f"Maximum allowed size is {max_allowed[unit]}{unit}.")
            return
    except ValueError:
        messagebox.showerror("Error", "Invalid size format.")
        return

    if not disk_name.endswith(f".{disk_format}"):
        disk_name += f".{disk_format}"

    full_path = os.path.join(save_path, disk_name)
    command = [QEMU_IMG_PATH, "create", "-f", disk_format, full_path, disk_size]

    try:
        subprocess.run(command, check=True)
        messagebox.showinfo("Success", f"Disk created at:\n{full_path}")
        clear_create_fields()
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to create disk.\nError: {e}")


def select_disk():
    global disk_path
    file = filedialog.askopenfilename(filetypes=[("Disk Files", "*.qcow2 *.img *.vdi *.vmdk *.raw *.vhdx")])
    if file:
        disk_path = file
        entry_disk_path.config(state="normal")
        entry_disk_path.delete(0, tk.END)
        entry_disk_path.insert(0, disk_path)
        entry_disk_path.config(state="readonly")
        
def load_existing_disk():
    global disk_path
    file = filedialog.askopenfilename(filetypes=[("All Disks", "*.qcow2 *.img *.vdi *.vmdk *.raw *.vhdx")])
    if not file:
        return
    disk_path = file
    entry_existing_disk.config(state="normal")
    entry_existing_disk.delete(0, tk.END)
    entry_existing_disk.insert(0, disk_path)
    entry_existing_disk.config(state="readonly")

    # Try to get info
    try:
        output = subprocess.check_output([QEMU_IMG_PATH, "info", disk_path], text=True)
        messagebox.showinfo("Disk Info", output)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to read disk info:\n{e}")

def resize_disk():
    if not disk_path:
        messagebox.showerror("Error", "No disk selected!")
        return

    new_size = entry_resize.get().strip().upper()
    if not new_size:
        messagebox.showerror("Error", "Please enter a new disk size!")
        return

    # Check suffix
    if not new_size[-1] in ['K', 'M', 'G']:
        messagebox.showerror("Invalid Size", "Size must end with K, M, or G (e.g., +1G or 20G)")
        return

    # Convert to bytes
    try:
        size_val = float(new_size[:-1])
        multiplier = {'K': 1024, 'M': 1024**2, 'G': 1024**3}
        new_bytes = size_val * multiplier[new_size[-1]]
    except ValueError:
        messagebox.showerror("Error", "Invalid size format.")
        return

    current_size = get_current_disk_size(disk_path)
    if current_size is None:
        return

    if new_bytes < current_size:
        messagebox.showerror("Error", "Shrinking disks is not supported! Please specify a larger size.")
        return

    # Warn for unsupported formats
    ext = os.path.splitext(disk_path)[1].lower()
    if ext in [".vhdx", ".vmdk", ".vdi"]:
        messagebox.showwarning("Unsupported Format", f"Resizing not supported for {ext.upper()} format.")
        return

    try:
        subprocess.run([QEMU_IMG_PATH, "resize", disk_path, new_size], check=True)
        messagebox.showinfo("Success", f"Disk resized to {new_size} successfully!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Resize failed", f"Command failed.\n\nDetails:\n{e}")


def convert_disk_format():
    if not disk_path:
        messagebox.showerror("Error", "No disk selected!")
        return
    new_format = var_convert_format.get()
    target_path = disk_path + f".converted.{new_format}"
    try:
        subprocess.run([QEMU_IMG_PATH, "convert", "-O", new_format, disk_path, target_path], check=True)
        messagebox.showinfo("Success", f"Converted disk saved as:\n{target_path}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Conversion failed:\n{e}")
        
def show_disk_info():
    if not disk_path:
        messagebox.showerror("Error", "No disk selected!")
        return

    try:
        output = subprocess.check_output([QEMU_IMG_PATH, "info", disk_path], text=True)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to retrieve disk info.\n\n{e}")
        return

    info_win = tk.Toplevel(root)
    info_win.title("Disk Information")
    info_win.configure(bg=COLORS["bg_dark"])
    info_win.geometry("600x400")

    text = tk.Text(info_win, wrap="word", bg=COLORS["bg_medium"], fg=COLORS["text_light"],
                   font=("Segoe UI", 10), relief="flat", bd=1)
    text.insert("1.0", output)
    text.config(state="disabled")
    text.pack(expand=True, fill="both", padx=10, pady=10)



def select_iso():
    global iso_path
    file = filedialog.askopenfilename(filetypes=[("ISO Files", "*.iso")])
    if file:
        iso_path = file
        entry_iso_path.config(state="normal")
        entry_iso_path.delete(0, tk.END)
        entry_iso_path.insert(0, iso_path)
        entry_iso_path.config(state="readonly")

def start_vm():
    if not disk_path or not iso_path:
        messagebox.showerror("Error", "Please select both Disk and ISO!")
        return

    try:
        ram = int(entry_ram.get())
        cpu = int(entry_cpu.get())
    except ValueError:
        messagebox.showerror("Error", "RAM and CPU must be numbers!")
        return

    settings_summary = f"""
    ➤ Disk: {disk_path}
    ➤ ISO: {iso_path}
    ➤ RAM: {ram} MB
    ➤ CPUs: {cpu}
    """
    confirm = messagebox.askyesno("Confirm VM Settings", f"Start VM with the following settings?\n{settings_summary}")
    if not confirm:
        return

    command = [
        QEMU_SYSTEM_PATH,
        "-m", str(ram),
        "-smp", str(cpu),
        "-hda", disk_path,
        "-cdrom", iso_path,
        "-boot", "d"
    ]

    try:
        subprocess.Popen(command)
        messagebox.showinfo("Success", "Virtual Machine started!")
        save_vm_project()
        clear_vm_fields()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start VM.\n{e}")



def get_current_disk_size(path):
    try:
        output = subprocess.check_output([QEMU_IMG_PATH, "info", "--output=json", path], text=True)
        info = json.loads(output)
        return info["virtual-size"]
    except Exception as e:
        messagebox.showerror("Error", f"Could not get current disk size.\n{e}")
        return None

def save_vm_project():
    vm_name = os.path.splitext(os.path.basename(disk_path))[0]
    project = {
        "disk_path": disk_path,
        "iso_path": iso_path,
        "ram": int(entry_ram.get()),
        "cpu": int(entry_cpu.get())
    }
    with open(os.path.join(VM_PROJECTS_DIR, vm_name + ".json"), "w") as f:
        json.dump(project, f, indent=4)

def load_vm_projects():
    listbox_vms.delete(0, tk.END)
    for file in os.listdir(VM_PROJECTS_DIR):
        if file.endswith(".json"):
            listbox_vms.insert(tk.END, file[:-5])

def start_selected_vm():
    selected = listbox_vms.get(tk.ACTIVE)
    if not selected:
        return
    project_path = os.path.join(VM_PROJECTS_DIR, selected + ".json")
    with open(project_path, "r") as f:
        config = json.load(f)

    command = [
        QEMU_SYSTEM_PATH,
        "-m", str(config["ram"]),
        "-smp", str(config["cpu"]),
        "-hda", config["disk_path"],
        "-cdrom", config["iso_path"],
        "-boot", "d"
    ]

    try:
        subprocess.Popen(command)
        messagebox.showinfo("Success", f"Started VM: {selected}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start VM.\n{e}")

def delete_selected_vm():
    selected = listbox_vms.get(tk.ACTIVE)
    if not selected:
        return
    confirm = messagebox.askyesno("Confirm Delete", f"Delete VM project '{selected}'?")
    if confirm:
        project_path = os.path.join(VM_PROJECTS_DIR, selected + ".json")
        os.remove(project_path)
        load_vm_projects()

def clear_create_fields():
    entry_name.delete(0, tk.END)
    entry_size.delete(0, tk.END)
    entry_save_path.config(state="normal")
    entry_save_path.delete(0, tk.END)
    entry_save_path.config(state="readonly")

def clear_vm_fields():
    entry_disk_path.config(state="normal")
    entry_disk_path.delete(0, tk.END)
    entry_disk_path.config(state="readonly")
    entry_iso_path.config(state="normal")
    entry_iso_path.delete(0, tk.END)
    entry_iso_path.config(state="readonly")
    entry_ram.delete(0, tk.END)
    entry_ram.insert(0, "2048")
    entry_cpu.delete(0, tk.END)
    entry_cpu.insert(0, "2")

def show_frame(frame, btn=None):
  
    for button in sidebar_buttons:
        button.config(bg=COLORS["bg_medium"])
    
    
    if btn:
        btn.config(bg=COLORS["bg_light"])
    
    frame.tkraise()


def create_section_label(parent, text):
    return tk.Label(parent, text=text, font=("Segoe UI", 18, "bold"), 
                   bg=COLORS["bg_dark"], fg=COLORS["text_light"], 
                   pady=10)

def create_field_label(parent, text):
    return tk.Label(parent, text=text, font=("Segoe UI", 11),
                   bg=COLORS["bg_dark"], fg=COLORS["text_light"])

def create_entry(parent, width=30):
    entry = tk.Entry(parent, font=("Segoe UI", 11), width=width,
                    bg=COLORS["bg_medium"], fg=COLORS["text_light"],
                    insertbackground=COLORS["text_light"],
                    relief="flat", bd=1)
    return entry

def create_button(parent, text, command, accent_color):
    return tk.Button(parent, text=text, command=command,
                    font=("Segoe UI", 11),
                    bg=accent_color, fg=COLORS["text_light"],
                    activebackground=COLORS["bg_light"],
                    activeforeground=COLORS["text_light"],
                    relief="flat", bd=0, padx=10, pady=5,
                    cursor="hand2")

def create_sidebar_button(parent, text, icon, command, accent_color):
    btn = tk.Button(parent, text=f"{icon}  {text}", command=command,
                   font=("Segoe UI", 12, "bold"),
                   bg=COLORS["bg_medium"], fg=COLORS["text_light"],
                   activebackground=accent_color,
                   activeforeground=COLORS["text_light"],
                   relief="flat", bd=0, padx=20, pady=12,
                   anchor="w", width=20, cursor="hand2")
    return btn


root = tk.Tk()
root.title("QEMU Manager Pro")
root.geometry("1000x650")
root.configure(bg=COLORS["bg_dark"])
root.option_add("*TCombobox*Listbox*Background", COLORS["bg_medium"])
root.option_add("*TCombobox*Listbox*Foreground", COLORS["text_light"])


style = ttk.Style()
style.theme_use('default')
style.configure("TCombobox", 
                fieldbackground=COLORS["bg_medium"],
                background=COLORS["bg_light"],
                foreground=COLORS["text_light"],
                arrowcolor=COLORS["text_light"],
                relief="flat")


sidebar = tk.Frame(root, width=250, bg=COLORS["bg_medium"], bd=0)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False) 


tk.Label(sidebar, text="QEMU Manager Pro", 
         font=("Segoe UI", 16, "bold"), 
         bg=COLORS["bg_medium"], fg=COLORS["accent_blue"],
         pady=25).pack(fill="x")


frame_disk = tk.Frame(root, bg=COLORS["bg_dark"])
frame_vm = tk.Frame(root, bg=COLORS["bg_dark"])
frame_manage = tk.Frame(root, bg=COLORS["bg_dark"])

for frame in (frame_disk, frame_vm, frame_manage):
    frame.place(x=250, y=0, relwidth=0.75, relheight=1.0)
    




sidebar_buttons = []

btn_disk = create_sidebar_button(sidebar, "Create Virtual Disk", "🖴", 
                              lambda: show_frame(frame_disk, btn_disk), 
                              COLORS["accent_blue"])
btn_disk.pack(fill="x", pady=2)
sidebar_buttons.append(btn_disk)
frame_edit_disk = tk.Frame(root, bg=COLORS["bg_dark"])
frame_edit_disk.place(x=250, y=0, relwidth=0.75, relheight=1.0)
btn_edit = create_sidebar_button(sidebar, "Edit Virtual Disk", "🛠",
    lambda: show_frame(frame_edit_disk, btn_edit),
    COLORS["accent_purple"])
btn_edit.pack(fill="x", pady=2)
sidebar_buttons.append(btn_edit)

create_section_label(frame_edit_disk, "🛠 Edit Existing Disk").pack(pady=(30, 20))

btn_vm = create_sidebar_button(sidebar, "Launch VM", "🚀", 
                            lambda: show_frame(frame_vm, btn_vm), 
                            COLORS["accent_green"])
btn_vm.pack(fill="x", pady=2)
sidebar_buttons.append(btn_vm)

btn_manage = create_sidebar_button(sidebar, "Manage VMs", "🖥️", 
                                lambda: [show_frame(frame_manage, btn_manage), load_vm_projects()], 
                                COLORS["accent_orange"])
btn_manage.pack(fill="x", pady=2)
sidebar_buttons.append(btn_manage)





create_section_label(frame_disk, "🖴  Create Virtual Disk").pack(pady=(30, 20))

disk_container = tk.Frame(frame_disk, bg=COLORS["bg_dark"], padx=40)
disk_container.pack(fill="both", expand=True)


disk_form = tk.Frame(disk_container, bg=COLORS["bg_dark"])
disk_form.pack(pady=20)

# Row 1 - Disk Name
create_field_label(disk_form, "Disk Name:").grid(row=0, column=0, sticky="e", padx=10, pady=10)
entry_name = create_entry(disk_form)
entry_name.grid(row=0, column=1, sticky="w", pady=10)

# Row 2 - Disk Size
create_field_label(disk_form, "Disk Size (e.g., 20G):").grid(row=1, column=0, sticky="e", padx=10, pady=10)
entry_size = create_entry(disk_form)
entry_size.grid(row=1, column=1, sticky="w", pady=10)

# Row 3 - Disk Format
create_field_label(disk_form, "Disk Format:").grid(row=2, column=0, sticky="e", padx=10, pady=10)
var_format = tk.StringVar(value="qcow2")
format_combo = ttk.Combobox(disk_form, textvariable=var_format, 
                          values=["qcow2", "raw", "vmdk", "vhdx", "vdi"],
                          state="readonly", width=28, font=("Segoe UI", 11))
format_combo.grid(row=2, column=1, sticky="w", pady=10)

# Row 4 - Save Location
create_field_label(disk_form, "Save Location:").grid(row=3, column=0, sticky="e", padx=10, pady=10)
entry_save_path = create_entry(disk_form)
entry_save_path.config(state="readonly")
entry_save_path.grid(row=3, column=1, sticky="w", pady=10)
create_button(disk_form, "Browse", select_save_folder, COLORS["accent_purple"]).grid(row=3, column=2, padx=10)



# Create button
create_button(disk_container, "Create Disk", create_disk, COLORS["accent_orange"]).pack(pady=10)
# --- Edit Existing Disk ---


edit_container = tk.Frame(frame_edit_disk, bg=COLORS["bg_dark"], padx=40)
edit_container.pack(fill="both", expand=True)

edit_disk_form = tk.Frame(edit_container, bg=COLORS["bg_dark"])
edit_disk_form.pack(pady=20)




# Select existing disk
create_field_label(edit_disk_form, "Disk File:").grid(row=0, column=0, sticky="e", padx=10, pady=10)
entry_existing_disk = create_entry(edit_disk_form, width=40)
entry_existing_disk.config(state="readonly")
entry_existing_disk.grid(row=0, column=1, pady=10)
create_button(edit_disk_form, "Browse", load_existing_disk, COLORS["accent_purple"]).grid(row=0, column=2, padx=10)

# Resize disk
create_field_label(edit_disk_form, "Resize (e.g., +5G):").grid(row=1, column=0, sticky="e", padx=10, pady=10)
entry_resize = create_entry(edit_disk_form, width=20)
entry_resize.grid(row=1, column=1, sticky="w", pady=10)
create_button(edit_disk_form, "Resize Disk", resize_disk, COLORS["accent_orange"]).grid(row=1, column=2, padx=10)

# Convert format
create_field_label(edit_disk_form, "Convert to Format:").grid(row=2, column=0, sticky="e", padx=10, pady=10)
var_convert_format = tk.StringVar(value="qcow2")
format_combo2 = ttk.Combobox(edit_disk_form, textvariable=var_convert_format,
                              values=["qcow2", "raw", "vmdk", "vhdx", "vdi"],
                              state="readonly", width=20, font=("Segoe UI", 11))
format_combo2.grid(row=2, column=1, sticky="w", pady=10)
create_button(edit_disk_form, "Convert Disk", convert_disk_format, COLORS["accent_green"]).grid(row=2, column=2, padx=10)

# View info
create_button(edit_disk_form, "View Disk Info", show_disk_info, COLORS["accent_blue"]).grid(row=3, column=1, pady=20)


# --- VM Launcher Page ---
create_section_label(frame_vm, "🚀  Launch Virtual Machine").pack(pady=(30, 20))

# Container for better spacing
vm_container = tk.Frame(frame_vm, bg=COLORS["bg_dark"], padx=40)
vm_container.pack(fill="both", expand=True)

# Form frame
vm_form = tk.Frame(vm_container, bg=COLORS["bg_dark"])
vm_form.pack(pady=20)

# Row 1 - Virtual Disk
create_field_label(vm_form, "Virtual Disk:").grid(row=0, column=0, sticky="e", padx=10, pady=10)
entry_disk_path = create_entry(vm_form, width=40)
entry_disk_path.config(state="readonly")
entry_disk_path.grid(row=0, column=1, sticky="w", pady=10)
create_button(vm_form, "Select Disk", select_disk, COLORS["accent_blue"]).grid(row=0, column=2, padx=10)

# Row 2 - ISO Image
create_field_label(vm_form, "ISO Installer:").grid(row=1, column=0, sticky="e", padx=10, pady=10)
entry_iso_path = create_entry(vm_form, width=40)
entry_iso_path.config(state="readonly")
entry_iso_path.grid(row=1, column=1, sticky="w", pady=10)
create_button(vm_form, "Select ISO", select_iso, COLORS["accent_purple"]).grid(row=1, column=2, padx=10)

# Row 3 - RAM
create_field_label(vm_form, "RAM (MB):").grid(row=2, column=0, sticky="e", padx=10, pady=10)
entry_ram = create_entry(vm_form)
entry_ram.insert(0, "2048")
entry_ram.grid(row=2, column=1, sticky="w", pady=10)

# Row 4 - CPU Cores
create_field_label(vm_form, "CPU Cores:").grid(row=3, column=0, sticky="e", padx=10, pady=10)
entry_cpu = create_entry(vm_form)
entry_cpu.insert(0, "2")
entry_cpu.grid(row=3, column=1, sticky="w", pady=10)

# Start VM button
create_button(vm_container, "Start Virtual Machine", start_vm, COLORS["accent_green"]).pack(pady=30)

# --- Manage VMs Page ---
create_section_label(frame_manage, "🖥️  Manage Virtual Machines").pack(pady=(30, 20))

# Container for better spacing
manage_container = tk.Frame(frame_manage, bg=COLORS["bg_dark"], padx=40)
manage_container.pack(fill="both", expand=True)

# VM List with better styling
vm_list_frame = tk.Frame(manage_container, bg=COLORS["bg_dark"])
vm_list_frame.pack(pady=10, fill="both", expand=True)

# Create canvas with scrollbar for VM list
vm_canvas = tk.Canvas(vm_list_frame, bg=COLORS["bg_dark"], highlightthickness=0)
scrollbar = ttk.Scrollbar(vm_list_frame, orient="vertical", command=vm_canvas.yview)
vm_scrollable_frame = tk.Frame(vm_canvas, bg=COLORS["bg_dark"])

# Configure scrolling
vm_scrollable_frame.bind(
    "<Configure>",
    lambda e: vm_canvas.configure(scrollregion=vm_canvas.bbox("all"))
)
vm_canvas.create_window((0, 0), window=vm_scrollable_frame, anchor="nw")
vm_canvas.configure(yscrollcommand=scrollbar.set)

# Pack scrollbar and canvas
vm_canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
scrollbar.pack(side="right", fill="y")

# VM Listbox
listbox_frame = tk.Frame(vm_canvas, bg=COLORS["bg_dark"])
listbox_frame.pack(fill="both", expand=True)

listbox_vms = tk.Listbox(manage_container, 
                       font=("Segoe UI", 12),
                       width=50, height=12,
                       bg=COLORS["bg_medium"], 
                       fg=COLORS["text_light"],
                       selectbackground=COLORS["accent_blue"],
                       selectforeground=COLORS["text_light"],
                       relief="flat", bd=1)
listbox_vms.pack(pady=10, fill="both")

# Buttons frame for better layout
buttons_frame = tk.Frame(manage_container, bg=COLORS["bg_dark"])
buttons_frame.pack(pady=20, fill="x")

create_button(buttons_frame, "🚀 Start VM", start_selected_vm, COLORS["accent_green"]).pack(side=tk.LEFT, padx=10)
create_button(buttons_frame, "🗑️ Delete VM", delete_selected_vm, COLORS["accent_red"]).pack(side=tk.LEFT, padx=10)

# Default Start Page - highlight the first button
show_frame(frame_disk, btn_disk)

# Configure message boxes to use themed colors
root.option_add("*Dialog.msg.font", "Segoe UI 11")
root.option_add("*Dialog.msg.wrapLength", "5i")

# Center window on screen
root.update_idletasks()
width = root.winfo_width()
height = root.winfo_height()
x = (root.winfo_screenwidth() // 2) - (width // 2)
y = (root.winfo_screenheight() // 2) - (height // 2)
root.geometry(f'{width}x{height}+{x}+{y}')

root.mainloop()