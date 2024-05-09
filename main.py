import psutil
from datetime import datetime
import pandas as pd
import tkinter as tk
from tkinter import ttk
import threading
 
 
 
 
def format_size(bytes, suffix='B'):
   """
   Scale bytes to its proper format
   e.g:
       1253656 => '1.20MB'
       1253656678 => '1.17GB'
   """
   factor = 1024
   for unit in ["", "K", "M", "G", "T", "P"]:
       if bytes < factor:
           return f"{bytes:.2f}{unit}{suffix}"
       bytes /= factor
 
 
 
 
def collect_process_info(process):
   """
   Collect detailed information about a given process.
   """
   try:
       with process.oneshot():
           pid = process.pid
           if pid == 0:
               return None
           name = process.name()
           create_time = datetime.fromtimestamp(process.create_time())
           cores = len(process.cpu_affinity())
           cpu_usage = process.cpu_percent(interval=0.1)
           status = process.status()
           nice = process.nice()
           memory_usage = process.memory_full_info().uss
           io_counters = process.io_counters()
           read_bytes, write_bytes = io_counters.read_bytes, io_counters.write_bytes
           n_threads = process.num_threads()
           username = process.username()
 
 
           return {
               'pid': pid, 'name': name, 'create_time': create_time,
               'cores': cores, 'cpu_usage': cpu_usage, 'status': status, 'nice': nice,
               'memory_usage': memory_usage, 'read_bytes': read_bytes, 'write_bytes': write_bytes,
               'n_threads': n_threads, 'username': username
           }
   except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
       return None
 
 
 
 
def get_processes_info():
   """
   Get a list of all processes info.
   """
   return [collect_process_info(p) for p in psutil.process_iter() if collect_process_info(p)]
 
 
 
 
def construct_dataframe(processes, sort_by='memory_usage', descending=True, columns=None):
   """
   Construct dataframe from processes information.
   """
   df = pd.DataFrame(processes)
   df.set_index('pid', inplace=True)
   df.sort_values(by=sort_by, inplace=True, ascending=not descending)
   if columns:
       df = df[columns]
   df['memory_usage'] = df['memory_usage'].apply(format_size)
   df['read_bytes'] = df['read_bytes'].apply(format_size)
   df['write_bytes'] = df['write_bytes'].apply(format_size)
   df['create_time'] = df['create_time'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
   return df
 
 
 
 
def create_widgets(root, tree, column_config):
   tree.pack(expand=True, fill=tk.BOTH)
   for col in column_config:
       tree.heading(col, text=col.title())
   refresh_button = ttk.Button(root, text="Refresh", command=lambda: refresh(tree, column_config, refresh_button))
   refresh_button.pack(side=tk.BOTTOM, fill=tk.X)
 
 
 
 
def refresh(tree, column_config, button):
   button.config(state="disabled")
   threading.Thread(target=update_processes, args=(tree, column_config, button)).start()
 
 
 
 
def update_processes(tree, column_config, button):
   processes = get_processes_info()
   df = construct_dataframe(processes, columns=column_config)
   # Update the treeview in the main thread
   tree.after(0, populate_treeview, tree, df, button)
 
 
 
 
def populate_treeview(tree, df, button):
   # Clear existing entries
   for i in tree.get_children():
       tree.delete(i)
   # Insert new entries
   for row in df.itertuples():
       tree.insert("", tk.END, values=row[1:])  # Skip the index
   button.config(state="normal")
 
 
 
 
if __name__ == "__main__":
   root = tk.Tk()
   root.title("Process Monitor - The Pycodes")
   root.geometry("1400x600")
   column_config = "name,cpu_usage,memory_usage,read_bytes,write_bytes,status,create_time,nice,n_threads,cores".split(
       ",")
   tree = ttk.Treeview(root, columns=column_config, show="headings")
   create_widgets(root, tree, column_config)
   root.mainloop()
