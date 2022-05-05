#!/usr/bin/python

from math import sqrt
from inspect import getouterframes,currentframe
from traceback import print_exc
from sys import stdout

#############################
#  Auxilery Math Functions  #
#############################
def calcDistance(p1,p2):
	val=0
	for dv1,dv2 in zip(p1,p2):
		val += (dv1-dv2)**2
	return sqrt(val)
def factors(n):
	
	while n > 1:
		for i in range(2, int(n + 1)):
			if n % i == 0:
				n /= i
				yield i
				break

####################################
#  Auxilery Dict Helper functions  #
####################################
def flattenDictionary(lookup,rtn_type=dict):
	def recFlatten(lu,luk):
		if not(isinstance(lu,dict)): return [(tuple(luk),lu)]
		else:
			rtn = []
			for key in lu:
				rtn += recFlatten(lu[key],luk+[key])
			return rtn
	return rtn_type(recFlatten(lookup,[]))
def get_lookup(kargs,lookup):
	current_lookup=lookup
	lvl = 0
	for kid in kargs:
		lvl+=1
		if not(kid in current_lookup): raise 
		current_lookup = current_lookup[kid]
	return current_lookup	
def add_lookup(kargs,v,lookup,**kwargs):
	if 'replace'in kwargs:
		replace = kwargs['replace']
	else: replace = True
	current_lookup=lookup
	lvl = 0
	try:
		for kid in kargs:
			lvl+=1
			if not(kid in current_lookup):
				if lvl < len(kargs): current_lookup[kid] = {}
				else: current_lookup[kid] = v
			elif not(lvl < len(kargs)) and replace:
				current_lookup[kid] = v
			current_lookup = current_lookup[kid] 
	except: 
		try: breakpoint(identifier=kargs,value=v,lvl=lvl)
		except: pass
		try: breakpoint(kid=kid)
		except: pass
		try: breakpoint(lookup=lookup,current_lookup=current_lookup)
		except: pass
		raise
def in_lookup(kargs,v,lookup,**kwargs):
	current_lookup=lookup
	lvl = 0
	for kid in kargs:
		lvl+=1
		if not(kid in current_lookup):
			return False	
		current_lookup = current_lookup[kid]
	if 'exact' in kwargs:
		exact = kwargs['exact']
	else: exact = True
	if 'at_all' in kwargs:
		at_all =  kwargs['at_all']
	else: at_all = False
	
	if at_all: return True
	
		
	if exact:
		return v is current_lookup
	else:
		if isinstance(v,(WebPath,WebNode,tuple)) and isinstance(current_lookup,(WebPath,WebNode,tuple)):
			try:
				if equal_identifiers(current_lookup, v):
					return True
			except: print('eq_id fail')
		return v == current_lookup

############################
#  Custom Debug Functions  #
############################
def breakpoint(**kwargs):
	print("BREAKPOINT")
	for kw in kwargs:
		arg=kwargs[kw]
		if isinstance(arg,(int,float,str)):
			print('\t%s = %s'%(kw,arg))
		elif isinstance(arg,dict):
			print('\t%s = {'%kw)
			for kv in arg.items():
				print('\t\t%s:\t%s,'%kv)
			print('\t}')
		elif isinstance(arg,list):
			print('\t%s = ['%kw)
			for kv in arg:
				print('\t\t%s,'%(kv,))
			print('\t]')	
		else: print('\t%s = %s'%(kw,arg))
def backtrace():
	print("BACKTRACE:")
	i=0
	for frame in getouterframes(currentframe(), 2)[1:]:
		file = frame.filename.split('\\')[-1] 
		print('    %s\t%s:%d\tin %s'%(i,file,frame.lineno,frame.function))
		i+=1		
def command_line(l,condition=True):
	if not(condition): return
	running=True
	while(running):
		inp = input('<cmd>')
		if inp=='q':
			inp = input('Are you sure you want to quit?')
			if inp=='n' or inp == 'no': continue
			running = False
		elif inp == 'bt' or inp == 'backtrace':
			backtrace()
		else:
			try: exec(inp,globals(),l)
			except Exception:
				print("-"*60)
				print_exc(file=stdout)
				print("-"*60)
				print('Invalid command, try again')



#####################
#  Other Functions  #
#####################
