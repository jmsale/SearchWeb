#!/usr/bin/python

from copy import copy,deepcopy
from search_web.Auxiliary import *
from search_web.Mapping import generateMap,groupImages
import pickle

def get_node(item):
	if isinstance(item,WebNode):
		return item
	elif isinstance(item,tuple) and len(item)==2 and isinstance(item[1],WebNode):
		return item[1]
	elif isinstance(item,WebPath)and isinstance(item.node,WebNode):
		return item.node 
def get_all_nodes(grouping):
	rtn = []
	if isinstance(grouping, Region):
		if grouping.loaded:
			temp = flattenDictionary(grouping.lookup,list)
			for _,node in temp:
				rtn.append(node)
		else:
			if grouping.unloaded_state == None and grouping.lookup != None:
				temp = flattenDictionary(grouping.lookup,list)
				for _,node in temp:
					rtn.append(node)
			else:
				temp = flattenDictionary(grouping.unloaded_state['known_paths'],list)
				for pid,path in temp:
					try: rtn.append(get_node(path))
					except: print('get_all_nodes failed get WebPath WebNode')
	elif isinstance(grouping,dict):
		try:
			temp = flattenDictionary(grouping.lookup,list)
			for _,node in temp:
				rtn.append(node)
		except: print('get_all_nodes failed get dict WebNode')
	elif isinstance(grouping,list):
		for _,node in grouping:
			rtn.append(node)
	else: print('get_all_nodes failed to recognize input grouping')
	return rtn
def all_region(loaded):
	data={}
	marks={}
	def add_level(group,level,lookup,base=1):
		for node in group:
			if not(in_lookup(node.identifier, base, lookup,at_all=True)):
				add_lookup(node.identifier, base, lookup, replace=False)
			
			if isinstance(level,(int,float)):
				val = get_lookup(node.identifier,lookup)
				val*=level
			elif isinstance(level,tuple):
				val = level
			else:
				val = level(node)
			add_lookup(node.identifier,val,lookup)
	for region in loaded:
		R = loaded[region]
		nodes = get_all_nodes(R)
		if R.use_lookup(): add_level(nodes, level=lambda x:x.current_value, lookup=data)
		else: add_level(nodes,(255,0,255,255),marks)
	if len(marks) == 0: marks=None
	groupImages(
		generateMap(data, map_type='heat_map',mark=marks),
		generateMap(data, map_type='value_map',mark=marks),
	).show()	
		

#######################
#  SearchWeb Classes  #
#######################
class SearchQueue:
	def __init__(queue):
		queue.head = None
		queue.tail = None
		queue.length = 0
		queue.items = {}
	def __len__(queue):
		if queue.length != len(queue.items): raise
		return queue.length
	def __contains__(queue,item):
		return item in queue.items
	def remove(queue,item):
		if not(item in queue.items): raise
		qnode = queue.items.pop(item)
		if qnode == queue.head:
			queue.head = qnode.next
		if qnode == queue.tail:
			queue.tail = qnode.prev
		qnode.remove()
		queue.length -= 1
	
	def enqueue(queue,*args):
		for item in args:
			qnode = queue.QueueNode(item)
			
			if queue.tail == None:
				queue.tail = qnode
				queue.head = qnode
			else:
				queue.tail.add(qnode)
				queue.tail = qnode
			queue.length += 1
			if item in queue.items: raise
			queue.items[item] = qnode
	def dequeue(queue):
		if queue.head == None: raise
		qnode = queue.head
		queue.remove(qnode.data)
		return qnode.data
	def __iter__(queue):
		rtn = []
		qnode=queue.head
		while(qnode!=None):
			rtn.append(qnode)
			qnode=qnode.next
		return rtn.__iter__()
	def __repr__(queue):	
		rtn = '['
		qnode=queue.head
		while(qnode != None):
			rtn+=' %s,'%qnode
			qnode=qnode.next
		rtn+=']'
		return rtn
	class QueueNode:
		def __init__(qnode,data):
			qnode.data = data
			qnode.prev = None
			qnode.next = None
		def add(qnode,new_node,after=True):
			if after:
				new_node.prev = qnode
				if qnode.next != None:
					new_node.next = qnode.next
					qnode.next.prev = new_node
				else:
					new_node.next = None
				qnode.next = new_node
			else: raise
		def remove(qnode):
			if qnode.prev != None:
				qnode.prev.next = qnode.next
			if qnode.next != None:
				qnode.next.prev = qnode.prev
			qnode.prev=None
			qnode.next=None
			return qnode
		def __repr__(qnode):	
			return '%s'%qnode.data
