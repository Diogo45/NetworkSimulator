import sys
import math
nodes = {}
routers = {}

ipToName = {}


def mask(item):
    return int(item.Dest.split('/')[1])
    
class Node():
    def __init__(self, NodeName, MAC, IP, MTU, Gateway):
        self.NodeName = NodeName
        self.MAC = MAC
        self.IP = IP
        self.MTU = MTU
        self.Gateway = Gateway
        self.ARPs = {}
    def __str__(self):
        return self.NodeName + ", " + self.MAC + ", " + self.IP + ", " + str(self.MTU) + ", " + self.Gateway
    def SameNet(self, dest):
        ipm1 = self.IP
        ipm2 = nodes[dest].IP
        mask1 = int(ipm1.split('/')[1])
        mask2 = int(ipm2.split('/')[1])
        if mask1 != mask2:
            return False
        ip1 = ""
        for v in ipm1.split('/')[0].split('.'):
            ip1 += "{:08b}".format(int(v))
        ip2 = ""
        for v in ipm2.split('/')[0].split('.'):
            ip2 += "{:08b}".format(int(v))

        for i in range(0, mask1):
            if(ip1[i] != ip2[i]):
                return False
        return True

    def SendNewPackage(self, dest, data, msgType):
        inNet = self.SameNet(dest)
        #ARP Req and Resp
        
        if inNet:
            nextHopIP = nodes[dest].IP
            (nextHopName, ID) = ipToName[nextHopIP]
            nextHop = nodes[nextHopName]
            if nextHopIP not in self.ARPs.keys():

                nextHopMAC = nextHop.MAC
                self.ARPs[nextHopIP] = nextHopMAC  
                #Ver se faz sentido
                nextHop.ARPs[self.IP] = self.MAC    
                ###################################################################################
                print(self.NodeName + " box " + self.NodeName + " : ETH (src=" + self.MAC + " dst=FF:FF:FF:FF:FF:FF) \\n ARP - Who has - " + nextHopIP.split('/')[0] + "? Tell " + self.IP.split('/')[0] + ";")
                print(nextHopName + " => " + self.NodeName + " : ETH (src=" + nextHopMAC + " dst=" + self.MAC + ") \\n ARP - " + nextHopIP.split('/')[0] + " is at " + nextHopMAC + ";")        
            else:
                nextHopMAC = self.ARPs[nextHopIP]
        else:
            #Resolver /24 no hora que le e os strip tbm
            nextHopIP = self.Gateway + "/" + self.IP.split('/')[1]
            (nextHopName, ID) = ipToName[nextHopIP]
            nextHop = routers[nextHopName]
            if nextHopIP not in self.ARPs.keys():
                nextHopMAC = nextHop.MAC[ID]
                self.ARPs[nextHopIP] = nextHopMAC
                nextHop.ARPs[self.IP] = self.MAC 
                ###################################################################################
                print(self.NodeName + " box " + self.NodeName + " : ETH (src=" + self.MAC + " dst=FF:FF:FF:FF:FF:FF) \\n ARP - Who has - " + self.Gateway + "? Tell " + self.IP.split('/')[0] + ";")
                print(nextHopName + " => " + self.NodeName + " : ETH (src=" + nextHopMAC + " dst=" + self.MAC + ") \\n ARP - " + self.Gateway + " is at " + nextHopMAC + ";")
            else:
                nextHopMAC = self.ARPs[nextHopIP]
        fragments = []
        if len(data) > self.MTU:
           MTU = self.MTU
           off = 0
           for i in range(0, math.ceil(len(data)/MTU)):
                idata = data[off:off+MTU]
                if i == (math.ceil(len(data)/MTU) - 1):
                    msgi = Message(self.MAC, nextHopMAC, self.IP, nodes[dest].IP, msgType, 8, 0, off, idata)
                    fragments.append(msgi)
                    ###################################################################################
                    print(self.NodeName + " => " + nextHopName + " : ETH (src=" + self.MAC + " dst=" + nextHopMAC + ") \\n IP (src=" + self.IP + " dst=" + nodes[dest].IP + " ttl=8 mf=0 off=" + str(msgi.off) + ") \\n ICMP - "+ msgi.msgType + " (data=" + msgi.data + ");")
                else:
                    msgi = Message(self.MAC, nextHopMAC, self.IP, nodes[dest].IP, msgType, 8, 1, off, idata)
                    fragments.append(msgi)
                    ###################################################################################
                    print(self.NodeName + " => " + dest + " : ETH (src=" + self.MAC + " dst=" + nextHopMAC + ") \\n IP (src=" + self.IP + " dst=" + nodes[dest].IP + " ttl=8 mf=1 off=" + str(msgi.off) + ") \\n ICMP -  "+ msgi.msgType + " (data=" + msgi.data + ");")
                off += MTU

        else:
            msg = Message(self.MAC, nextHopMAC, self.IP, nodes[dest].IP, msgType, 8, 0, 0, data)
            ###################################################################################
            print(self.NodeName + " => " + str(nextHopName) + " : ETH (src=" + self.MAC + " dst=" + str(nextHopMAC) + ") \\n IP (src=" + self.IP + " dst=" + str(nodes[dest].IP) + " ttl=8 mf=" + str(msg.mf) + " off=" + str(msg.off) + ") \\n ICMP - " + str(msg.msgType) + " (data=" + str(msg.data) + ");")
            fragments.append(msg)    

        nextHop.RelayPackage(fragments)

    def RelayPackage(self, frags):
        msg = frags[0]
        if msg.msgType == "Time Exceeded":
            return

        if len(frags) > 1:
            fullMsg = ""
            for i in range(0, len(frags)):
                msgi = frags[i]
                fullMsg += msgi.data
            print(ipToName[msgi.dstIP][0] +" rbox "+ ipToName[msgi.dstIP][0] + " : Received " + fullMsg + ";")
            if msg.msgType == "Echo Reply":
                return
            else:
                self.SendNewPackage(ipToName[msg.srcIP][0], fullMsg, "Echo Reply") 
        else:
            print(ipToName[msg.dstIP][0] +" rbox "+ ipToName[msg.dstIP][0] + " : Received " + msg.data + ";")
            if msg.msgType == "Echo Reply":
                return
            else:
                self.SendNewPackage(ipToName[msg.srcIP][0], msg.data, "Echo Reply") 


        
    
