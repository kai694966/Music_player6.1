import psycopg2
import psycopg2.extras
import os
from datetime import datetime
import re
import download
import output
import subprocess


config = {
    "dbname":"snowmiku",
    "user":"postgres",
    "password":os.environ.get("PSQL_PASSWORD"),
    "host":"localhost",
    "port":5432,
}#download.py,output.pyにもconfigがある

def connect_db(dbname):
    temp_config = config.copy()
    temp_config["dbname"] = "postgres"

    conn = psycopg2.connect(**temp_config)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;",(dbname,))

    exists = cur.fetchone() is not None
    
    if not exists:
        print(f"{dbname}が存在しないため作成します")

        cur.execute(f"CREATE DATABASE {dbname} WITH TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE='C' LC_CTYPE='C';")

    cur.close()
    conn.close()
    return psycopg2.connect(**config)

def create_tables():
    command = """
        CREATE TABLE IF NOT EXISTS tracks (
            id SERIAL PRIMARY KEY,
            type VARCHAR(10) NOT NULL,
            
            path_original TEXT NOT NULL,
            path_480p TEXT,
            path_audio TEXT,

            time TEXT[],
            signal_time char(4),
            is_travel BOOLEAN DEFAULT FALSE,
            is_travel_only BOOLEAN DEFAULT FALSE,
            weather TEXT[],

            name TEXT,
            cover TEXT,
            original TEXT,

            registered char(8),
            volume_offset INTEGER DEFAULT 0,
            duration INTEGER,
            source TEXT UNIQUE,
            language char(10) DEFAULT 'ja',
            hour INTEGER

        );
        """
    
    conn = None
    try:
        conn = connect_db(config["dbname"])
        

        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        cur.close()
    
    except Exception as e:
        print(f"エラーが発生しました:{e}")

    finally:
        if conn is not None:
            conn.close()

def registration():
    
    sql_select = """
        SELECT id, name, source, path_audio,language
        FROM tracks
        WHERE time IS NULL OR array_length(time,1) IS NULL;
    """

    unregistered_rows = []
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(sql_select)
                unregistered_rows = cur.fetchall()
            
    except Exception as e:
        print(f"DB error:{e}")

    if unregistered_rows:
        type = input("bgm?music?\n>>")
        for i,track in enumerate(unregistered_rows,1):
            process_metadata_entry(track,i,len(unregistered_rows),type)

def process_metadata_entry(db_track, index, total,type):

    if type == "music":

        print(f"\n--- [{index}/{total}] {db_track['name']} ---")

        if os.path.exists(db_track['path_audio']):
            os.startfile(db_track['path_audio'])

        type_input = type

        time_map = {"ln": "lateNight", "em": "earlyMorning", "m": "morning", "lm": "lateMorning", 
                    "ea": "earlyAfternoon", "la": "lateAfternoon", "en": "earlyNight", "n": "night", "all": "all"}

        time_input = input(f"[{index}/{total}]その音楽を再生する時間帯は？','で区切る\n0-4   lateNight\n5-6   earlyMorning\n7-9   morning\n10-12 lateMorning\n13-15 earlyAfternoon\n16-17 lateAfternoon\n18-20 earlyNight\n21-23 night\n0-23  all\n(none)none\n>>") or "all"
        time_list = [time_map.get(t.strip().lower(), t.strip()) for t in time_input.split(",")]

        signal_time = input("その音楽を時報として流す時間(HHMM)\n[none]\n>>")

        if signal_time == "":
            signal_time = None

        is_travel = input("旅行の時のみ流れる？(t/f)\n[false]\n>>")
        if is_travel in ["t","ｔ","true","True"]:
            is_travel = True
            only_travel = input("旅行する時のみ流す？\n>>")
            if only_travel in ["t","ｔ","true","True"]:
                only_travel = True
            else:
                only_travel = False
        else:
            only_travel = False
            is_travel = False

        # ... (signal_time, is_travel, weather などの入力は以前のコードと同じ) ...
        weather = input("天気 (Clear, Clouds, Rain, Snow)\n>>").split(",")

        # メタデータ推論
        s_name, s_cover, s_original = name_suggestion(db_track['name'])
        name = input(f"その曲は何と呼ばれている？ [{s_name}] >>") or s_name
        cover = input(f"カバーした人はだれ？ [{s_cover}] >>") or s_cover
        original = input(f"原曲をうたったのはだれ？ [{s_original}] >>") or s_original

        today = datetime.now().strftime('%Y%m%d')
        registered = input(f"登録日 [{today}] >>") or today
        language = input(f"曲の言語[{db_track["language"]}]\n>>") or db_track["language"]
        volume_offset = 0
        source = ""
        hour=25

        # データの集約
        track_data = {
            "id": db_track['id'], # これがあるから UPDATE できる
            "type": type_input,
            "time": time_list,
            "signal_time":signal_time,
            "is_travel":is_travel,
            "is_travel_only":only_travel,
            "weather": [w.strip() for w in weather if w.strip()],
            "name": name,
            "cover": cover,
            "original": original,
            "registered": registered,
            "volume_offset":volume_offset,
            "source":source,
            "language":language,
            "hour":hour,

        }

    elif type == "bgm":
        print(f"\n--- [{index}/{total}] {db_track['name']} ---")

        hour = input("何時台の曲?/n>>")

        today = datetime.now().strftime('%Y%m%d')
        registered = input(f"登録日 [{today}] >>") or today

        volume_offset = 0

        source = ""

        track_data = {
            "id": db_track['id'],
            "type": type_input,
            "time": ["none"],
            "signal_time":None,
            "is_travel":False,
            "is_travel_only":False,
            "weather": [],
            "name": "",
            "cover": "",
            "original": "",
            "registered": registered,
            "volume_offset":volume_offset,
            "source":source,
            "language":"",
            "hour":hour,

        }



        # 登録実行
    save_track_to_db(track_data)

