from mininet.net import Mininet
from mininet.node import Controller
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import os

def setupFirewallVnf():
	info('*** Adding Docker Firewall VNF\n')
	info('*** Setting up routing to Docker Firewall VNF\n')
	os.system('ovs-docker add-port br0 eth1 vnf_firewall --ipaddress=10.0.0.4/24')
	os.system('docker exec vnf_firewall ip route del default')
	os.system('docker exec vnf_firewall ip route add default via 10.0.0.5')

def setupNatVnf():
	info('*** Adding Docker NAT VNF\n')
	info('*** Setting up routing to Docker NAT VNF\n')
	os.system('ovs-docker add-port br0 eth1 vnf_nat --ipaddress=10.0.0.5/24')

def setupDnsVnf(hosts):
	info('*** Adding Docker DNS VNF\n')
	info('*** Setting up routing to Docker DNS VNF\n')
	os.system('ovs-docker add-port br0 eth1 vnf_dns --ipaddress=10.0.0.6/24')
	os.system('docker exec vnf_firewall ip route del default')
	os.system('docker exec vnf_firewall ip route add default via 10.0.0.5')
	info('*** Setting up DNS on Mininet hosts\n')
	for host in hosts:
		host.cmd("echo 'nameserver 10.0.0.6' >> /etc/resolv.conf")

def topology():
	setLogLevel('info')

	net = Mininet(controller=Controller, link=TCLink)

	info('*** Adding controller\n')
	net.addController('c0')

	info('*** Adding hosts\n')
	host1 = net.addHost('h1', ip='10.0.0.2/24')
	host2 = net.addHost('h2', ip='10.0.0.3/24')

	info('*** Adding switch\n')
	switch = net.addSwitch('s1')

	info('*** Creating links\n')
	net.addLink(host1, switch)
	net.addLink(host2, switch)

	info('*** Starting network\n')
	net.start()

	setupFirewallVnf()
	setupNatVnf()
	setupDnsVnf(net.hosts)
	
	os.system('ip link add veth_mininet type veth peer name veth_br0')

	info('*** Add port veth_mininet to s1\n')
	os.system('ovs-vsctl add-port s1 veth_mininet')
	os.system('ip link set veth_mininet up')

	info('*** Add port veth_br0 to br0\n')
	os.system('ovs-vsctl add-port br0 veth_br0')
	os.system('ip link set veth_br0 up')

	for host in net.hosts:
		host.cmd('ip route add default via 10.0.0.4')

	info('*** Testing network\n')
	CLI(net)

	info('*** Stopping network\n')
	net.stop()

	info('*** Cleanup\n')

	os.system('ovs-vsctl del-port br0 veth_br0')
	os.system('ip link set veth_mininet down')
	os.system('ip link set veth_br0 down')
	os.system('ip link delete veth_mininet')
	os.system('ovs-docker del-port br0 eth1 vnf_nat')
	os.system('ovs-docker del-port br0 eth1 vnf_firewall')
	os.system('ovs-docker del-port br0 eth1 vnf_dns')

if __name__ == '__main__':
	topology()
