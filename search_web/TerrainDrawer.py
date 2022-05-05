#!/usr/bin/python
import sys
from PIL import Image,ImageTk,ImageGrab,EpsImagePlugin
import tkinter as tk
sys.path.insert(1, '''C:\Program Files\gs\gs9.56.1\bin''')
EpsImagePlugin.gs_windows_binary =  r'C:\Program Files\gs\gs9.56.1\bin\gswin64c'


def draw_terrain(filename):
	global color_value,draw_width
	app = tk.Tk()
	canvas_size=600
	final_size=2048
	color_value=(255//2,255//2,255//2)
	draw_width=8
	draw_var = tk.StringVar()
	draw_var.set('%d'%draw_width)
	color_var= tk.StringVar()
	color_var.set('%d'%color_value[0])
	filename='map'
	scale_factor=1.26
	
	app.geometry("%dx%d"%(canvas_size,canvas_size+25))
	canvas = tk.Canvas(app, bg='black')
	canvas.config(width=canvas_size, height=canvas_size)
	#image = Image.new('RGBA',(canvas_size,canvas_size),(*color_value,255))
	
	image = Image.open("%s.png"%filename)
	image = image.resize((canvas_size,canvas_size))#, Image.ANTIALIAS)
	tk_image = ImageTk.PhotoImage(image)
	canvas.pack(anchor='nw',fill='both', expand=1)
	canvas.create_image(0,0, image=tk_image, anchor='nw')
	
	def get_x_and_y(event):
		global lasx, lasy
		lasx, lasy = event.x, event.y
	def draw_smth(event):
		global lasx, lasy, color_value,draw_width
		cir_os = int(draw_width/2)
		canvas.create_oval(lasx-cir_os,lasy-cir_os,lasx+cir_os,lasy+cir_os,fill='#%02x%02x%02x'%color_value,outline='#%02x%02x%02x'%color_value)
		#canvas.create_line((lasx, lasy, event.x, event.y), fill='#%02x%02x%02x'%color_value, width=draw_width)
		lasx, lasy = event.x, event.y
	def resize_postscript(psimg,rs):
		w,h = psimg.size
		dif = h-w
		return psimg.crop((0,1,w,h-(3+dif-1))).resize(rs)
	def getColor(event):
		canvas.update()
		canvas.postscript(file="temp.eps", colormode='color')
		pimg = Image.open("temp.eps")
		pimg = resize_postscript(pimg,(canvas_size,canvas_size))
		
		pix = pimg.load()
		try:
			set_color_value(pix[event.x,event.y])
		except: print('(x: %d , y: %d)(w: %d , h: %d)'%(event.x,event.y,*pimg.size),flush=True)
	def getSave(widget):
		def savefile():
			#filename = filedialog.asksaveasfile(mode='w', defaultextension=".jpg")
			
			if not filename:
				return
			widget.update()
			widget.postscript(file="%s.eps"%filename, colormode='color')
			psimg = Image.open("%s.eps"%filename) 
			w,h = psimg.size
			dif = h-w
			psimg = psimg.crop((0,1,w,h-(3+dif-1)))
			psimg = psimg.resize((final_size,final_size))
			psimg.save("%s.png"%filename, 'png')
			"""
			x=app.winfo_rootx()+ widget.winfo_x()
			y=app.winfo_rooty()+ widget.winfo_y()
			x=app.winfo_rootx()#+ int(widget.winfo_x() * (1-(1-scale_factor)))
			y=app.winfo_rooty()#+ int(widget.winfo_y() * (1-(1-scale_factor)))
			x=1+int(app.winfo_rootx() * (1-(1-scale_factor)))# + int(widget.winfo_x() * (1-(1-scale_factor)))
			y=1+int(app.winfo_rooty() * (1-(1-scale_factor)))# + int(widget.winfo_y() * (1-(1-scale_factor)))
			dif_w = (canvas_size - widget.winfo_width() )//2
			dif_h = (canvas_size - widget.winfo_height())//2
			
			x1 = x + int(widget.winfo_width()*scale_factor)
			y1 = y + int(widget.winfo_height()*scale_factor)
			x1 = x + int(canvas_size*scale_factor)-5
			y1 = y + int(canvas_size*scale_factor)-5
			full_image = ImageGrab.grab()
			pix=full_image.load()
			for dx in range(x,x1):
				pix[dx,y] = (255,0,0)
				pix[dx,y1] = (255,0,0)
			for dy in range(y,y1):
				pix[x,dy] = (255,0,0)
				pix[x1,dy] = (255,0,0)
			full_image.show()
			#ImageGrab.grab(0,0,canvas_size,canvas_size).show()
			ImageGrab.grab().crop((x,y,x1,y1)).save(filename)
			"""
			#ImageGrab.grab().crop((x-dif_w,y-dif_h,x1+dif_w,y1+dif_h)).save(filename)
			#image.save(filename)
		return savefile
	def set_color_value(value):
		global color_value
		if isinstance(value,tuple) and len(value) == 3:
			color_value = value
		elif isinstance(value,(int,float)):
			if value > 255: value = 255
			elif value < 0: value = 0
			value = int(value)
			color_value = (value,value,value)
		color_var.set('%d%%'%((color_value[0]/255)*100))	
	def change_color_value(delta):
		global color_value
		set_color_value(color_value[0]+delta)
	def on_mousewheel(event):
		change_color_value((event.delta/5))
	canvas.bind("<Button-1>", get_x_and_y)
	canvas.bind("<B1-Motion>", draw_smth)
	canvas.bind("<MouseWheel>",on_mousewheel)
	canvas.bind("<Button-2>",getColor)
	#canvas.bind("<Enter>",savefile)
	def size_up():
		global draw_width
		draw_width+=1
		draw_var.set('%d'%draw_width)
	def size_down():
		global draw_width
		draw_width-=1
		draw_var.set('%d'%draw_width)
	
	draw_label = tk.Label( app, textvariable=draw_var, relief=tk.RAISED )
	color_label = tk.Label( app, textvariable=color_var, relief=tk.RAISED )
	
	size_up_button = tk.Button(app, text="+", command=size_up)
	size_down_button = tk.Button(app, text="-", command=size_down)
	save_button = tk.Button(app, text="save as", command=getSave(canvas))
	
	
	size_up_button.pack(side=tk.RIGHT,expand=True,fill=tk.BOTH)
	draw_label.pack(side=tk.RIGHT,fill=tk.BOTH)
	color_label.pack(side=tk.RIGHT,fill=tk.BOTH)
	size_down_button.pack(side=tk.RIGHT,expand=True,fill=tk.BOTH)
	save_button.pack(side=tk.LEFT,fill=tk.BOTH)
	
	app.mainloop()
