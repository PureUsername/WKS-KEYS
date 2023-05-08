import tkinter as tk
from tkinter import filedialog, messagebox
import base64
import sqlite3
import pyperclip

# 创建并连接数据库
conn = sqlite3.connect('widevine_keys.db')
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY,
            key TEXT,
            pssh TEXT,
            license_url TEXT,
            manifest_file TEXT,
            video_url TEXT,
            video_type TEXT,
            video_title TEXT)""")

def add_key():
    print("Adding key...")

    key = entry_key.get()
    key_id = key_id_entry.get()
    key_id = str(uuid.UUID(hex=key_id))

    print(f"Key: {key}")
    print(f"Key ID: {key_id}")

    with sqlite3.connect("keys.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO keys (key, key_id) VALUES (?, ?)",
            (key, key_id),
        )
        conn.commit()

    entry_key.delete(0, "end")
    key_id_entry.delete(0, "end")


def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("Manifest files", "*.mpd;*.m3u8")])
    entry_manifest_file.delete(0, tk.END)
    entry_manifest_file.insert(0, file_path)

def refresh_listbox():
    listbox.delete(0, tk.END)
    c.execute("SELECT * FROM keys")
    rows = c.fetchall()
    for row in rows:
        listbox.insert(tk.END, f"ID: {row[0]}, Key: {row[1]}, License URL: {row[3]}, Manifest File: {row[4]}, Additional Info: {row[5]}")

def on_listbox_select(event):
    global selected_item
    index = listbox.curselection()
    if not index:
        return
    selected_item = listbox.get(index)
    id_ = int(selected_item.split(',')[0].split(': ')[1])
    c.execute("SELECT * FROM keys WHERE id=?", (id_,))
    row = c.fetchone()
    if row:
        entry_key.delete(0, tk.END)
        entry_key.insert(0, row[1])
        entry_pssh.delete(0, tk.END)
        entry_pssh.insert(0, base64.b64encode(row[2]).decode())
        entry_license_url.delete(0, tk.END)
        entry_license_url.insert(0, row[3])
        entry_manifest_file.delete(0, tk.END)
        entry_manifest_file.insert(0, row[4])
        entry_additional_info.delete(0, tk.END)
        entry_additional_info.insert(0, row[5])
        entry_video_url.delete(0, tk.END)
        entry_video_url.insert(0, row[5])
        video_type_var.set(row[6])
        entry_video_title.delete(0, tk.END)
        entry_video_title.insert(0, row[7])

def update_key():
    if not selected_item:
        return
    id_ = int(selected_item.split(',')[0].split(': ')[1])
    key = entry_key.get()
    pssh = entry_pssh.get()
    license_url = entry_license_url.get()
    manifest_file = entry_manifest_file.get()
    additional_info = entry_additional_info.get()

    pssh_data = base64.b64decode(pssh)

    c.execute("UPDATE keys SET key=?, pssh=?, license_url=?, manifest_file=?, video_url=?, video_type=?, video_title=? WHERE id=?", (key, pssh, license_url, manifest_file, video_url, video_type, video_title, id_))
    conn.commit()
    refresh_listbox()
    update_key_count()

def delete_key():
    if not selected_item:
        return
    id_ = int(selected_item.split(',')[0].split(': ')[1])
    c.execute("DELETE FROM keys WHERE id=?", (id_,))
    conn.commit()
    refresh_listbox()
    update_key_count()

# 密钥复制及导出
def export_keys():
    selected_keys = listbox.curselection()
    if not selected_keys:
        messagebox.showerror("Error", "Please select at least one key.")
        return

    key_string = ""
    for index in selected_keys:
        id_ = int(listbox.get(index).split(',')[0].split(': ')[1])
        c.execute("SELECT key FROM keys WHERE id=?", (id_,))
        key = c.fetchone()[0]
        key_string += f"--key {key} "
    
    pyperclip.copy(key_string.strip())

# 密钥总数 (计数)
def get_key_count():
    c.execute("SELECT COUNT(*) FROM keys")
    count = c.fetchone()[0]
    return count

# Update Key Content
def update_key_count():
    label_key_count.config(text=f"Key Count: {get_key_count()}")

# 多行密钥
def on_key_return(event):
    entry_key.focus_set()


app = tk.Tk()
app.title("Widevine Key Storage")

# 列表框
listbox = tk.Listbox(app, width=80, height=10, selectmode=tk.MULTIPLE)
listbox.grid(row=0, column=2, rowspan=10, padx=20, pady=20, sticky="NS")
listbox.bind('<<ListboxSelect>>', on_listbox_select)
refresh_listbox()

# 输入框
entry_key = tk.Text(app, height=5, wrap=tk.WORD)
entry_pssh = tk.Entry(app, width=100)
entry_license_url = tk.Entry(app, width=100)
entry_manifest_file = tk.Entry(app, width=100)
entry_video_url = tk.Entry(app, width=100)
entry_video_title = tk.Entry(app, width=100)

entry_key.grid(row=0, column=1, padx=(0,10), ipady=50, sticky=tk.W)
entry_key.bind('<Enter>', on_key_return)
entry_pssh.grid(row=1, column=1, padx=(0, 10), sticky=tk.W)
entry_license_url.grid(row=2, column=1, padx=(0, 10), sticky=tk.W)
entry_manifest_file.grid(row=3, column=1, padx=(0, 10), sticky=tk.W)
entry_video_url.grid(row=4, column=1, padx=(0, 10), sticky=tk.W)
entry_video_title.grid(row=6, column=1, padx=(0, 10), sticky=tk.W)

# 标签
label_key = tk.Label(app, text="Key")
label_pssh = tk.Label(app, text="PSSH (Base64)")
label_license_url = tk.Label(app, text="License URL")
label_manifest_file = tk.Label(app, text="Manifest File (.mpd or .m3u8)")
label_video_url = tk.Label(app, text="视频播放网址")
label_video_type = tk.Label(app, text="视频类型")
label_video_title = tk.Label(app, text="视频标题")
label_key_count = tk.Label(app, text="")
label_key_count.grid(row=9, column=0)

label_key.grid(row=0, column=0, sticky=tk.W)
label_pssh.grid(row=1, column=0, sticky=tk.W)
label_license_url.grid(row=2, column=0, sticky=tk.W)
label_manifest_file.grid(row=3, column=0, sticky=tk.W)
label_video_url.grid(row=4, column=0, sticky=tk.W)
label_video_type.grid(row=5, column=0, sticky=tk.W)
label_video_title.grid(row=6, column=0, sticky=tk.W)
update_key_count()


# 按钮
button_add = tk.Button(app, text="Add Key", command=add_key)
button_update = tk.Button(app, text="Update Key", command=update_key)
button_delete = tk.Button(app, text="Delete Key", command=delete_key)
button_export = tk.Button(app, text="Export Key(s)", command=export_keys)

button_add.grid(row=7, column=1, padx=10, pady=0, sticky="E")
button_update.grid(row=8, column=1, padx=10, pady=0, sticky="E")
button_delete.grid(row=9, column=1, padx=10, pady=0, sticky="E")
button_export.grid(row=10, column=1, padx=10, pady=0, sticky="E")

# 下拉菜单
video_type_var = tk.StringVar(app)
video_type_var.set("电影")  # 默认值
video_type_dropdown = tk.OptionMenu(app, video_type_var, "电影", "电视剧")
video_type_dropdown.grid(row=5, column=1)

'''
# 密钥列表框
listbox_keys = tk.Listbox(app, width=40, height=10)  # 将宽度从75调整为40
scrollbar_keys = tk.Scrollbar(app, command=listbox_keys.yview)
listbox_keys.config(yscrollcommand=scrollbar_keys.set)

listbox_keys.grid(row=0, column=3, rowspan=7, padx=(20, 0))
scrollbar_keys.grid(row=0, column=4, rowspan=7, sticky=tk.NS, padx=(0, 20))
'''

'''
# 密钥列表框及滚动条
listbox_frame = tk.Frame(app)
listbox_frame.grid(row=0, column=0, rowspan=10, padx=10, pady=10, sticky='ns')
scrollbar = tk.Scrollbar(listbox_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
listbox = tk.Listbox(listbox_frame, width=40, yscrollcommand=scrollbar.set)
listbox.pack(side=tk.LEFT, fill=tk.BOTH)
scrollbar.config(command=listbox.yview)
'''

'''
# 密钥总数标签
label_key_count = tk.Label(app, text="")
label_key_count.grid(row=9, column=0, pady=10, sticky=tk.W)
update_key_count()
'''

# 初始化密钥列表
refresh_listbox()

selected_item = None

app.mainloop()

conn.close()
