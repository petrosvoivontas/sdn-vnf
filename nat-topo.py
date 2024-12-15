from mininet.net import Mininet
from mininet.node import Host, Controller
from mininet.link import Link, TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import os

def topology():
    setLogLevel('info')

    net = Mininet(controller=Controller, link=TCLink)

    info('*** Adding controller\n')
    net.addController('c0')

    info('*** Adding hosts\n')
    host1 = net.addHost('h1', ip='10.0.0.3/24')
    host2 = net.addHost('h2', ip='10.0.0.4/24')

    info('*** Adding switch\n')
    switch = net.addSwitch('s1')

    info('*** Creating links\n')
    net.addLink(host1, switch)
    net.addLink(host2, switch)

    info('*** Starting network\n')
    net.start()

    info('*** Adding Docker NAT VNF\n')
    info('*** Setting up routing to Docker NAT VNF\n')
    
    os.system('ip link add veth_mininet type veth peer name veth_br0')
    os.system('ovs-vsctl add-port s1 veth_mininet')
    os.system('ip link set veth_mininet up')
    os.system('ovs-vsctl add-port br0 veth_br0')
    os.system('ip link set veth_br0 up')

    nat_gateway = '10.0.0.2'
    host1.cmd(f'route add default gw {nat_gateway}')

    info('*** Testing network\n')
    CLI(net)

    info('*** Stopping network\n')
    net.stop()

    info('*** Cleanup\n')

    os.system('ovs-vsctl del-port br0 veth_br0')
    os.system('ip link set veth_mininet down')
    os.system('ip link set veth_br0 down')
    os.system('ip link delete veth_mininet')

if __name__ == '__main__':
    topology()