class Region:
	def __init__(region,region_num,loaded=True):
		region_num=region_num
		region.lookup={}
		region.loaded = loaded
		if region.loaded:
			region.unloaded_state = None
		else: region.unloaded_state = {}
	def __len__(region): return len(region.lookup)
	def __contains__(region,b): return b in region.lookup
	def __delitem__(region,b): del region.lookup[b]
	def __getitem__(region,b): return region.lookup[b]
	def __setitem__(region,b,c): region.lookup[b] = c
	def __iter__(region): return region.lookup.__iter__()
	def __next__(region): return region.lookup.__next__()
	def get(region,*args): return region.lookup.get(*args)
	def items(region): return region.lookup.items()
	def keys(region): return region.lookup.keys()
	def pop(region,*args): return region.lookup.pop(*args)
	def popitem(region): return region.lookup.popitem()
	def setdefault(region,*args): return region.lookup.setdefault(*args)
	def update(region, *args): return region.lookup.update(*args)
	def values(region): return region.lookup.values()
		
	def use_lookup(region):
		if region.loaded: return True
		elif region.lookup == None: return False
		return True
	def __getstate__(region):
		if region.loaded: region.loaded=False
		else: raise Exception("Can not get state of unloaded Region")
		unloaded_state={
			'known_paths':{}
		}
		nodes_total = 0
		remaining_nodes=flattenDictionary(region.lookup,list)
		
		for identifier,node in remaining_nodes:
			nodes_total+=1
			
			if node.current_path != None:
				for parent,child in node.current_path.regionAdj(allow_None=True,lookup=region.lookup):
					if parent != None and not(parent.pid in unloaded_state['known_paths']): unloaded_state['known_paths'][parent.pid] = parent
					if child != None and not(child.pid in unloaded_state['known_paths']): unloaded_state['known_paths'][child.pid] = child
				if hasattr(node.current_path,'parent'):
					if node.current_path.parent == None: pass
					elif not(isinstance(node.current_path.parent,WebPath)): raise Exception('Invalid type for WebNodes current_path parent')
					else:	
						node.current_path.parent = node.current_path.parent.pid
				if hasattr(node.current_path,'sub_paths'):
					if node.current_path.sub_paths == None: pass
					elif not(isinstance(node.current_path.sub_paths,(list,set,tuple))): raise Exception('Invalid type for WebNodes current_path sub_paths')
					else:
						rset=set()
						for sp in node.current_path.sub_paths:
							rset.add(sp.pid)
						node.current_path.sub_paths=rset
		rtn_dict = copy(region.__dict__)
		region.unloaded_state = unloaded_state
		region.lookup = None
		return rtn_dict
		
	def __setstate__(region,d):
		region.__dict__ = d
		if region.loaded: raise Exception("Can not set state of loaded Region")
	def __call__(region,reloaded_region):
		if region.loaded: raise Exception("Can not perform a reload call on a loaded region")
		elif reloaded_region.loaded: raise Exception("Can not perform a reload call using a loaded region")
		
		remaining_nodes = flattenDictionary(reloaded_region.lookup,list)
		i=0
		last_size=None
		missing_pids = []
		saved_paths = copy(region.unloaded_state['known_paths'])
		try:
			
			for identifier,node in remaining_nodes:
				if node.getCurrentPath(allow_All=True) == None: continue
				elif not(isinstance(node.current_path, WebPath)): raise Exception('Invalid type for reloaded WebNodes current_path')
				
				if not(node.current_path.pid in region.unloaded_state['known_paths']):
					region.unloaded_state['known_paths'][node.current_path.pid] = node.current_path
				else: 
					node.setCurrentPath(region.unloaded_state['known_paths'][node.current_path.pid],allow_kill=False)
					node.current_path.node = node
			for pid in saved_paths:
				saved_p = saved_paths[pid]
				#if saved_p.web.region(saved_p.node.identifier) == region.region_num:
				saved_p.replace_pids(region.unloaded_state['known_paths'],True)
			for identifier,node in remaining_nodes:
				if node.getCurrentPath(allow_All=True) == None: continue
				elif not(isinstance(node.current_path,WebPath)): raise Exception('Invalid type for reloaded WebNodes current_path')
				
				#Current Path
				if not(node.current_path.pid in region.unloaded_state['known_paths']):
					raise Exception('WebPath pid missing from known_paths')				
				#Parent
				parent_complete=True
				if hasattr(node.current_path,'parent'):
					parent_complete = False
					if isinstance(node.current_path.parent,int):
						if node.current_path.parent in region.unloaded_state['known_paths']:
							node.current_path.parent = region.unloaded_state['known_paths'][node.current_path.parent] 
							parent_complete=True
						else: raise Exception('WebPath parent pid missing from known_paths')
					elif node.current_path.parent == None or isinstance(node.current_path.parent,WebPath): 
						parent_complete=True
					else: raise Exception('WebPath parent of invalid type')
				#Sub_paths
				sub_paths_complete=True
				if hasattr(node.current_path,'sub_paths'):
					if node.current_path.sub_paths == None: pass
					elif isinstance(node.current_path.sub_paths,(list,tuple,set)):
						rset=set()
						for sp in node.current_path.sub_paths:
							if isinstance(sp,WebPath): pass
							elif isinstance(sp,int):
								if sp in region.unloaded_state['known_paths']:
									sp = region.unloaded_state['known_paths'][sp]
								else: 
									sub_paths_complete = False
									raise Exception('WebPath sub_path pid missing from known_paths')
							else: raise Exception('WebPath sub_path of invalid type')
							rset.add(sp)
						node.current_path.sub_paths=rset
					else: raise Exception('WebPath sub_paths of invalid type')
				if not(parent_complete and sub_paths_complete): 
					raise Exception('WebPath parent or sub_path was not completed on rebuild')
		except:
			raise
		region.lookup = reloaded_region.lookup
		region.loaded=True
		region.unloaded_state = None
	def unloadedLookup(region,*args):
		if region.loaded: raise
		for k in region.unloaded_state['known_paths']:
			matched=True
			for kid,klu in zip(region.unloaded_state['known_paths'][k].node.identifier, args):
				if kid != klu: 
					matched = False
					break
			if matched:
				return region.unloaded_state['known_paths'][k].node
		return None