def save_track_to_db(data):
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                if "id" in data and data["id"]:
                    # UPDATE処理
                    sql = """
                        UPDATE tracks SET 
                            type=%s, 
                            time=%s, 
                            signal_time=%s,
                            is_travel=%s,
                            is_travel_only=%s,
                            weather=%s, 
                            name=%s, 
                            cover=%s, 
                            original=%s, 
                            registered=%s,
                            volume_offset=%s,
                            language=%s,
                            hour=%s
                        WHERE id=%s;
                    """
                    cur.execute(sql, (
                        data["type"], 
                        data["time"], 
                        data["signal_time"],
                        data["is_travel"],
                        data["is_travel_only"],
                        data["weather"],
                        data["name"],
                        data["cover"],
                        data["original"],
                        data["registered"],
                        data["volume_offset"],
                        data["language"],
                        data["id"],
                        data["hour"]
                    ))
                else:
                    # INSERT処理 (もし新規ファイルから登録する場合用)
                    # ... 以前の register_track と同様の処理 ...
                    pass
                conn.commit()
                print("DB更新")
    except Exception as e:
        print(f"保存エラー: {e}")



def get_metadata(target_path,output_path):
    extentions = [".mp3",".m4a",".mkv",".webm",".mp4"]
    type = input("bgm?music?\n>>")

    length = len(os.listdir(target_path))
    i = 0

    for file in os.listdir(target_path):
        path,ext = os.path.splitext(file)#ext=拡張子
        if ext in extentions:
            pass
        else:
            print("対象の拡張子ではありません")
            i += 1
            continue

        check_path = os.path.join(output_path,"original",path)
        if is_already_registrated(check_path):
            print(f"[{i}/{length}]{path}は既に登録されています")
            i += 1
            continue

        full_path = os.path.join(target_path, file)
        os.startfile(full_path)

        path_original = output_path+"\original\\"+path
        path_480p = output_path+"\compressed_480p\\"+path
        path_audio = output_path+"\\audio_only\\"+path

        time_map = {
            "ln": "lateNight",
            "em": "earlyMorning",
            "m":  "morning",
            "lm": "lateMorning",
            "ea": "earlyAfternoon",
            "la": "lateAfternoon",
            "en": "earlyNight",
            "n":  "night",
            "all": "all"
        }

        time_input = input(f"[{i}/{length}]その音楽を再生する時間帯は？','で区切る\n0-4   lateNight\n5-6   earlyMorning\n7-9   morning\n10-12 lateMorning\n13-15 earlyAfternoon\n16-17 lateAfternoon\n18-20 earlyNight\n21-23 night\n0-23  all\n(none)none\n>>") or "all"


        time = []
        for t in time_input.split(","):
            t = t.strip().lower() # 空白を消して小文字に統一
            # 辞書にあれば変換、なければそのままの文字（数字など）を使う
            time.append(time_map.get(t, t))

        print(f"登録内容: {time}") # 例: ['ln', '7-9'] -> ['lateNight', '7-9']

        signal_time = input("その音楽を時報として流す時間(HHMM)\n[none]\n>>")
        if signal_time == "":
            signal_time = None

        is_travel = input("旅行の時のみ流れる？(t/f)\n[false]\n>>")
        if is_travel in ["t","ｔ","true","True"]:
            is_travel = True
            only_travel = input("旅行する時のみ流す？\n>>")
            if only_travel in ["t","ｔ","true","True"]:
                only_travel = True
            else:
                only_travel = False
        else:
            only_travel = False
            is_travel = False

        weather = input("その音楽が再生されやすくなる天気\nClear,Clouds,Rain,Snow ,で区切る\n>>")
        weather = weather.split(",")

        today = datetime.now().strftime('%Y%m%d')
        registered = input("その音楽を追加したときは？\n["+str(today)+"]\n>>") or today
        volume_offset = 0
        duration = 0
        source = ""
        hour = 25

        suggested_name,suggested_cover,suggested_original = name_suggestion(path)

        name = input(f"その音楽は何と呼ばれている？\n[{suggested_name}]\n>>") or suggested_name
        cover = input(f"その曲をカバーしたのはだれ？\n[{suggested_cover}]\n>>") or suggested_cover

        if suggested_original == "Unknown" and cover != "Unknown":
            suggested_original = suggested_cover

        original = input(f"その曲はもともと誰の曲？\n[{suggested_original}]\n>>") or suggested_original

        track_data = {
            "type":type,
            "path_original":path_original,
            "path_480p":path_480p,
            "path_audio":path_audio,
            "time":time,
            "signal_time":signal_time,
            "is_travel":is_travel,
            "is_travel_only":only_travel,
            "weather":weather,
            "name":name,
            "cover":cover,
            "original":original,
            "registered":registered,
            "volume_offset":volume_offset,
            "duration":duration,
            "source":source,
            "hour":hour,
        }

        register_track(track_data)
        i += 1


