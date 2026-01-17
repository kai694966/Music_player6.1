import subprocess
import os
import re
import glob
import psycopg2


class download:
    def __init__(self,output_base):
        self.txt_path = "download_url.txt"
        self.output_base = output_base
        if not os.path.exists(self.txt_path):
            print(f"{self.txt_path}が見つかりません")
            print(1/0)
        
        self.start_download(output_base)

    def register_to_db(self,url,clean_title,file_paths):
        print(type(clean_title))
        print(repr(clean_title))

        for k,v in file_paths.items():
            print(k,type(v),repr(v))
        
        try:
            conn = psycopg2.connect(
                dbname="test_61",
                user="postgres",
                password=os.environ.get("PSQL_PASSWORD",""),
                host="localhost",
                port="5432",
            )
            cur = conn.cursor()

            sql = """
            INSERT INTO tracks (type,path_original,path_480p,path_audio,name,source,duration)
            VALUES(%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (source) DO NOTHING;
            """

            safe_title = str(clean_title).encode("utf-8","replace").decode("utf-8")

            data = (
                "music",
                file_paths["orig"],
                file_paths["p480"],
                file_paths["audio"],
                safe_title,
                str(url),
                self.get_duration(file_paths["orig"])
            )
            cur.execute(sql,data)
            conn.commit()
            cur.close()
            conn.close()
            print(f"登録完了:{clean_title}")
        except Exception as e:
            print(f"sqlにsourceなどを登録中にエラーが発生しました\n{e}")

    def get_duration(self,path):
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

    def read_urls(self):
        with open(self.txt_path,"r",encoding="utf-8") as f:
            self.urls = [line.strip() for line in f if line.strip()]
        
        if not self.urls:
            print(f"URLがありません")
            print(1/0)

    def download_urls(self,url,i,length):

        result = subprocess.run([r"C:\yt-dlp\yt-dlp.exe","--get-filename","-o","%(title)s",url],
            capture_output=True,
            text=False,
        )

        if result.returncode != 0:
            error_msg = result.stderr.decode("cp932",errors="replace")
            print(f"\n\nyt-dlp Error:\n{error_msg}\n\n")
            return

        raw_title_bytes = result.stdout.strip()
        raw_title = raw_title_bytes.decode("cp932",errors="replace").replace("?","？")
        clean_title = re.sub(r'[\\/:*?"<>|]', "", raw_title).replace("＊","")

        print(f"\n[開始] {clean_title}")

        subprocess.run([
                        r"C:\yt-dlp\yt-dlp.exe", 
                        "--quiet",
                        "--no-warnings",
                        "-f", 
                        "bestvideo+bestaudio/best", 
                        "--merge-output-format", 
                        "mp4", 
                        "-o", 
                        "temp_%(id)s.%(ext)s",
                        url
        ])

        paths = {
            "orig": os.path.join(self.output_base, "original"),
            "p480": os.path.join(self.output_base, "compressed_480p"),
            "audio": os.path.join(self.output_base, "audio_only")
        }

        for p in paths.values():
            os.makedirs(p,exist_ok=True)

        found_files = glob.glob(f"temp_*")
        if not found_files:
            print(f"ファイルが見つかりませんでした:(")
            return
        
        downloaded_file = found_files[0]
        temp_ext = os.path.splitext(downloaded_file)[1]

        subprocess.run([
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "info",
            "-stats",
            "-i",
            downloaded_file,
            "-vf",
            "scale=-2:480,format=nv12",
            "-c:v",
            "h264_qsv",
            "-global_quality",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "320k",
            os.path.join(paths["p480"],f"{clean_title}.mp4")
        ])
        
        subprocess.run([
            "ffmpeg", 
            "-y", 
            "-hide_banner",
            "-loglevel",
            "info",
            "-stats",
            "-i", 
            downloaded_file, 
            "-vn", 
            "-c:a",
            "aac",
            "-b:a",
            "320k",
            os.path.join(paths["audio"], f"{clean_title}.m4a")
        ])

        orig_filename = f"{clean_title}{temp_ext}"
        p480_filename = f"{clean_title}.mp4"
        audio_filename = f"{clean_title}.m4a"

        final_file_paths = {
            "orig": os.path.join(paths["orig"], orig_filename),
            "p480": os.path.join(paths["p480"], p480_filename),
            "audio": os.path.join(paths["audio"], audio_filename)
        }

        os.replace(downloaded_file,final_file_paths["orig"])

        self.register_to_db(url,clean_title,final_file_paths)

        print(f"\n\n###################################################################################################\n[完了] {clean_title}\n###################################################################################################\n\n")



    def start_download(self,path):

        input = ("ダウンロード中のファイルがないことを確認してください\n[Done]\n>>")

        self.read_urls()
        length = len(self.urls)
        i = 1
        for url in self.urls:
            print(f"[{i}/{length}]",end="")
            if url:
                self.download_urls(url,i,length)
            
            i += 1