class Message():
    def __init__(self, srcMAC, dstMAC, srcIP, dstIP, msgType, ttl, mf, off, data):
        self.srcMAC = srcMAC
        self.dstMAC = dstMAC
        self.srcIP = srcIP
        self.dstIP = dstIP
        self.msgType = msgType
        self.ttl = ttl
        self.mf = mf
        self.off = off
        self.data = data



        
class Router():
    
    def __init__(self, NodeName, NumPorts, MAC, IP, MTU):
        self.NodeName = NodeName
        self.NumPorts = NumPorts
        self.MAC = MAC
        self.IP = IP
        self.MTU = MTU
        self.RouterTable = []
        self.ARPs = {}
    def __str__(self):
        return self.NodeName + ", " + str(self.NumPorts) + ", " + str(self.MAC) + ", " + str(self.IP) + ", " + str(self.MTU)    


    def SameNet(self, ipm1, routerNet):
        #mask1 = int(ipm1.split('/')[1])
        mask2 = int(routerNet.split('/')[1])
        ip1 = ""
        for v in ipm1.split('/')[0].split('.'):
            ip1 += "{:08b}".format(int(v))
        ip2 = ""
        for v in routerNet.split('/')[0].split('.'):
            ip2 += "{:08b}".format(int(v))

        for i in range(0, mask2):
            if(ip1[i] != ip2[i]):
                return False
        return True

    def SameNetPort(self, ipm1, ipm2):
        mask1 = int(ipm1.split('/')[1])
        mask2 = int(ipm2.split('/')[1])
        if mask1 != mask2:
            return False
        ip1 = ""
        for v in ipm1.split('/')[0].split('.'):
            ip1 += "{:08b}".format(int(v))
        ip2 = ""
        for v in ipm2.split('/')[0].split('.'):
            ip2 += "{:08b}".format(int(v))

        for i in range(0, mask1):
            if(ip1[i] != ip2[i]):
                return False
        return True


    def RelayPackage(self, frags):
        #ttl checar e mandar TTL Exceeded
        msg = frags[0]
        if (msg.ttl - 1) < 1 or msg.msgType == "Time Exceeded":
            destIP = msg.srcIP
            for i in range(0, len(self.RouterTable)):
                if self.SameNet(destIP, self.RouterTable[i].Dest):
                    portID = self.RouterTable[i].Port
                    portMAC = self.MAC[portID]
                    portIP = self.IP[portID]
                    break
                
            destNode = nodes[ipToName[destIP][0]]
            if self.SameNetPort(destNode.IP, portIP):
                nextHopIP = destIP
                (nextHopName, ID) = ipToName[nextHopIP]
                nextHop = nodes[nextHopName]
                nextHopMAC = nextHop.MAC
            else:
                for router in routers.values():
                    if router.NodeName == self.NodeName:
                        continue
                    for i in range(0, len(router.IP)):
                        #CHECK if same CONECTION
                        if self.SameNetPort(portIP, router.IP[i]): 
                            nextHopIP = router.IP[i]
                            (nextHopName, ID) = ipToName[nextHopIP]
                            nextHop = routers[nextHopName]
                            break

                nextHopMAC = self.ARPs[nextHopIP]    

            if msg.msgType == "Time Exceeded":
                ttl = msg.ttl - 1
            else:
                ttl = 8
            fullMsg = ""
            fragments = []
            for i in range(0, len(frags)):
                msgi = frags[i]
                fullMsg += msgi.data

            MTU = self.MTU[portID]
            off = 0
            
            for frag in frags:
                idata = fullMsg[off:off+MTU]
                msgi = Message(self.MAC[portID], nextHopMAC, msg.srcIP, msg.dstIP, "Time Exceeded", ttl, 0, off, idata)
                fragments.append(msgi)
                print(self.NodeName + " => " + nextHopName + " : ETH (src=" + self.MAC[portID] + " dst=" + nextHopMAC + ") \\n IP (src=" + portIP + " dst=" + msg.srcIP + " ttl=" + str(ttl) +  " mf=0 off=0) \\n ICMP - Time Exceeded;")
           

            nextHop.RelayPackage(fragments)
            return


        destIP = msg.dstIP
        for i in range(0, len(self.RouterTable)):
            if self.SameNet(destIP, self.RouterTable[i].Dest):
                portID = self.RouterTable[i].Port
                portMAC = self.MAC[portID]
                portIP = self.IP[portID]
                break

        destNode = nodes[ipToName[destIP][0]]
        if self.SameNetPort(destNode.IP, portIP):
            nextHopIP = destIP
            (nextHopName, ID) = ipToName[nextHopIP]
            nextHop = nodes[nextHopName]
            if nextHopIP not in self.ARPs.keys():
                nextHopMAC = nextHop.MAC
                self.ARPs[nextHopIP] = nextHopMAC  
                nextHop.ARPs[portIP] = self.MAC[ID]    
                ###################################################################################
                print(self.NodeName + " box " + self.NodeName + " : ETH (src=" + portMAC + " dst=FF:FF:FF:FF:FF:FF) \\n ARP - Who has - " + nextHopIP.split('/')[0] + "? Tell " + portIP.split('/')[0] + ";")
                print(nextHopName + " => " + self.NodeName + " : ETH (src=" + nextHopMAC + " dst=" + portMAC + ") \\n ARP - " + nextHopIP.split('/')[0] + " is at " + nextHopMAC + ";")        
            else:
                nextHopMAC = self.ARPs[nextHopIP]
        else:
            
            for router in routers.values():
                if router.NodeName == self.NodeName:
                    continue
                for i in range(0, len(router.IP)):
                    #CHECK if same CONECTION
                    if self.SameNetPort(portIP, router.IP[i]): 
                        nextHopIP = router.IP[i]
                        (nextHopName, ID) = ipToName[nextHopIP]
                        nextHop = routers[nextHopName]
                        break
           
            if nextHopIP not in self.ARPs.keys():
                nextHopMAC = nextHop.MAC[ID]
                self.ARPs[nextHopIP] = nextHopMAC
                nextHop.ARPs[portIP] = self.MAC[ID]
                ###################################################################################
                print(self.NodeName + " box " + self.NodeName + " : ETH (src=" + portMAC + " dst=FF:FF:FF:FF:FF:FF) \\n ARP - Who has - " + nextHopIP + "? Tell " + portIP.split('/')[0] + ";")
                print(nextHopName + " => " + self.NodeName + " : ETH (src=" + nextHopMAC + " dst=" + portMAC + ") \\n ARP - " + nextHopIP + " is at " + nextHopMAC + ";")
            else:
                nextHopMAC = self.ARPs[nextHopIP]
        fragments = []
        fullMsg = ""
        for i in range(0, len(frags)):
                msgi = frags[i]
                fullMsg += msgi.data
        MTU = self.MTU[portID]
        off = 0
        if len(fullMsg) > self.MTU[portID]:
           ttl = msg.ttl - 1
           for i in range(0, math.ceil(len(fullMsg)/MTU)):
                idata = fullMsg[off:off+MTU]
                if i == (math.ceil(len(fullMsg)/MTU) - 1):
                    msgi = Message(self.MAC[portID], nextHopMAC, msg.srcIP, msg.dstIP, msg.msgType, ttl, 0, off, idata)
                    fragments.append(msgi)
                    ###################################################################################
                    print(self.NodeName + " => " + nextHopName + " : ETH (src=" + self.MAC[portID] + " dst=" + nextHopMAC + ") \\n IP (src=" + msg.srcIP + " dst=" +msg.dstIP + " ttl=" +str(msg.ttl) +  " mf=0 off=" + str(msgi.off) + ") \\n ICMP - "+ msgi.msgType + " (data=" + msgi.data + ");")
                else:
                    msgi = Message(self.MAC[portID], nextHopMAC, msg.srcIP, msg.dstIP, msg.msgType, ttl, 1, off, idata)
                    fragments.append(msgi)
                    ###################################################################################
                    print(self.NodeName + " => " + nextHopName + " : ETH (src=" + self.MAC[portID] + " dst=" + nextHopMAC + ") \\n IP (src=" + msg.srcIP + " dst=" + msg.dstIP + " ttl=" + str(msg.ttl) +  " mf=1 off=" + str(msgi.off) + ") \\n ICMP -  "+ msgi.msgType + " (data=" + msgi.data + ");")
                off += MTU
        else:
            ttl = msg.ttl - 1
            msg = Message(self.MAC[portID], nextHopMAC, msg.srcIP, msg.dstIP, msg.msgType, ttl , 0, 0, fullMsg)
            ###################################################################################
            print(self.NodeName + " => " + nextHopName + " : ETH (src=" + self.MAC[portID] + " dst=" + nextHopMAC + ") \\n IP (src=" + msg.srcIP + " dst=" + msg.dstIP + " ttl= " + str(msg.ttl) +  " mf=" + str(msg.mf) + " off=" + str(msg.off) + ") \\n ICMP - " + msg.msgType + " (data=" + fullMsg + ");")
            fragments.append(msg)    

        nextHop.RelayPackage(fragments)





       
        




