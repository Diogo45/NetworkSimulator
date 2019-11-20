import sys

nodes = {}
routers = {}


class Node():
    def __init__(self, NodeName, MAC, IP, MTU, Gateway):
        self.NodeName = NodeName
        self.MAC = MAC
        self.IP = IP
        self.MTU = MTU
        self.Gateway = Gateway
    def __str__(self):
        return self.NodeName + ", " + self.MAC + ", " + self.IP + ", " + str(self.MTU) + ", " + self.Gateway
        
class Router():
    def __init__(self, RouterName, NumPorts, MAC, IP, MTU):
        self.RouterName = RouterName
        self.NumPorts = NumPorts
        self.MAC = MAC
        self.IP = IP
        self.MTU = MTU
        self.RouterTable = {}
    def __str__(self):
        return self.RouterName + ", " + str(self.NumPorts) + ", " + str(self.MAC) + ", " + str(self.IP) + ", " + str(self.MTU)    

class RouterTableEntry():
    def __init__(self, Dest, NextHop, Port):
            self.Dest = Dest
            self.NextHop = NextHop
            self.Port = Port
    def __str__(self):
        return self.Dest + ", " + self.NextHop + ", " + str(self.Port)

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
            node = Node(NodeName = nodeargs[0], MAC = nodeargs[1], IP = nodeargs[2], MTU = int(nodeargs[3]), Gateway = nodeargs[4])
            nodes[nodeargs[0]] = node
        elif reading == "ROUTER":
            routerArgs = line.split(',')
            routerName = routerArgs[0]
            numPorts = int(routerArgs[1])
            MACs = []
            IPs = []
            MTUs = []
            for i in range(0, numPorts):
                MACi = routerArgs[2 + 3*i]
                MACs.append(MACi)
                IPi = routerArgs[3 + 3*i]
                IPs.append(IPi)
                MTUi = int(routerArgs[4 + 3*i])
                MTUs.append(MTUi)
            router = Router(RouterName = routerName, NumPorts = numPorts, MAC = MACs, IP = IPs, MTU = MTUs)
            routers[routerName] = router
        elif reading == "ROUTERTABLE":
            tableArgs = line.split(',')
            key = tableArgs[0]
            tableEntry = RouterTableEntry(Dest = tableArgs[1], NextHop = tableArgs[2], Port = int(tableArgs[3]))
            routers[key].RouterTable[tableArgs[1]] = tableEntry

    

def ARP_REQ(origem, destino):
    ipm1 = nodes[origem].IP
    ipm2 = nodes[destino].IP
    mask1 = int(ipm1.split('/')[1])
    mask2 = int(ipm2.split('/')[1])
    if mask1 != mask2:
        #print("not in the same network")
        return False
    ip1 = ""
    for v in ipm1.split('/')[0].split('.'):
        ip1 += "{:08b}".format(int(v))
    ip2 = ""
    for v in ipm2.split('/')[0].split('.'):
        ip2 += "{:08b}".format(int(v))

    for i in range(0, mask1):
        if(ip1[i] != ip2[i]):
            #print("not in the same network")

            return False
    #print("in the same network")
    return True

def SendARP(sameNetwork, source, destiny):
    
    if sameNetwork:
        print(source + " box " + source + " : ETH (src=" + nodes[source].MAC + " dst=FF:FF:FF:FF:FF:FF) \\n ARP - Who has - " + nodes[destiny].IP.split('/')[0] + "? Tell " + nodes[source].IP.split('/')[0] + ";")
        print(destiny + " => " + source + " : ETH (src=" + nodes[destiny].MAC + " dst=" + nodes[source].MAC + ") \\n ARP - " + nodes[destiny].IP.split('/')[0] + " is at " + nodes[destiny].MAC + ";")
        return nodes[destiny].MAC
    else:
        print(source + " box " + source + " : ETH (src=" + nodes[source].MAC + " dst=FF:FF:FF:FF:FF:FF) \\n ARP - Who has - " + nodes[source].Gateway + "? Tell " + nodes[source].IP.split('/')[0] + ";")
        ipdest = nodes[source].Gateway
        myRouter = ""

        for router in routers.values():
            for ip in router.IP:
                if nodes[source].Gateway.strip() in ip.strip():
                    myRouter = router.RouterName


        for i in range(0, len(routers[myRouter].MAC)):
            if ipdest == routers[myRouter].IP[i]:
                print(myRouter + " => " + source + " : ETH (src=" + routers[myRouter].MAC[i] + " dst=" + nodes[source].MAC + ") \\n ARP - " + nodes[source].Gateway + " is at " + routers[myRouter].MAC[i] + ";")
                return routers[myRouter].MAC[i]


