import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import subprocess, threading, os, sys, json, time
from datetime import datetime, timedelta
from tkinter.font import Font
from tkinter import ttk


DOCKER_EXEC = sys.executable  
PROJECT_SCRIPT   = os.path.join(os.path.dirname(__file__), 'project.py')
DOCKER_SCRIPT    = os.path.join(os.path.dirname(__file__), 'dockermanager2.py')

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

def run_container_interactively():
    def fetch_images():
        try:
            result = subprocess.run(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
                                    capture_output=True, text=True)
            return result.stdout.strip().split('\n') if result.stdout else []
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve images.\n{e}")
            return []

    def run_selected_image():
        img = combo.get().strip()
        cname = entry_name.get().strip()

        if not img:
            return messagebox.showerror("Error", "Please select an image")

        
        cmd = ["docker", "run", "--rm"]
        if cname:
            cmd += ["--name", cname]
        cmd.append(img)

        win.destroy()
        show_frame(frame_general)
        run_command(cmd, show_general)

    images = fetch_images()
    if not images or images == ['']:
        return messagebox.showinfo("No Images", "No Docker images found. Please pull or build one first.")

    win = tk.Toplevel(root)
    win.title("Run Docker Container")
    win.geometry("450x220")
    win.configure(bg=COLORS['bg_dark'])

    tk.Label(win, text="Select Image to Run:", bg=COLORS['bg_dark'],
             fg=COLORS['text_light'], font=("Segoe UI", 11)).pack(pady=(10, 2))

    combo = ttk.Combobox(win, values=images, font=("Segoe UI", 10), width=35)
    combo.pack(pady=5)
    combo.set(images[0])  # default selection

    tk.Label(win, text="Optional Container Name:", bg=COLORS['bg_dark'],
             fg=COLORS['text_light'], font=("Segoe UI", 11)).pack(pady=(10, 2))

    entry_name = create_entry(win, width=40)
    entry_name.pack(pady=5)

    create_button(win, "Run", run_selected_image, COLORS['accent_green']).pack(pady=15)



def stop_container_interactively():
    def stop():
        identifier = entry.get().strip()
        if not identifier:
            return messagebox.showerror("Error", "Container name or ID is required")
        win.destroy()
        show_frame(frame_general)
        run_command(["docker", "stop", identifier], show_general)
    win = tk.Toplevel(root)
    win.title("Stop Docker Container")
    win.geometry("400x150")
    win.configure(bg=COLORS['bg_dark'])
    tk.Label(win, text="Container Name or ID:", bg=COLORS['bg_dark'],
             fg=COLORS['text_light'], font=("Segoe UI", 11)).pack(pady=10)
    entry = create_entry(win, width=40)
    entry.pack(pady=5)
    create_button(win, "Stop", stop, COLORS['accent_red']).pack(pady=10)


def create_sidebar_button(parent, text, icon, command, accent):
    btn = tk.Button(parent, text=f"{icon}  {text}", command=command,
                   font=("Segoe UI", 12, "bold"),
                   bg=COLORS['bg_medium'], fg=COLORS['text_light'],
                   activebackground=accent, activeforeground=COLORS['text_light'],
                   relief="flat", bd=0, padx=15, pady=10, anchor="w", cursor="hand2")
    return btn

def create_section_label(parent, text):
    return tk.Label(parent, text=text, font=("Segoe UI", 18, "bold"),
                    bg=COLORS['bg_dark'], fg=COLORS['text_light'], pady=10)

def create_field_label(parent, text):
    return tk.Label(parent, text=text, font=("Segoe UI", 11),
                    bg=COLORS['bg_dark'], fg=COLORS['text_light'])

def create_entry(parent, width=30):
    e = tk.Entry(parent, font=("Segoe UI", 11), width=width,
                 bg=COLORS['bg_medium'], fg=COLORS['text_light'],
                 insertbackground=COLORS['text_light'], relief="flat", bd=1)
    return e

def create_button(parent, text, cmd, accent):
    return tk.Button(parent, text=text, command=cmd,
                     font=("Segoe UI", 11), bg=accent, fg=COLORS['text_light'],
                     activebackground=COLORS['bg_light'], relief="flat", bd=0, padx=10, pady=5, cursor="hand2")

def show_frame(frame, btn=None):
    for b in sidebar_buttons:
        b.config(bg=COLORS['bg_medium'])
    if btn: btn.config(bg=COLORS['bg_light'])
    frame.tkraise()



