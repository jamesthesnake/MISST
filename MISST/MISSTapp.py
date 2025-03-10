import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import tkinter
from tkinter import PhotoImage
import customtkinter
from pypresence import Presence
import threading
import time
import pygame
import random
import datetime
import nightcore as nc
from PIL import Image
from werkzeug.utils import secure_filename
import shutil
import requests

from MISSTplayer import MISSTplayer
from MISSTserver import MISSTserver
from MISSTsettings import MISSTsettings
from MISSThelpers import MISSThelpers
from MISSTpreprocess import MISSTconsole, MISSTpreprocess

from __version__ import __version__ as version

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("./Assets/Themes/MISST.json")  # Themes: "blue" (standard), "green", "dark-blue"

class MISSTapp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # remove download folder if it exists
        try:
            shutil.rmtree('./dl-songs')
        except:
            pass

        self.player = MISSTplayer()
        self.settings = MISSTsettings()
        self.server_base = self.settings.getSetting("server_base")
        self.server = MISSTserver(self.server_base)
        self.server_connected = requests.get(self.server_base).status_code == 200

        self.rpc = self.settings.getSetting("rpc")
        self.discord_client_id = self.settings.getSetting("discord_client_id")

        if self.rpc == "true":
            try:
                self.RPC = Presence(self.discord_client_id)
                self.RPC.connect()
                self.RPC_CONNECTED = True
            except:
                self.RPC_CONNECTED = False
        else:
            self.RPC_CONNECTED = False

        self.importsDest = os.path.abspath(self.settings.getSetting("importsDest"))
        if not os.path.isdir(self.importsDest):
            os.mkdir(self.importsDest)

        self.playing = False

        self.cur_sound_datas = {}
        self.uiThread = None

        # configure window
        self.title("MISST")
        self.iconbitmap(default=r"./Assets/icon.ico")
        self.WIDTH = int(self.winfo_screenwidth() * 0.3932291666666667)
        self.HEIGHT = int(self.winfo_screenheight() * 0.3981481481481481)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(self.WIDTH, self.HEIGHT)
        self.maxsize(755, 430)

        customtkinter.set_widget_scaling(((self.WIDTH / 755) + (self.HEIGHT / 430)) / 2)  # widget dimensions and text size
        #customtkinter.set_window_scaling(((self.WIDTH / 755) + (self.HEIGHT / 430)) / 2)  # window geometry dimensions

        self.check_var1 = tkinter.StringVar(value="on")
        self.check_var2 = tkinter.StringVar(value="on")
        self.check_var3 = tkinter.StringVar(value="on")
        self.check_var4 = tkinter.StringVar(value="on")
        self.nc_var = tkinter.StringVar(value="off")

        self.loop = False
        self.autoplay = True

        # create widgets
        self.FONT = "Roboto Medium"

        self.west_frame = customtkinter.CTkFrame(master=self, width=self.WIDTH * (175 / self.WIDTH), height=self.HEIGHT * (430 / self.HEIGHT), corner_radius=0)
        self.west_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), rowspan=4)

        self.north_frame = customtkinter.CTkFrame(master=self, width=self.WIDTH * (350 / self.WIDTH), height=self.HEIGHT * (100 / self.HEIGHT), corner_radius=8)
        self.north_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=(5, 0))

        self.center_frame = customtkinter.CTkFrame(master=self, width=self.WIDTH * (350 / self.WIDTH), height=self.HEIGHT * (200 / self.HEIGHT), corner_radius=8)
        self.center_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        self.south_frame = customtkinter.CTkFrame(master=self, width=self.WIDTH * (350 / self.WIDTH), height=self.HEIGHT * (100 / self.HEIGHT), corner_radius=8)
        self.south_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=(0, 5))       

        self.interface_frame = customtkinter.CTkFrame(master=self, width=self.WIDTH * (195 / self.WIDTH), height=self.HEIGHT * (100 / self.HEIGHT), corner_radius=8)
        self.interface_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=(5, 0))
        
        self.east_frame = customtkinter.CTkFrame(master=self, width=self.WIDTH * (195 / self.WIDTH), height=self.HEIGHT * (100 / self.HEIGHT), corner_radius=8)
        self.east_frame.grid(row=1, column=2, sticky="nsew", padx=(5, 0), pady=(10, 5), rowspan=3)

        # Interface Frame
        self.shuffle_button = customtkinter.CTkButton(
            master=self.interface_frame,
            image=customtkinter.CTkImage(Image.open("./Assets/Images/player-shuffle.png"), size=(25,25)),
            command=lambda: self.shuffle(),
            text="",
            width=5,
            height=5,
            fg_color='transparent',
            hover_color=self.interface_frame.cget("bg_color"),
            corner_radius=8
        )

        self.loop_button = customtkinter.CTkButton(
            master=self.interface_frame,
            image=customtkinter.CTkImage(Image.open("./Assets/Images/loop-off.png"), size=(25,25)),
            command=lambda: self.loopEvent(),
            text="",
            width=5,
            height=5,
            fg_color='transparent',
            hover_color=self.interface_frame.cget("bg_color"),
            corner_radius=8
        )

        self.next_button = customtkinter.CTkButton(
            master=self.interface_frame,
            image=customtkinter.CTkImage(Image.open("./Assets/Images/player-skip-forward.png"), size=(30,30)),
            command=lambda: print("test"),
            text="",
            width=5,
            height=5,
            fg_color='transparent',
            hover_color=self.interface_frame.cget("bg_color"),
            corner_radius=8,
            state=tkinter.DISABLED
        )

        self.previous_button = customtkinter.CTkButton(
            master=self.interface_frame,
            image=customtkinter.CTkImage(Image.open("./Assets/Images/player-skip-back.png"), size=(30,30)),
            command=lambda: print("test"),
            text="",
            width=5,
            height=5,
            fg_color='transparent',
            hover_color=self.interface_frame.cget("bg_color"),
            corner_radius=8,
            state=tkinter.DISABLED
        )

        self.playpause_button = customtkinter.CTkButton(
            master=self.interface_frame,
            image=customtkinter.CTkImage(Image.open("./Assets/Images/player-pause.png"), size=(32,32)),
            command=lambda: self.playpause(),
            text="",
            width=5,
            height=5,
            fg_color='transparent',
            hover_color=self.interface_frame.cget("bg_color"),
            corner_radius=8,
            state=tkinter.DISABLED
        )

        self.next_button.place(relx=0.67, rely=0.5, anchor=tkinter.CENTER)
        self.previous_button.place(relx=0.33, rely=0.5, anchor=tkinter.CENTER)
        self.shuffle_button.place(relx=0.16, rely=0.5, anchor=tkinter.CENTER)
        self.loop_button.place(relx=0.84, rely=0.5, anchor=tkinter.CENTER)
        self.playpause_button.place(relx=0.50, rely=0.5, anchor=tkinter.CENTER)

        ## EAST FRAME ----------------------------------------------------------------------------------------------------

        self.east_frame_title = customtkinter.CTkLabel(
            master=self.east_frame, text="Imported", font=(self.FONT, -16)
        )
        self.east_frame_title.place(relx=0.5, rely=0.08, anchor=tkinter.CENTER)

        self.search_entry = customtkinter.CTkEntry(
            master=self.east_frame,
            width=150,
            height=25,
            placeholder_text="Search for audio",
        )
        self.search_entry.place(relx=0.5, rely=0.16, anchor=tkinter.CENTER)

        self.listframe = customtkinter.CTkFrame(
            master=self.east_frame, width=150, height=175, corner_radius=8
        )
        self.listframe.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.songs_box = customtkinter.CTkTextbox(
            master=self.listframe,
            width=140,
            height=165,
            bg_color='transparent',
            fg_color='transparent',
            corner_radius=8,
        )
        self.songs_box.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.index_entry = customtkinter.CTkEntry(
            master=self.east_frame,
            width=150,
            height=25,
            placeholder_text="Enter index of audio",
        )
        self.index_entry.place(relx=0.5, rely=0.84, anchor=tkinter.CENTER)

        self.playbutton = customtkinter.CTkButton(
            master=self.east_frame,
            text="Play",
            width=150,
            height=25,
            command=lambda: self.play_search(self.index_entry.get(), MISSThelpers.MISSTlistdir(self.importsDest)),
        )
        self.playbutton.place(relx=0.5, rely=0.93, anchor=tkinter.CENTER)

        importsBoxUpdates = threading.Thread(target=self.global_checks, args=(self.search_entry, self.songs_box))
        importsBoxUpdates.daemon = True
        importsBoxUpdates.start()
        ## WEST FRAME ----------------------------------------------------------------------------------------------------

        self.logolabel = customtkinter.CTkLabel(
            master=self.west_frame, text=f"MISST {version}", font=(self.FONT, -16)
        )
        self.logolabel.place(relx=0.5, rely=0.12, anchor=tkinter.CENTER)

        self.themelabel = customtkinter.CTkLabel(master=self.west_frame, text="Appearance Mode:")
        self.themelabel.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)

        self.thememenu = customtkinter.CTkOptionMenu(
            master=self.west_frame,
            values=["System", "Dark", "Light"],
            command=lambda x: MISSThelpers.change_theme(x)
        )
        self.thememenu.place(relx=0.5, rely=0.8, anchor=tkinter.CENTER)

        self.settings_button = customtkinter.CTkButton(
            master=self.west_frame,
            font=(self.FONT, -12),
            text="",
            image=customtkinter.CTkImage(Image.open(f"./Assets/settings.png"), size=(25,25)),
            bg_color='transparent',
            fg_color='transparent',
            hover_color=self.west_frame.cget("bg_color"),
            width=5,
            height=5,
            command=lambda: self.draw_settings_frame(),
        )
        self.settings_button.place(relx=0.3, rely=0.9, anchor=tkinter.CENTER)

        self.lyrics = customtkinter.CTkButton(
            master=self.west_frame,
            font=(self.FONT, -12),
            text="",
            image=customtkinter.CTkImage(Image.open(f"./Assets/lyrics.png"), size=(25,25)),
            bg_color='transparent',
            fg_color='transparent',
            hover_color=self.west_frame.cget("bg_color"),
            width=5,
            height=5,
            corner_radius=16,
            command=lambda: print("test"),
        )
        self.lyrics.place(relx=0.7, rely=0.9, anchor=tkinter.CENTER)

        self.refresh_button = customtkinter.CTkButton(
            master=self.west_frame,
            font=(self.FONT, -12),
            text="",
            image=customtkinter.CTkImage(Image.open(f"./Assets/reload.png"), size=(25,25)),
            bg_color='transparent',
            fg_color='transparent',
            hover_color=self.west_frame.cget("bg_color"),
            width=5,
            height=5,
            command=lambda: threading.Thread(target=MISSThelpers.refreshConnection, args=(self,), daemon=True).start(),
        )
        self.refresh_button.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)

        ## NORTH FRAME ----------------------------------------------------------------------------------------------------

        self.songlabel = customtkinter.CTkButton(
            master=self.north_frame,
            text=f"Play Something!",
            width=240,
            height=50,
            font=(self.FONT, -14),
            command=lambda: print("test"),
            fg_color='transparent',
            hover_color=self.north_frame.cget("bg_color"),
            text_color=self.logolabel.cget("text_color")
        )
        self.songlabel.place(relx=0.5, rely=0.3, anchor=tkinter.CENTER)

        self.progressbar = customtkinter.CTkSlider(master=self.north_frame, width=225, height=15, from_=0, to=100, number_of_steps=100, command=lambda x: self.slider_event(x), state=tkinter.DISABLED)
        self.progressbar.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)
        self.progressbar.set(0)

        self.progress_label_left = customtkinter.CTkLabel(
            master=self.north_frame, text="0:00", font=(self.FONT, -12), width=5
        )
        self.progress_label_left.place(relx=0.1, rely=0.7, anchor=tkinter.CENTER)

        self.progress_label_right = customtkinter.CTkLabel(
            master=self.north_frame, text="0:00", font=(self.FONT, -12), width=5
        )
        self.progress_label_right.place(relx=0.9, rely=0.7, anchor=tkinter.CENTER)

        ## CENTER FRAME ----------------------------------------------------------------------------------------------------

        self.checkbox1 = customtkinter.CTkCheckBox(
            master=self.center_frame,
            text="bass",
            command=lambda: MISSThelpers.checkbox_event(self.check_var1, self.player.bass, self.slider1),
            variable=self.check_var1,
            onvalue="on",
            offvalue="off",
        )
        self.checkbox1.place(relx=0.1, rely=0.2, anchor=tkinter.W)

        self.checkbox2 = customtkinter.CTkCheckBox(
            master=self.center_frame,
            text="drums",
            command=lambda: MISSThelpers.checkbox_event(self.check_var2, self.player.drums, self.slider2),
            variable=self.check_var2,
            onvalue="on",
            offvalue="off",
        )
        self.checkbox2.place(relx=0.1, rely=0.35, anchor=tkinter.W)

        self.checkbox3 = customtkinter.CTkCheckBox(
            master=self.center_frame,
            text="other",
            command=lambda: MISSThelpers.checkbox_event(self.check_var3, self.player.other, self.slider3),
            variable=self.check_var3,
            onvalue="on",
            offvalue="off",
        )
        self.checkbox3.place(relx=0.1, rely=0.5, anchor=tkinter.W)

        self.checkbox4 = customtkinter.CTkCheckBox(
            master=self.center_frame,
            text="vocals",
            command=lambda: MISSThelpers.checkbox_event(self.check_var4, self.player.vocals, self.slider4),
            variable=self.check_var4,
            onvalue="on",
            offvalue="off",
        )
        self.checkbox4.place(relx=0.1, rely=0.65, anchor=tkinter.W)

        self.slider1 = customtkinter.CTkSlider(
            master=self.center_frame,
            from_=0,
            to=1,
            command=lambda x: MISSThelpers.slider_event(x,  self.player.bass,  self.checkbox1),
            number_of_steps=10,
        )
        self.slider1.place(relx=0.6, rely=0.2, anchor=tkinter.CENTER)

        self.slider2 = customtkinter.CTkSlider(
            master=self.center_frame,
            from_=0,
            to=1,
            command=lambda x: MISSThelpers.slider_event(x,  self.player.drums,  self.checkbox2),
            number_of_steps=10,
        )
        self.slider2.place(relx=0.6, rely=0.35, anchor=tkinter.CENTER)

        self.slider3 = customtkinter.CTkSlider(
            master=self.center_frame,
            from_=0,
            to=1,
            command=lambda x: MISSThelpers.slider_event(x,  self.player.other,  self.checkbox3),
            number_of_steps=10,
        )
        self.slider3.place(relx=0.6, rely=0.5, anchor=tkinter.CENTER)

        self.slider4 = customtkinter.CTkSlider(
            master=self.center_frame,
            from_=0,
            to=1,
            command=lambda x: MISSThelpers.slider_event(x,  self.player.vocals,  self.checkbox4),
            number_of_steps=10,
        )
        self.slider4.place(relx=0.6, rely=0.65, anchor=tkinter.CENTER)

        self.nc_checkbox = customtkinter.CTkSwitch(
            master=self.center_frame,
            text="nightcore",
            command=lambda: print("test"),
            variable=self.nc_var,
            onvalue="on",
            offvalue="off",
        )
        self.nc_checkbox.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)
        self.nc_checkbox.configure(state=tkinter.DISABLED)

        ## SOUTH FRAME ----------------------------------------------------------------------------------------------------

        self.import_button = customtkinter.CTkButton(
            master=self.south_frame,
            command=lambda: self.draw_imports_frame(),
            image=customtkinter.CTkImage(Image.open(f"./Assets/import.png"), size=(30, 30)),
            fg_color='transparent',
            hover_color=self.south_frame.cget("bg_color"),
            text="Import Song(s)",
            font=(self.FONT, -14),
            width=240,
            height=50,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_button.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)        

    def imports_checkbox_event(self, current_var):
        vars = [self.import_Spotify_var, self.import_Youtube_var, self.import_Deezer_var, self.import_Soundcloud_var]
        checkboxes = [self.import_Spotify_checkbox, self.import_Youtube_checkbox, self.import_Deezer_checkbox, self.import_Soundcloud_checkbox]
        for var in vars:
            if var.get() == "on":
                var.set("off")
                checkboxes[vars.index(var)].deselect()
        current_var.set("on")
        checkboxes[vars.index(current_var)].select()

    def draw_imports_frame(self):
        self.imports_frame = customtkinter.CTkFrame(
            master=self, width=self.WIDTH * (755 / self.WIDTH), height=self.HEIGHT * (430 / self.HEIGHT)
        )
        self.imports_frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.left_frame = customtkinter.CTkFrame(
            master=self.imports_frame, width=350, height=380
        )
        self.left_frame.place(relx=0.25, rely=0.47, anchor=tkinter.CENTER)

        self.right_frame = customtkinter.CTkFrame(
            master=self.imports_frame, width=350, height=380
        )
        self.right_frame.place(relx=0.75, rely=0.47, anchor=tkinter.CENTER)

        self.import_title = customtkinter.CTkLabel(
            master=self.left_frame,
            text="Choose a source",
            font=(self.FONT, -20),
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_title.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

        self.import_Spotify_var = tkinter.StringVar()   
        self.import_Youtube_var = tkinter.StringVar()
        self.import_Deezer_var = tkinter.StringVar()
        self.import_Soundcloud_var = tkinter.StringVar()

        self.import_Spotify_button = customtkinter.CTkLabel(
            master=self.left_frame,
            image=customtkinter.CTkImage(Image.open(f"./Assets/Sources/Spotify.png"), size=(40, 40)),
            fg_color='transparent',
            text="",
            font=(self.FONT, -14),
            width=50,
            height=50,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_Spotify_button.place(relx=0.3, rely=0.2375, anchor=tkinter.CENTER)

        self.import_Spotify_checkbox = customtkinter.CTkCheckBox(
            master=self.left_frame,
            text="",
            command=lambda: self.imports_checkbox_event(self.import_Spotify_var),
            variable=self.import_Spotify_var,
            onvalue="on",
            offvalue="off",
        )
        self.import_Spotify_checkbox.place(relx=0.61, rely=0.2375, anchor=tkinter.CENTER)


        self.import_Youtube_button = customtkinter.CTkLabel(
            master=self.left_frame,
            image=customtkinter.CTkImage(Image.open(f"./Assets/Sources/YoutubeMusic.png"), size=(40, 40)),
            fg_color='transparent',
            text="",
            font=(self.FONT, -14),
            width=50,
            height=50,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_Youtube_button.place(relx=0.3, rely=0.3750, anchor=tkinter.CENTER)

        self.import_Youtube_checkbox = customtkinter.CTkCheckBox(
            master=self.left_frame,
            text="",
            command=lambda: self.imports_checkbox_event(self.import_Youtube_var),
            variable=self.import_Youtube_var,
            onvalue="on",
            offvalue="off",
        )
        self.import_Youtube_checkbox.place(relx=0.61, rely=0.3750, anchor=tkinter.CENTER)

        self.import_Deezer_button = customtkinter.CTkLabel(
            master=self.left_frame,
            image=customtkinter.CTkImage(Image.open(f"./Assets/Sources/Deezer.png"), size=(40, 40)),
            fg_color='transparent',
            text="",
            font=(self.FONT, -14),
            width=50,
            height=50,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_Deezer_button.place(relx=0.3, rely=0.5125, anchor=tkinter.CENTER)

        self.import_Deezer_checkbox = customtkinter.CTkCheckBox(
            master=self.left_frame,
            text="",
            command=lambda: self.imports_checkbox_event(self.import_Deezer_var),
            variable=self.import_Deezer_var,
            onvalue="on",
            offvalue="off",
        )
        self.import_Deezer_checkbox.place(relx=0.61, rely=0.5125, anchor=tkinter.CENTER)

        self.import_Soundcloud_button = customtkinter.CTkLabel(
            master=self.left_frame,
            image=customtkinter.CTkImage(Image.open(f"./Assets/Sources/Soundcloud.png"), size=(40, 40)),
            fg_color='transparent',
            text="",
            font=(self.FONT, -14),
            width=50,
            height=50,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_Soundcloud_button.place(relx=0.3, rely=0.6500, anchor=tkinter.CENTER)

        self.import_Soundcloud_checkbox = customtkinter.CTkCheckBox(
            master=self.left_frame,
            text="",
            command=lambda: self.imports_checkbox_event(self.import_Soundcloud_var),
            variable=self.import_Soundcloud_var,
            onvalue="on",
            offvalue="off",
        )
        self.import_Soundcloud_checkbox.place(relx=0.61, rely=0.6500, anchor=tkinter.CENTER)

        self.source_entry = customtkinter.CTkEntry(
            master=self.left_frame,
            width=200,
            text_color=self.logolabel.cget("text_color"),
            placeholder_text="Enter your share URL here",
        )
        self.source_entry.place(relx=0.5, rely=0.8, anchor=tkinter.CENTER)

        self.import_button = customtkinter.CTkButton(
            master=self.left_frame,
            command=lambda: self.sourcePreprocess(self.source_entry.get()),
            text="Import",
            font=(self.FONT, -14),
            width=75,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_button.place(relx=0.32, rely=0.9, anchor=tkinter.CENTER)

        self.or_label = customtkinter.CTkLabel(
            master=self.left_frame,
            text="OR",
            font=(self.FONT, -14),
            text_color=self.logolabel.cget("text_color"),
        )
        self.or_label.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)

        self.import_file_button = customtkinter.CTkButton(
            master=self.left_frame,
            command=lambda: self.filePreprocess(),
            text="From File",
            font=(self.FONT, -14),
            width=75,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_file_button.place(relx=0.68, rely=0.9, anchor=tkinter.CENTER)

        self.preprocess_status_label = customtkinter.CTkLabel(
            master=self.right_frame,
            text="Preprocess Status",
            font=(self.FONT, -20),
            text_color=self.logolabel.cget("text_color"),
        )
        self.preprocess_status_label.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

        self.preprocess_terminal = customtkinter.CTkFrame(
            master=self.right_frame,
            width=275,
            height=290,
            fg_color="#0C0C0C",
            border_width=1,
        )
        self.preprocess_terminal.place(relx=0.5, rely=0.55, anchor=tkinter.CENTER)

        self.preprocess_terminal_text = customtkinter.CTkTextbox(
            master=self.preprocess_terminal,
            font=(self.FONT, -14),
            width=250,
            height=250,
            bg_color="transparent",
            fg_color="transparent",
            text_color="#CCCCCC",
        )
        self.preprocess_terminal_text.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.note_label = customtkinter.CTkLabel(
            master=self.imports_frame,
            text="Note: You can only import one source at a time.",
            font=(self.FONT, -12),
            state=tkinter.DISABLED,
        )
        self.note_label.place(relx=0.5, rely=0.95, anchor=tkinter.CENTER)

        wait_time = str(self.server.getAverageWaitTime())

        self.wait_time_label = customtkinter.CTkLabel(
            master=self.imports_frame,
            text=f"Avrg. Wait Time: {wait_time}s",
            font=(self.FONT, -12),
            text_color=self.logolabel.cget("text_color"),
            state=tkinter.DISABLED,
        )
        self.wait_time_label.place(relx=0.9, rely=0.95, anchor=tkinter.CENTER)

        self.return_button = customtkinter.CTkButton(
            master=self.imports_frame,
            command=lambda: self.imports_frame.destroy(),
            image=customtkinter.CTkImage(light_image=Image.open("./Assets/goback.png"), dark_image=Image.open("./Assets/goback_dark.png")),
            fg_color='transparent',
            hover_color=self.imports_frame.cget("bg_color"),
            text="Return",
            font=(self.FONT, -12),
            width=5,
            text_color="#6D6D6D",
        )
        self.return_button.place(relx=0.1, rely=0.95, anchor=tkinter.CENTER)

        self.console = MISSTconsole(self.preprocess_terminal_text, "MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n\nMISST>")

        if self.server_connected == False:
            self.console.update(" Error: Server is not running")
            self.server_down_cover = customtkinter.CTkFrame(
                master=self.imports_frame, width=350, height=380
            )
            self.server_down_cover.place(relx=0.25, rely=0.47, anchor=tkinter.CENTER)
            self.server_down_cover_label = customtkinter.CTkLabel(
                image=customtkinter.CTkImage(Image.open("./Assets/server_off.png"), size=(100, 100)),
                text="",
                master=self.server_down_cover,
                font=(self.FONT, -20),
                text_color=self.logolabel.cget("text_color"),
            )
            self.server_down_cover_label.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        else:
            self.console.update(" waiting")

    def filePreprocess(self):
        self.import_file_button.configure(state=tkinter.DISABLED)
        self.import_button.configure(state=tkinter.DISABLED)
        file = tkinter.filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("mp3 files","*.mp3"),("wav files", "*.wav"),("all files","*.*")), multiple=False)
        if file != "":
            self.console.endUpdate()
            threading.Thread(target=MISSTpreprocess.preprocess, args=(self, file, self.importsDest), daemon=True).start()

    def sourcePreprocess(self, url):
        if url != "":

            # Spotify Import
            if self.import_Spotify_var.get() == "on":
                self.console.endUpdate()
                threading.Thread(target=MISSTpreprocess.importSpotify, args=(self, url, self.importsDest), daemon=True).start()
            
            # Youtube Import
            elif self.import_Youtube_var.get() == "on":
                self.console.endUpdate()
                threading.Thread(target=MISSTpreprocess.importYoutube, args=(self, url, self.importsDest), daemon=True).start()

            # Deezer Import
            elif self.import_Deezer_var.get() == "on":
                self.console.endUpdate()
                threading.Thread(target=MISSTpreprocess.importDeezer, args=(self, url, self.importsDest), daemon=True).start()

            # Soundcloud Import
            elif self.import_Soundcloud_var.get() == "on":
                self.console.endUpdate()
                threading.Thread(target=MISSTpreprocess.importSoundcloud, args=(self, url, self.importsDest), daemon=True).start()

            else:
                pass
        return

    def draw_settings_frame(self):
        self.settings_window = customtkinter.CTkFrame(
            master=self, width=self.WIDTH * (755 / self.WIDTH), height=self.HEIGHT * (430 / self.HEIGHT)
        )
        self.settings_window.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.return_button = customtkinter.CTkButton(
            master=self.settings_window,
            command=lambda: self.settings_window.destroy(),
            image=customtkinter.CTkImage(light_image=Image.open("./Assets/goback.png"), dark_image=Image.open("./Assets/goback_dark.png")),
            fg_color='transparent',
            hover_color=self.settings_window.cget("bg_color"),
            text="",
            font=(self.FONT, -14),
            width=5,
            text_color=self.logolabel.cget("text_color"),
        )
        self.return_button.place(relx=0.25, rely=0.95, anchor=tkinter.CENTER)

        self.settings_frame = customtkinter.CTkFrame(
            master=self.settings_window, width=350, height=380
        )
        self.settings_frame.place(relx=0.25, rely=0.47, anchor=tkinter.CENTER)

        self.setting_header = customtkinter.CTkLabel(
            master=self.settings_frame, text="Settings", font=(self.FONT, -18)
        )
        self.setting_header.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

        self.general_frame = customtkinter.CTkFrame(master=self.settings_frame, width=300, height=125)
        self.general_frame.place(relx=0.5, rely=0.35, anchor=tkinter.CENTER)

        self.general_header = customtkinter.CTkLabel(
            master=self.general_frame, text="General", font=(self.FONT, -16)
        )
        self.general_header.place(relx=0.2, rely=0.15, anchor=tkinter.CENTER)

        self.autoplay_box = customtkinter.CTkSwitch(
            master=self.general_frame,
            text="Autoplay",
            font=(self.FONT, -12),
            command=lambda: MISSThelpers.autoplay_event(self),
            width=50,
        )
        self.autoplay_box.place(relx=0.28, rely=0.4, anchor=tkinter.CENTER)
        if self.settings.getSetting('autoplay') == 'true':
            self.autoplay_box.select()

        self.rpc_box = customtkinter.CTkSwitch(
            master=self.general_frame,
            text="Discord RPC",
            font=(self.FONT, -12),
            command=lambda: MISSThelpers.rpc_event(self),
            width=50,
        )
        self.rpc_box.place(relx=0.31, rely=0.625, anchor=tkinter.CENTER)
        if self.settings.getSetting('rpc') == 'true':
            self.rpc_box.select()

        self.preprocess_method_box = customtkinter.CTkSwitch(
            master=self.general_frame,
            text="Preprocess on Server?",
            font=(self.FONT, -12),
            command=lambda: MISSThelpers.preprocess_method_event(self),
            width=50,
        )
        self.preprocess_method_box.place(relx=0.4, rely=0.85, anchor=tkinter.CENTER)
        if self.settings.getSetting('process_on_server') == 'true':
            self.preprocess_method_box.select()

        ### General Settings ###

        self.storage_frame = customtkinter.CTkFrame(master=self.settings_frame, width=300, height=125)
        self.storage_frame.place(relx=0.5, rely=0.75, anchor=tkinter.CENTER)

        self.storage_header = customtkinter.CTkLabel(
            master=self.storage_frame, text="Storage", font=(self.FONT, -16)
        )
        self.storage_header.place(relx=0.2, rely=0.15, anchor=tkinter.CENTER)

        self.downloads_header = customtkinter.CTkLabel(
            master=self.storage_frame, text="Downloads:", font=(self.FONT, -12, "bold")
        )
        self.downloads_header.place(relx=0.24, rely=0.4, anchor=tkinter.CENTER)

        bytes = MISSThelpers.getsize(MISSThelpers, self.importsDest)
        gb = bytes / 1000000000
        gb = round(gb, 2)

        text = str(gb) + " GB"

        self.downloads_info = customtkinter.CTkLabel(
            master=self.storage_frame,
            text=text,
            font=(self.FONT, -12),
            width=25,
            state=tkinter.DISABLED,
        )
        self.downloads_info.place(relx=0.46, rely=0.4, anchor=tkinter.CENTER)

        self.downloads_subheader = customtkinter.CTkLabel(
            master=self.storage_frame,
            text="Downloaded Content",
            font=(self.FONT, -11),
            state=tkinter.DISABLED,
        )
        self.downloads_subheader.place(relx=0.29, rely=0.55, anchor=tkinter.CENTER)

        self.clear_downloads_button = customtkinter.CTkButton(
            master=self.storage_frame,
            text="Clear Downloads",
            font=(self.FONT, -12),
            width=15,
            height=2,
            command=lambda: MISSThelpers.clearDownloads(self),
        )
        self.clear_downloads_button.place(relx=0.75, rely=0.475, anchor=tkinter.CENTER)

        self.storage_location_header = customtkinter.CTkLabel(
            master=self.storage_frame, text="Storage Location:", font=(self.FONT, -12, "bold")
        )
        self.storage_location_header.place(relx=0.305, rely=0.7, anchor=tkinter.CENTER)

        dir = os.path.abspath(self.importsDest)
        dirlen = len(dir)
        n = 20
        location_text = dir if dirlen <= n else "..." + dir[-(n - dirlen) :]

        self.storage_location_info = customtkinter.CTkLabel(
            master=self.storage_frame,
            text=location_text,
            font=(self.FONT, -11),
            width=25,
            state=tkinter.DISABLED,
        )
        self.storage_location_info.place(relx=0.345, rely=0.85, anchor=tkinter.CENTER)

        self.change_location_button = customtkinter.CTkButton(
            master=self.storage_frame,
            text="Change Location",
            font=(self.FONT, -12),
            width=15,
            height=2,
            command=lambda: MISSThelpers.change_location(self),
            corner_radius=10,
        )
        self.change_location_button.place(relx=0.75, rely=0.775, anchor=tkinter.CENTER)

        self.theme_frame = customtkinter.CTkFrame(master=self.settings_window, width=350, height=380)
        self.theme_frame.place(relx=0.75, rely=0.47, anchor=tkinter.CENTER)

        self.theme_header = customtkinter.CTkLabel(
            master=self.theme_frame, text="Theme", font=(self.FONT, -18)
        )
        self.theme_header.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

        self.theme_frame_mini = customtkinter.CTkFrame(master=self.theme_frame, width=300, height=275)
        self.theme_frame_mini.place(relx=0.5, rely=0.55, anchor=tkinter.CENTER)

        self.button_light = customtkinter.CTkButton(
            master=self.theme_frame_mini,
            height=100,
            width=200,
            corner_radius=10,
            border_color="white",
            fg_color=self.settings.getSetting("chosenLightColor"),
            hover_color=self.settings.getSetting("chosenLightColor"),
            border_width=2,
            text="Light",
            command=lambda: MISSThelpers.updateTheme(self, "light"),
        )
        self.button_light.place(relx=0.5, rely=0.25, anchor=tkinter.CENTER)

        self.button_dark = customtkinter.CTkButton(
            master=self.theme_frame_mini,
            height=100,
            width=200,
            corner_radius=10,
            border_color="white",
            fg_color=self.settings.getSetting("chosenDarkColor"),
            hover_color=self.settings.getSetting("chosenDarkColor"),
            border_width=2,
            text="Dark",
            command=lambda: MISSThelpers.updateTheme(self, "dark"),
        )
        self.button_dark.place(relx=0.5, rely=0.75, anchor=tkinter.CENTER)

        self.info_label = customtkinter.CTkLabel(
            master=self.settings_window,
            text="Note: You must restart the app for changes to take effect.",
            font=(self.FONT, -12),
            state=tkinter.DISABLED,
            height=10,
        )
        self.info_label.place(relx=0.5, rely=0.95, anchor=tkinter.CENTER)

        self.reset_button = customtkinter.CTkButton(
            master=self.settings_window,
            text="Reset",
            font=(self.FONT, -12, "underline"),
            command=lambda: MISSThelpers.resetSettings(self),
            fg_color=self.settings_window.cget("fg_color"),
            hover_color=self.theme_frame.cget("fg_color"),
            width=15,
            text_color=self.info_label.cget("text_color")
        )
        self.reset_button.place(relx=0.75, rely=0.95, anchor=tkinter.CENTER)

    def global_checks(self, search_entry, songs_box):
        entry_val = None
        num = 0
        songs = []
        for _ in MISSThelpers.MISSTlistdir(self, self.importsDest):
            num += 1
            songs.append(f"{num}. {_}")
        while True:
            time.sleep(0.5)
            if len(MISSThelpers.MISSTlistdir(self, self.importsDest)) != num:
                num = 0
                songs = []
                for _ in MISSThelpers.MISSTlistdir(self, self.importsDest):
                    num += 1
                    songs.append(f"{num}. {_}")
                songs_box.configure(state="normal")
                songs_box.delete("0.0", "end")
                songs_box.insert("0.0", "\n\n".join(songs))
                songs_box.configure(state=tkinter.DISABLED)
            if len(songs) == 0:
                songs_box.configure(state="normal")
                songs_box.delete("0.0", "end")
                songs_box.insert("0.0", "No songs Imported!")
                songs_box.configure(state=tkinter.DISABLED)
            search = search_entry.get()
            found_songs = []
            for _ in songs:
                if search.lower() in _.lower():
                    found_songs.append(_)
            if entry_val == search_entry.get():
                pass
            else:
                songs_box.configure(state="normal")
                songs_box.delete("0.0", "end")
                songs_box.insert("0.0", "\n\n".join(found_songs))
                songs_box.configure(state=tkinter.DISABLED)
                entry_val = search_entry.get()

    def play_search(self, index_label, songs):
        try:
            index = int(index_label)
            song = songs[index - 1]
            self.playing = True
            self.nc_checkbox.deselect()
            MISSTplayer.play(self, f"{self.importsDest}/{song}", 0)
        except:
            pass

    def shuffle(self):
        try:
            songs = MISSThelpers.MISSTlistdir(self, self.importsDest) 
            random.shuffle(songs)
            self.playing = True
            self.nc_checkbox.deselect()
            MISSTplayer.play(self, f"{self.importsDest}/{songs[0]}", 0)
        except:
            pass

    def next(self, songName):
        try:
            songs = MISSThelpers.MISSTlistdir(self, self.importsDest) 
            index = songs.index(songName)
            self.playing = True
            self.nc_checkbox.deselect()
            MISSTplayer.play(self, f"{self.importsDest}/{songs[index + 1]}", 0)
        except:
            pass

    def previous(self, songName):
        try:
            songs = MISSThelpers.MISSTlistdir(self, self.importsDest) 
            index = songs.index(songName)
            self.playing = True
            self.nc_checkbox.deselect()
            MISSTplayer.play(self, f"{self.importsDest}/{songs[index - 1]}", 0)
        except:
            pass

    def slider_event(self, value, progressbar):
        progressbar.configure(state=tkinter.DISABLED)
        MISSTplayer.change_pos(self, f"{self.importsDest}/{self.songlabel._text}", int(value) * 1000)
        progressbar.configure(state="normal")
        return

    def nightcore(self, nightcore_check, progressbar):
        nightcore_check.configure(state=tkinter.DISABLED)
        if self.nc_var.get() == "on":
            for sound in self.cur_sound_datas:
                nc_sound = self.cur_sound_datas[sound] @ nc.Tones(1)
                self.cur_sound_datas[sound] = nc_sound
            MISSTplayer.change_pos(self, f"{self.importsDest}/{self.songlabel._text}", progressbar.get() * 1000)
        else:
            MISSTplayer.play(self, f"{self.importsDest}/{self.songlabel._text}", progressbar.get() * 1000)
        nightcore_check.configure(state="normal")
        return
    
    def playpause(self, progressbar):
        if self.playing == True:
            self.playpause_button.configure(state="normal", image=customtkinter.CTkImage(Image.open(f"./Assets/images/player-play.png"), size=(32, 32)))
            pygame.mixer.pause()
            self.playing = False
            progressbar.configure(state=tkinter.DISABLED)
            self.nc_checkbox.configure(state=tkinter.DISABLED)
        else:
            self.playpause_button.configure(state="normal", image=customtkinter.CTkImage(Image.open(f"./Assets/images/player-pause.png"), size=(32, 32)))
            pygame.mixer.unpause()
            self.playing = True
            progressbar.configure(state="normal")
            self.nc_checkbox.configure(state="normal")

    def loopEvent(self):
        if self.loop == True:
            self.loop = False
            self.loop_button.configure(state="normal", image=customtkinter.CTkImage(Image.open(f"./Assets/Images/loop-off.png"), size=(25, 25)))
        else:
            self.loop = True
            self.loop_button.configure(state="normal", image=customtkinter.CTkImage(Image.open(f"./Assets/Images/loop.png"), size=(25, 25)))

    def update_UI(self, audioPath, start_ms):
        pygame.mixer.unpause()
        self.next_button.configure(state="normal")
        self.previous_button.configure(state="normal")

        self.songlabel.configure(text="")
        song_name = os.path.basename(os.path.dirname(audioPath))
        web_name = secure_filename(song_name)
        song_dir = os.path.dirname(audioPath)

        self.next_button.configure(command=lambda: self.next(song_name))
        self.previous_button.configure(command=lambda: self.previous(song_name))
        try:
            cover_art = customtkinter.CTkImage(Image.open(MISSThelpers.resize_image(self, f"{song_dir}/{web_name}.png", 40)), size=(40, 40))
        except Exception as e:
            print(e)
            cover_art = customtkinter.CTkImage(Image.open("./Assets/default.png"), size=(40, 40))
        self.songlabel = customtkinter.CTkButton(
            master=self.north_frame,
            text=song_name,
            width=240,
            height=50,
            font=(self.FONT, -14),
            command=lambda: print("test"),
            fg_color='transparent',
            hover_color=self.north_frame.cget("bg_color"),
            text_color=self.logolabel.cget("text_color"), 
            image=cover_art
        )
        duration = self.cur_sound_datas['other'].duration_seconds

        progressbar = customtkinter.CTkSlider(master=self.north_frame, width=225, height=15, from_=0, to=int(duration), number_of_steps=int(duration), state="normal", command=lambda x: threading.Thread(target=self.slider_event, args=(x, progressbar), daemon=True).start())
        progressbar.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)
        progressbar.set(int(start_ms / 1000))

        self.playpause_button.configure(state="normal", command=lambda: self.playpause(progressbar))

        self.songlabel.place(relx=0.5, rely=0.3, anchor=tkinter.CENTER)
        self.nc_checkbox.configure(state="normal", command=lambda: threading.Thread(target=self.nightcore,args=(self.nc_checkbox, progressbar),daemon=True).start())

        MISSThelpers.update_rpc(
            self,
            Ltext="Listening to seperated audio",
            Dtext=song_name,
            image=f"{self.server_base}/getcoverart/{web_name}.png",
            large_text=song_name,
            end_time=time.time() + duration,
            small_image="icon-0",
        )
        t = start_ms / 1000

        progress_label_left = customtkinter.CTkLabel(
            master=self.north_frame, text=f"{str(datetime.timedelta(seconds=start_ms/1000)).split('.')[0][2:]}", font=(self.FONT, -12), width=50
        )
        progress_label_left.place(relx=0.1, rely=0.7, anchor=tkinter.CENTER)

        progress_label_right = customtkinter.CTkLabel(
            master=self.north_frame, text=f"{str(datetime.timedelta(seconds=duration-start_ms/1000)).split('.')[0][2:]}", font=(self.FONT, -12), width=50
        )
        progress_label_right.place(relx=0.9, rely=0.7, anchor=tkinter.CENTER)

        for _ in os.listdir(self.importsDest + "/" + song_name):
            if _.endswith("_nc.wav"):
                os.remove(self.importsDest + "/" + song_name + "/" + _)

        percent = 0

        while True:

            if self.songlabel._text == "" or progress_label_right._text == "0:00" or MISSTplayer().bass.get_busy() == False or MISSTplayer().drums.get_busy() == False or MISSTplayer().vocals.get_busy() == False or MISSTplayer().other.get_busy() == False:

                if self.loop == True:
                    self.nc_checkbox.deselect()
                    MISSTplayer.play(self, song_dir, 0)
                    break
                else:
                    pygame.mixer.pause()
                    progressbar.set(0)
                    progressbar.configure(state=tkinter.DISABLED)
                    self.songlabel = customtkinter.CTkButton(
                        master=self.north_frame,
                        text="Play Something!",
                        width=240,
                        height=50,
                        font=(self.FONT, -14),
                        command=lambda: print("test"),
                        fg_color='transparent',
                        hover_color=self.north_frame.cget("bg_color"),
                        text_color=self.logolabel.cget("text_color"), 
                    )
                    self.songlabel.place(relx=0.5, rely=0.3, anchor=tkinter.CENTER)
                    progress_label_left.configure(text="0:00")
                    progress_label_right.configure(text="0:00")
                    MISSThelpers.update_rpc(
                        self,
                        Ltext="Idle",
                        Dtext="Nothing is playing",
                        image="icon-0",
                        large_text="MISST",
                    )
                    self.nc_checkbox.configure(state=tkinter.DISABLED)
                    self.playpause_button.configure(state=tkinter.DISABLED)
                    self.next_button.configure(state=tkinter.DISABLED)
                    self.previous_button.configure(state=tkinter.DISABLED)
                    break

            if self.songlabel._text != song_name:
                break

            if self.playing == False:
                MISSThelpers.update_rpc(
                    self,
                    Ltext="(Paused)",
                    Dtext=song_name,
                    image=f"{self.server_base}/getcoverart/{web_name}.png",
                    large_text=song_name,
                    end_time=None,
                    small_image="icon-0",
                )
                while self.playing == False:
                    time.sleep(0.1)
                    if self.playing != False:
                        MISSThelpers.update_rpc(
                            self,
                            Ltext="Listening to seperated audio",
                            Dtext=song_name,
                            image=f"{self.server_base}/getcoverart/{web_name}.png",
                            large_text=song_name,
                            end_time=time.time() + duration - t,
                            small_image="icon-0",
                        )
                        break
            t += 1
            percent = t / duration
            progressbar.set(int(duration * percent))
            progress_label_left.configure(
                text=f"{str(datetime.timedelta(seconds=t)).split('.')[0][2:]}"
            )
            progress_label_right.configure(
                text=f"{str(datetime.timedelta(seconds=duration-t)).split('.')[0][2:]}"
            )
            time.sleep(1)
        if self.settings.getSetting('autoplay') == 'true' and percent >= 0.99 and self.loop != True:
            try:
                MISSTplayer.next()
                return
            except:
                pass
        return   

if __name__ == "__main__":
    app = MISSTapp()
    MISSThelpers.update_rpc(app, Ltext="Idle", Dtext="Nothing is playing")
    app.mainloop()