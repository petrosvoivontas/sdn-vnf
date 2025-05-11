from mininet.net import Mininet
from mininet.node import Host, Controller
from mininet.link import Link, TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import os

def setupRouterVnf(router_default_route):
	eth1Ip = '10.0.0.2'
	eth2Ip = '10.0.1.2'

	info('*** Adding Docker Router VNF\n')
	info('*** Setting up routing to Docker Router VNF\n')
	os.system('ovs-docker add-port br0 eth1 vnf_frr --ipaddress={}/24'.format(eth1Ip))
	os.system('ovs-docker add-port br1 eth2 vnf_frr --ipaddress={}/24'.format(eth2Ip))

	# route traffic to the firewall VNF
	os.system('docker exec vnf_frr ip route del default')
	os.system('docker exec vnf_frr ip route add default via {}'.format(router_default_route))

	return (eth1Ip, eth2Ip)

def setupFirewallVnf(firewall_default_route, prev_vnf_ip):
	eth1Ip = '10.0.0.3'

	info('*** Adding Docker Firewall VNF\n')
	info('*** Setting up routing to Docker Firewall VNF\n')
	os.system('ovs-docker add-port br0 eth1 vnf_firewall --ipaddress={}/24'.format(eth1Ip))

	# route traffic to the NAT VNF
	os.system('docker exec vnf_firewall ip route del default')
	os.system('docker exec vnf_firewall ip route add default via {}'.format(firewall_default_route))

	# route packets from the 2nd subnet back the VNF chain
	subnet2IpRange = '10.0.1.0/24'
	subnet2Gateway = prev_vnf_ip
	subnet2IpRouteCmd = 'ip route add {} via {} dev eth1'.format(subnet2IpRange, subnet2Gateway)
	os.system('docker exec vnf_firewall {}'.format(subnet2IpRouteCmd))

	return eth1Ip

def setupNatVnf(prev_vnf_ip):
	eth1Ip = '10.0.0.4'

	info('*** Adding Docker NAT VNF\n')
	info('*** Setting up routing to Docker NAT VNF\n')
	os.system('ovs-docker add-port br0 eth1 vnf_nat --ipaddress={}/24'.format(eth1Ip))

	# route packets from the 2nd subnet back the VNF chain
	subnet2IpRange = '10.0.1.0/24'
	subnet2Gateway = prev_vnf_ip
	subnet2IpRouteCmd = 'ip route add {} via {} dev eth1'.format(subnet2IpRange, subnet2Gateway)
	os.system('docker exec vnf_nat {}'.format(subnet2IpRouteCmd))

	return eth1Ip

def topology():
	setLogLevel('info')

	net = Mininet(controller=Controller, link=TCLink)

	info('*** Adding controller\n')
	net.addController('c0')

	info('*** Adding hosts\n')
	host1 = net.addHost('h1', ip='10.0.0.5/24')
	host2 = net.addHost('h2', ip='10.0.0.6/24')
	host3 = net.addHost('h3', ip='10.0.1.3/24')

	info('*** Adding switch\n')
	switch = net.addSwitch('s1')

	info('*** Creating links\n')
	net.addLink(host1, switch)
	net.addLink(host2, switch)
	net.addLink(host3, switch)

	info('*** Starting network\n')
	net.start()

	natIp = setupNatVnf(prev_vnf_ip='10.0.0.3')
	firewallIp = setupFirewallVnf(firewall_default_route=natIp, prev_vnf_ip='10.0.0.2')
	(defaultRouteForEth1, defaultRouteForEth2) = setupRouterVnf(router_default_route=firewallIp)
	
	os.system('ip link add veth_mininet type veth peer name veth_br0')

	info('*** Add port veth_mininet to s1\n')
	os.system('ovs-vsctl add-port s1 veth_mininet')
	os.system('ip link set veth_mininet up')

	info('*** Add port veth_br0 to br0\n')
	os.system('ovs-vsctl add-port br0 veth_br0')
	os.system('ip link set veth_br0 up')

	os.system('ip link add veth_mininet1 type veth peer name veth_br1')

	info('*** Add port veth_mininet1 to s1\n')
	os.system('ovs-vsctl add-port s1 veth_mininet1')
	os.system('ip link set veth_mininet1 up')

	info('*** Add port veth_br1 to br1\n')
	os.system('ovs-vsctl add-port br1 veth_br1')
	os.system('ip link set veth_br1 up')

	host1.cmd("ip route add default via {}".format(defaultRouteForEth1))
	host2.cmd("ip route add default via {}".format(defaultRouteForEth1))
	host3.cmd("ip route add default via {}".format(defaultRouteForEth2))

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
	os.system('ovs-docker del-port br0 eth1 vnf_frr')

	os.system('ovs-vsctl del-port br1 veth_br1')
	os.system('ip link set veth_mininet1 down')
	os.system('ip link set veth_br1 down')
	os.system('ip link delete veth_mininet1')
	os.system('ovs-docker del-port br1 eth2 vnf_frr')

if __name__ == '__main__':
	topology()