def search_local_image():
    def search():
        term = entry.get().strip().lower()
        if not term:
            return messagebox.showerror("Error", "Image name required")
        
        try:
            result = subprocess.run(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
                                    capture_output=True, text=True)
            images = result.stdout.strip().split('\n') if result.stdout else []

          
            filtered = [img for img in images if term in img.lower()]
            
            show_frame(frame_general)
            output_text = "\n".join(filtered) if filtered else "No matching images found."
            show_general(output_text)
            win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to search images.\n{e}")
            win.destroy()

    win = tk.Toplevel(root)
    win.title("Search Local Docker Images")
    win.geometry("400x150")
    win.configure(bg=COLORS['bg_dark'])

    tk.Label(win, text="Image Name:", bg=COLORS['bg_dark'], fg=COLORS['text_light'],
             font=("Segoe UI", 11)).pack(pady=10)
    entry = create_entry(win, width=40)
    entry.pack(pady=5)
    create_button(win, "Search", search, COLORS['accent_blue']).pack(pady=10)


def pull_dockerhub_image():
    def pull():
        image = entry.get().strip()
        if not image:
            return messagebox.showerror("Error", "Image name is required")
        win.destroy()
        show_frame(frame_general)
        output.delete('1.0', tk.END)
        output.insert(tk.END, f"Pulling Docker image: {image}...\n\n")
        def after_pull(result):
            output.insert(tk.END, result)
            messagebox.showinfo("Download Complete", f"Image '{image}' pulled successfully")
        run_command(["docker", "pull", image], after_pull)

    win = tk.Toplevel(root)
    win.title("Download Docker Image")
    win.geometry("400x150")
    win.configure(bg=COLORS['bg_dark'])

    tk.Label(win, text="Docker Image (e.g., python:3.11):", bg=COLORS['bg_dark'],
             fg=COLORS['text_light'], font=("Segoe UI", 11)).pack(pady=10)
    entry = create_entry(win, width=40)
    entry.pack(pady=5)
    create_button(win, "Download", pull, COLORS['accent_green']).pack(pady=10)



def search_dockerhub_image():
    def search():
        term = entry.get().strip()
        if not term:
            return messagebox.showerror("Error", "Search term required")
        win.destroy()
        show_frame(frame_general)
        run_command(["docker", "search", term], show_general)

    win = tk.Toplevel(root)
    win.title("Search DockerHub")
    win.geometry("400x150")
    win.configure(bg=COLORS['bg_dark'])
    tk.Label(win, text="Search term:", bg=COLORS['bg_dark'], fg=COLORS['text_light'], font=("Segoe UI", 11)).pack(pady=10)
    entry = create_entry(win, width=40)
    entry.pack(pady=5)
    create_button(win, "Search", search, COLORS['accent_purple']).pack(pady=10)


def open_dockerfile():
    path = filedialog.askopenfilename(filetypes=[("Dockerfile", "*.Dockerfile"), ("All Files", "*.*")])
    if not path:
        return
    try:
        with open(path, 'r') as f:
            content = f.read()
        show_frame(frame_general)
        output.delete('1.0', tk.END)
        output.insert(tk.END, f"--- Dockerfile: {os.path.basename(path)} ---\n\n{content}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read Dockerfile\n{e}")

def build_image_interactively():
    def build():
        dockerfile = entry_dockerfile.get().strip()
        img_name = entry_imgname.get().strip()

        if not dockerfile or not img_name:
            return messagebox.showerror("Error", "Both Dockerfile path and image name are required")

        if not os.path.isfile(dockerfile):
            return messagebox.showerror("Error", "Invalid Dockerfile path")

        win.withdraw()  # hide while building

        def on_done(output_text):
            show_frame(frame_general)
            show_general(output_text)
            messagebox.showinfo("Docker Build", "Docker image build process completed.")
            win.destroy()

        cmd = ["docker", "build", "-t", img_name, "-f", dockerfile, os.path.dirname(dockerfile)]
        show_frame(frame_general)
        output.delete('1.0', tk.END)
        output.insert(tk.END, "Building Docker image...\n\n")
        run_command(cmd, on_done)

    def browse_file():
        file = filedialog.askopenfilename(filetypes=[("Dockerfile", "*.Dockerfile"), ("All files", "*.*")])
        if file:
            entry_dockerfile.delete(0, tk.END)
            entry_dockerfile.insert(0, file)

    win = tk.Toplevel(root)
    win.title("Build Docker Image")
    win.geometry("500x250")
    win.configure(bg=COLORS['bg_dark'])

   
    tk.Label(win, text="Dockerfile Path:", bg=COLORS['bg_dark'], fg=COLORS['text_light'],
             font=("Segoe UI", 11)).pack(pady=(10, 2))

    dockerfile_frame = tk.Frame(win, bg=COLORS['bg_dark'])
    dockerfile_frame.pack(fill='x', padx=20)
    entry_dockerfile = create_entry(dockerfile_frame, width=40)
    entry_dockerfile.pack(side='left', fill='x', expand=True, padx=(0, 10), pady=5)
    create_button(dockerfile_frame, "Browse", browse_file, COLORS['accent_purple']).pack(side='right')

  
    tk.Label(win, text="Image Name/Tag:", bg=COLORS['bg_dark'], fg=COLORS['text_light'],
             font=("Segoe UI", 11)).pack(pady=(15, 2))

    entry_imgname = create_entry(win, width=50)
    entry_imgname.pack(padx=20, pady=5, fill='x')

    
    create_button(win, "Build Image", build, COLORS['accent_green']).pack(pady=20)



