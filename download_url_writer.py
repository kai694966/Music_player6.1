import pyperclip
import time
import os
import winsound
import time

target_file = "download_url.txt"

def watch_clipboard():
    i = 0
    existing_links = set()
    if os.path.exists(target_file):
        with open(target_file,"r",encoding="utf-8") as f:
            existing_links = set(line.strip() for line in f if line.strip()
                                 )
    winsound.Beep(440,500)
    time.sleep(1)
    winsound.Beep(440,500)
    before_clipboard = pyperclip.paste()
    print("Watching Clipboard")
    last_link = pyperclip.paste().strip()
    while True:
        try:
            link = pyperclip.paste().strip()

            if link != last_link:
                if "youtu" in link or "nicovideo" in link:
                    if "&list" in link:
                        link = link.split("&list")[0]
                    
                    if "&pp" in link:
                        link = link.split("&pp")[0]
                        

                    if link not in existing_links:
                        with open(target_file,"a",encoding="utf-8") as f:
                            f.write(link+"\n")

                        print(f"added:{link}")
                        winsound.Beep(440,500)
                        existing_links.add(link)
                        i = 0
                    else:
                        print(f"#### already exists:{link} ####")

                last_link = link

        except KeyboardInterrupt:
            pyperclip.copy(before_clipboard)
            print("\nStopped Watching")
            break
        except Exception as e:
            print(f"error:{e}")
        
        if i < 5:
            print("\n")

        time.sleep(0.5)
        i += 1



if __name__ == "__main__":
    watch_clipboard()