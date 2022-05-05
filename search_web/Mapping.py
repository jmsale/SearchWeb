#!/usr/bin/python
from PIL import Image
from search_web.Auxiliary import *
import os

Image.MAX_IMAGE_PIXELS = None

#######################
#  Mapping Functions  #
#######################

# Color Functions
def intRGB(o_val,min,max=None):
	#p_val = o_val + min
	p_val = o_val - min
	if isinstance(o_val,(float,int)):
		if max != None: n_factor = 0xFFFFFFFF/(max-min)
		else: n_factor = 1
		p_val *= n_factor
		p_val = int(p_val)
	byte_mask = 0xFF
	def readChannel(c,tcs):
		c*=2
		rtn = 0x0
		for t in tcs:
			rtn = rtn<<2
			b1 = t>>c
			b2 = b1&0x3
			rtn = rtn|b2
		return rtn
	#r,g,b,a = 0,0,0,0
	s_val = p_val
	tiers = []
	for i in range(0,4):
		
		v = (s_val>>(8*(3-i)))&byte_mask
		#s_val = s_val >> 8
		tiers += [v]
	r,g,b,a = readChannel(1,tiers),readChannel(2,tiers),readChannel(3,tiers),255-readChannel(0,tiers)
	#r,g,b,a = readChannel(1,tiers),readChannel(3,tiers),readChannel(2,tiers),255-readChannel(0,tiers)
	#r,g,b,a = readChannel(2,tiers),readChannel(3,tiers),readChannel(1,tiers),255-readChannel(0,tiers)
	rgb = r,g,b,a
	#if tiers[0] > 1 or tiers[1] > 1 or tiers[2] > 1 or tiers[3] > 1:print(tiers,flush=True,end='')
	#if r > 0 or b > 0 or g > 0: print("(%d,%d,%d,%d)"%(r,g,b,a),flush=True,end='')
	return r,g,b,a
	
	r = s_val&byte_mask
	s_val = s_val>8
	g = s_val&byte_mask
	s_val = s_val>8
	b = s_val&byte_mask
	s_val = s_val>8
	a = 255 - (s_val&byte_mask)
	s_val = s_val>8
	
	return (r,g,b,a)
def rgbToInt(rgba):
	r,g,b,a = rgba
	a = 255-a
	rgba = [b,g,r,a]
	def readChannel(c,tcs):
		c*=2
		rtn = 0x0
		for t in tcs:
			rtn = rtn<<2
			b1 = t>>c
			b2 = b1&0x3
			rtn = rtn|b2
		return rtn
	val = 0x0
	for i in range(3,-1,-1):
		val = val<<8
		val = val|readChannel(i,rgba)
	return val
	rtn = 0x0
	rtn = rtn<<8
	rtn = rtn|r
	rtn = rtn<<8
	rtn = rtn|g
	rtn = rtn<<8
	rtn = rtn|b
	rtn = rtn<<8
	rtn = rtn|a
	return rtn