class WebNode:
	def __init__(node,*args,**kwargs):
		node.identifier = args
		node.__setcurrentpath(None)
		if 'web' in kwargs:
			node.web = kwargs['web']
		if 'init_value' in kwargs:
			node.current_value = kwargs['init_value']
		elif 'init_value_func' in kwargs:
			node.current_value = kwargs['init_value_func'](*node.identifier)
		else: node.current_value = None
	def real(node):
		return node.web.getNode(*node.identifier)
	def evaluate(node,new_value,overwrite=False):
		if (node.current_value == None) or node.web.eval_func(node.current_value,new_value):
			if overwrite: 
				node.current_value = new_value
			return True
		return False
	def stop(node):
		if node.web.stop_func != None: 
			return node.web.stop_func(*node.identifier)
		else: return False
	def value(node):
		return node.web.val_func(*node.identifier)
	def transition(node,other):
		return node.web.transition_func(*node.identifier,*other.identifier)
	def adjacent(node):
		try:
			rtn_adj = []
			for adj_id in node.web.adj_func(*node.identifier) :
				adj_node = node.web.getNode(*adj_id)

				if adj_node.stop(): continue
				if adj_node.evaluate(node.current_value + node.transition(adj_node), overwrite=True):
					rtn_adj.append(adj_node)
			return tuple(rtn_adj)
		except: print(node.identifier);raise
	def search(node,allow_stop=True):
		node = node.real()
		if node.web.buffer_interval != None:
			if node.web.buffer_store != None:
				node.web.buffer_store(node.web.buffer,locals())
			node.web.buffer.add((node.identifier,node.current_value))
		
		#Gets search function pointers for adjacent nodes
		if allow_stop and node.stop(): rtn = tuple()
		else: rtn = node.getSearchAdjacent()
		
		
		if not(isinstance(node.current_path,WebPath)): raise Exception(' search() called on WebNode without WebPath as current_path')
		
		node.current_path.end()
		#else: 
		#	node.web.endAt(*node.identifier)
		#	raise Exception(' search() called on WebNode without WebPath as current_path')
		return rtn
	def search_noStop(node):
		node = node.real()
		return node.search(False)
	def getSearch(node,allow_stop=True):
		node.web.startAt(*node.identifier)
		if allow_stop:
			return node.search
		else: return node.search_noStop
	def getSearchAdjacent(node):
		return tuple(node.web.WebPath.getSubPathFrom(node,adj_node) for adj_node in node.adjacent())
	def __setcurrentpath(node,path):
		node.current_path = path
	def __getcurrentpath(node):
		return node.current_path
	def getCurrentPath(node,**kwargs):
		#Key Word Arg for disabling all get safe features 
		if 'allow_All' in kwargs: 
			allow_All = kwargs['allow_All']
		else: allow_All = False
		#Key Word Arg for disabling disallow_None get safe feature 
		if 'allow_None' in kwargs:
			allow_None = kwargs['allow_None']
		else: allow_None = allow_All
		#Key Word Arg for disabling disallow_disabled get safe feature 
		if 'allow_disabled' in kwargs:
			allow_disabled = kwargs['allow_disabled']
		else: allow_disabled = allow_All
		
		if node.__getcurrentpath() == None:
			if allow_None: return node.current_path
			else: raise Exception('WebNode getCurrentPath(_) can not return None current_path without allow_None feature enabled')
		elif isinstance(node.current_path,WebPath):
			if node.current_path.isDisabled():
				if allow_disabled: return node.current_path
				else: raise Exception('WebNode getCurrentPath(_) can not return disabled current_path without allow_disabled feature enabled')
			else: return node.current_path
		elif allow_All: return node.current_path
		else: raise Exception('Invalid type for current_path in WebNode')
		
	def setCurrentPath(node,path,**kwargs):
		#Key Word Arg for disabling all set safe features 
		if 'allow_All' in kwargs: 
			allow_All = kwargs['allow_All']
		else: allow_All = False
		#Key Word Arg for disabling disallow_None set safe feature 
		if 'allow_None' in kwargs:
			allow_None = kwargs['allow_None']
		else: allow_None = allow_All
		#Key Word Arg for disabling disallow_int set safe feature 
		if 'allow_int' in kwargs:
			allow_int = kwargs['allow_int']
		else: allow_int = allow_All
		
		#Key Word Arg for disabling allow_kill set feature 
		if 'allow_kill' in kwargs:
			allow_kill = kwargs['allow_kill']
		else: allow_kill = True
		
		#Kills Current Path if enabled
		if node.current_path == None: pass
		elif isinstance(node.current_path,int): pass
		elif isinstance(node.current_path,WebPath):
			if node.current_path.isEnabled() and allow_kill:
				node.current_path.killPath()
		
		#Sets current_path based on set safe enabled features
		if path == None:
			if allow_None: node.__setcurrentpath(path)
			else: raise Exception('WebNode setCurrentPath(_) can not set current_path to None without allow_None feature enabled')
		elif isinstance(path,(WebPath,int)):
			if isinstance(path,int):
				if allow_int: node.__setcurrentpath(path)
				else: raise Exception('WebNode setCurrentPath(_) can not set current_path to int without allow_int feature enabled')
			else: node.__setcurrentpath(path)
		elif allow_All: node.__setcurrentpath(path)
		else: raise Exception('Invalid type for current_path in WebNode')
		return
		#node = node.real()
		if node.current_path != None: 
			kills = node.current_path.killPath()
		node.__setcurrentpath(path)
	def inPath(node):
		
		if node.__getcurrentpath() == None: return False
		elif isinstance(node.current_path,WebPath):
			return node.current_path.isEnabled()
		else: raise Exception('WebNodes current_path is of invlaid type')
	def disablePath(node,path):
		if node.current_path != path: raise
		node.__setcurrentpath(None)
	def isLoaded(node):
		if not(isinstance(node.web,SearchWeb)): return False
		elif node.__getcurrentpath() == None: return True
		elif not(isinstance(node.current_path,WebPath)): raise Exception('Invalid type for WebNode current_path')
		
		return node.current_path.isLoaded()
	def regionAdj(node,**kwargs):
		#Get region value for source WebNode
		origin_region = node.web.region(*node.identifier)
		
		rtn=[]
		for adj_identifier in node.web.adj_func(*node.identifier):
			
			#Gets region value for adj_identifier
			adj_region = node.web.region(*adj_identifier)
			#Skips adj_identifier if in same region
			if origin_region == adj_region: continue
			
			#Gets adj_node using adj_identifier
			adj_node = node.web.getNode(*adj_identifier,allow_unloaded=True,**kwargs)
			if adj_node == None: continue
			elif isinstance(adj_node,WebNode):
				#if not(adj_node.isLoaded()): raise Exception('adj_node returned unloaded')
				rtn.append(adj_node)
			else: raise Exception('Invalid type for adj_node')
		return tuple(rtn)
	def __getstate__(node):
		if isinstance(node.current_path,WebPath):
			if node.current_path.search_func != None: raise Exception('Can not unload while search_func in SearchQueue')
			if hasattr(node.current_path,'sub_paths'):
				if isinstance(node.current_path.sub_paths,(list,tuple,set)):
					rset=set()
					for sp in node.current_path.sub_paths:
						if isinstance(sp,int): rset.add(sp)
						if isinstance(sp,WebPath):
							rset.add(sp.pid)
							print('The state of Node %s was not handled correctly'%node)
							raise Exception("The state of Node was not handled correctly on subpath")
					node.current_path.sub_paths=rset
			if hasattr(node.current_path,'parent'):
				if isinstance(node.current_path.parent,int): pass
				if isinstance(node.current_path.parent,WebPath):
					node.current_path.parent = node.current_path.parent.pid
					print('The state of Node %s was not handled correctly'%node)
					raise Exception('The state of Node was not handled correctly on parent_path')
		
		return node.__dict__
	def __setstate__(node,d):
		node.__dict__ = d
		if hasattr(node,'web'): node.web = node.web.real()
	def __repr__(node):
		def pstr(path):
			if path == None:
				return 'None'
			elif isinstance(path,int):
				return '%d'%path
			elif isinstance(path,WebPath):
				return '{%d}'%path.pid
		
		path_str='current_path='
		if node.current_path != None:
			path_str='{'
			path_str+='pid=%d,'%node.current_path.pid
			if hasattr(node.current_path,'parent'):
				path_str+='parent=%s'%pstr(node.current_path.parent)
			if hasattr(node.current_path, 'sub_paths'):
				if node.current_path.sub_paths == None:
					path_str += 'sub_paths=None'
				elif isinstance(node.current_path.sub_paths, (list,tuple,set)):
					path_str+= 'sub_paths={'
					for item in node.current_path.sub_paths:
						path_str += ' %s,'%pstr(item)
					path_str+= '}'
			
		else:
			path_str+='None'
		return "NODE{%s,%s,%s}"%(node.identifier,node.current_value,path_str)
