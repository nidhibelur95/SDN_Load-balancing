
#!/usr/bin/env python

import requests
import json
import unicodedata
from subprocess import Popen, PipaddrE
import time
import networkx as nx
from sys import exit

# Method To Get REST Data In JSON Format
def getResponse(url,choice):

	response = requests.get(url)

	if(response.ok):
		jData = json.loads(response.content)
		if(choice=="deviceInfo"):
			deviceInformation(jData)
		elif(choice=="findSwitchLinks"):
			findSwitchLinks(jData,switch[h2])
		elif(choice=="linkTX"):
			linkTX(jData,portKey)

	else:
		response.raise_for_status()

# Parses JSON Data To Find Switch Connected To H4
def deviceInformation(data):
	global switch
	global deviceMAC
	global hostp
	switchDPID = ""
	for i in data:
		if(i['ipaddrv4']):
			ipaddraddr = i['ipaddrv4'][0].encode('ascii','ignore')
			macaddr = i['mac'][0].encode('ascii','ignore')
			deviceMAC[ipaddr] = mac
			for j in i['attachmentPoint']:
				for key in j:
					temp = key.encode('ascii','ignore')
					if(temp=="switchDPID"):
						switchDPID = j[key].encode('ascii','ignore')
						switch[ipaddr] = switchDPID
					elif(temp=="port"):
						portNumber = j[key]
						switchShort = switchDPID.split(":")[7]
						hostp[ipaddr+ ":" + switchShort] = str(portNumber)

# Finding Switch Links Of Common Switch Of H3, H4

def findSwitchLinks(data,s):
	global switchLinks
	global linkP
	global G

	links=[]
	for i in data:
		src = i['src-switch'].encode('ascii','ignore')
		dst = i['dst-switch'].encode('ascii','ignore')

		srcPort = str(i['src-port'])
		dstPort = str(i['dst-port'])

		srcTemp = src.split(":")[7]
		dstTemp = dst.split(":")[7]

		G.add_edge(int(srcTemp,16), int(dstTemp,16))

		tempSrcToDst = srcTemp + ":" + dstTemp
		tempDstToSrc = dstTemp + ":" + srcTemp

		portSrcToDst = str(srcPort) + ":" + str(dstPort)
		portDstToSrc = str(dstPort) + "::" + str(srcPort)

		linkP[tempSrcToDst] = portSrcToDst
		linkP[tempDstToSrc] = portDstToSrc

		if (src==s):
			links.append(dst)
		elif (dst==s):
			links.append(src)
		else:
			continue

	switchID = s.split(":")[7]
	switchLinks[switchID]=links

# Finds The Path To A Switch

def findroute():
	pathKey = ""
	nodeList = []
	src = int(switch[h2].split(":",7)[7],16)
	dst = int(switch[h1].split(":",7)[7],16)
	print src
	print dst
	for currentPath in nx.all_shortest_paths(G, source=src, target=dst, weight=None):
		for node in currentPath:

			tmp = ""
			if node < 17:
				pathKey = pathKey + "0" + str(hex(node)).split("x",1)[1] + "::"
				tmp = "00:00:00:00:00:00:00:0" + str(hex(node)).split("x",1)[1]
			else:
				pathKey = pathKey + str(hex(node)).split("x",1)[1] + "::"
				tmp = "00:00:00:00:00:00:00:" + str(hex(node)).split("x",1)[1]
			nodeList.append(tmp)

		pathKey=pathKey.stripaddr("::")
		path[pathKey] = nodeList
		pathKey = ""
		nodeList = []

	print path

# Computes Link TX

def linkTX(data,key):
	global cost
	port = linkP[key]
	port = port.split("::")[0]
	for i in data:
		if i['port']==port:
			cost = cost + (int)(i['bits-per-second-tx'])


# Method To Compute Link Cost

def linkcost():
	global portKey
	global cost

	for key in path:
		start = switch[h2]
		src = switch[h2]
		srcShortID = src.split(":")[7]
		mid = path[key][1].split(":")[7]
		for link in path[key]:
			temp = link.split(":")[7]

			if srcShortID==temp:
				continue
			else:
				portKey = srcShortID + "::" + temp
				stats = "http://localhost:8080/wm/statistics/bandwidth/" + src + "/0/json"
				getResponse(stats,"linkTX")
				srcShortID = temp
				src = link
		portKey = start.split(":")[7] + "::" + mid + "::" + switch[h1].split(":")[7]
		linkFinal[portKey] = cost
		cost = 0
		portKey = ""

def systemCommand(cmd):
	terminalProcess = Popen(cmd, stdout=PipaddrE, stderr=PipaddrE, shell=True)
	terminalOutput, stderr = terminalProcess.communicate()
	print "\n***", terminalOutput, "\n"