def SendICMPSameNet(source, dest, data, off, mf):
    if mf > 0:
        MTU = nodes[source].MTU
        for i in range(0, len(data)//MTU):
            idata = data[off:off+MTU]
            if i == (len(data)//MTU - 1):
                print(source + " => " + dest + " : ETH (src=" + nodes[source].MAC + " dst=" + nodes[dest].MAC + ") \\n IP (src=" + nodes[source].IP + " dst=" + nodes[dest].IP + " ttl=8 mf=0 off=" + str(off) + ") \\n ICMP - Echo request (data=" + idata + ");")
            else:
                print(source + " => " + dest + " : ETH (src=" + nodes[source].MAC + " dst=" + nodes[dest].MAC + ") \\n IP (src=" + nodes[source].IP + " dst=" + nodes[dest].IP + " ttl=8 mf=1 off=" + str(off) + ") \\n ICMP - Echo request (data=" + idata + ");")
            off += MTU

        print(dest +" rbox "+ dest + " : Received "+data+";")
        off = 0

        for i in range(0, len(data)//MTU):
            idata = data[off:off+MTU]
            if i == (len(data)//MTU - 1):
                print(dest + " => " + source + " : ETH (src=" + nodes[dest].MAC + " dst=" + nodes[source].MAC + ") \\n IP (src=" + nodes[dest].IP + " dst=" + nodes[source].IP + " ttl=8 mf=0 off=" + str(off) + ") \\n ICMP - Echo reply (data=" + idata + ");")
            else:
                print(dest + " => " + source + " : ETH (src=" + nodes[dest].MAC + " dst=" + nodes[source].MAC + ") \\n IP (src=" + nodes[dest].IP + " dst=" + nodes[source].IP + " ttl=8 mf=1 off=" + str(off) + ") \\n ICMP - Echo reply (data=" + idata + ");")
            off += MTU
        
        print(source +" rbox "+ source + " : Received "+data+";")
            
    else:
        print(source + " => " + dest + " : ETH (src=" + nodes[source].MAC + " dst=" + nodes[dest].MAC + ") \\n IP (src=" + nodes[source].IP + " dst=" + nodes[dest].IP + " ttl=8 mf=" + str(mf) + " off=" + str(off) + ") \\n ICMP - Echo request (data=" + data + ");")

        print(dest +" rbox "+ dest + " : Received "+data+";")

        print(dest + " => " + source + " : ETH (src=" + nodes[dest].MAC + " dst=" + nodes[source].MAC + ") \\n IP (src=" + nodes[dest].IP + " dst=" + nodes[source].IP + " ttl=8 mf=" + str(mf) + " off=" + str(off) + ") \\n ICMP - Echo reply (data=" + data + ");")

        print(source +" rbox "+ source + " : Received "+data+";")






def SendICMPOtherNet(source, dest, data, off, mf, ttl):
    return NotImplementedError


def main():
    if(len(sys.argv) < 5):
        print("Not enough arguments")
        return
    TopologyParse(sys.argv[1])
    origem = sys.argv[2]
    destino = sys.argv[3]
    mensagem = sys.argv[4]

    # 11000000.10101000.00000000.00000001 
    # 11000000.10101000.00000001.00000001 
    
    inNet = ARP_REQ(origem, destino)

    SendARP(inNet, origem, destino)
    
    if inNet:
        #NIVEL ENLACE
        if len(mensagem) > nodes[origem].MTU:
            SendICMPSameNet(origem, destino, mensagem, 0, 1)
        else:
            SendICMPSameNet(origem, destino, mensagem, 0, 0)
    else:
        return NotImplementedError
        #NIVEL REDE
    
    # get source(n2) ip
    # n1 --> ARP_REQ n1 n2?
    # ta na minha rede? --> gateway
    #     n2 responde
    # senao checar RouterTable
    #     router responde



    
        
    
    

if __name__ == "__main__":
    main()
    