# Image Functions
def generateMap(values,**kwargs):
	#print('GENERATE MAP',flush=True)
	# kw_width
	if 'width' in kwargs:
		kw_width = kwargs['width']
		if isinstance(kw_width,int):
			width_range=(0,kw_width)
		elif isinstance(kw_width,(list,tuple)) and len(kw_width)==2:
			if isinstance(kw_width,list):
				width_range = tuple(kw_width)
			else:
				width_range = kw_width
		else: raise Exception("kw_width must be of type <int>/<tuple>/<list>")
	else: width_range = None
	# kw_height
	if 'height' in kwargs:
		kw_height = kwargs['height']
		if isinstance(kw_height,int):
			height_range=(0,kw_height)
		elif isinstance(kw_height,(list,tuple)) and len(kw_height)==2:
			if isinstance(kw_height,list):
				height_range = tuple(kw_height)
			else:
				height_range=kw_height
		else: raise Exception("kw_height must be of type <int>/<tuple>/<list>")
	else: height_range = None
	
	# kw_value_range
	if 'value_range' in kwargs:
		kw_value_range = kwargs['value_range']
		if isinstance(kw_value_range,(list,tuple)) and len(kw_value_range)==2:
			if isinstance(kw_value_range,list):
				value_range=tuple(kw_value_range)
			else:
				value_range=kw_value_range
		else: raise Exception("kw_value_range must be of type <tuple>/<list>")
	else: # kw_min_value , kw_max_value
		#kw_max_value
		if 'max_value' in kwargs:
			kw_max_value = kwargs['max_value']
			if isinstance(kw_max_value,(float,int)):
				#kw_min_value
				if 'min_value' in kwargs:
					kw_min_value = kwargs['min_value']
					if isinstance(kw_min_value,(float,int)):
						value_range = (kw_min_value,kw_max_value)
					else: raise Exception("kw_min_value must be of type <float>/<int>")
				else: 
					value_range = (0,kw_max_value)
			else: raise Exception("kw_max_value must be of type <float>/<int>")
		else: value_range = None
	
	# kw_map_type
	map_type_values={ 'value_map':0, 'heat_map':1}
	if 'map_type' in kwargs:
		kw_map_type = kwargs['map_type']
		if not(isinstance(kw_map_type,(tuple,list))):
			kw_map_type = (kw_map_type,)
		map_type_set = []
		for mt in kw_map_type:
			if isinstance(mt,str):
				if mt in map_type_values:
					map_type_set.append(map_type_values[mt])
				else: raise Exception("kw_map_type string not recognized")
			else: raise Exception("kw_map_type must be of type <str>")
		map_type_set = tuple(map_type_set)
	else: 
		map_type_set = tuple(map_type_values['value_map'])
	
	if 'mark' in kwargs:
		#print('READ_MARK',flush=True)
		base_mark_color=(255,0,0,255)
		kw_mark = kwargs['mark']
		#breakpoint(marks=kw_mark)
		if isinstance(kw_mark,tuple):
			if len(kw_mark) == 2 and isinstance(kw_mark[0], tuple) and len(kw_mark[0]) == 4 and isinstance(kw_mark[1],(list,tuple,set)):
				mark_color=kw_mark[0]
				mark_points=kw_mark[1]
			else:
				mark_color = base_mark_color
				mark_points=kw_mark
		elif isinstance(kw_mark,(list,set)):
			mark_color = base_mark_color
			mark_points = list(kw_mark)
		elif isinstance(kw_mark,dict):
			#mark_color = base_mark_color
			mark_points,mark_color = zip(*flattenDictionary(kw_mark,list))
			if isinstance(mark_color,(list,tuple)):
				if len(mark_color)>0:
					if isinstance(mark_color[0],tuple) and len(mark_color[0]) == 4: pass
					elif isinstance(mark_color[0],(int,float)): mark_color=base_mark_color
					else: raise Exception('Invalid dictionary value for mark')
				else:
					mark_color=base_mark_color
			else: raise Exception('Invalid zip return type for mark_color')
		elif kw_mark == None: pass 
		else: raise Exception('Invalid kw_mark type')
		
		if kw_mark == None: marks={}
		elif isinstance(mark_points,(list,tuple)):
			marks = {}
			if isinstance(mark_color,(tuple)) and len(mark_color)==4 and isinstance(mark_color[0],int):
				mark_color = [mark_color for _ in range(len(mark_points))]
			for point,color in zip(mark_points,mark_color):
				add_lookup(point,color,marks)
		else: raise Exception('Invalid mark_points type')
	else: marks={}
	# kw_value_func
	def base_value_funct(v): return v
	if 'value_func' in kwargs:
		value_func = kwargs['value_func']
	else: value_func = base_value_funct 
	
	#print('START GENERATE',flush=True)
	#min_value = None
	#max_value = None
	##if width_range == None: 
	#width_min = None
	#width_max = None
	##if height_range == None: 
	#height_min = None
	#height_max = None
	if value_range == None or width_range == None or height_range == None:
		#if value_range == None:
		min_value = None
		max_value = None
		#if width_range == None: 
		width_min = None
		width_max = None
		#if height_range == None: 
		height_min = None
		height_max = None
		def updateOn(vx,vy,v):
			if value_range == None and (min_value == None or min_value > v): min_value = v
			if value_range == None and (max_value == None or max_value < v): max_value = v
			
			if width_range == None and (width_min == None or width_min > vx): width_min = vx
			if width_range == None and (width_max == None or width_max < vx): width_max = vx
			
			if height_range == None and (height_min == None or height_min > vy): height_min = vy
			if height_range == None and (height_max == None or height_max < vy): height_max = vy
		
		
		if isinstance(values,dict):
			for kx in values:
				#if width_range == None and (width_min == None or width_min > kx): width_min = kx
				#if width_range == None and (width_max == None or width_max < kx): width_max = kx
				for ky in values[kx]:
					cv = value_func(values[kx][ky])
					if not(isinstance(cv,(int,float))): continue
					if value_range == None and (min_value == None or min_value > cv): min_value = cv
					if value_range == None and (max_value == None or max_value < cv): max_value = cv
					
					if width_range == None and (width_min == None or width_min > kx): width_min = kx
					if width_range == None and (width_max == None or width_max < kx): width_max = kx
					
					if height_range == None and (height_min == None or height_min > ky): height_min = ky
					if height_range == None and (height_max == None or height_max < ky): height_max = ky
		
					#updateOn(kx,ky,cv)
					
		elif isinstance(values,(list,tuple)):
			raise
			if height_range != None and len(values) != height_range[1]-height_range[0]:
				pass
		else:
			raise
		if isinstance(marks,dict):
			for kx in marks:
				for ky in marks[kx]:
					cv = marks[kx][ky]
					if not(isinstance(cv,(tuple))): continue
					#if value_range == None and (min_value == None or min_value > cv): min_value = cv
					#if value_range == None and (max_value == None or max_value < cv): max_value = cv
					
					if width_range == None and (width_min == None or width_min > kx): width_min = kx
					if width_range == None and (width_max == None or width_max < kx): width_max = kx
					
					if height_range == None and (height_min == None or height_min > ky): height_min = ky
					if height_range == None and (height_max == None or height_max < ky): height_max = ky
		try:
			print('Calculated:')
			if value_range == None: value_range = (min_value,max_value); print('\t value_range: %s - %s'%value_range,flush=True)
			if width_range == None: width_range = (width_min,width_max+1); print('\t width_range: %s - %s'%width_range,flush=True)
			if height_range == None: height_range = (height_min,height_max+1); print('\t height_range: %s - %s'%height_range,flush=True)
		except:
			#if value_range == None: 
			#if width_range == None: 
			#if height_range == None:
			print('\nvalue_range: %s: %s'%(value_range,(min_value,max_value)))
			print('width_range: %s: %s'%(width_range,(width_min,width_max)))
			print('height_range: %s: %s'%(height_range,(height_min,height_max)))
			print('values: %s'%values,flush=True)
			raise
			
		
	rtn_maps=[]
	for map_type in map_type_set:
		#print('MAKE MAP')
		def getForImage(x=None,y=None,value=None):
			
			rtn = []
			if x != None: rtn.append(x-width_range[0])
			if y != None: rtn.append(y-height_range[0])
			if value != None:
				
				if isinstance(value,tuple) and len(value)==4 and x !=None and y!=None:
					rtn.append(value)	
				elif map_type == map_type_values['value_map']: rtn.append(intRGB(value_func(value),int(value_range[0]),int(value_range[1])))
				elif map_type == map_type_values['heat_map']:
					heat = (value_func(value) - value_range[0])/(value_range[1] - value_range[0])
					c=int(heat*255)
					rtn.append((c,c,c,255))
			if len(rtn)==1: return rtn[0]
			else: return tuple(item for item in rtn)
		if map_type == map_type_values['value_map'] or map_type == map_type_values['heat_map']:
			#base_map = Image.open('base_height_map.png')
			base_map = Image.new('RGBA',(width_range[1]-width_range[0],height_range[1]-height_range[0]),(0,0,0,0))
			base_map = base_map.resize((width_range[1]-width_range[0],height_range[1]-height_range[0]))
			pix =  base_map.load()
			if value_range[1] == value_range[0]: 
				print('Range not wide enough for value_map')
				return base_map
			if isinstance(values,dict):
				attempt_count=0
				success_count=0
				for kx in values:
					for ky in values[kx]:
						attempt_count += 1
						if not(isinstance(values[kx][ky],(int,float))): continue
						else: success_count+=1
						try: 
							ix,iy,rgba = getForImage(x=kx,y=ky,value=values[kx][ky])
							try: pix[ix,iy] = rgba
							except: print('\nx: %d,\ny: %d,\nrgba: %s,\nw: %s,\nh: %s,\nv: %s\n'%(ix,iy,rgba,width_range,height_range,value_range,)); raise
						except:
							print('failed to get for image @ (%d,%d)'%(kx,ky))
							
						#intRGB(values[kx][ky],int(value_range[0]),int(value_range[1]))
						#getRGB(kx,ky)
				if attempt_count != success_count:
					fail_count=attempt_count-success_count
					print('\n%d / %d (%.2f%%) attempts failed during map generation'%(fail_count,attempt_count,(fail_count/attempt_count)*100))
			#for y in range(0,self.height):
			#	print('writing pixel row %d of %d (%.3f%%)'%(y,self.height,(y/self.height)*100),flush=True,end='\r')
			#	for x in range(0,self.width):
			marked=0
			m=0
			for point,color in flattenDictionary(marks,list):
				m+=1
				try:
					mx,my,rgba = getForImage(*point,color)
					try: pix[mx,my] = rgba; marked+=1
					except: print('\nx: %d,\ny: %d,\nrgba: %s,\nw: %s,\nh: %s,\nv: %s\n'%(mx,my,rgba,width_range,height_range,value_range,)); raise
				except:
					print('failed to get for image @ %s'%(point,))
			if m != marked:
				print('Marked %d/%d points'%(marked,m))
			rtn_maps.append(base_map)
			#pix[x,y] = getRGB(x,y)
			#hm_im.save(fn)
	if len(rtn_maps) == 1:
		return rtn_maps[0]
	elif len(rtn_maps) > 1: 
		return tuple(rtn_maps)
	else: return None
