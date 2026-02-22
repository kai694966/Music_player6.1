import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import os

QUERY = """
SELECT name, signal_time, selection FROM public.tracks WHERE NOT (selection @> ARRAY['v6.1-a']) ORDER BY name ASC
"""

# データベース接続設定
DB_CONFIG = {
    "dbname":"musicplayer61",
    "user":"postgres",
    "password":os.environ.get("PSQL_PASSWORD"),
    "host":"localhost",
    "port":5432,
}

def update_selection():
    # 1. GUIで選択された行を取得
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("警告", "行を選択してください")
        return

    add_text = entry_text.get()
    if not add_text:
        messagebox.showwarning("警告", "追加する文字列を入力してください")
        return

    # 2. データベース更新
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        for item in selected_item:
            # Treeviewの隠し列(ID)を取得
            track_id = tree.item(item)['values'][0]
            
            # 配列に重複がない場合のみ追加するSQL
            query = """
            UPDATE public.tracks 
            SET selection = array_append(selection, %s)
            WHERE name = %s AND NOT (selection @> ARRAY[%s]);
            """
            cur.execute(query, (add_text, track_id, add_text))
        
        conn.commit()
        messagebox.showinfo("成功", f"'{add_text}' を追加しました")
        load_data() # 一覧をリフレッシュ
        
    except Exception as e:
        messagebox.showerror("エラー", str(e))
    finally:
        if conn: conn.close()

def load_data():
    # データを読み込んでTreeviewに表示
    for i in tree.get_children():
        tree.delete(i)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(QUERY)
    for row in cur.fetchall():
        tree.insert("", "end", values=row)
    conn.close()

# --- GUI 構築 ---
root = tk.Tk()
root.title("SQL Data Updater")

# 入力エリア
frame_top = tk.Frame(root)
frame_top.pack(pady=10)
tk.Label(frame_top, text="追加する文字:").pack(side=tk.LEFT)
entry_text = tk.Entry(frame_top)
entry_text.insert(0, "v6.1-a")
entry_text.pack(side=tk.LEFT)
btn_update = tk.Button(frame_top, text="選択行を更新", command=update_selection)
btn_update.pack(side=tk.LEFT)

# データ一覧表示 (Treeview)
columns = ("name", "signal_time", "selection")
tree = ttk.Treeview(root, columns=columns, show='headings')
for col in columns:
    tree.heading(col, text=col)
tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

root.bind("<Return>", lambda event: update_selection())

load_data()
root.mainloop()