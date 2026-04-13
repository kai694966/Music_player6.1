import psycopg2
from psycopg2 import extras
import csv
import os
import ast

DB_CONFIG = {
    "host": "localhost",
    "dbname": "musicplayer61",
    "user": "postgres",
    "password": os.environ.get("PSQL_PASSWORD"),
    "port": 5432,
    "options":"-c search_path=public"
}

# tracksテーブルの配列型カラム
ARRAY_COLUMNS = {"time", "weather", "selection"}

# 真偽値型カラム
BOOL_COLUMNS = {"is_travel", "is_travel_only"}

def parse_value(col_name, val):
    """カラム型に応じた値変換"""
    if val == "" or val is None:
        return None

    if col_name in ARRAY_COLUMNS:
        # "{a,b,c}" 形式 or "['a','b']" 形式に対応
        val = val.strip()
        if val.startswith("{") and val.endswith("}"):
            # PostgreSQL形式: {a,b,c} → リストに変換
            inner = val[1:-1]
            return [item.strip().strip('"') for item in inner.split(",")] if inner else []
        elif val.startswith("["):
            # Python形式: ['a', 'b']
            return ast.literal_eval(val)
        else:
            return [val]

    if col_name in BOOL_COLUMNS:
        return val.lower() in ("true", "1", "t", "yes")

    return val

class initDb:
    def __init__(self):
        tn = "public.tracks"
        csvFile = input("csvがあるファイルのパスを入力してください\n>> ").strip()
        self.import_csv_to_psql(tn, csvFile)

    def import_csv_to_psql(self, TABLE_NAME, CSV_FILE):
        try:
            with psycopg2.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    with open(CSV_FILE, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        all_columns = reader.fieldnames

                        # idカラムはSERIALなので除外
                        columns = [c for c in all_columns if c.lower() != "id"]

                        if not columns:
                            print("エラー: 有効なカラムが見つかりません。")
                            return

                        cols_str = ", ".join(columns)
                        placeholders = ", ".join(["%s"] * len(columns))
                        query = f"INSERT INTO {TABLE_NAME} ({cols_str}) VALUES ({placeholders})"

                        data_to_insert = []
                        for row in reader:
                            values = [parse_value(col, row.get(col)) for col in columns]
                            data_to_insert.append(values)

                        if not data_to_insert:
                            print("警告: CSVにデータ行がありません。")
                            return

                        extras.execute_batch(cur, query, data_to_insert)

                    conn.commit()
                    print(f"成功: {len(data_to_insert)} 件のデータをインポートしました。")

        except psycopg2.errors.UndefinedTable:
            print(f"エラー: テーブル '{TABLE_NAME}' が見つかりません。先にテーブルを作成してください。")
        except psycopg2.errors.UndefinedColumn as e:
            print(f"エラー: CSVのカラム名がテーブルと一致しません。\n詳細: {e}")
        except FileNotFoundError:
            print(f"エラー: ファイル '{CSV_FILE}' が見つかりません。")
        except Exception as e:
            print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    initDb()