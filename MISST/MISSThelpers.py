import customtkinter
import os
import time
from PIL import Image
from vcolorpicker import getColor, rgb2hex, hex2rgb, useLightTheme
from colorsys import rgb_to_hls, hls_to_rgb
import shutil
import tkinter
import uuid
import ping3
import time
import requests
import ctypes
from tkinter import PhotoImage

class MISSThelpers():
    def change_theme(theme):
        customtkinter.set_appearance_mode(theme)

    def checkbox_event(checkbox, sound, slider):
        if checkbox.get() == "on":
            sound.set_volume(slider.get())
        else:
            slider.set(0)
            sound.set_volume(slider.get())

    def slider_event(value, sound, checkbox):
        if value >= 0.01:
            checkbox.select()
            sound.set_volume(value)
        else:
            checkbox.deselect()
            sound.set_volume(value)

    def update_rpc(
        self,
        Ltext=None,
        Dtext=None,
        image="icon-0",
        large_text="MISST",
        end_time=None,
        small_image=None,
    ):
        start_time = time.time()
        if self.RPC_CONNECTED:
            try:
                self.RPC.update(
                    large_image=image,
                    small_image=small_image,
                    start=start_time,
                    end=end_time,
                    large_text=large_text,
                    state=Ltext,
                    details=Dtext,
                )
            except:
                return
        return
    
    def MISSTlistdir(self, directory):
        try:
            os_list = os.listdir(directory)
            misst_list = []
            for _ in os_list:
                if os.path.isfile(f"{directory}/{_}/bass.wav") and os.path.isfile(f"{directory}/{_}/drums.wav") and os.path.isfile(f"{directory}/{_}/other.wav") and os.path.isfile(f"{directory}/{_}/vocals.wav"):
                    misst_list.append(_)
            return misst_list
        except:
            return []
        
    def resize_image(self, image, size):
        im = Image.open(image)
        im = im.resize((size, size))
        im.save(image)
        return image
    
    def getsize(self, dir):
        total = 0
        for entry in os.scandir(dir):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += self.getsize(self, entry.path)
        return total

    def adjust_color_lightness(r, g, b, factor):
        h, l, s = rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        l = max(min(l * factor, 1.0), 0.0)
        r, g, b = hls_to_rgb(h, l, s)
        return f"#{rgb2hex(int(r * 255), int(g * 255), int(b * 255))}"
    
    def darken_color(r, g, b, factor=0.1):
        return MISSThelpers.adjust_color_lightness(r, g, b, 1 - factor)

    def updateTheme(self, color): 
        if color == "light":
            cur_color = self.settings.getSetting("chosenLightColor")
            old_color = (hex2rgb(cur_color.replace("#", "")))
            useLightTheme(True if customtkinter.get_appearance_mode() == "Light" else False)
            self.withdraw() # Hide the window
            chosen_color = f"#{rgb2hex(getColor(old_color))}"
            self.deiconify() # Show the window
            rgb_chosen = hex2rgb(chosen_color.replace("#", ""))
            self.settings.setSetting("chosenLightColor", chosen_color)
            self.settings.setSetting("chosenLightHoverColor", MISSThelpers.darken_color(rgb_chosen[0], rgb_chosen[1], rgb_chosen[2], 0.2))
            self.settings.setSetting("chosenLightDarker", MISSThelpers.darken_color(rgb_chosen[0], rgb_chosen[1], rgb_chosen[2], 0.35))
            self.settings.applyThemeSettings("./Assets/Themes/MISST.json", "./Assets/Themes/maluableJSON")
            self.button_light.configure(fg_color=chosen_color, hover_color=chosen_color)
        else:
            cur_color = self.settings.getSetting("chosenDarkColor")
            old_color = (hex2rgb(cur_color.replace("#", "")))
            useLightTheme(True if customtkinter.get_appearance_mode() == "Light" else False)
            self.withdraw() # Hide the window
            chosen_color = f"#{rgb2hex(getColor(old_color))}"
            self.deiconify() # Show the window
            rgb_chosen = hex2rgb(chosen_color.replace("#", ""))
            self.settings.setSetting("chosenDarkColor", chosen_color)
            self.settings.setSetting("chosenDarkHoverColor", MISSThelpers.darken_color(rgb_chosen[0], rgb_chosen[1], rgb_chosen[2], 0.2))
            self.settings.setSetting("chosenDarkDarker", MISSThelpers.darken_color(rgb_chosen[0], rgb_chosen[1], rgb_chosen[2], 0.35))
            self.settings.applyThemeSettings("./Assets/Themes/MISST.json", "./Assets/Themes/maluableJSON")
            self.button_dark.configure(fg_color=chosen_color, hover_color=chosen_color)
        return chosen_color
    
    def resetSettings(self):
        self.settings.resetDefaultTheme("./Assets/Themes/MISST.json", "./Assets/Themes/maluableJSON")
        self.settings.setSetting("rpc", "true")
        self.settings.setSetting("autoplay", "true")
        self.settings.setSetting("process_on_server", "true")
        self.rpc_box.select()
        self.autoplay_box.select()
        self.preprocess_method_box.select()
        self.button_light.configure(fg_color=self.settings.getSetting("defaultLightColor"), hover_color=self.settings.getSetting("defaultLightColor"))
        self.button_dark.configure(fg_color=self.settings.getSetting("defaultDarkColor"), hover_color=self.settings.getSetting("defaultDarkColor"))

    def autoplay_event(self):
        if self.autoplay_box.get() == 1:
            self.settings.setSetting("autoplay", "true")
        else:
            self.settings.setSetting("autoplay", "false")

    def rpc_event(self):
        if self.rpc_box.get() == 1:
            self.settings.setSetting("rpc", "true")
        else:
            self.settings.setSetting("rpc", "false")

    def preprocess_method_event(self):
        if self.preprocess_method_box.get() == 1:
            self.settings.setSetting("process_on_server", "true")
        else:
            self.settings.setSetting("process_on_server", "false")

    def clearDownloads(self):
        self.confirmation_frame = customtkinter.CTkFrame(
            master=self.settings_window, width=350, height=350, corner_radius=10
        )
        self.confirmation_frame.place(relx=0.25, rely=0.5, anchor=tkinter.CENTER)

        self.confirmation_header = customtkinter.CTkLabel(
            master=self.confirmation_frame, text="Are you sure?", font=(self.FONT, -16)
        )
        self.confirmation_header.place(relx=0.5, rely=0.45, anchor=tkinter.CENTER)
        self.confirmation_yes = customtkinter.CTkButton(
            master=self.confirmation_frame,
            text="Yes",
            font=(self.FONT, -12),
            command=lambda: clear(),
            width=80,
        )
        self.confirmation_yes.place(relx=0.35, rely=0.55, anchor=tkinter.CENTER)
        self.confirmation_no = customtkinter.CTkButton(
            master=self.confirmation_frame,
            text="No",
            font=(self.FONT, -12),
            command=lambda: self.confirmation_frame.destroy(),
            width=80,
        )
        self.confirmation_no.place(relx=0.65, rely=0.55, anchor=tkinter.CENTER)
        def clear():
            try:
                shutil.rmtree(self.importsDest)
                os.mkdir(self.importsDest)
                self.confirmation_frame.destroy()
                bytes = MISSThelpers.getsize(MISSThelpers, self.importsDest)
                gb = bytes / 1000000000
                gb = round(gb, 2)
                text = str(gb) + " GB"
                self.downloads_info.configure(text=text)
            except:
                pass

    def change_location(self):
        try:
            importsdest_nocheck = tkinter.filedialog.askdirectory(
                initialdir=os.path.abspath(self.importsDest)
            )
            importsdest_nocheck = importsdest_nocheck.replace("\\", "/")
            if importsdest_nocheck != "" and os.path.isdir(
                os.path.abspath(importsdest_nocheck)
            ):
                dummypath = os.path.join(importsdest_nocheck, str(uuid.uuid4()))
                try:
                    with open(dummypath, "w"):
                        pass
                    os.remove(dummypath)
                    importsdest = importsdest_nocheck
                except IOError:
                    importsdest = os.path.abspath(importsdest)
                self.settings.setSetting("importsDest", importsdest)
                self.importsDest = importsdest
                dir = os.path.abspath(self.importsDest)
                dirlen = len(dir)
                n = 20
                location_text = dir if dirlen <= n else "..." + dir[-(n - dirlen) :]
                self.storage_location_info.configure(text=location_text)
                return None
            else:
                self.importsDest = os.path.abspath(self.importsDest)
                return None
        except Exception as e:
            print(e)
            self.importsDest = os.path.abspath(self.importsDest)
            return None

    def refreshConnection(self):
        try:
            req = requests.get(self.server_base, timeout=3)
        except:
            self.refresh_button.configure(image=PhotoImage(file="./Assets/no-connection.png"), state=tkinter.DISABLED)
            time.sleep(3)
            self.refresh_button.configure(image=PhotoImage(file="./Assets/reload.png"), state='normal')
            return            
        
        if req.status_code == 200:
            try:
                server_address = self.server_base.replace("http://", "").replace(":5001", "")
                ping = ping3.ping(server_address, unit='s', timeout=3)
                pinginfo_button = customtkinter.CTkLabel(
                    master=self.west_frame,
                    text=f"{int(ping * 100)}ms",
                    font=(self.FONT, -12),
                    bg_color='transparent',
                    fg_color='transparent',
                    width=35,
                    height=35,
                )
                pinginfo_button.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)
                self.server_connected = True
                time.sleep(3)
                pinginfo_button.destroy()
            except:
                self.refresh_button.configure(image=PhotoImage(file="./Assets/no-connection.png"), state=tkinter.DISABLED)
                time.sleep(3)
                self.refresh_button.configure(image=PhotoImage(file="./Assets/reload.png"), state='normal')
        else:
            self.refresh_button.configure(image=PhotoImage(file="./Assets/no-connection.png"), state=tkinter.DISABLED)
            time.sleep(3)
            self.refresh_button.configure(image=PhotoImage(file="./Assets/reload.png"), state='normal')

    def count(label, text, og_text=""):
        t = 0
        try:
            while True:
                time.sleep(0.5)
                if label.cget("text") == "":
                    break
                if t > 3:
                    t -= t
                periods = ["", ".", "..", "..."]
                label.configure(text=f"{og_text}{text}{periods[t]}")
                t += 1
        except:
            pass
        return
    
    def terminate_thread(self, thread):
        """Terminates a python thread from another thread.

        :param thread: a threading.Thread instance
        """
        if not thread.is_alive():
            return

        exc = ctypes.py_object(SystemExit)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread.ident), exc)
        if res == 0:
            raise ValueError("nonexistent thread id")
        elif res > 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")