def name_suggestion(path):
    if path[0:9] == "DECO27 - ":
        name = path.split(" ")[2]
        cover = "DECO*27"
        original = "DECO*27"

    elif path[0:10] == "DECO＊27 - ":
        name = path.split(" ")[2]
        cover = "DECO*27"
        original = "DECO*27"
    
    elif path[0:10] == "DECO*27 - ":
        name = path.split(" ")[2]
        cover = "DECO*27"
        original = "DECO*27"

    elif path[0:7] == "MIMI - ":
        name = path.split(" ")[2]
        cover = "MIMI"
        original = "MIMI"

    elif path[0:17] == "Official髭男dism - ":
        name = path.split(" ")[2]
        cover = "higedan"
        original = "higedan"

    elif path[0:7] == "YOASOBI":
        match = re.search(r"「(.*?)」",path)
        name = match.group(1) if match else path
        cover = "YOASOBI"
        original = "YOASOBI"

    elif "covered by Kotoha" in path:
        name = path.split(" ")[0]
        cover = "Kotoha"
        original = "Unknown"

    elif path[0:5] == "ロクデナシ":
        match = re.search(r"「(.*?)」",path)
        name = match.group(1) if match else path
        cover = "ロクデナシ"
        original = "ロクデナシ"

    elif path[0:4] == "幾田りら":
        match = re.search(r"(.*?)",path)
        name = match.group(1) if match else path
        cover = "幾田りら"
        original = "幾田りら"

    elif "『" in path and "』" in path:#『~~』 ->MIMI
        match = re.search(r"『(.*?)』",path)
        name = match.group(1) if match else path
        name = name.strip()
        cover = "MIMI"
        original = "MIMI"

    elif "／まふまふ" in path:
        name = path.split("／")[0]
        cover = "まふまふ"
        original = "Unknown"

    else:
        name = path
        cover = "Unknown"
        original = "Unknown"

    return name,cover,original

def register_track(track_data):
    colums = track_data.keys()
    values = [track_data[col] for col in colums]

    placeholders = ["%s"] * len(colums)
    sql = f"INSERT INTO tracks ({', '.join(colums)}) VALUES ({', '.join(placeholders)}) RETURNING id;"

    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql,values)
                new_id = cur.fetchone()[0]
                conn.commit()
                return new_id
    except Exception as e:
        print(f"DB ERROR:{e}")
        return None
    
def is_already_registrated(path_original):
    sql = "SELECT id FROM tracks WHERE path_original = %s;"
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql,(path_original,))
                return cur.fetchone() is not None
    except Exception as e:
        print(f"既に入力済みかチェック中にエラー:{e}")
        return False



def get_duration(path):
    try:
        cmd = [
            "ffprobe",
            "-v","error",
            "-show_entries","format=duration",
            "-of","default=noprint_wrappers=1:nokey=1",
            path
        ]
        result = subprocess.run(cmd,capture_output=True,text=True,check=True)
        duration = float(result.stdout.strip())
        return int(duration*1000)
    except Exception as e:
        return 0
    
    

if __name__ == "__main__":

    mode = input("\n\n1.メタデータが入力されていない部分のみ入力する\n2.データを出力する\n3.時間帯や天気から曲を検索する\n4.ダウンロードする\n>>")
    mode = int(mode)
    if mode == 1:
        create_tables()
        registration()
    elif mode == 2:
        output.output()
    elif mode == 3:
        pass
    elif mode == 4:
        create_tables()
        download.download(input("出力先のフォルダを指定\n['E:\Music\MusicPlayerStorage']\n>>") or 'E:\Music\MusicPlayerStorage')#output_pathにダウンロードを開始