def run_command(cmd, callback):
    def task():
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, shell=False)
            out = p.stdout if p.returncode==0 else p.stderr
        except Exception as e:
            out = str(e)
        root.after(0, lambda: callback(out))
    threading.Thread(target=task, daemon=True).start()


root = tk.Tk()




top_bar = tk.Frame(root, bg=COLORS['bg_dark'], height=45, highlightthickness=1, highlightbackground=COLORS['border'])
top_bar.pack(side="top", fill="x")


top_bar_center = tk.Frame(top_bar, bg=COLORS['bg_dark'])
top_bar_center.pack(anchor="center")  
def style_nav_button(text, command, bg, hover_bg, parent=top_bar):
    btn = tk.Label(parent, text=text, bg=bg, fg='white',
                   font=("Segoe UI", 10, "bold"), padx=20, pady=8, cursor="hand2")
    btn.pack(side="left", padx=4, pady=5)

    def on_enter(e): btn.config(bg=hover_bg)
    def on_leave(e): btn.config(bg=bg)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    btn.bind("<Button-1>", lambda e: command())
    return btn


def open_virtual_disk():
    try:
        subprocess.Popen([sys.executable, PROJECT_SCRIPT])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Could not open Virtual Disk Manager:\n{e}")

def open_docker_manager():
    try:
        subprocess.Popen([sys.executable, DOCKER_SCRIPT])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Could not open Docker Manager:\n{e}")


style_nav_button("Virtual Disk Manager", open_virtual_disk, COLORS['accent_blue'], COLORS['accent_purple'], parent=top_bar_center)
style_nav_button("Docker Manager", open_docker_manager, COLORS['accent_green'], COLORS['accent_orange'], parent=top_bar_center)
root.title("Docker Manager Pro")
root.geometry("1000x650")
root.configure(bg=COLORS['bg_dark'])

sidebar = tk.Frame(root, bg=COLORS['bg_medium'], width=220)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

sidebar_buttons = []

frame_create = tk.Frame(root, bg=COLORS['bg_dark'])
frame_build  = tk.Frame(root, bg=COLORS['bg_dark'])
frame_general= tk.Frame(root, bg=COLORS['bg_dark'])
frame_add_dockerfile = tk.Frame(root, bg=COLORS['bg_dark'])
frame_add_dockerimage = tk.Frame(root, bg=COLORS['bg_dark'])
TOP_BAR_HEIGHT = 45  
SIDEBAR_WIDTH = 220

for f in (frame_create, frame_build, frame_general, frame_add_dockerimage, frame_add_dockerfile):
    f.place(x=SIDEBAR_WIDTH, y=TOP_BAR_HEIGHT, relwidth=1, relheight=1, anchor="nw")


output = scrolledtext.ScrolledText(frame_general, bg=COLORS['bg_medium'], fg=COLORS['text_light'],
                                   font=("Consolas",10), relief="flat", bd=1)
output.place(relx=0.05, rely=0.3, relwidth=0.9, relheight=0.6)

def show_general(out_text):
    output.delete('1.0', tk.END)
    output.insert(tk.END, out_text)


create_section_label(frame_create, "🐳  Create Dockerfile").pack(pady=(20,10))
cf_container = tk.Frame(frame_create, bg=COLORS['bg_dark'], padx=40)
cf_container.pack(fill='x')

create_field_label(cf_container, "Save to:").grid(row=0,column=0, pady=10, sticky='e')
ent_docker_path = create_entry(cf_container, width=40)
ent_docker_path.grid(row=0,column=1,padx=10)
def_browse=lambda: ent_docker_path.insert(0, filedialog.asksaveasfilename(defaultextension=".Dockerfile"))
create_button(cf_container, "Browse", def_browse, COLORS['accent_purple']).grid(row=0,column=2)