def groupImages(*images):
	best_fit = None
	for root in range(0,len(images)+1):
		sq = root**2
		dif = sq - len(images)
		if dif >= 0:
			if best_fit == None or best_fit[1] > dif:
				best_fit = (root,dif)
	num_edge_images,num_slots_empty=best_fit
	slots = [[None for _ in range(num_edge_images)] for _ in range(num_edge_images)]
	def measureSlots():
		row_measure = [ 0 for _ in range(num_edge_images)]
		col_measure = [ 0 for _ in range(num_edge_images)]
		
		for r in range(len(slots)):
			for c in range(len(slots[r])):
				im = slots[r][c]
				if im != None:
					im_w,im_h = im.size
					row_measure[r] += im_w
					col_measure[c] += im_h
		return row_measure,col_measure
	def availableSlots():
		avail=[]
		for r in range(len(slots)):
			for c in range(len(slots[r])):
				if slots[r][c] == None:
					avail.append((r,c))
		return avail
		
		return row_measure,col_measure
	for image in images:
		rM,cM = measureSlots()
		i_w,i_h = image.size
		try:
			sdif = sorted([ (sr,sc,abs( (rM[sr]+i_w)-(cM[sc]+i_h))) for sr,sc in availableSlots()],key=lambda x: x[2])
			pr,pc,_ = sdif[0]
		except: print(rM,cM);raise
		slots[pr][pc] = image
	widths,heights = measureSlots()
	max_w,max_h = max(widths),max(heights)
	
	curY=0
	curX=0
	max_width=0
	for row in slots:
		max_height = 0
		curX=0
		for image in row:
			if image == None: continue
			iw,ih = image.size
			if ih > max_height: max_height = ih
			curX += iw
		if curX > max_width: max_width=curX
		curY += max_height
	max_height=curY
	print('nm_wxh(%d,%d)'%(max_width,max_height))
	
	nim = Image.new('RGBA',(max_width,max_height),(0,0,0,0))
	curY=0
	i_count = 0
	for row in slots:
		max_height = 0
		curX=0
		for image in row:
			if image == None: continue
			iw,ih = image.size
			try:
				
				nim.paste(image,(curX,curY))
			except:
				print('paste Fail (%d,%d)'%(x,y),flush=True)
				continue
			print('pasted image %d at (%d,%d)'%(i_count,curX,curY))
			i_count+=1
			if ih > max_height: max_height = ih
			curX += iw
		curY += max_height
	return nim
