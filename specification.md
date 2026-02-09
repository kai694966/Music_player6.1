v5.1からの変更点(v6.1)

0-4,5-6,7-8,9-12,13-15,16-17,18-20,21-23の時間帯に分ける
曲の追加

天候による選挙区のシステムの修正
　天候ブーストでその曲が任意の倍率選ばれやすくなる
音楽のランダム再生システムの修正
　時間帯にあった曲を選ぶ
　再生回数が少ないものを選ぶ
　時報が近くにないものを選ぶ
　時報までの時間＋αより短いものを選ぶ
　最近再生されていないものを選ぶ（本番環境）
　ランダムに選ぶ


Music_manager5.2を追加
曲に対して
type|str,"music" or "bgm"

type="music"のとき
path_original|str,E:\Music\MusicPlayerStorage\original以降のpath
path_480p|str,E:\Music\MusicPlayerStorage\compressed_480p以降のpath
path_audio|str,E:\Music\MusicPlayerStorage\audio_only以降のpath
name|str,その曲が何と呼ばれているか
cover|str,誰がその曲を発表したか
original|str,原曲はだれがその曲を発表したか
time|list リスト内の項目は整数または時間を表す言葉,その曲をどの時間帯に再生するか

"ln": "lateNight", "em": "earlyMorning", "m": "morning", "lm": "lateMorning", 
                "ea": "earlyAfternoon", "la": "lateAfternoon", "en": "earlyNight", "n": "night", "all": "all"

signal|str "HHMM",その曲は何時何分の時報か
travel|bool,その曲は旅行中に再生されるか
travelOnly|bool,その曲は旅行中のみに再生されるか
weather|list "Clear" "Clouds" "Rain" "Snow"の中から選ぶ,その曲が流れやすくなる天気は何か
registrated|UNIX time(int?),その曲が登録されたのはいつか
volume|int,極端に音量が小さいものは音量を増加させる
duration|int[ms]長さ
source|str,曲をとってきたURL

PRIMARY_KEY|int 曲を追加した順に0~追加



type="bgm"のとき
path
time

PRIMARY_KEY

のデータを追加（postgresql）


テストの曲
0-4     あやふや
        メルティランドナイトメア
5-6     About you
        草々不一
7-9     スーパーヒーロー
        はぐ
10-12   ヴァンパイア
        テレパシ
13-15   Surges
        Journey
16-17   サイエンス
        群青
18-20   ハナタバ
        Pretender
21-23   星寂夜
        アンコール




InputFolder\Setttings.json ユーザーの同意のうえで書き換え可能
           \Statics.json web上では書き換え不可能
           \music\~~


Settings.json
"type"="setting"のとき
quality:"orig","p480","audio"

ここから下は設定のデフォルトの値
SceneSelect:bool
SceneSelectRange:int
betweenSongs:int[s]
betweenSignal:int[s]
timezone:int

Statics.json
type="music"のとき
"name":pathの最後の部分から拡張子を除いた
"cover"
"original"うたった人、カバーした人
"time":List|再生する時間帯
"signal":時報
"travel":速度が速いときに流れやすくなるか
"travelOnly":速度が速いときのみ
"weather":その天気の時流れやすくなる
"duration":int[ms]
"source":ダウンロード元


index.html
SceneSelect(true/false)
SceneSelectの範囲(0~24)現在の時刻±この時間の曲が流れる
曲が終わってから次の曲まで(int:SECOND)
曲が終わってから時報まで最小(int:SECOND)
タイムゾーン(+/-),(0~12)

IndexedDBに保存する内容
音楽ファイルがあるPath
filePlayed




html構成
JS
時計
class DB
play(path)
changeVolume()+.addEventListener()
bgmのsetTimeout()
timeSignalのsetTimeout()
  playBeep()
playByRandom()
  getMusicByHour()
  getMusicByPlayed()
  getMusicByRecent(Future)Played()
  getMusicByTimeToSignal()
  chooseByRandom()
天気を取得、表示する関数

folderInput.addEventListener()
  PlayedDBがなければ作る

  audioJ.onended = videoJ.onended = () => {}
    playByRandom()

  audioM.onended = videoM.onended = () => {}
    playByRandom()




ページの読み込みが完了する ->時計を表示
ファイルを読み込むというボタンを押す
もしIndexedDBにパスが保存されていなければパスを指定させる
IndexedDBに保存されているパスをもとに設定、メタデータ、音楽ファイルを読み込む
設定を変更、保存する要素を表示
再生ボタンを押す->ランダムに再生










Setting-bool
SceneSelect
TimeSignal
Bgm

Setting-input
曲同士の間の長さ
曲から時報の長さ最小
タイムゾーン
SceneSelect Range


天気
速度

205