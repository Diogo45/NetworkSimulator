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
                print(MACi)
                MACs.append(MACi)
                IPi = routerArgs[3 + 3*i]
                print(IPi)
                IPs.append(IPi)
                MTUi = int(routerArgs[4 + 3*i])
                print(MTUi)
                MTUs.append(MTUi)
            router = Router(RouterName = routerName, NumPorts = numPorts, MAC = MACs, IP = IPs, MTU = MTUs)
            routers[routerName] = router
        elif reading == "ROUTERTABLE":
            tableArgs = line.split(',')
            key = tableArgs[0]
            tableEntry = RouterTableEntry(Dest = tableArgs[1], NextHop = tableArgs[2], Port = int(tableArgs[3]))
            routers[key].RouterTable[tableArgs[1]] = tableEntry

    



def main():
    if(len(sys.argv) < 5):
        print("Not enough arguments")
        return
    TopologyParse(sys.argv[1])
    get source(n1) ip
    get source(n2) ip
    n1 --> ARP_REQ n1 n2?
    ta na minha rede? --> gateway
        n2 responde
    senao checar RouterTable
        router responde





        
    
    

if __name__ == "__main__":
    main()
    