def combineImages(images,sw,sh):
	max_x = len(images)
	max_y = 0
	for col in images:
		if len(col) >  max_y: max_y = len(col)
	nim = Image.new('RGBA',(sw*max_x,sh*max_y),(0,0,0,0))
	for x in range(0,max_x):
		for y in range(0,max_y):
			if images[x][y] == None: continue
			try:
				nim.paste(images[x][y],(x*sw,y*sh))
			except:
				print('paste Fail (%d,%d)'%(x,y),flush=True)
	return nim


# 2D array manipulation function
def loadLocation(fn,value_range):
	h_range = value_range[1]-value_range[0]
	
	limg = Image.open(fn)
	w,h = limg.size
	pix = limg.load()
	
	def getHeightFor(*args):
		if len(args)==4: r,g,b,a = args
		elif len(args)==3: r,g,b = args
		else: raise
		
		return value_range[0] + ((r/255)*h_range)
	matrix = []
	for y in range(h):
		row = []
		for x in range(w):
			row.append(getHeightFor(*pix[x,y]))
		matrix.append(row)
	return matrix


def expand(matrix,mul=2):
	return [  [  matrix[r//mul][c//mul] for c in range(len(matrix[r//mul])*mul)] for r in range(len(matrix)*mul)]
def contract(matrix,div=2):
	def blockAvg(x,y):
		sum = 0
		for i in range(div):
			for j in range(div):
				sum += matrix[y+i][x+j]
		return sum/ (div**2)
	return [ [ blockAvg(c,r) for c in range(0,len(matrix[r]),div)]for r in range(0,len(matrix),div)]
	
def smooth(matrix,hp=1,vp=1,**kwargs):
	step = 0
	if 'update_interval' in kwargs:
		kw_update_interval = kwargs['update_interval']
		if isinstance(kw_update_interval,int):
			update_interval = kw_update_interval
		elif isinstance(kw_update_interval,float):
			update_interval = int(kw_update_interval * max(hp,vp))
	else: update_interval = None
	while(hp > step or vp > step):
		if hp > step:
			last = None
			for r in range(len(matrix)):
				for c in range(len(matrix[r])):
					
					if last != None and last[2] != matrix[r][c]:	
						matrix[r][c] +=  (last[2]-matrix[r][c])/2
					
					last = (r,c,matrix[r][c])

		if vp > step:			
			last = None
			for c in range(len(matrix)):
				for r in range(len(matrix[c])):
					
					if last != None and last[2] != matrix[r][c]:	
						matrix[r][c] +=  (last[2]-matrix[r][c])/2
					
					last = (r,c,matrix[r][c])
		if update_interval != None and step % update_interval == 0: print("Smoothed[%d / %d]"%(step,max(hp,vp)),flush=True,end='\n')
		step += 1
	return matrix
def smoothExpansion(matrix,mul=2,**kwargs):
	if 'hv_ratio' in kwargs:
		kw_hv_ratio = kwargs['hv_ratio']
		if isinstance(kw_hv_ratio,(float,int)):
			hv_ratio = (kw_hv_ratio,kw_hv_ratio)
			if kw_hv_ratio > 1: pass
			elif kw_hv_ratio < 1: pass
			else: pass
		elif isinstance(kw_hv_ratio,(tuple,list)) and len(kw_hv_ratio) == 2:
			hv_ratio = tuple(kw_hv_ratio)
		else: raise
	else: hv_ratio = (1,1)
	
	if 'hv_min' in kwargs:
		kw_hv_min = kwargs['hv_min']
		if isinstance(kw_hv_min,int):
			hv_min = (kw_hv_min,kw_hv_min)
			
		elif isinstance(kw_hv_min,(tuple,list)) and len(kw_hv_min) == 2:
			hv_min = tuple(kw_hv_min)
		else: raise
	else: hv_min = (1,1)
	
	step = 0
	if 'update_interval' in kwargs:
		kw_update_interval = kwargs['update_interval']
		if isinstance(kw_update_interval,int):
			update_interval = kw_update_interval
		elif isinstance(kw_update_interval,float):
			update_interval = int(kw_update_interval * max(hp,vp))
	else: update_interval = None
	
	total_expansion_amount=1
	for f in factors(mul):
		matrix = expand(matrix,f)
		hp = max(int(hv_ratio[0]*f),hv_min[0])
		vp = max(int(hv_ratio[1]*f),hv_min[1])
		matrix = smooth(matrix,hp,vp)
		total_expansion_amount*=f
		if update_interval != None and step % update_interval == 0: 
			print("Exansion to[%d / %d]"%(total_expansion_amount,mul),flush=True,end='\n')
		step += 1
	return matrix




#################
#  Height Maps  #
#################
class HeightMap:
	def __init__(self,fn,min,max,scale=1.0):
		if isinstance(fn,list):
			mesh = fn
			height = len(mesh)
			width = len(mesh[0])
		else:
			im = Image.open(fn)
			pix = im.load()
			
			width,height = im.size
			
			mesh = []
			for y in range(0,height):
				row = []
				for x in range(0,width):
					r,g,b,a = pix[x,y]
					if r == 0: ht = min
					elif r == 255: ht = max
					else: ht = min + (r/255 * (max - min))
					row += [ht]
				mesh += [row]
				
		#print('height map made (%d,%d)'%(width,height),flush=True)
		
		self.mesh = mesh
		self.width,self.height = width,height
		self.min,self.max = min,max
		self.scale = scale
	def getHeight(self,x,y):
		if isinstance(x,int) and isinstance(y,int):
			if (y < len(self.mesh) and y >= 0) and (x < len(self.mesh[y]) and x >= 0): return self.mesh[y][x]
			#else: raise
			else: print(x,y,flush=True); print(len(self.mesh),flush=True);raise
		elif isinstance(x,float) or isinstance(y,float):
			raise
	def Max(self):
		max = 0
		mx = 0
		my = 0
		for y in range(0,self.height):
			for x in range(0,self.width):
				ht = self.mesh[y][x]
				if ht > max or ht == self.max:
					#print('new max: %.5f (%d,%d)'%(ht,x,y),flush=True)
					max = ht
					mx = x
					my = y
		print('%f Max Found at (%d,%d)'%(max,mx,my),flush=True)
		return max
	def testHeightMap(self,start,end,step=1,x=None,y=None):
		print('Test (%d,%d)(%d,%d)'%(len(self.mesh),len(self.mesh[0]),self.min,self.max),flush=True)
		for v in range(start,end,step):
			if not(y == None): print('\t(%d,%d): %.5f'%(v,y,self.getHeight(v,y)),flush=True)
			elif not(x == None): print('\t(%d,%d): %.5f'%(x,v,self.getHeight(x,v)),flush=True)

	def savePNG(self,fn,raw=False):
		def getRGB(x,y):
			ht = self.mesh[y][x]
			if raw: return intRGB(ht,int(self.min),int(self.max))
			
			wl = 0
			
			r,g,b,a = (0,0,0,255)
			
			if ht > wl:
				g = min(255,int(255*( ((self.max + wl) - ht) / (wl + self.max) )))
			elif ht < wl:
				b = min(255,int(255*(((self.min-wl) - ht) / (self.min-wl))))
			#else: r = 255
			return r,g,b,a
			
		base_hm = Image.open('base_height_map.png')
		hm_im = base_hm.resize((self.width,self.height))
		pix =  hm_im.load()
		
		for y in range(0,self.height):
			print('writing pixel row %d of %d (%.3f%%)'%(y,self.height,(y/self.height)*100),flush=True,end='\r')
			for x in range(0,self.width):
				pix[x,y] = getRGB(x,y)
		hm_im.save(fn)
	#def __repr__(self):
	#	return str(self)
	#	rtn = ''
	#	for x in range(0,len(self.mesh)):
	#		rtn += '%s\n'%self.mesh[x]
	#	return rtn


class DynamicHeightMap:
	
	def __init__(self,fn,min,max,sub_folder=None,split_size=None):
		self.base_fn = fn
		self.dynamic = sub_folder != None
		
		if self.dynamic:
			self.sub_folder = sub_folder
			self.split_width = split_size[0]
			self.split_height = split_size[1]
			sx,sy = 0,0
			while(True): #x
				if not(os.path.exists('%s\/%d_%d_%d_%d_%s'%(self.sub_folder,sx,sy,self.split_width,self.split_height,self.base_fn))):
					break;
				sx += self.split_width
			print('width: %d'%sx)
			self.full_width = sx
			
			sx,sy = 0,0
			while(True): #y
				if not(os.path.exists('%s\/%d_%d_%d_%d_%s'%(self.sub_folder,sx,sy,self.split_width,self.split_height,self.base_fn))):
					break;
				sy += self.split_height
			print('height: %d'%sy)
			self.full_height = sy
				
			self.map_usage={}
		self.min = min
		self.max = max
		
		self.hm_lookup = {} 	
	def scaleHeight(self,i):
		return ( i /(0xFFFFFFFF/(self.max - self.min))) + self.min
	def getImageFor(self,x,y):
		if self.dynamic:
			sx = int(x/self.split_width)*self.split_width
			sy = int(y/self.split_height)*self.split_height
			im = Image.open('%s\/%d_%d_%d_%d_%s'%(self.sub_folder,sx,sy,self.split_width,self.split_height,self.base_fn))
			#im.show()
			#time.sleep(2)
			return im
		else:
			return Image.open(self.base_fn)
	def getMarkedMap(self,x=None,y=None,ms=1,c=(255,0,0,255),heat_map=None):
		if isinstance(x,tuple): x = list(x)
		if isinstance(y,tuple): y = list(y)
		#print('\nx',x,'\ny',y,'\nms',ms,'\nc',c,'\nheat_map',heat_map)
		heat_max = None
		heat_min = None
		if heat_map != None and isinstance(heat_map,dict) and isinstance(c,tuple) and len(c) == 2:
			x=[]
			y=[]
			for hx in heat_map:
				for hy in heat_map[hx]:
					heat = heat_map[hx][hy]
					if heat_min == None or heat_min > heat: heat_min = heat
					if heat_max == None or heat_max < heat: heat_max = heat
					x += [hx]
					y += [hy]
		if heat_max != None and heat_min == heat_max:heat_min=0 
		def heatRGB(h):
			if heat_min == None or heat_max == None: raise
			hp = (h-heat_min)/(heat_max-heat_min)
			def cHeat(n,c_min,c_max):
				return int(int(hp*(c_max[n] - c_min[n]))+c_min[n])
				#return (int(hp*abs(c_max[n] - c_min[n]))+min(c_min[n],c_max[n]))
				#if hp == 0: return c_min[n]
				#else: return int(hp*c_max[n])
				
			return (cHeat(0,c[0],c[1]),cHeat(1,c[0],c[1]),cHeat(2,c[0],c[1]),cHeat(3,c[0],c[1]))
		
		if not(isinstance(x,list)): lx = [x]
		else: lx = x
		if not(isinstance(y,list)): ly = [y]
		else: ly = y
		if not(len(lx) == len(ly)): raise
		im,x_min,x_max,y_min,y_max = self.getMapImage(dim=True)
		#print(x_min,x_max,y_min,y_max)
		pix = im.load()
		
		for i in range(0,len(lx)):
			
			x,y = lx[i],ly[i]
						
			#print('try (%d,%d)'%(x,y))
			sx = int(x - x_min)
			sy = int(y - y_min)
			if heat_max != None: pix[sx,sy] = heatRGB(heat_map[x][y]); continue
			for mx in range(sx,(sx) + ms):
				#print('try %d'%mx)
			
				for my in range(sy,(sy) + ms):
					#print('\ttry (%d,%d)'%(mx,my))
					if mx >= 0 and mx < ((x_max-x_min)+self.split_width) and my >= 0 and my < ((y_max - y_min)+self.split_height):
						#print('try %d'%my)
						pix[mx,my] = c
		return im
		
		im = self.getImageFor(x,y)
		pix = im.load()
		sx = int(x/self.split_width)*self.split_width
		sy = int(y/self.split_height)*self.split_height
		for mx in range(x-sx,(x-sx) + ms):
			for my in range(y-sy,(y-sy) + ms):
				if mx >= 0 and mx < self.split_width and my >= 0 and my < self.split_height:
					pix[mx,my] = c
		return im
	def getMapImage(self,dim=False):
		x_min = None
		x_max = None
		y_min = None
		y_max = None
		for x in self.hm_lookup:
			if x_min == None or x_min > x: x_min = x
			if x_max == None or x_max < x: x_max = x
			
			for y in self.hm_lookup[x]:
				if y_min == None or y_min > y: y_min = y
				if y_max == None or y_max < y: y_max = y
		images = []
		for x in range(x_min,x_max+self.split_width,self.split_width):
			col = []
			for y in range(y_min,y_max+self.split_height,self.split_height):
				try:
					self.hm_lookup[x][y]
				except:
					col += [None]
				else:
					col += [self.getImageFor(x,y)]
			images += [col]
		if dim: return combineImages(images,self.split_width,self.split_height),x_min,x_max,y_min,y_max
		else: return combineImages(images,self.split_width,self.split_height)
	def deleteHeightMap(self,factor):
		buffer = sorted(flattenDictionary(self.map_usage,list),key=lambda x: x[1],reverse=False)
		
		for i in range(len(buffer)//factor):
			identifier,value = buffer[i]
			sx,sy = identifier
			del self.hm_lookup[sx][sy]
		print('deleted %d height_maps'%(len(buffer)//factor)) 
		
		self.map_usage = {}
	def clear_unused(self,limit=0):
		buffer = sorted(flattenDictionary(self.map_usage,list),key=lambda x: x[1],reverse=False)
		deleted=0
		for identifier,value in buffer:
			sx,sy = identifier
			if value <= limit:
				del self.hm_lookup[sx][sy]
				del self.map_usage[sx][sy]
				deleted+=1
			else: self.map_usage[sx][sy] = 0
		print('deleted %d/%d height_maps'%(deleted,len(buffer))) 
			
	def record_usage(self,sx,sy):
		if not(sx in self.map_usage): self.map_usage[sx] = {}
		
		if not(sy in self.map_usage[sx]): self.map_usage[sx][sy] = 1
		else: self.map_usage[sx][sy] += 1
		
	def getHeightMap(self,x,y,split=False):
		def makeHM():
			im = self.getImageFor(x,y)
			pix = im.load()
			mesh = [[self.scaleHeight(rgbToInt(pix[x,y])) for x in range(0,self.split_width)] for y in range(0,self.split_height)]
			hm = HeightMap(mesh,self.min,self.max,1.0)
			return hm
		
		if split:
			sx = int(x/self.split_width)*self.split_width
			sy = int(y/self.split_height)*self.split_height
		else:
			sx = x
			sy = y
		if sx in self.hm_lookup:
			for_sx_hm_lookup = self.hm_lookup[sx]
			if sy in for_sx_hm_lookup:
				return for_sx_hm_lookup[sy]
			else:
				for_sx_hm_lookup[sy] = makeHM()
		else:
			self.hm_lookup[sx] = {sy:makeHM()}
		return self.hm_lookup[sx][sy]	
	def getHeight(self,x,y):
		if not(self.inRange(x,y)):
			x,y = self.getInRange(x,y)
		sx = int(x/self.split_width)*self.split_width
		sy = int(y/self.split_height)*self.split_height
		self.record_usage(sx,sy)
		return self.getHeightMap(sx,sy).getHeight(x-sx,y-sy)
	
	def inRange(self,x,y):
		return x >= 0 and x < self.full_width and self.validRange(x,y)
	def wrapInRange(self,x,y):
		x %= self.full_width
		y %= self.full_height
		return x,y
	
	def validRange(self,x,y):
		return y >= 0 and y < self.full_height
	def getInRange(self,x,y):
		if self.validRange(x,y):
			x %= self.full_width
			return x,y
		else: raise
	def isEdge(self,x,y,require_width=False,require_height=False):
		w_e = (x==0 or x==self.full_width-1)
		h_e = (y==0 or y==self.full_height-1)
		if not(require_width) and not(require_height):
			return w_e or h_e
		elif require_width and not(require_height):
			return w_e
		elif require_height and not(require_width):
			return h_e
		elif require_width and require_height:
			return w_e and h_e
	def pointAdjacent(self,x1,y1,x2,y2):
		w_a = ((x1 == x2+1 or x1 == x2-1) and y1 == y2)
		h_a = ((y1 == y2+1 or y1 == y2-1) and x1 == x2)
		#if self.isEdge(x1,y1,require_height=True) and self.isEdge(x2,y2,require_height=True):
		if x1 != x2 and y1 == y2 and self.isEdge(x1,y1,require_width=True) and self.isEdge(x2,y2,require_width=True):	
			return True
		else:
			return w_a or h_a
		#if self.isEdge(x1,y1) or self.isEdge(x2,y2):
		#	if self.isEdge(x1,y1,require_width=True) or self.isEdge(x2,y2,require_width=True):
		#		if self.isEdge(x1,y1,require_width=True) and :			
