import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psycopg2
import os
import time
import google.generativeai as genai
from rapidfuzz import process, fuzz

# --- 設定エリア ---
DB_CONFIG = {
    "dbname": "musicplayer61",
    "user": "postgres",
    "password": os.environ.get("PSQL_PASSWORD"),
    "host": "localhost",
    "port": 5432,
}

# 取得したGemini APIキーをここに貼り付けてください
GEMINI_API_KEY = os.environ.get("Mp61_videoTitleAPI")
genai.configure(api_key=GEMINI_API_KEY)
# 高速かつ軽量な1.5-flashモデルを使用
model = genai.GenerativeModel('models/gemini-1.5-flash')

SELECT_QUERY = "SELECT path_audio, signal_time, selection FROM public.tracks ORDER BY path_audio ASC"

# --- ロジック関数 ---

def get_clean_filename(path):
    if not path: return ""
    base = os.path.basename(path)
    name, ext = os.path.splitext(base)
    return name

def ask_gemini_if_match(local_name, db_candidate_name):
    """
    YouTube/ニコニコ動画の表記ゆれを考慮してGeminiに同一性を問い合わせる
    """
    prompt = f"""
    以下の2つのファイル名が、YouTubeやニコニコ動画の表記ゆれ（装飾記号や順序の違い）を除いて、
    「実質的に同じ動画・楽曲ソース」を指しているか判定してください。

    【判定基準】
    ・「[MV]」「【実況】」「feat.初音ミク」「Official Video」等の付加情報の有無は無視する。
    ・「アーティスト名 / 曲名」と「曲名 - アーティスト名」のような順序逆転は同一とみなす。
    ・「歌ってみた」と「本家」のように、投稿者が明らかに異なる場合は False とする。

    ファイルA: {local_name}
    ファイルB: {db_candidate_name}

    回答は 'True' または 'False' の1単語のみで行ってください。
    """
    try:
        response = model.generate_content(prompt)
        # 返答にTrueが含まれているかチェック
        return "True" in response.text
    except Exception as e:
        print(f"AI APIエラー: {e}")
        return False

def batch_update_by_folder():
    # 1. フォルダ選択
    folder_path = filedialog.askdirectory(title="照合するファイルが入ったフォルダを選択")
    if not folder_path:
        return

    add_text = entry_text.get()
    if not add_text:
        messagebox.showwarning("警告", "追加する文字列を入力してください")
        return

    # 2. ローカルファイル取得
    target_extensions = {'.mkv', '.webm', '.mp4', '.m4a', '.mp3', '.wav'}
    local_names = []
    try:
        for f in os.listdir(folder_path):
            name, ext = os.path.splitext(f)
            if ext.lower() in target_extensions:
                local_names.append(name)
    except Exception as e:
        messagebox.showerror("エラー", f"フォルダ読み込み失敗: {e}")
        return

    if not local_names:
        messagebox.showinfo("情報", "対象ファイルが見つかりませんでした。")
        return

    # 3. DB照合とAI判定
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 判定用にDBの全レコードをメモリに展開
        cur.execute("SELECT path_audio, selection FROM public.tracks")
        db_rows = cur.fetchall()
        
        # 比較しやすい形式に整理
        db_entries = []
        for r in db_rows:
            db_entries.append({
                "path": r[0],
                "name": get_clean_filename(r[0]),
                "selection": r[1] if r[1] else []
            })
        
        db_names_list = [e["name"] for e in db_entries]
        updated_count = 0

        # メインループ
        for local_n in local_names:
            target_path = None
            
            # A. まず完全一致を確認（高速化のため）
            found_index = -1
            if local_n in db_names_list:
                found_index = db_names_list.index(local_n)
            
            # B. 完全一致がない場合、AIに問い合わせ
            if found_index == -1:
                # 類似度が高い上位3件に絞り込む（API節約）
                # scorer=fuzz.token_sort_ratio は単語の入れ替わりに強い
                best_matches = process.extract(local_n, db_names_list, scorer=fuzz.token_sort_ratio, limit=3)
                
                for candidate_name, score, index in best_matches:
                    if score > 45:  # 最低限の類似度（45%以上）があればAIに聞く
                        print(f"AI判定中... [{local_n}] vs [{candidate_name}] (類似度: {score:.1f})")
                        if ask_gemini_if_match(local_n, candidate_name):
                            found_index = index
                            print(f"  → ★一致と判定されました")
                            time.sleep(1)  # 無料枠のRate Limit（1分間の制限）対策
                            break
            
            # 4. DB更新実行
            if found_index != -1:
                entry = db_entries[found_index]
                if add_text not in entry["selection"]:
                    update_sql = "UPDATE public.tracks SET selection = array_append(selection, %s) WHERE path_audio = %s"
                    cur.execute(update_sql, (add_text, entry["path"]))
                    updated_count += 1
        
        conn.commit()
        messagebox.showinfo("完了", f"照合終了\n更新したレコード: {updated_count}件")
        load_data() 
        
    except Exception as e:
        messagebox.showerror("データベース/AIエラー", str(e))
    finally:
        if conn:
            conn.close()

def load_data():
    try:
        for i in tree.get_children():
            tree.delete(i)
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(SELECT_QUERY)
        for row in cur.fetchall():
            tree.insert("", "end", values=row)
        conn.close()
    except Exception as e:
        print(f"データロードエラー: {e}")

# --- GUI 構築 ---
root = tk.Tk()
root.title("AI-Powered SQL Data Updater")
root.geometry("900x600")

frame_top = tk.Frame(root)
frame_top.pack(pady=10, padx=10, fill=tk.X)

tk.Label(frame_top, text="追加する文字列:").pack(side=tk.LEFT)
entry_text = tk.Entry(frame_top, width=20)
entry_text.insert(0, "v6.1-a")
entry_text.pack(side=tk.LEFT, padx=5)

btn_folder = tk.Button(
    frame_top, 
    text="フォルダを選択してAI一括更新", 
    command=batch_update_by_folder,
    bg="#e8f5e9",
    relief=tk.RAISED,
    font=("MS Gothic", 10, "bold")
)
btn_folder.pack(side=tk.LEFT, padx=10)

columns = ("path_audio", "signal_time", "selection")
tree = ttk.Treeview(root, columns=columns, show='headings')
tree.heading("path_audio", text="ファイルパス")
tree.heading("signal_time", text="時間")
tree.heading("selection", text="Selection(配列)")
tree.column("path_audio", width=450)
tree.column("signal_time", width=80)
tree.column("selection", width=250)

scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscroll=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

load_data()
root.mainloop()