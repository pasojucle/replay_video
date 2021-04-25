from tkinter import Tk
from tkinter import PhotoImage
from tkinter import Canvas
from tkinter import CENTER
import sys
import os
from pprint import pprint
import subprocess


sys.path.append('/home/pi/replay_video')
from network import Network

if os.environ.get('DISPLAY','') == '':
    print('no display found. Using :0.0')
    os.environ.__setitem__('DISPLAY', ':0.0')

class Fullscreen_Example:
    def __init__(self):
        self.window = Tk()
        self.window.attributes('-fullscreen', True)
        self.fullScreenState = False
        self.window.bind("<F11>", self.toggleFullScreen)
        self.window.bind("<Escape>", self.quitFullScreen)
        self.message = 'Démarrage en cours'
        self.rotate = 0

        height = self.window.winfo_screenheight()
        width = self.window.winfo_screenwidth()
        canvas = Canvas(self.window, width=width, height=height, background='#15264c', highlightthickness=0)

        replay_video = PhotoImage(file="./images/replay_video.png")
        canvas.create_image(int(width/2), int(height/2), anchor=CENTER, image=replay_video)

        self.ipconfig = Network.get_ip_config()
        wifi = PhotoImage(file="./images/wifi.png")
        canvas.create_image(100, int(height-110), image=wifi)
        canvas.create_text(175, int(height-100), text=self.ipconfig['wlan0'], fill="#1570d2")

        network = PhotoImage(file="./images/network.png")
        canvas.create_image(100, int(height-160), image=network)
        canvas.create_text(175, int(height-150), text=self.ipconfig['eth0'], fill="#1570d2")

        status = canvas.create_text(int(width/2), int(height-400), text="Démarrage en cours", fill="#1570d2")
        loader = canvas.create_arc(int(width/2-35), int(height-300-35), int(width/2+35), int(height-300+35), start=self.rotate, extent=280, fill="#1570d2", outline="#1570d2")
        canvas.create_oval(int(width/2-30), int(height-300-30), int(width/2+30), int(height-300+30), fill="#15264c", width=0)
        canvas.pack()

        while True:
            self.rotate -= 10
            canvas.itemconfigure(loader, start=self.rotate)
            self.window.update()
            processing = self.is_processing()
            text = self.message
            canvas.itemconfigure(status, text=text)
            self.window.update()
            if processing:
                canvas.delete(loader)
                break

        self.window.mainloop()

    def toggleFullScreen(self, event):
        self.fullScreenState = not self.fullScreenState
        self.window.attributes("-fullscreen", self.fullScreenState)

    def quitFullScreen(self, event):
        self.fullScreenState = False
        self.window.attributes("-fullscreen", self.fullScreenState)

    def is_processing(self):
        command = "curl 127.0.0.1/processing --max-time 0.05"
        result = subprocess.run(['bash', '-c', command], capture_output=True, text=True)
        pprint(result.stdout.rstrip('\n'))
        if result.stdout.rstrip('\n') == '1':
            self.message = f"Pour regarder un film, connectez-vous sur http://{self.ipconfig['wlan0']}"
            return True

        self.message = "Démarrage en cours"
        return False


if __name__ == '__main__':
    app = Fullscreen_Example()