class WebPath:
	numPaths=0
	def __init__(path,node,**kwargs):
		#Key Word Arg for enabling the getSearch() call on the paths node
		if 'build_search' in kwargs:
			build_search = kwargs['build_search']
		else: build_search = True
		
		#Key Word Arg for enabling the getSearch() call on the paths node
		if 'allow_stop' in kwargs:
			allow_stop = kwargs['allow_stop']
		else: allow_stop = True
		
		
		#Key Word Arg for WebPath required SearchWeb 'web' attribute
		if 'web' in kwargs: path.web = kwargs['web']
		else: raise Exception('WebPath must be called with a SearchWeb kwargs')
		
		#Sets WebPath Path ID attribute
		path.pid = path.web.WebPath.numPaths
		path.web.WebPath.numPaths+=1	

		#Sets WebPath's 'enabled' attribute
		path.enabled=True
		
		#Sets WebPath's 'sub_paths' attribute with initial None value
		path.sub_paths = None
		
		#Sets WebPath's 'node' attribute to provided <WebNode> object
		path.node = node
		
		#Sets WebPath's 'search_func' attribute based on 'build_search' kwargs
		if build_search: path.search_func = node.getSearch(allow_stop)
		else: path.search_func = None

	def root(*args,**kwargs):
		if 'web' in kwargs:
			web = kwargs['web']
		else: raise Exception('WebPath root requires a web kw')
		
		#Get Root WebNode
		node = web.WebNode(*args,**kwargs)
		web.setNode(node,*args)
		#node = web.getNode(*args,**kwargs)
		
		#Sets allow_stop key word
		if 'allow_stop' in kwargs and kwargs['allow_stop']: raise Exception('Root WebPaths must have allow_stop set to False')
		kwargs['allow_stop'] = False
		
		#Builds Root WebPath
		root = web.WebPath(node,**kwargs)
		node.setCurrentPath(root)
		
		#Returns WebPath search function
		return root.search_func
	def getSubPath(path,node):
		if not(path.enabled): raise Exception('Path must be enabled to branch from it')
		
		#Initialize path.sub_path as an empty set
		if path.sub_paths == None: path.sub_paths = set()
		
		#Creates a new WebPath for the subpath
		sp = path.web.WebPath(node,web=path.web)
		
		#Sets the subpath's parent to this path
		sp.parent = path
		
		#Sets the current path of the subpath's node 
		node.setCurrentPath(sp)
		
		#Adds the subpath to this paths sub_paths set
		path.sub_paths.add(sp)
		
		#Returns the subpath's search function
		return sp.search_func
	def getSubPathFrom(node,other):
		#Returns subpath from Origin Node's current_path if valid one exists 
		if isinstance(node.current_path,WebPath):
			return node.current_path.getSubPath(other)
		#Build Origin Path
		origin_path = node.web.WebPath(node, web=node.web, build_search=False)
		
		#Set Origin Path
		node.setCurrentPath(origin_path)
		
		#Return subpath of Origin Path
		return origin_path.getSubPath(other)
	def isEnabled(path):
		return path.enabled
	def isDisabled(path):
		return not(path.isEnabled())
	def isParent(path,other):
		if not(hasattr(path,'parent')): return False
		elif path.parent == None: return False
		elif isinstance(path.parent,int):
			if isinstance(other,WebPath):
				test = path.parent == other.pid
			else: raise Exception('Invalid type of other WebPath')
		elif isinstance(path.parent,WebPath):
			if isinstance(other,WebPath):
				test = path.parent == other
			else: raise Exception('Invalid type of other WebPath')
		else: raise Exception('Invalid type of WebPath parent')
		
		inverse = other.isSubPath(path)
		
		if test != inverse: raise Exception('Test does not agree with Test Inverse')
		return test
	def isSubPath(path,other):
		if not(hasattr(path,'sub_paths')): return False
		elif path.sub_paths == None: return False
		elif isinstance(path.sub_paths,(set,list,tuple)):
			test=False
			for sp in path.sub_paths:
				if isinstance(sp,int):
					if isinstance(other,WebPath):
						test = sp == other.pid
					else: raise Exception('Invalid type of other WebPath')
				elif isinstance(sp,WebPath):
					if isinstance(other,WebPath):
						test = sp == other
					else: raise Exception('Invalid type of other WebPath')
				else: raise Exception('Invalid type of WebPath parent')
				if test: break
		else: raise Exception('Invalid type of WebPath sub_paths')
		
		
		#test =  other in path.sub_paths
		#inverse = other.isParent(path)
		#if test != inverse: raise Exception('Test does not agree with Test Inverse')
		return test
	def isLoaded(path):
		if hasattr(path,'parent'):
			if isinstance(path.parent,int): return False
		if hasattr(path,'sub_paths') and isinstance(path.sub_paths,(set,list,tuple)):
			for c in path.sub_paths:
				if isinstance(c,int): return False
		return True
	def ensure(path):
		if path.isLoaded(): return True
		elif not(path.enabled): return False
		elif not(isinstance(path.node, WebNode)): raise Exception('Enabled WebPath must have valid WebNode')
		
		path.node = path.node.real()
		return True
	def removeParent(path):
		path.ensure()
		if hasattr(path,'parent'):
			if path.parent == None: return False
			elif not(isinstance(path.parent,WebPath)): raise Exception('parent of path is not of type WebPath')
			path.parent.removeSubPath(path)
			path.parent = None
			return True
		else: return True
	def removeSubPath(path,sp):
		path.ensure()
		if hasattr(path,'sub_paths'):
			if path.sub_paths == None: raise Exception('Cannot remove path from sub_paths when sub_paths is None')
			elif not(sp in path.sub_paths): raise Exception('WebPath sp not in path.sub_paths')
			path.sub_paths.remove(sp)
		else: raise Exception('WebPath has no attribute sub_paths')
	def end(path):
		path.node.web.endAt(*path.node.identifier)
		path.search_func = None
	
	def killPath(path):
		#Kill Path
		if not(path.ensure()): raise Exception('WebPath killed while disabled')
		path.removeParent()
		if path.search_func != None:
			if not(path.search_func in path.web.Q): raise Exception('WebPath search_func improperly removed from SearchQueue')
			path.web.Q.remove(path.search_func)
			path.end()
		kill_count = 1
		
		#Kill SubPaths
		if hasattr(path,'sub_paths'):
			if isinstance(path.sub_paths,(set,list,tuple)):
				for sp in copy(path.sub_paths):
					if not(isinstance(sp,WebPath)): raise Exception('All killed sub_paths must be of type WebPath')
					kill_count += sp.killPath()
		return kill_count
	def regionAdj(path,**kwargs):
		if not(isinstance(path.node,WebNode)): raise Exception('WebPath must have valid WebNode to get adjacent WebPaths')
		rtn = []
		for adj_node in path.node.regionAdj(**kwargs):
			if not(adj_node.inPath()): continue
			#print('adj_node found',flush=True)
			adj_path = adj_node.getCurrentPath()
			if path.isParent(adj_path):
				rtn.append((path,adj_path))
			elif path.isSubPath(adj_path):
				rtn.append((adj_path,path))
		return tuple(rtn)
	def replace_pids(path,pid_dict,ignore_missing=False):
		if hasattr(path,'parent'):
			if path.parent == None: pass
			elif isinstance(path.parent,int):
				if path.parent in pid_dict:
					path.parent = pid_dict[path.parent]
				elif ignore_missing: pass
				else: raise Exception('replacement pid not in pid_dict')
			elif isinstance(path.parent,WebPath):
				if path.parent.pid in pid_dict:
					path.parent = pid_dict[path.parent.pid]
				elif ignore_missing: pass
				else: raise Exception('replacement pid not in pid_dict')
			else: raise Exception('Invalid type for WebPath parent')
		if hasattr(path,'sub_paths'):
			if path.sub_paths == None: pass
			elif isinstance(path.sub_paths,(set,list,tuple)):
				r_set=set()
				for sp in path.sub_paths:
					if isinstance(sp,int):
						if sp in pid_dict:
							r_set.add(pid_dict[sp])
						elif ignore_missing:
							r_set.add(sp)
						else: raise Exception('replacement pid not in pid_dict')
					elif isinstance(sp,WebPath):
						if sp.pid in pid_dict:
							r_set.add(pid_dict[sp.pid])
						elif ignore_missing: 
							r_set.add(sp)	
						else: raise Exception('replacement pid not in pid_dict')
					else: raise Exception('Invalid type for WebPath sub_path')
				path.sub_paths = r_set
			else: raise Exception('Invalid type for WebPath sub_paths')
		
	def __getstate__(path):
		return path.__dict__
	def __setstate__(path,d):
		path.__dict__ = d
		if hasattr(path,'web'): path.web = path.web.real()
	def __repr__(path):
		def pstr(path):
			if path == None:
				return 'None'
			elif isinstance(path,int):
				return '%d'%path
			elif isinstance(path,WebPath):
				return '{%d}'%path.pid
		path_str='pid=%d,'%path.pid
		if path.node != None:
			path_str+='node=%s,'%(path.node.identifier,)
		else: path_str+='node=None,'
		if hasattr(path,'parent'):
			path_str+='parent=%s,'%pstr(path.parent)
		if hasattr(path, 'sub_paths'):
			if path.sub_paths == None:
				path_str += 'sub_paths=None'
			elif isinstance(path.sub_paths, (list,tuple,set)):
				path_str+= 'sub_paths={'
				for item in path.sub_paths:
					path_str += ' %s,'%pstr(item)
				path_str+= '}'
		return 'PATH{%s}'%path_str