create_field_label(cf_container, "Content:").grid(row=1,column=0, sticky='ne', pady=10)
DEFAULT_DOCKERFILE = """\
# Base image with Python and GUI support
FROM python:3.11-slim

# Install Tkinter dependencies
RUN apt-get update && apt-get install -y python3-tk && apt-get clean

# Set working directory
WORKDIR /

# Copy current directory contents into the container
COPY . /

# Set the default command to run your GUI app
CMD ["python", "main.py"]
"""

text_cf = tk.Text(cf_container, bg=COLORS['bg_medium'], fg=COLORS['text_light'],
                  font=("Segoe UI", 10), height=15)
text_cf.insert("1.0", DEFAULT_DOCKERFILE)
text_cf.grid(row=1, column=1, columnspan=2)

def save_cf():
    path=ent_docker_path.get(); content=text_cf.get('1.0','end-1c')
    if not path or not content.strip(): return messagebox.showerror("Error","Path and content required")
    try:
        with open(path,'w') as f: f.write(content)
        messagebox.showinfo("Saved",f"Dockerfile saved to {path}")
    except Exception as e:
        messagebox.showerror("Error",str(e))

btn_add_dockerfile = create_sidebar_button(
    sidebar, "Add Dockerfile", "📄 ",  
    lambda: show_frame(frame_create, btn_add_dockerfile),
    COLORS['accent_purple']
)

btn_add_dockerfile.pack(fill='x', pady=2)
sidebar_buttons.append(btn_add_dockerfile)

btn_add_image = create_sidebar_button(sidebar, "Add Docker Image", "🛠️", lambda: show_frame(frame_build, btn_add_image), COLORS['accent_orange'])

btn_add_image.pack(fill='x', pady=2)
sidebar_buttons.append(btn_add_image)

create_button(frame_create, "Save Dockerfile", save_cf, COLORS['accent_green']).pack(pady=20)
btn_search_local = create_sidebar_button(sidebar, "Search Local Image", "🔍 ", search_local_image, COLORS['accent_blue'])
btn_search_local.pack(fill='x', pady=2)
sidebar_buttons.append(btn_search_local)

btn_search_hub = create_sidebar_button(sidebar, "Search DockerHub", "🌐 ", search_dockerhub_image, COLORS['accent_blue'])
btn_search_hub.pack(fill='x', pady=2)
sidebar_buttons.append(btn_search_hub)

btn_pull_image = create_sidebar_button(sidebar, "Download Image", "⬇️ ", pull_dockerhub_image, COLORS['accent_green'])
btn_pull_image.pack(fill='x', pady=2)

sidebar_buttons.append(btn_pull_image)



def do_build():
    df=ent_build_file.get(); img=ent_image.get()
    if not df or not img: return messagebox.showerror("Error","Both fields required")
    cmd=["docker","build","-t",img,"-f",df,os.path.dirname(df)]
    show_frame(frame_general, None)
    output.delete('1.0',tk.END)
    run_command(cmd, show_general)

create_section_label(frame_build, "⚙️  Build Docker Image").pack(pady=(30, 10))


bd_container = tk.Frame(frame_build, bg=COLORS['bg_dark'])
bd_container.pack(pady=20)


create_field_label(bd_container, "Dockerfile:").grid(row=0, column=0, pady=10, padx=10, sticky='e')
ent_build_file = create_entry(bd_container, width=40)
ent_build_file.grid(row=0, column=1, padx=(0, 10), pady=10)
def_browse2 = lambda: ent_build_file.insert(0, filedialog.askopenfilename(filetypes=[("Dockerfile", "Dockerfile")]))
create_button(bd_container, "Browse", def_browse2, COLORS['accent_purple']).grid(row=0, column=2, padx=10)


create_field_label(bd_container, "Image Name:").grid(row=1, column=0, pady=10, padx=10, sticky='e')
ent_image = create_entry(bd_container, width=40)
ent_image.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky='w')


create_button(bd_container, "Build Image", lambda: do_build(), COLORS['accent_orange']).grid(row=2, column=0, columnspan=3, pady=20)



ops = [
    ("List Images", "📦 ", ["docker", "images"]),
    ("List Containers", "🧊 ", ["docker", "ps"]),
    ("Run Container", "🚀 ", run_container_interactively),
    ("Stop Container", "⛔ ", stop_container_interactively),
]

for label, icon, cmd in ops:
    if isinstance(cmd, list):
        callback = lambda c=cmd: (show_frame(frame_general, None), run_command(c, show_general))
    elif callable(cmd):
        callback = cmd
    else:
        continue
    btn = create_sidebar_button(sidebar, label, icon, callback, COLORS['accent_blue'])
    btn.pack(fill='x', pady=2)
    sidebar_buttons.append(btn)

tk.Buttons=[]
show_frame(frame_create, None)
root.mainloop()