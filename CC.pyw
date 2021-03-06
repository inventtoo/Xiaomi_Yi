#! /usr/bin/env python
#Â encoding: utf-8
#
# Res andy

AppVersion = "0.5.4"

import base64, functools, json, os, platform, re, select, socket, subprocess, sys, tempfile, threading, time, tkMessageBox, urllib2, webbrowser, zlib
from Tkinter import *
from operator import itemgetter

class App:

	def __init__(self, master):
		self.connected = False
		self.camconfig = {}
		self.ActualAction = ""
		self.defaultbg = master.cget('bg')
		self.camsettableconfig = {}
		self.JsonData = {}
		self.MediaDir = ""
		self.ExpertMode = ""
		self.DefaultChunkSize = 8192
		
		self.DonateUrl = "http://sw.deltaflyer.cz/donate.html"
		self.GitUrl = "https://github.com/deltaflyer4747/Xiaomi_Yi"
		self.UpdateUrl = "https://raw.githubusercontent.com/deltaflyer4747/Xiaomi_Yi/master/version.txt"
		self.ConfigInfo = {"auto_low_light":"Automaticaly increase exposure time in low-light conditions", "auto_power_off":"Power down camera after specified time of inactivity", "burst_capture_number":"Specify ammount of images taken in Burst mode", "buzzer_ring":"Enable/disable camera locator beacon", "buzzer_volume":"Volume of camera beep", "camera_clock":"Tick&Apply to set Camera clock to the same as this PC", "capture_default_mode":"Mode to enter when changing to Capture via system_default_mode/HW button", "capture_mode":"Changes behavior of \"Photo\" button", "emergency_file_backup":"Locks file when shock is detected-for car dashcam (related to \"loop_record\")", "led_mode":"Set preferred LED behavior", "loop_record":"Overwrites oldest files when memory card is full", "meter_mode":"Metering mode for exposure/white ballance", "osd_enable":"Overlay info to hdmi/TV out", "photo_quality":"Set quality of still images", "photo_size":"Set resolution of still images", "photo_stamp":"Overlay date and time of capture to still images", "precise_cont_time":"Delay between individual images in timelapse mode", "precise_selftime":"Set delay to capture in Timer mode", "preview_status":"Turn this on to enable LIVE view", "start_wifi_while_booted":"Enable WiFi on boot", "system_default_mode":"Mode for HW trigger to set when camera is turned on", "system_mode":"Current mode for HW trigger", "timelapse_video":"Create timelapse video from image taken every 2 seconds", "video_output_dev_type":"Select video out HDMI or AV out over USB, use same cable as SJ4000", "video_quality":"Set quality of video recordings", "video_rotate":"Rotate video by 180° (upsidedown mount)", "video_resolution":"video_resolution is limited by selected video_standard", "video_stamp":"Overlay date and time to video recordings", "video_standard":"video_standard limits possible video_resolution options", "warp_enable":"On = No fisheye (Compensation ON), Off = Fisheye (Compensation OFF)", "wifi_ssid":"WiFi network name; reboot camera after Apply to take effect", "wifi_password":"WiFi network password; reboot camera after Apply to take effect"}
		self.ConfigTypes = {"auto_low_light":"checkbutton", "auto_power_off":"optionmenu", "burst_capture_number":"optionmenu", "buzzer_ring":"checkbutton", "buzzer_volume":"optionmenu", "camera_clock":"button", "capture_default_mode":"optionmenu", "emergency_file_backup":"checkbutton", "led_mode":"optionmenu", "loop_record":"checkbutton", "meter_mode":"optionmenu", "osd_enable":"checkbutton", "photo_quality":"optionmenu", "photo_size":"optionmenu", "photo_stamp":"optionmenu", "precise_cont_time":"optionmenu", "precise_selftime":"optionmenu", "preview_status":"checkbutton", "start_wifi_while_booted":"checkbutton", "system_default_mode":"radiobutton", "system_mode":"radiobutton", "timelapse_photo":"radiobutton", "timelapse_video":"radiobutton", "video_output_dev_type":"optionmenu", "video_quality":"optionmenu", "video_resolution":"optionmenu","video_rotate":"checkbutton", "video_stamp":"optionmenu", "video_standard":"radiobutton", "warp_enable":"checkbutton", "wifi_ssid":"entry", "wifi_password":"entry"}
		self.ConfigIgnores = ["dev_reboot", "restore_factory_settings", "capture_mode", "precise_self_running"]
		self.FileTypes = {"/":"Folder", ".bmp":"Image", ".ico":"Image", ".jpg":"Image", ".mka":"Audio", ".mkv":"Video", "mp3":"Audio", ".mp4":"Video", ".mpg":"Video", ".png":"Image", ".txt":"Text", "wav":"Audio"}
		self.ChunkSizes = [0.5,1,2,4,8,16,32,64,128,256]
		self.master = master
		self.master.geometry("445x250+300+75")
		self.master.wm_title("Xiaomi Yi C&C by Andy_S | ver %s" %AppVersion)
		
		self.statusBlock = LabelFrame(self.master, bd=1, relief=SUNKEN, text="")
		self.statusBlock.pack(side=BOTTOM, fill=X)
		self.status = Label(self.statusBlock, width=28, text="Disconnected", anchor=W)
		self.status.grid(column=0, row=0)
		self.battery = Label(self.statusBlock, width=13, text="", anchor=E)
		self.battery.grid(column=1, row=0)
		self.usage = Label(self.statusBlock, width=20, text="", anchor=E)
		self.usage.grid(column=2, row=0)
		self.Settings()
	
		
		# create a menu
		self.menu = Menu(self.master)
		root.config(menu=self.menu)
		
		self.Cameramenu = Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="Camera", menu=self.Cameramenu, underline=0)
		self.Cameramenu.add_command(label="Info", command=self.ActionInfo, state=DISABLED, underline=0)
		self.Cameramenu.add_command(label="Format", command=self.ActionFormat, state=DISABLED, underline=0)
		self.Cameramenu.add_command(label="Reboot", command=self.ActionReboot, state=DISABLED, underline=0)
		self.Cameramenu.add_command(label="Factory settings", command=self.ActionFactory, state=DISABLED, underline=8)
		if self.ExpertMode == "":
			self.Cameramenu.add_command(label="Expert Mode", command=self.ExpertEnable, state=DISABLED)
		self.Cameramenu.add_separator()
		self.Cameramenu.add_command(label="Exit", command=self.quit, underline=1)
		
		self.helpmenu = Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="Help", menu=self.helpmenu, underline=0)
		self.helpmenu.add_command(label="Donate", command=lambda aurl=self.DonateUrl:webbrowser.open_new(aurl), underline=0)
		self.helpmenu.add_command(label="About...", command=self.AboutProg, underline=0)
		self.UpdateCheck()
		self.ConnWindow()		

	def noaction(self, *args):
		return				

	def Settings(self, add="", rem=""):
		if add == "" and rem == "": #nothing to add or remove = initial call
			try: #open the settings file (if exists) and read the settings
				filek = open("settings.cfg","r")
				filet = filek.read()
				filek.close()
				ConfigFile = json.loads(filet)
				
				for pname in ConfigFile.keys():
					pvalue = ConfigFile[pname]
					if pname in ("camaddr", "camauto", "camport", "camdataport", "custom_vlc_path", "DefaultChunkSize", "ExpertMode"): setattr(self, pname, pvalue)
				if not {"camaddr", "camauto", "camport", "camdataport", "custom_vlc_path"} <= set(ConfigFile.keys()): raise
			except Exception: #no settings file yet, lets create default one & set defaults
				filek = open("settings.cfg","w")
				ConfigFile = '{"camaddr":"192.168.42.1","camauto":"","camport":7878,"camdataport":8787,"custom_vlc_path":"."}'
				filek.write(ConfigFile) 
				filek.close()
				self.camaddr = "192.168.42.1"
				self.camauto = ""
				self.camport = 7878
				self.camdataport = 8787
				self.custom_vlc_path = "."
		else:
			if len(add)>0:
				filek = open("settings.cfg","r")
				filet = filek.read()
				filek.close()
				ConfigFile = json.loads(filet)
				ConfigFile.update(add)
				filek = open("settings.cfg","w")
				filek.write(json.dumps(ConfigFile)) 
				filek.close()
			elif len(rem)>0:
				filek = open("settings.cfg","r")
				filet = filek.read()
				filek.close()
				ConfigFile = json.loads(filet)
				for pname in add:
					del ConfigFile[pname]
				filek = open("settings.cfg","w")
				filek.write(json.dumps(ConfigFile)) 
				filek.close()
	
	def ConnWindow(self):
		self.camconn = Frame(self.master) #create connection window with buttons
		self.addrv1 = StringVar()
		self.addrv2 = StringVar()
		self.addrv3 = StringVar()
		self.addrv4 = StringVar()
		self.addrv5 = StringVar()
		b = Button(self.camconn, text="Connect C&C", width=11, command=self.CamConnect)
		b.focus_set()
		b.grid(row=1, column=1, padx=10, pady=2)
		c = Checkbutton(self.camconn, text="Autoconnect", variable=self.addrv3, onvalue="on", offvalue="", height=1)
		c.grid(row=2, column=1)


		l = Label(self.camconn, width=12, text="IP address:", anchor=E)
		l.grid(row=1, column=2)
		e1 = Entry(self.camconn, textvariable=self.addrv1, width=20)
		e1.grid(row=1, column=3)
		l = Label(self.camconn, width=12, text="Own VLC Path:", anchor=E)
		l.grid(row=2, column=2)
		e5 = Entry(self.camconn, textvariable=self.addrv5, width=20)
		e5.grid(row=2, column=3)
		l = Label(self.camconn, width=17, text="*default path = .", anchor=W)
		l.grid(row=3, column=3, pady=3)

		l = Label(self.camconn, width=10, text="Json Port:", anchor=E)
		l.grid(row=1, column=4)
		e2 = Entry(self.camconn, textvariable=self.addrv2, width=4)
		e2.grid(row=1, column=5)
		l = Label(self.camconn, width=10, text="Data Port:", anchor=E)
		l.grid(row=2, column=4)
		e3 = Entry(self.camconn, textvariable=self.addrv4, width=4)
		e3.grid(row=2, column=5)
		self.addrv1.set(self.camaddr)
		self.addrv2.set(self.camport)
		self.addrv3.set(self.camauto)
		self.addrv4.set(self.camdataport)
		self.addrv5.set(self.custom_vlc_path)
		self.camconn.pack(side=TOP, fill=X)
		if self.camauto == "on":
			self.CamConnect()

	def GetPres(self, Value, option=0):
		Value = float(Value)
		fileName = ""
		while 1:
			if Value > 1024:
				Value = Value/float(1024)
				option += 1
			else:
				break
		pres = ["B", "KB", "MB", "GB", "TB"]
		return("%.1f%s" %(Value, pres[option]))

	def UpdateCheck(self):
		try:
			newversion = urllib2.urlopen(self.UpdateUrl, timeout=2).read()
		except Exception:
			newversion = "0"
		if newversion > AppVersion:
			if tkMessageBox.askyesno("New version found", "NEW VERSION FOUND (%s)\nYours is %s\n\nOpen download page?" %(newversion, AppVersion)):
				webbrowser.open_new(self.GitUrl)


	def GetAllConfig(self):
		for param in self.camconfig.keys():
			if param not in self.ConfigIgnores:
				tosend = '{"msg_id":3,"token":%s,"param":"%s"}' %(self.token, param)
				resp = self.Comm(tosend)
				thisresponse = resp["param"][0].values()[0]
				if thisresponse.startswith('settable:'):
					try:
						thisoptions = re.findall('settable:(.+)', thisresponse)[0]
						allparams = thisoptions.replace("\\/","/").split("#")
					except:
						allparams = ""
					self.camsettableconfig[param]=allparams


	def GetDetailConfig(self, param):
		if param not in self.ConfigIgnores:
			tosend = '{"msg_id":3,"token":%s,"param":"%s"}' %(self.token, param)
			resp = self.Comm(tosend)
			thisresponse = resp["param"][0].values()[0]
			if thisresponse.startswith('settable:'):
				thisoptions = re.findall('settable:(.+)', thisresponse)[0]
				allparams = thisoptions.replace("\\/","/").split("#")
				self.camsettableconfig[param]=allparams


	def ReadConfig(self):
		tosend = '{"msg_id":3,"token":%s}' %self.token 
		resp = self.Comm(tosend)
		self.camconfig = {}
		for each in resp["param"]: self.camconfig.update(each)
			
	
	def quit(self):
		sys.exit()

	
	def AboutProg(self):
		tkMessageBox.showinfo("About", "Control&Configure | ver. %s\nCreated by Andy_S, 2015\n\nandys@deltaflyer.cz" %AppVersion)
	
	def CamConnect(self):
		try:
			self.camaddr = self.addrv1.get() #read IP address from inputbox
			self.camport = int(self.addrv2.get()) #read port from inputbox & convert to integer
			self.camauto = self.addrv3.get() #read autoconnect status
			self.camdataport = int(self.addrv4.get()) #read data port from inputbox & convert to integer
			self.custom_vlc_path = self.addrv5.get() #read custom_vlc_path
			socket.setdefaulttimeout(5)
			self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create socket
			self.srv.connect((self.camaddr, self.camport)) #open socket
			self.srv.setblocking(0)
			self.connected = True
			self.thread_read = threading.Thread(target=self.JsonReader)
			self.thread_read.setDaemon(True)
			self.thread_read.setName('JsonReader')
			self.thread_read.start()
			self.token = ""
			tokentime = time.time()
			self.srv.send('{"msg_id":257,"token":0}') #auth to the camera
			while self.token == "":
				if time.time()+5>tokentime:
					continue
				else:
					raise Exception('Connection', 'failed') #throw an exception
			ToWrite = {"camaddr":self.camaddr, "camauto":self.camauto, "camport":self.camport, "camdataport":self.camdataport, "custom_vlc_path":self.custom_vlc_path}
			self.Settings(add=ToWrite)
			self.status.config(text="Connected") #display status message in statusbar
			self.status.update_idletasks()
			self.camconn.destroy() #hide connection selection
			self.UpdateUsage()
			self.UpdateBattery()
			self.ReadConfig()
			if self.camconfig["sd_card_status"] == "insert" and self.totalspace > 0:
				if self.camconfig["sdcard_need_format"] != "no-need":
					if self.ActionForceFormat():
						self.Cameramenu.entryconfig(0, state="normal")
						self.Cameramenu.entryconfig(1, state="normal")
						self.Cameramenu.entryconfig(2, state="normal")
						self.Cameramenu.entryconfig(3, state="normal")
						if self.ExpertMode == "":
							self.Cameramenu.entryconfig(4, state="normal")
						else:
							self.ShowExpertMenu()
						self.MainWindow()
					else:
						l = Label(self.master, width=40, text="SD memory card not formatted!\n\nPlease insert formatted SD card or format this one\n\nand restart C&C.", anchor=CENTER)
						l.pack(side=TOP, fill=BOTH)
				else:
					self.Cameramenu.entryconfig(0, state="normal")
					self.Cameramenu.entryconfig(1, state="normal")
					self.Cameramenu.entryconfig(2, state="normal")
					self.Cameramenu.entryconfig(3, state="normal")
					if self.ExpertMode == "":
						self.Cameramenu.entryconfig(4, state="normal")
					else:
						self.ShowExpertMenu()
					self.MainWindow()
			else:
				l = Label(self.master, width=40, text="No SD memory card inserted in camera!\n\nPlease power off camera, insert SD & restart C&C.", anchor=CENTER)
				l.pack(side=TOP, fill=BOTH)


		except Exception:
			self.connected = False
			tkMessageBox.showerror("Connect", "Cannot connect to the address specified")
			self.srv.close()
	
	def JsonReader(self):
		data = ""
		counter = 0
		flip = 0
		while self.connected:
			try:
				ready = select.select([self.srv], [], [])
				if ready[0]:
					byte = self.srv.recv(1)
					if byte == "{":
						counter += 1
						flip = 1
					elif byte == "}":
						counter -= 1
					data += byte
					
					if flip == 1 and counter == 0:
						try:
							data_dec = json.loads(data)
							data = ""
							flip = 0
							if "msg_id" in data_dec.keys():
								if data_dec["msg_id"] == 257:
									self.token = data_dec["param"]
								elif data_dec["msg_id"] == 7:
									if "type" in data_dec.keys() and "param" in data_dec.keys():
										if data_dec["type"] == "battery":
											self.thread_read = threading.Thread(target=self.UpdateBattery)
											self.thread_read.setName('UpdateBattery')
											self.thread_read.start()
										elif data_dec["type"] == "start_photo_capture":
											if self.camconfig["capture_mode"] == "precise quality cont.":
												self.bphoto.config(text="Stop\nTIMELAPSE", bg="#ff6666")
												self.brecord.config(state=DISABLED) 
												self.brecord.update_idletasks()
												self.bphoto.update_idletasks()
												self.thread_ReadConfig = threading.Thread(target=self.ReadConfig)
												self.thread_ReadConfig.setDaemon(True)
												self.thread_ReadConfig.setName('ReadConfig')
												self.thread_ReadConfig.start()
										elif data_dec["type"] == "precise_cont_complete":
											if self.camconfig["capture_mode"] == "precise quality cont.":
												self.bphoto.config(text="Start\nTIMELAPSE", bg="#66ff66")
												self.brecord.config(state="normal") 
												self.brecord.update_idletasks()
												self.bphoto.update_idletasks()
												self.thread_ReadConfig = threading.Thread(target=self.ReadConfig)
												self.thread_ReadConfig.setDaemon(True)
												self.thread_ReadConfig.setName('ReadConfig')
												self.thread_ReadConfig.start()


								self.JsonData[data_dec["msg_id"]] = data_dec
							else:
								raise Exception('Unknown','data')
						except Exception:
							print data
			except Exception:
				self.connected = False

	def Comm(self, tosend):
		Jtosend = json.loads(tosend)
		msgid = Jtosend["msg_id"]
		self.JsonData[msgid] = ""
		self.srv.send(tosend)
		while self.JsonData[msgid]=="":continue
		if self.JsonData[msgid]["rval"] == -4: #wrong token, ackquire new one & resend - "workaround" for camera insisting on tokens
			self.token = ""
			self.srv.send('{"msg_id":257,"token":0}')
			while self.token=="":continue
			Jtosend["token"] = self.token
			tosend = json.dumps(Jtosend)
			self.JsonData[msgid] = ""
			self.srv.send(tosend)
			while self.JsonData[msgid]=="":continue
		return self.JsonData[msgid]

	def UpdateUsage(self):
		tosend = '{"msg_id":5,"token":%s,"type":"total"}' %self.token
		self.totalspace = self.Comm(tosend)["param"]
		tosend = '{"msg_id":5,"token":%s,"type":"free"}' %self.token
		self.freespace = float(self.Comm(tosend)["param"])
		self.usedspace = self.totalspace-self.freespace
		self.totalpre = 0
		self.usedpre = 0
		while 1:
			if self.usedspace > 1024:
				self.usedspace = self.usedspace/float(1024)
				self.usedpre += 1
			else:
				break
		while 1:
			if self.totalspace > 1024:
				self.totalspace = self.totalspace/float(1024)
				self.totalpre += 1
			else:
				break
		pres = ["kB", "MB", "GB", "TB"]
		usage = "Used %.1f%s of %.1f%s" %(self.usedspace, pres[self.usedpre], self.totalspace, pres[self.totalpre])
		self.usage.config(text=usage) #display usage message in statusbar
		self.usage.update_idletasks()
	
	def UpdateBattery(self):
		tosend = '{"msg_id":13,"token":%s}' %self.token
		resp = self.Comm(tosend)
		Ctype = resp["type"]
		charge = resp["param"]

		if Ctype == "adapter":
			Ctype = "Charging"
		else:
			Ctype = "Battery"
		battery = "%s: %s%%" %(Ctype, charge)
		self.battery.config(text=battery) #display usage message in statusbar
		self.battery.update_idletasks()
	
	def ShowExpertMenu(self):
		self.Expertmenu = Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label="ExpertMenu", menu=self.Expertmenu, underline=0)
		self.Expertmenu.add_command(label="Show all camera variables", command=self.ExpertVariables, underline=0)
		self.Expertmenu.add_command(label="Enable Telnet access", command=self.ExpertTelnet, underline=0)
		self.ExpertmenuChunkSize = Menu(self.menu, tearoff=0)
		self.Expertmenu.add_cascade(label="File transfer chunk size", menu=self.ExpertmenuChunkSize, underline=0)
		self.ShowExpertChunkMenu()
		self.Expertmenu.add_command(label="Activate camera jetpack", command=self.ActionInfo, state=DISABLED, underline=0)
		self.Expertmenu.add_command(label="Explode camera", command=self.ActionInfo, state=DISABLED, underline=0)
		self.Expertmenu.add_command(label="Kill ALL puppies", command=self.ActionInfo, state=DISABLED, underline=0)
		
	def ShowExpertChunkMenu(self):
		self.ExpertmenuChunkSize.delete(0,END)
		for thislabel in sorted(self.ChunkSizes):
			if self.DefaultChunkSize == thislabel*1024:
				selected = " ✓"
			else:
				selected = "  "
			self.ExpertmenuChunkSize.add_command(label="%skB%s" %(thislabel,selected), command=functools.partial(self.ExpertChunkChange,thislabel*1024))


	def ExpertChunkChange(self, NewChunkSize):
		self.DefaultChunkSize = int(NewChunkSize)
		self.Settings(add={"DefaultChunkSize":self.DefaultChunkSize})
		self.ShowExpertChunkMenu()

	def ExpertVariables(self):
		toshow = ""
		for pname in sorted(self.camconfig):
			pvalue = self.camconfig[pname]
			toshow += "%s: %s\n" %(pname, pvalue)
		tkMessageBox.showinfo("All current camera variables", toshow)
			
	def ExpertTelnet(self):
		tosend = '{"msg_id":1283,"token":%s,"param":"."}' %self.token
		self.curPwd = self.Comm(tosend)["pwd"].replace("/","\\/")
		tosend = '{"msg_id":1283,"token":%s,"param":"\/tmp\/fuse_d"}' %self.token
		self.Comm(tosend)
		tosend = '{"msg_id":1286,"token":%s,"param":"enable_info_display.script", "offset":0, "size":0, "md5sum":"d41d8cd98f00b204e9800998ecf8427e"}' %self.token
		self.Comm(tosend)
		if tkMessageBox.askyesno("Restart Camera", "You have to reboot camera for telnet to be enabled.\n\nReboot now? (C&C will close)"):
			tosend = '{"msg_id":2,"token":%s, "type":"dev_reboot", "param":"on"}' %self.token
			self.srv.send(tosend)
			time.sleep(1)
			sys.exit()
		else:
			tosend = '{"msg_id":1283,"token":%s,"param":"%s"}' %(self.token, self.curPwd)
			self.Comm(tosend)
			if self.ActualAction.startswith("FileManager"):
				self.FilePrintList()


		



	def MainWindow(self):
		self.mainwindow = Frame(self.master, width=550, height=400)
		self.topbuttons = Frame(self.mainwindow, bg="#aaaaff")
		self.MainButtonControl = Button(self.topbuttons, text="Control", width=7, command=self.MenuControl)
		self.MainButtonControl.pack(side=LEFT, padx=10, ipadx=5, pady=5)
		self.MainButtonConfigure = Button(self.topbuttons, text="Configure", width=7, command=self.MenuConfig)
		self.MainButtonConfigure.pack(side=LEFT, padx=10, ipadx=5, pady=5)
		self.MainButtonFiles = Button(self.topbuttons, text="Files", width=7, command=self.FileManager)
		self.MainButtonFiles.pack(side=LEFT, padx=10, ipadx=5, pady=5)
		self.topbuttons.pack(side=TOP, fill=X)
		self.mainwindow.pack(side=TOP, fill=X)
		self.MenuControl()
	
	def MenuControl(self):
		self.master.geometry("445x250+300+75")
		self.ReadConfig()
		try:
			self.content.destroy()
		except Exception:
			pass
		self.content = Frame(self.mainwindow)
		self.controlbuttons = Frame(self.content)
		if self.camconfig["capture_mode"] == "precise quality":
			self.bphoto = Button(self.controlbuttons, text="Take a \nPHOTO", width=13, command=self.ActionPhoto, bg="#ccccff")
		elif self.camconfig["capture_mode"] == "precise quality cont.":
			if self.camconfig["precise_cont_capturing"] == "off":
				self.bphoto = Button(self.controlbuttons, text="Start\nTIMELAPSE", width=13, command=self.ActionPhoto, bg="#66ff66")
			else:
				self.bphoto = Button(self.controlbuttons, text="Stop\nTIMELAPSE", width=13, command=self.ActionPhoto, bg="#ff6666")
		elif self.camconfig["capture_mode"] == "burst quality":
			self.bphoto = Button(self.controlbuttons, text="Burst \nPHOTOS", width=13, command=self.ActionPhoto, bg="#ffccff")
		elif self.camconfig["capture_mode"] == "precise self quality":
			self.bphoto = Button(self.controlbuttons, text="Delayed\nPHOTO", width=13, command=self.ActionPhoto, bg="#ccffff")
		self.bphoto.pack(side=LEFT, padx=12, pady=5)
		
	
		if "record" in self.camconfig["app_status"]:
			self.brecord = Button(self.controlbuttons, text="STOP\nRecording", width=7, command=self.ActionRecordStop, bg="#ff6666")
			self.bphoto.config(state=DISABLED)
			self.bphoto.update_idletasks() 
		else:
			self.brecord = Button(self.controlbuttons, text="START\nRecording", width=7, command=self.ActionRecordStart, bg="#66ff66")
		self.brecord.pack(side=LEFT, padx=10, ipadx=5, pady=5)
		if self.camconfig["capture_mode"] == "precise quality cont.":
			if self.camconfig["precise_cont_capturing"] == "on":
				self.brecord.config(state=DISABLED) 
				self.brecord.update_idletasks()


		if "off" in self.camconfig["preview_status"] or "record" in self.camconfig["app_status"]:
			self.bstream = Button(self.controlbuttons, text="LIVE\nView", width=7, command=self.ActionVideoStart, bg="#ffff66", state=DISABLED)
		else:
			self.bstream = Button(self.controlbuttons, text="LIVE\nView", width=7, command=self.ActionVideoStart, bg="#ffff66")
		self.bstream.pack(side=LEFT, padx=10, ipadx=5, pady=5)
		self.controlbuttons.pack(side=TOP, fill=X)

		self.FramePhotoButtonMod = Frame(self.content)
		self.Photo_options = {"precise quality":"Single","precise quality cont.":"Timelapse","burst quality":"Burst","precise self quality":"Delayed"}
		self.Photo_thisvalue = StringVar(self.FramePhotoButtonMod)
		self.Photo_thisvalue.set(self.Photo_options[self.camconfig["capture_mode"]]) # actual value
		self.Photo_thisvalue.trace("w", self.MenuPhoto_changed)
		self.Photo_valuebox = OptionMenu(self.FramePhotoButtonMod, self.Photo_thisvalue, *self.Photo_options.values())
		self.Photo_valuebox.config(width=10)
		self.Photo_valuebox.pack(side=LEFT, padx=10)
		self.FramePhotoButtonMod.pack(side=TOP, fill=X)


		self.content.pack(side=TOP, fill=X)
	
	def MenuPhoto_changed(self, *args):
		myoption = self.Photo_options.keys()[self.Photo_options.values().index(self.Photo_thisvalue.get())]
		tosend = '{"msg_id":2,"token":%s, "type":"capture_mode", "param":"%s"}' %(self.token, myoption)
		self.Comm(tosend)
		self.MenuControl()

		
	
	def ExpertEnable(self):
		if tkMessageBox.askyesno("Enable expert mode", "Are you sure you want to\nENABLE EXPERT MODE?\n\nThis will enable potentionaly dangerous,\nbut also enhanced and useful features!\n\nBy accepting this you accept\nall responsibility for your actions you do\nin expert mode.\n\nAuthor of this program does not take ANY responsibility\nfor potentional damage to your camera\ncaused by your improper usage of this software."):
			self.ExpertMode = self.camconfig["serial_number"]
			tosend = {"ExpertMode":self.ExpertMode}
			self.Settings(add=tosend)
			self.Cameramenu.delete(4)
			self.ShowExpertMenu()


	def ActionInfo(self):
		tkMessageBox.showinfo("Camera information", "SW ver: %s\nHW ver: %s\nSN: %s" %(self.camconfig["sw_version"], self.camconfig["hw_version"], self.camconfig["serial_number"]))
		self.UpdateUsage()


	def ActionForceFormat(self):
		if tkMessageBox.askyesno("Format memory card", "Memory card is not formatted\nFORMAT MEMORY CARD NOW?\n\nThis action can't be undone\nALL PHOTOS & VIDEOS WILL BE LOST!"):
			tosend = '{"msg_id":4,"token":%s}' %self.token
			self.Comm(tosend)
			return(True)
		else:
			return(False)

	def ActionFormat(self):
		if tkMessageBox.askyesno("Format memory card", "Are you sure you want to\nFORMAT MEMORY CARD?\n\nThis action can't be undone\nALL PHOTOS & VIDEOS WILL BE LOST!"):
			tosend = '{"msg_id":4,"token":%s}' %self.token
			self.Comm(tosend)
		self.UpdateUsage()
		if self.ActualAction.startswith("FileManager"):
			self.FilePrintList()

	def ActionReboot(self):
		if tkMessageBox.askyesno("Reboot camera", "Are you sure you want to\nreboot camera?\n\nThis will close C&C"):
			tosend = '{"msg_id":2,"token":%s, "type":"dev_reboot", "param":"on"}' %self.token
			self.srv.send(tosend)
			time.sleep(1)
			sys.exit()

	def ActionFactory(self):
		if tkMessageBox.askyesno("Reboot camera", "Are you sure you want to\nRESET CAMERA TO FACTORY SETTINGS?\n\nThis will close C&C"):
			tosend = '{"msg_id":2,"token":%s, "type":"restore_factory_settings", "param":"on"}' %self.token
			self.srv.send(tosend)
			time.sleep(1)
			sys.exit()

	def ActionPhoto(self):
		myid = 769
		tosend = '{"msg_id":769,"token":%s}' %self.token
		if self.camconfig["capture_mode"] == "precise quality cont.":
			if self.camconfig["precise_cont_capturing"] == "on":
				tosend = '{"msg_id":770,"token":%s}' %self.token
				myid = 770
			self.Comm(tosend)
		else:
			self.Comm(tosend)
		self.ReadConfig()
		self.UpdateUsage()


	def ActionRecordStart(self):
		self.UpdateUsage()
		tosend = '{"msg_id":513,"token":%s}' %self.token
		self.Comm(tosend)
		self.brecord.config(text="STOP\nrecording", command=self.ActionRecordStop, bg="#ff6666")
		self.brecord.update_idletasks()
		self.bphoto.config(state=DISABLED)
		self.bphoto.update_idletasks() 
		self.ReadConfig()

	def ActionRecordStop(self):
		tosend = '{"msg_id":514,"token":%s}' %self.token
		self.Comm(tosend)
		self.brecord.config(text="START\nrecording", command=self.ActionRecordStart, bg="#66ff66")
		self.brecord.update_idletasks()
		self.bphoto.config(state="normal")
		self.bphoto.update_idletasks() 
		self.ReadConfig()
		self.UpdateUsage()
	
	def ActionVideoStart(self):
		tosend = '{"msg_id":259,"token":%s,"param":"none_force"}' %self.token
		self.Comm(tosend)
		try:
			if self.custom_vlc_path != ".":
				if os.path.isfile(self.custom_vlc_path):
					torun = '"%s" rtsp://%s:554/live' %(self.custom_vlc_path, self.camaddr)
					subprocess.Popen(torun, shell=True)
				else:
					tkMessageBox.showinfo("Live View", "VLC Player not found\nUse your preferred player to view:\n rtsp://%s:554/live" %(self.camaddr))
			else:
				mysys = platform.system()
				if mysys == "Windows":
					if os.path.isfile("c:/Program Files/VideoLan/VLC/vlc.exe"):
						torun = '"c:/Program Files/VideoLan/VLC/vlc.exe" rtsp://%s:554/live' %(self.camaddr) 
						subprocess.Popen(torun, shell=True)
					else:
						if os.path.isfile("c:/Program Files (x86)/VideoLan/VLC/vlc.exe"):
							torun = '"c:/Program Files (x86)/VideoLan/VLC/vlc.exe" rtsp://%s:554/live' %(self.camaddr)
							subprocess.Popen(torun, shell=True)
						else:
							tkMessageBox.showinfo("Live View", "VLC Player not found\nUse your preferred player to view:\n rtsp://%s:554/live" %(self.camaddr))
				elif mysys == "Darwin":
					if os.path.isfile("/Applications/VLC.app/Contents/MacOS/VLC"):
						torun = '"/Applications/VLC.app/Contents/MacOS/VLC" rtsp://%s:554/live' %(self.camaddr)
						subprocess.Popen(torun, shell=True)
					else:
						tkMessageBox.showinfo("Live View", "VLC Player not found\nUse your preferred player to view:\n rtsp://%s:554/live" %(self.camaddr))
				else:
					tkMessageBox.showinfo("Live View", "VLC Player not found\nUse your preferred player to view:\n rtsp://%s:554/live" %(self.camaddr))
		except Exception:
			tkMessageBox.showinfo("Live View", "VLC Player not found\nUse your preferred player to view:\n rtsp://%s:554/live" %(self.camaddr))
	

	def MenuConfig_Apply(self, *args):
		for ThisOption in self.config_ToChange.keys():
			ThisValue = self.config_ToChange[ThisOption]
			self.MenuConfig_Commit(ThisOption, ThisValue)
		self.config_ToChange = {}
			
	def MenuConfig_Commit(self, ThisOption, ThisValue):
		tosend = '{"msg_id":2,"token":%s, "type":"%s", "param":"%s"}' %(self.token, ThisOption, ThisValue.replace("/","\\/"))
		if ThisOption == "camera_clock":
			ThisValue = time.strftime("%Y-%m-%d %H:%M:%S")
		self.ReadConfig()
		self.Comm(tosend)

	def MenuConfig_modify(self, *args):

		ThisOption = self.ConfigValues[args[0]]
		if ThisOption == "wifi_ssid":
			ThisValue = self.Config_WiSS.get()
		elif ThisOption == "wifi_password":
			ThisValue = self.Config_WiPW.get()
		else:
			ThisValue = self.master.getvar(args[0])
		self.config_ToChange[ThisOption] = ThisValue 

		if ThisOption == "video_standard":
			menu = self.config_VidRes['menu']
			menu.delete(0, END)
			if ThisValue == "NTSC":
				for value in self.MenuConfig_VideoresNtsc:
					menu.add_command(label=value, command=lambda value=value: self.config_VidResValue.set(value))
			else:
				for value in self.MenuConfig_VideoresPal:
					menu.add_command(label=value, command=lambda value=value: self.config_VidResValue.set(value))


	def myfunction(self, event):
		self.controlcanvas.configure(scrollregion=self.controlcanvas.bbox("all"),width=740,height=485)

	def MenuConfig(self):
		self.master.geometry("760x550+300+75")
		self.ReadConfig()
		self.GetAllConfig()
		try:
			self.content.destroy()
		except Exception:
			pass
		
		#First step of video_standard workaround
		This_video_standard = self.camconfig["video_standard"]
		This_video_resolution = self.camconfig["video_resolution"]
		if This_video_standard == "NTSC":
			self.MenuConfig_VideoresNtsc = self.camsettableconfig["video_resolution"]
			self.MenuConfig_Commit("video_standard", "PAL")
			self.GetDetailConfig("video_resolution")
			self.MenuConfig_VideoresPal = self.camsettableconfig["video_resolution"]
			self.MenuConfig_Commit("video_standard", "NTSC")
			self.GetDetailConfig("video_resolution")
		else:		
			self.MenuConfig_VideoresPal = self.camsettableconfig["video_resolution"]
			self.MenuConfig_Commit("video_standard", "NTSC")
			self.GetDetailConfig("video_resolution")
			self.MenuConfig_VideoresNtsc = self.camsettableconfig["video_resolution"]
			self.MenuConfig_Commit("video_standard", "PAL")
			self.GetDetailConfig("video_resolution")
		self.MenuConfig_Commit("video_resolution", This_video_resolution)
		
		
		self.status = []
		self.config_ToChange = {}
		self.config_options = sorted(self.camsettableconfig.keys())
		self.content = Frame(self.mainwindow, width=445, height=490)
		self.controlselect = Frame(self.content)
		self.controlselect.place(x=0,y=0)
		self.controlcanvas = Canvas(self.controlselect)
		self.controloptions = Frame(self.controlcanvas)
		self.config_scrollbar=Scrollbar(self.controlselect,orient="vertical",command=self.controlcanvas.yview)
		self.controlcanvas.configure(yscrollcommand=self.config_scrollbar.set)	
		self.config_scrollbar.pack(side="right",fill="y")
		self.controlcanvas.pack(side="left")
		self.controlcanvas.create_window((0,0),window=self.controloptions,anchor='nw')
		self.controloptions.bind("<Configure>",self.myfunction)

		self.controlbuttons = Frame(self.controloptions, width=445, height=20)
		self.config_apply = Button(self.controlbuttons, text="Apply", width=7, command=self.MenuConfig_Apply)
		self.config_apply.pack(side=LEFT, padx=10, pady=5)
		self.controlbuttons.pack(side=TOP, fill=X)

		row = 0
		self.ConfigValues = {}
		for ThisOption in self.config_options:
			if ThisOption in self.ConfigTypes.keys():
				ThisType = self.ConfigTypes[ThisOption]
			else:
				ThisType = "optionmenu"
			ThisFrame = Frame(self.controloptions)
			ThisLabel = Label(ThisFrame, width=18, text=ThisOption, anchor=W).grid(row=row,column=0)
			if ThisOption == "video_resolution":
				self.config_VidResValue = StringVar(self.controlselect)
				self.config_VidResValue.set(self.camconfig[ThisOption])
				self.config_VidResValue.trace("w", self.MenuConfig_modify)
				self.ConfigValues[self.config_VidResValue._name] = ThisOption
				self.config_VidRes = OptionMenu(ThisFrame, self.config_VidResValue, *self.camsettableconfig[ThisOption])
				self.config_VidRes.config(width=18, anchor=W)
				self.config_VidRes.grid(row=row,column=1)
			else:
				ThisValue = StringVar(self.controlselect)
				ThisValue.set(self.camconfig[ThisOption])
				ThisValue.trace("w", self.MenuConfig_modify)
				self.ConfigValues[ThisValue._name] = ThisOption
				if ThisType == "optionmenu":
					ValueBox = OptionMenu(ThisFrame, ThisValue, *self.camsettableconfig[ThisOption])
					ValueBox.config(width=18, anchor=W)
					ValueBox.grid(row=row,column=1)
				elif ThisType == "checkbutton":
					ValueBox = Checkbutton(ThisFrame, variable=ThisValue, onvalue="on", offvalue="off")
					ValueBox.config(width=18, anchor=W)
					ValueBox.grid(row=row,column=1)
					self.status.append((ValueBox,ThisValue))
				elif ThisType == "button":
					ValueBox = Checkbutton(ThisFrame, text=self.camconfig[ThisOption], variable=ThisValue, onvalue="on", offvalue="off")
					ValueBox.config(width=18, anchor=W)
					ValueBox.grid(row=row,column=1)
					self.status.append((ValueBox,ThisValue))
				elif ThisType == "radiobutton":
					RadioFrame = Frame(ThisFrame)
					ValueBox1 = Radiobutton(RadioFrame, text=self.camsettableconfig[ThisOption][0], variable=ThisValue, value=self.camsettableconfig[ThisOption][0])
					ValueBox1.config(width=7, anchor=W)
					ValueBox1.pack(side=LEFT)
					ValueBox2 = Radiobutton(RadioFrame, text=self.camsettableconfig[ThisOption][1], variable=ThisValue, value=self.camsettableconfig[ThisOption][1])
					ValueBox2.config(width=7, anchor=E)
					ValueBox2.pack(side=RIGHT)
					RadioFrame.grid(row=row,column=1)
					self.status.append((ValueBox1,ThisValue))
					self.status.append((ValueBox2,ThisValue))
				elif ThisType == "entry":
					if ThisOption == "wifi_ssid":
						self.Config_WiSS = ThisValue
						ValueBox = Entry(ThisFrame, textvariable=self.Config_WiSS, width=25)
						ValueBox.grid(row=row,column=1)
						self.status.append((ValueBox,self.Config_WiSS))
					elif ThisOption == "wifi_password":
						self.Config_WiPW = ThisValue
						ValueBox = Entry(ThisFrame, textvariable=self.Config_WiPW, width=25)
						ValueBox.grid(row=row,column=1)
						self.status.append((ValueBox,self.Config_WiPW))
			
			if ThisOption in self.ConfigInfo:
				ThisHint = Label(ThisFrame, width=62, text="*%s" %self.ConfigInfo[ThisOption], anchor=W).grid(row=row, column=2, padx=10)
			else:
				ThisHint = Label(ThisFrame, width=62, text='* Unknown config option, if you know what it does, let me know.' , anchor=W).grid(row=row, column=2, padx=10)
			ThisFrame.pack(side=TOP)
			row += 1

		self.controlbuttons = Frame(self.controloptions, width=445, height=20)
		self.config_apply = Button(self.controlbuttons, text="Apply", width=7, command=self.MenuConfig_Apply)
		self.config_apply.pack(side=LEFT, padx=10, pady=5)
		self.controlbuttons.pack(side=TOP, fill=X)


		self.content.pack(side=TOP, fill=X)
	
	
	def FileYScroll(self, *args):
		apply(self.ListboxFileName.yview, args)
		apply(self.ListboxFileSize.yview, args)
		apply(self.ListboxFileDate.yview, args)

	def FileDownReport(self, bytes_so_far, chunk_size, total_size, FileTP):
		percent = float(bytes_so_far) / total_size
		percent = round(percent*100, 2)
		thistime = time.time()
		if thistime - self.FileTime > 0.01:
			ActualSpeed = float(chunk_size/(thistime-self.FileTime))
			self.FileSpeed.append(ActualSpeed)
			self.FileTime = thistime
			pre = 0
			AvgSpeed = sum(self.FileSpeed) / float(len(self.FileSpeed))

			self.FileProgress.config(text="Downloading %s at %s/s (%0.2f%%)" %(FileTP, self.GetPres(Value=AvgSpeed), percent), bg=self.defaultbg)

		if bytes_so_far >= total_size:
			self.FileProgress.config(text="%s downloaded" %(FileTP), bg="#ddffdd")

	def FileDownChunk(self, chunk_size=0, report_hook=None, FileTP=""):
		if chunk_size == 0:
			chunk_size = self.DefaultChunkSize
		tosend = '{"msg_id":1285,"token":%s,"param":"%s", "offset":0, "fetch_size":%s}' %(self.token, FileTP, chunk_size)
		resp = self.Comm(tosend)
		total_size = int(resp["size"])
		this_size = int(resp["rem_size"])
		bytes_so_far = 0
		
		ThisFileName = "Files/%s" %FileTP
		filek = open(ThisFileName, "wb")
		self.FileTime = time.time()
		self.FileSpeed = []
		while 1:
			chunk = bytearray(this_size)
			view = memoryview(chunk)
			while this_size:
				nbytes = self.Datasrv.recv_into(view, this_size)
				view = view[nbytes:]
				this_size -= nbytes
			bytes_so_far += len(chunk)
			
			if not chunk:
				break
			filek.write(chunk)
			if report_hook:
				report_hook(bytes_so_far, chunk_size, total_size, FileTP)
			if bytes_so_far >= total_size:
				break
			else:
				tosend = '{"msg_id":1285,"token":%s,"param":"%s", "offset":%s, "fetch_size":%s}' %(self.token, FileTP, bytes_so_far, chunk_size)
				resp = self.Comm(tosend)
				this_size = int(resp["rem_size"])
					

		filek.close()

	

	def FileDownloadThread(self):
		FileIds = ()
		while FileIds == ():
			try:
				FileIds = self.ListboxFileName.curselection()
			except Exception:
				pass
		try:
			FilesToProcess = [self.ListboxFileName.get(idx) for idx in FileIds]
			if not os.path.isdir("Files"):
				os.mkdir("Files",0o777)
			for FileTP in FilesToProcess:
				if not FileTP.endswith("/"):
					self.Datasrv = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create data socket
					self.Datasrv.connect((self.camaddr, self.camdataport)) #open data socket
	
					self.FileProgress.config(text="Downloading", bg=self.defaultbg)
					try:
						self.FileDownChunk(report_hook=self.FileDownReport, FileTP=FileTP)
					except Exception as e:
						print e
						self.FileProgress.config(text="File download failed!", bg="#ffdddd")
						pass
					self.Datasrv.close()
				else:
					self.FileProgress.config(text="You cannot download a folder!", bg="#ffdddd")
			self.MainButtonControl.config(state="normal")
			self.MainButtonConfigure.config(state="normal")
			self.MainButtonFiles.config(state="normal")
			self.FileButtonDownload.config(state="normal")
			self.FileButtonDelete.config(state="normal")
			if self.ExpertMode:
				self.FileButtonCwd.config(state="normal")
			self.Cameramenu.entryconfig(1, state="normal")
			self.Cameramenu.entryconfig(2, state="normal")
			self.Cameramenu.entryconfig(3, state="normal")
			self.ListboxFileName.bind("<Double-Button-1>", self.FileDoubleClick)
							
		except Exception:
			self.FileProgress.config(text="File download failed!", bg="#ffdddd")
			self.MainButtonControl.config(state="normal")
			self.MainButtonConfigure.config(state="normal")
			self.MainButtonFiles.config(state="normal")
			self.FileButtonDownload.config(state="normal")
			if self.ExpertMode:
				self.FileButtonCwd.config(state="normal")
			self.FileButtonDelete.config(state="normal")
			self.Cameramenu.entryconfig(1, state="normal")
			self.Cameramenu.entryconfig(2, state="normal")
			self.Cameramenu.entryconfig(3, state="normal")
			self.ListboxFileName.bind("<Double-Button-1>", self.FileDoubleClick)
	

	def FileDownload(self, *args):
		self.MainButtonControl.config(state=DISABLED)
		self.MainButtonConfigure.config(state=DISABLED)
		self.MainButtonFiles.config(state=DISABLED)
		self.FileButtonDownload.config(state=DISABLED)
		self.FileButtonDelete.config(state=DISABLED)
		if self.ExpertMode:
			self.FileButtonCwd.config(state=DISABLED)
		self.Cameramenu.entryconfig(1, state=DISABLED)
		self.Cameramenu.entryconfig(2, state=DISABLED)
		self.Cameramenu.entryconfig(3, state=DISABLED)
		self.ListboxFileName.bind("<Double-Button-1>", self.noaction)
		
		self.thread_FileDown = threading.Thread(target=self.FileDownloadThread)
		self.thread_FileDown.start()
					
			
	def FileCwd(self):
		if len(self.ListboxFileName.curselection()) == 1:
			cwd = self.ListboxFileName.get(self.ListboxFileName.curselection()[0])
			if cwd.endswith("/"):
				tosend = '{"msg_id":1283,"token":%s,"param":"%s"}' %(self.token, cwd)
				self.curPwd = self.Comm(tosend)["pwd"]
				self.FilePrintList()
			
	def FileDoubleClick(self, *args):
		if len(self.ListboxFileName.curselection()) == 1:
			clicked = self.ListboxFileName.get(self.ListboxFileName.curselection()[0])
			if clicked.endswith("/"):
				self.FileCwd()
			else:
				self.FileDownload()


	def FileDelete(self, *args):
		try:
			FilesToProcess = [self.ListboxFileName.get(idx) for idx in self.ListboxFileName.curselection()]
			FilesToProcessStr = "\n".join(FilesToProcess)

			if tkMessageBox.askyesno("Delete file", "Are you sure you want to DELETE\n\n%s\n\nThis action can't be undone!" %FilesToProcessStr):
				if self.ExpertMode == "":
					tosend = '{"msg_id":1283,"token":%s,"param":"\/var\/www\/DCIM\/%s"}' %(self.token, self.MediaDir) #make sure we are still in the correct path
					self.Comm(tosend)
				for FileTP in FilesToProcess:
					self.FileProgress.config(text="Deleting %s" %FileTP, bg=self.defaultbg)
					tosend = '{"msg_id":1281,"token":%s,"param":"%s"}' %(self.token, FileTP)
					self.FileProgress.config(text="Deleted", bg=self.defaultbg)
			self.FileProgress.config(text="Deleted")
		except Exception:
			self.FileProgress.config(text="File deleting failed!", bg="#ffdddd")
		self.UpdateUsage()
		self.FilePrintList()
	
	def FileCreateList(self):
		self.filelist = Frame(self.content, bg="#ffffff")
		self.LabelFileHead = LabelFrame(self.filelist, bd=1, relief=SUNKEN, text="", width=760)
		self.LabelFileHead.pack(side=TOP, fill=X)
		self.LabelFileName = Label(self.LabelFileHead, width=14, bd=1, relief=RIDGE, text="Type", anchor=CENTER)
		self.LabelFileName.grid(column=0, row=0)
		self.LabelFileName = Label(self.LabelFileHead, width=35, bd=1, relief=RIDGE, text="Filename", anchor=CENTER)
		self.LabelFileName.grid(column=1, row=0)
		self.LabelFileSize = Label(self.LabelFileHead, width=12, bd=1, relief=RIDGE, text="Size", anchor=CENTER)
		self.LabelFileSize.grid(column=2, row=0)
		self.LabelFileDate = Label(self.LabelFileHead, width=30, bd=1, relief=RIDGE, text="DateTime ▼", anchor=CENTER)
		self.LabelFileDate.grid(column=3, row=0)        	

		self.FilesScrollbar = Scrollbar(self.filelist, orient=VERTICAL)
		self.ListboxFileType = Listbox(self.filelist, yscrollcommand=self.FilesScrollbar.set, height=8, width=12, bd=0, bg="#ffffff", fg="#000000", activestyle=NONE, highlightcolor="#ffffff", highlightthickness=0, selectborderwidth=0, selectbackground="#ffffff", selectforeground="#000000")
		self.ListboxFileName = Listbox(self.filelist, yscrollcommand=self.FilesScrollbar.set, selectmode=EXTENDED, height=27, width=37, bd=0, bg="#ffffff", fg="#000000", highlightcolor="#ffffff", highlightthickness=0)
		self.ListboxFileName.bind("<Double-Button-1>", self.FileDoubleClick)
		self.ListboxFileSize = Listbox(self.filelist, yscrollcommand=self.FilesScrollbar.set, height=8, width=12, bd=0, bg="#ffffff", fg="#000000", activestyle=NONE, highlightcolor="#ffffff", highlightthickness=0, selectborderwidth=0, selectbackground="#ffffff", selectforeground="#000000")
		self.ListboxFileDate = Listbox(self.filelist, yscrollcommand=self.FilesScrollbar.set, height=8, width=30, bd=0, bg="#ffffff", fg="#000000", activestyle=NONE, highlightcolor="#ffffff", highlightthickness=0, selectborderwidth=0, selectbackground="#ffffff", selectforeground="#000000")
		self.FilesScrollbar.config(command=self.FileYScroll)
		self.FilesScrollbar.pack(side=RIGHT, fill=Y)
		self.ListboxFileType.pack(side=LEFT, padx=10, fill=BOTH, expand=0)
		self.ListboxFileName.pack(side=LEFT, padx=15, fill=BOTH, expand=0)
		self.ListboxFileSize.pack(side=LEFT, padx=15, fill=BOTH, expand=0)
		self.ListboxFileDate.pack(side=LEFT, padx=15, fill=BOTH, expand=0)
		self.filelist.pack(side=TOP, fill=X)

	def FilePrintList(self):
		FileListing = {}
		DirListing = {}
		self.ListboxFileType.delete(0, END)
		self.ListboxFileName.delete(0, END)
		self.ListboxFileSize.delete(0, END)
		self.ListboxFileDate.delete(0, END)
		tosend = '{"msg_id":1282,"token":%s, "param":" -D -S"}' %self.token
		for each in self.Comm(tosend)["listing"]:
			if not each.keys()[0].endswith("/"):
				FileListing.update(each)
			else:
				DirListing.update(each)

		if len(FileListing) == 0 and self.ExpertMode == "":
			self.ListboxFileType.insert(END, "")
			self.ListboxFileName.insert(END, "")
			self.ListboxFileSize.insert(END, "")
			self.ListboxFileDate.insert(END, "")
		else:
			CamFiles=[]
			if self.curPwd != "/":
				CamDirs = [["../",""]]
			else:
				CamDirs = []
			for dirname in DirListing.keys():
				dirdate = re.findall(' bytes\|(.+)',DirListing[dirname])[0]
				CamDirs.append([dirname, dirdate])

			for filename in FileListing.keys():
				filetype = "File"
				for ThisFileType in self.FileTypes.keys():
					if filename.lower().endswith(ThisFileType):
						filetype = self.FileTypes[ThisFileType]

				filesize, filedate = re.findall('(.+) bytes\|(.+)',FileListing[filename])[0]
				filesize = float(filesize)
				filepre = 0
				while 1:
					if filesize > 1024:
						filesize = filesize/float(1024)
						filepre += 1
					else:
						break
				CamFiles.append([filetype, filename,filesize,filepre,filedate])
			pres = ["B", "kB", "MB", "GB", "TB"]
			if self.ExpertMode != "":
				for ThisCamDir in sorted(CamDirs):
					self.ListboxFileType.insert(END, "Folder")
					self.ListboxFileName.insert(END, ThisCamDir[0])
					self.ListboxFileSize.insert(END, "")
					self.ListboxFileDate.insert(END, ThisCamDir[1])
			
			for ThisCamFile in sorted(CamFiles, key=itemgetter(4)):
				self.ListboxFileType.insert(END, ThisCamFile[0])
				self.ListboxFileName.insert(END, ThisCamFile[1])
				self.ListboxFileSize.insert(END, " %.1f%s" %(ThisCamFile[2], pres[ThisCamFile[3]]))
				self.ListboxFileDate.insert(END, ThisCamFile[4])

	def FileManager(self):
		self.master.geometry("760x550+300+75")
		self.ActualAction = "FileManager"
		try:
			self.content.destroy()
		except Exception:
			pass
		self.content = Frame(self.mainwindow)
		tosend = '{"msg_id":1283,"token":%s,"param":"\/var\/www\/DCIM"}' %self.token #lets seth initial path in camera
		self.curPwd = self.Comm(tosend)["pwd"]
		tosend = '{"msg_id":1282,"token":%s, "param":" -D -S"}' %self.token
		resp = self.Comm(tosend)
		if len(resp["listing"]) > 0:
			self.MediaDir = resp["listing"][0].keys()[0]
		if self.MediaDir != "":
			tosend = '{"msg_id":1283,"token":%s,"param":"\/var\/www\/DCIM\/%s"}' %(self.token, self.MediaDir) #lets seth final path in camera
			self.curPwd = self.Comm(tosend)["pwd"]
		self.FileCreateList()
		self.FilePrintList()
		self.FileButtonDownload = Button(self.content, text="Download", width=8, command=self.FileDownload)
		self.FileButtonDownload.pack(side=LEFT, padx=5, pady=5)
		if self.ExpertMode != "":
			self.FileButtonCwd = Button(self.content, text="Change folder", width=11, bg="#ffff66", command=self.FileCwd)
			self.FileButtonCwd.pack(side=LEFT, padx=5, pady=5)
		self.FileButtonDelete = Button(self.content, text="DELETE", width=6, bg="#ff6666", command=self.FileDelete)
		self.FileButtonDelete.pack(side=LEFT, padx=5, pady=5)
		self.FileProgress = Label(self.content, width=45, anchor=W, bd=1, relief=SUNKEN, text="Select a file", bg=self.defaultbg)
		self.FileProgress.pack(side=RIGHT, fill=X, padx=10)
		self.content.pack(side=TOP, fill=X)


	
	
root = Tk()
mysys = os.name
if mysys == "nt":
	ICON = zlib.decompress(base64.b64decode('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'))
	_, ICON_PATH = tempfile.mkstemp()
	with open(ICON_PATH, 'wb') as icon_file:
		icon_file.write(ICON)
	
	root.iconbitmap(default=ICON_PATH)


app = App(root)

root.mainloop()