class SearchWeb:
	numWebs=0
	web_lookup = {}
	def __init__(web,**kwargs):
		"""
			identifier : unique identifier set
			getter : <func> for getting identifier set from
			key : <func> for getting unique
 			eval : <func>(id_set)
		"""
		web.wid=SearchWeb.numWebs
		SearchWeb.numWebs+=1
		SearchWeb.web_lookup[web.wid] = web
		web.node_lookup = {}
		
		if 'name' in kwargs:
			web.name = kwargs['name']	
		else: web.name = 'temp'
		
		if 'val_func' in kwargs:
			web.val_func = kwargs['val_func']	
		else: raise
		
		if 'transition_func' in kwargs:
			web.transition_func = kwargs['transition_func']
		else: raise
		
		if 'eval_func' in kwargs:
			web.eval_func = kwargs['eval_func']
		else: raise
		if 'stop_func' in kwargs:
			web.stop_func = kwargs['stop_func']
		else: raise
		
		if 'adj_func' in kwargs:
			web.adj_func = kwargs['adj_func']
		else: raise
		
		if 'region_func' in kwargs:
			web.region_func = kwargs['region_func']
			web.loaded_regions = {}
			web.unloaded_regions = set()
			web.unload_buffer = []
			web.region_contents = {}
		else: raise
		
		
		web.buffer = set()
		if 'buffer_interval' in kwargs:
			web.buffer_interval = kwargs['buffer_interval']
		else: web.buffer_interval = None
		
		
		web.Q = SearchQueue()
	
		web.WebNode = WebNode 
	
		web.WebPath = WebPath
	def __getstate__(web):
		return web.wid
	def __setstate__(web,d):
		web.__dict__ = SearchWeb.web_lookup[d].__dict__
	def clear(web):
		web.node_lookup={}
		web.Q = SearchQueue()
	def real(web):
		return SearchWeb.web_lookup[web.wid]
	def getNode(web,*args,**kwargs):
		if 'allow_unloaded' in kwargs:
			allow_unloaded = kwargs['allow_unloaded']
		else: allow_unloaded = False
		if 'allow_None' in kwargs:
			allow_None = kwargs['allow_None']
		else: allow_None = False
		
		if 'lookup' in kwargs:
			current_lookup = kwargs['lookup']
			other_options=True
		else:
			R = web.getRegion(*args,allow_unloaded=allow_unloaded)
			if not(R.loaded):
				if allow_unloaded:
					rtn = R.unloadedLookup(*args)
					if isinstance(rtn,WebNode) or (rtn == None and allow_None):
						return rtn
			current_lookup = web.getRegion(*args,allow_unloaded=False)
			other_options=False
		def try_again():
			if 'lookup' in kwargs:
				del kwargs['lookup']
				return web.getNode(*args,**kwargs)
			elif allow_unloaded:
				if 'allow_unloaded' in kwargs:
					del kwargs['allow_unloaded']
					return web.getNode(*args,**kwargs)
				else: raise Exception('Unexpected value for allow_unloaded')
			else: return None
		
		current_level = 0
		for kid in args:
			current_level += 1
			if not(kid in current_lookup):
				if other_options:
					return try_again()
				elif allow_None:
					return None
				elif current_level < len(args):
					current_lookup[kid] = {}
				else: current_lookup[kid] = web.WebNode(*args,web=web,**kwargs)
					
			current_lookup = current_lookup[kid]
		return current_lookup
	def setNode(web,node,*args):
		current_lookup = web.getRegion(*args)
		current_level = 0
		for kid in args:
			current_level += 1
			if not(kid in current_lookup):
				if current_level < len(args): current_lookup[kid] = {}
				else: current_lookup[kid] = node
			elif current_level == len(args):
				raise Exception('SearchWeb setNode() function can not replace already created WebNodes')
			current_lookup = current_lookup[kid]	
	def region(web,*args):
		return web.region_func(*args)
	def regionName(web,region):
		return '%s_region_%d.dictionary'%(web.name,region)
	def getRegion(web,*args,**kwargs):
		region = web.region(*args)
		if 'allow_unloaded' in kwargs:
			allow_unloaded = kwargs['allow_unloaded']
		else: allow_unloaded = False
		
		if not(region in web.loaded_regions): 
			web.loaded_regions[region] = Region(region)
		
		R = web.loaded_regions[region]
		
		if R.loaded: return R
		elif allow_unloaded: return R
		else: 
			web.load_region(region)
			return R
	def load_region(web,region):
		print('Loading Region %d'%region,flush=True)
		
		if not(region in web.loaded_regions): raise
		elif web.loaded_regions[region].loaded: raise
		else: R = web.loaded_regions[region]
		
		with open(web.regionName(region), 'rb') as config_dictionary_file:
			config_dictionary = pickle.load(config_dictionary_file)
			R(config_dictionary)
		if not(web.loaded_regions[region].loaded): raise
		elif not(R.loaded): raise
		return web.loaded_regions[region]
	def unload_region(web,region):
		print('Unloading Region %d'%region,flush=True)
		
		if not(region in web.loaded_regions): raise
		elif not(web.loaded_regions[region].loaded): raise
		else: R = web.loaded_regions[region]
		
		with open(web.regionName(region), 'wb') as config_dictionary_file:
			config_dictionary = R
			pickle.dump(config_dictionary, config_dictionary_file)

		if web.loaded_regions[region].loaded: raise Exception('Region remained loaded after unload')
		elif R.loaded: raise Exception('Region remained loaded after unload')
	def unloadBuffer(web,unload_factor=2):
		unloaded=0
		for ri in range(len(web.unload_buffer)//unload_factor):
			region=web.unload_buffer[ri]
			if web.region_contents[region] != 0: 
				for r in web.unload_buffer:
					breakpoint(r=r,contains=web.region_contents[r])
				raise
			web.unload_region(region)
			unloaded +=1
		print('UNLOAD_BUFFER[%d] %s'%(unloaded, set(web.unload_buffer[:unloaded])),flush=True,end='\n')
		web.unload_buffer = web.unload_buffer[unloaded:]
	def sizeof_unload_buffer(web):
		size = 0
		for region in web.unload_buffer:
			size += sys.getsizeof(flattenDictionary(web.loaded_regions[region]))
		return size
	def startAt(web,*args):
		region =  web.region(*args)
		if region in web.unload_buffer:
			if web.unload_buffer.index(region) < len(web.unload_buffer)//2:
				print('Unbuffered Older region')
			web.unload_buffer.remove(region)
			
		if region in web.region_contents: 
			web.region_contents[region] += 1
			
		else: web.region_contents[region] = 1
	def endAt(web,*args):
		region =  web.region(*args)
		if region in web.region_contents:
			if web.region_contents[region] <= 0: raise Exception('Region Content Value set below zero')
			web.region_contents[region] -= 1
		else: raise Exception('Ended in region that has not been visited before')
		if web.region_contents[region] == 0:
			web.unload_buffer.append(region)
			#print('Attempt Unload region_%d\tuBuf: %d\t@size ~%sB'%(region,len(web.unload_buffer),f'{web.sizeof_unload_buffer():,}'),flush=True,end='\r')
	def regionData(web,**kwargs):
		
		if 'strip_nodes' in kwargs:
			strip_nodes = kwargs['strip_nodes']
		else: strip_nodes = False
		if 'strip_paths' in kwargs:
			strip_paths = kwargs['strip_paths']
		else: strip_paths = strip_nodes 
		if strip_nodes and not(strip_paths): raise Exception('Can not strip nodes without striping paths')
		
		if 'raw_paths' in kwargs:
			raw_paths = kwargs['raw_paths']
		else: raw_paths = False
		if 'complete' in kwargs:
			complete = kwargs['complete']
		else: complete = True 
		if raw_paths and strip_paths: raise Exception('Can not strip paths and return raw paths')
		
		rtn_lookup = {}
		rtn_unloaded_state = {}
		for region in web.loaded_regions:
			R = web.loaded_regions[region]
			if not(R.loaded) and complete: web.load_region(region)
			if R.use_lookup():
				for node in get_all_nodes(R):
					identifier = node.identifier
					if strip_paths: node.current_path = None
					
					if raw_paths: add_lookup(identifier,node.current_path,rtn_lookup)
					else: add_lookup(identifier,node.current_value if strip_nodes else node,rtn_lookup)
			else:
				for node in get_all_nodes(R):
					identifier = node.identifier
					if strip_paths: node.current_path = None
					if raw_paths:
						add_lookup(identifier,node.current_path,rtn_unloaded_state)
					else: add_lookup(identifier,node.current_value if strip_nodes else node,rtn_unloaded_state)
		if complete:
			if len(rtn_unloaded_state) == 0: return rtn_lookup
			else: raise Exception('Region Data is not complete')
		else:
			return rtn_lookup,rtn_unloaded_state
	def search(web,id_set,**kwargs):
		if 'update_interval' in kwargs:
			update_interval = kwargs['update_interval']
		else: update_interval = None
		if 'buffer_interval' in kwargs and 'buffer_func' in kwargs:
			web.buffer_interval = kwargs['buffer_interval']
			buffer_func = kwargs['buffer_func']
			web.buffer = set()
			if 'buffer_store' in kwargs:
				web.buffer_store = kwargs['buffer_store']
			else: web.buffer_store = None
		else: web.buffer_interval = None
		
		#Key Word Args for region unload_buffer
		if 'unload_interval' in kwargs:
			unload_interval= kwargs['unload_interval']
		else: unload_interval = 10000
		if 'unload_min' in kwargs:
			unload_min= kwargs['unload_min']
		else: unload_min = 8
		if 'unload_factor' in kwargs:
			unload_factor= kwargs['unload_factor']
		else: unload_factor = 2
		
		if 'web' in kwargs: raise Exception('Keyword web should not be set')
		else: kwargs['web'] = web
		#Creates Search Root Nodes
		for identifier in id_set:
			web.Q.enqueue(web.WebPath.root(*identifier,**kwargs))
		del kwargs['web']
		
		#Loops Through Search Queue
		step=0
		while(len(web.Q) > 0):
			#Dequeues Next Search Function from Search Queue
			node_search_function = web.Q.dequeue()
			
			#Calls Search Function and enqueues returned adjacent node search functions into from Search Queue
			web.Q.enqueue(*node_search_function())
			
			#If region unload interval is set and the unload buffer is large enough
			if unload_interval!=None and step%unload_interval==0 and len(web.unload_buffer) > unload_min:
				web.unloadBuffer(unload_factor)
				#return web.regionData(complete=True,raw_paths=True)
			
			#If search update interval is set
			if update_interval!=None and step%update_interval==0: 
				print("Searched[%d/%d] ~%d in queue"%(step,len(web.Q)+step,len(web.Q)),flush=True,end='\n')
			step += 1
			
			#If identifier buffer interval is set
			if web.buffer_interval!=None and step%web.buffer_interval == 0: 
				buffer_func(web.buffer)
				all_region(web.loaded_regions)
				web.buffer=set()
			
		if 'rtn_type' in kwargs: 
			if kwargs['rtn_type'] == 'node_dict': return web.regionData(complete=True)
			elif kwargs['rtn_type'] == 'path_dict': return web.regionData(complete=True,raw_paths=True)
			elif kwargs['rtn_type'] == 'value_dict': return web.regionData(complete=True,strip_nodes=True)
			elif kwargs['rtn_type'] == 'value_list': return [ (k,node.current_value) for k,node in flattenDictionary(web.regionData(complete=True,strip_nodes=True),list)]
			elif kwargs['rtn_type'] == 'flat_value_dict':return {k:v.current_value for k,v in flattenDictionary(web.regionData(complete=True,strip_nodes=True),list)}
		else: return web.loaded_regions
