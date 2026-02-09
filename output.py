import os
import psycopg2
import json
from psycopg2.extras import RealDictCursor
import shutil

config = {
    "dbname":"snowmiku",
    "user":"postgres",
    "password":os.environ.get("PSQL_PASSWORD"),
    "host":"localhost",
    "port":5432,
}

setting = {#Settings.jsonにはこれが出力される
    "quality":"p480",
    "SceneSelect": True,
    "SceneSelectRange": 0,
    "betweenSongs": 6000,
    "timezone": 9
}

filter_command = "SELECT * FROM tracks ORDER BY id;"


"""
SELECT * FROM tracks WHERE (name,signal,coverなど) = '(ほしい文字列など)'
"""

class output():
    def __init__(self):

        while True:
            self.output_path = input("出力する先のファイルは\n>>")
            if os.path.exists(self.output_path):
                break

        
        self.quality = input("音声ファイルの質は？\n1.original\n2.480p\n3.audio only\n>>")
        self.quality = int(self.quality)

        self.quality = ["path_original","path_480p","path_audio"][self.quality-1]
        

        self.start_output()

    def fetch_tracks(self):
        conn = None
        try:
            conn = psycopg2.connect(**config)
            cur = conn.cursor(cursor_factory = RealDictCursor)

            query = filter_command

            print(f"実行するクエリ\n{query}")

            cur.execute(query)
            rows = cur.fetchall()

            print(f"{len(rows)}個のファイルを取得")

            tracks = []
            for row in rows:
                track = self.convert_track_to_json(row)
                tracks.append(track)

            cur.close()
            return tracks
        
        except psycopg2.Error as e:
            print(F"Error:{e}")
            return []
        
        finally:
            if conn:
                conn.close()

    def export_to_json(self,tracks,output_path):
        try:
            with open(os.path.join(output_path,"Statics.json"),"w",encoding="utf-8") as f:
                json.dump(tracks,f,ensure_ascii=False,indent=2)

            with open(os.path.join(output_path,"Settings.json"),"w", encoding="utf-8") as f:
                json.dump(setting,f,ensure_ascii=False,indent=2)
            print(f"{output_path}に出力しました")
            return True
        except Exception as e:
            print(f"Json export error:{e}")
            return False


    def convert_track_to_json(self,row):
        track_type = row["type"]

        if track_type == "music":

            print(row["time"])

            time_list = {
                "lateNight":[0,1,2,3,4],
                "earlyMorning":[5,6],
                "morning":[7,8,9],
                "lateMorning":[10,11,12],
                "earlyAfternoon":[13,14,15],
                "lateAfternoon":[16,17],
                "earlyNight":[18,19,20],
                "night":[21,22,23],
                "all":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],
                "none":[]
            }

            new_time = []
            for data in row["time"]:
                if data in time_list:
                    new_time+=time_list.get(data)
                else:
                    new_time.append(int(data))

            return {
                "type":"music",
                "path":row[str(self.quality)],
                "name":row["name"],
                "cover":row["cover"],
                "original":row["original"],
                "time":new_time,
                "signal":row["signal_time"],
                "travel":row["is_travel"],
                "travelOnly":row["is_travel_only"],
                "weather":row["weather"],
                "registered":row["registered"],
                "duration":row["duration"],
                "source":row["source"],
                "language":row["language"]
            }
        
        elif track_type == "bgm":
            return {
                "type":"bgm",
                "hour":row["hour"],
                "path":row["path_audio"],
                "registered":row["registered"],
                "duration":row["duration"],
                "source":row["source"]
            }
        
        else:
            print(f"unexpected track type:{track_type}")
            print(1/0)


    def copy_files(self,tracks):
        music_path = os.path.join(self.output_path,"Music")
        bgm_path = os.path.join(self.output_path,"BGM")

        if not os.path.exists(music_path):
            os.makedirs(music_path)

        if not os.path.exists(bgm_path):
            os.makedirs(bgm_path)


        for track in tracks:
            source_path = track["path"]
            if track["type"] == "music":
                if os.path.isfile(source_path):
                    shutil.copy2(source_path,music_path)
            elif track["type"] == "bgm":
                if os.path.isfile(source_path):
                    shutil.copy2(source_path,bgm_path)

    def start_output(self):
        if not os.environ.get("PSQL_PASSWORD"):
            print("環境変数PSQL_PASSWORDが設定されていません")
            return
        
        print("Start Exporting")
        print(filter_command)

        tracks = self.fetch_tracks()

        if tracks:
            self.export_to_json(tracks,self.output_path)
            self.copy_files(tracks)

        else:
            print("トラックが見つかりませんでした")