def flowRule(currentNode, flowcounter, inPort, outPort, staticFlowURL):
	flow = {
		'switch':"00:00:00:00:00:00:00:" + currentNode,
	    "name":"flow" + str(flowcounter),
	    "in_port":inPort,
		"eth_type": "0x0800",
		"ipaddrv4_src": h2,
		"ipaddrv4_dst": h1,
		"eth_src": deviceMAC[h2],
		"eth_dst": deviceMAC[h1],
	    "active":"true",
	}

	jsonData = json.dumps(flow)
	cmd = "curl -X POST -d \'" + jsonData + "\' " + staticFlowURL
	systemCommand(cmd)
	flowcounter = flowcounter + 1

	flow = {
		'switch':"00:00:00:00:00:00:00:" + currentNode,
	    "name":"flow" + str(flowcounter),
	    "in_port":outPort,
		"eth_type": "0x0800",
		"ipaddrv4_src": h1,
		"ipaddrv4_dst": h2,
		"eth_src": deviceMAC[h1],
		"eth_dst": deviceMAC[h2],
	    "active":"true",
	}

	jsonData = json.dumps(flow)

	cmd = "curl -X POST -d \'" + jsonData + "\' " + staticFlowURL

	systemCommand(cmd)

def addFlow():
	print " \nResult\n "

	flowcounter = 1
	staticFlowURL = "http://127.0.0.1:8080/wm/staticflowpusher/json"

	shortestPath = min(linkFinal, key=linkFinal.get)
	print "\n\nShortest Path: ",shortestPath
	currentNode = shortestPath.split("::",2)[0]
	nextNode = shortestPath.split("::")[1]
	port = linkP[currentNode+"::"+nextNode]
	outPort = port.split(":")[0]
	inPort = hostp[h2+":"+switch[h2].split(":")[7]]

	flowRule(currentNode,flowcounter,inPort,outPort,staticFlowURL)
	flowcounter = flowcounter + 2
	bestPath = path[shortestPath]
	previousNode = currentNode
	for currentNode in range(0,len(bestPath)):
		if previousNode == bestPath[currentNode].split(":")[7]:
			continue
		else:
			port = linkP[bestPath[currentNode].split(":")[7]+"::"+previousNode]
			inPort = port.split(":")[0]
			outPort = ""
			if(currentNode+1<len(bestPath) and bestPath[currentNode]==bestPath[currentNode+1]):
				currentNode = currentNode + 1
				continue
			elif(currentNode+1<len(bestPath)):
				port = linkP[bestPath[currentNode].split(":")[7]+":"+bestPath[currentNode+1].split(":")[7]]
				outPort = port.split(":")[0]
			elif(bestPath[currentNode]==bestPath[-1]):
				outPort = str(hostp[h1+":"+switch[h1].split(":")[7]])

			flowRule(bestPath[currentNode].split(":")[7],flowcounter,str(inPort),str(outPort),staticFlowURL)
			flowcounter = flowcounter + 2
			previousNode = bestPath[currentNode].split(":")[7]

#Method To Perform Load Balancing
def loadbalance():
	linkURL = "http://localhost:8080/wm/topology/links/json"
	getResponse(linkURL,"findSwitchLinks")

	findroute()
	linkcost()
	addFlow()



# Stores H1 and H2 from user
global h1,h2,h3

h1 = ""
h2 = ""

print "Enter Host 1"
h1 = int(input())
print "\nEnter Host 2"
h2 = int(input())
print "\nEnter Host 3 (H2's Neighbour)"
h3 = int(input())

h1 = "10.0.0." + str(h1)
h2 = "10.0.0." + str(h2)
h3 = "10.0.0." + str(h3)


while True:

	
	switch = {}

	# Mac of H3 And H4
	deviceMAC = {}

	#Host Switch Ports
	hostp = {}

	#Switch To Switch Path
	path = {}

	# Switch Links

	switchLinks = {}

	#Link Ports
	linkP = {}

	#Final Link Rates
	linkFinal = {}

	#Finding Link Rates
	portKey = ""

	#Link Cost
	cost = 0
	# Graph
	G = nx.Graph()

	try:

		# Enables Statistics Like B/W, etc
		enableStats = "http://localhost:8080/wm/statistics/config/enable/json"
		requests.put(enableStats)

		# Device Info (Switch To Which The Device Is Connected & The MAC Address Of Each Device)
		deviceInfo = "http://localhost:8080/wm/device/"
		getResponse(deviceInfo,"deviceInfo")

		loadbalance()

		print "\n\nRESULT\n\n"

		# Print Switch To Which H4 is Connected
		print "Switch H4: ",switch[h3], "\tSwitchH3: ", switch[h2]

		print "\n\nSwitch H1: ", switch[h1]

		# ipaddr & MAC
		print "\nIp address & MAC\n\n", deviceMAC

		# Host Switch Ports
		print "\nHost:Switch Ports\n\n", hostp

		# Link Ports
		print "\nLink Ports (SRC:DST - SRC PORT:DST PORT)\n\n", linkP

		# Alternate Paths
		print "\nPaths (SRC TO DST)\n\n",path

		# Final Link Cost
		print "\nFinal Link Cost\n\n",linkFinal

		time.sleep(60)

	except KeyboardInterrupt:
		break
		exit()