class RouterTableEntry():
    def __init__(self, Dest, NextHop, Port):
            self.Dest = Dest
            self.NextHop = NextHop
            self.Port = Port
    def __str__(self):
        return self.Dest + ", " + self.NextHop + ", " + str(self.Port)
    def __repr__(self):
        return '<'+str(self)+'>'

def TopologyParse(topologyPath):
    topologyFile = open(topologyPath)
    reading = ""
    for line in topologyFile.readlines():
        if '#' in line:
            if 'NODE' in line:
                reading = "NODE"
                continue
            elif 'ROUTERTABLE' in line:
                reading = "ROUTERTABLE"
                continue
            elif "ROUTER" in line:
                reading = "ROUTER"
                continue
            
        if reading == "NODE":
            nodeargs = line.split(',')
            ipToName[nodeargs[2]] = (nodeargs[0], -1)
            node = Node(NodeName = nodeargs[0].strip(), MAC = nodeargs[1].strip(), IP = nodeargs[2].strip(), MTU = int(nodeargs[3]), Gateway = nodeargs[4].strip().strip('\n'))
            nodes[nodeargs[0]] = node
        elif reading == "ROUTER":
            routerArgs = line.split(',')
            NodeName = routerArgs[0].strip()
            numPorts = int(routerArgs[1])
            MACs = []
            IPs = []
            MTUs = []
            for i in range(0, numPorts):
                MACi = routerArgs[2 + 3*i].strip()
                MACs.append(MACi)
                IPi = routerArgs[3 + 3*i].strip()
                ipToName[IPi] = (NodeName, i)
                IPs.append(IPi)
                MTUi = int(routerArgs[4 + 3*i])
                MTUs.append(MTUi)
            router = Router(NodeName = NodeName, NumPorts = numPorts, MAC = MACs, IP = IPs, MTU = MTUs)
            routers[NodeName] = router
        elif reading == "ROUTERTABLE":
            tableArgs = line.split(',')
            key = tableArgs[0].strip()
            tableEntry = RouterTableEntry(Dest = tableArgs[1], NextHop = tableArgs[2], Port = int(tableArgs[3]))
            routers[key].RouterTable.append(tableEntry)
    for router in routers.values():
        router.RouterTable = sorted(router.RouterTable, key=mask, reverse=True)

def main():
    if(len(sys.argv) < 5):
        print("Not enough arguments")
        return
    TopologyParse(sys.argv[1])
    origem = sys.argv[2]
    destino = sys.argv[3]
    mensagem = sys.argv[4]

    SrcHost = nodes[origem]

    SrcHost.SendNewPackage(destino, mensagem, "Echo Request")


if __name__ == "__main__":
    main()
    
