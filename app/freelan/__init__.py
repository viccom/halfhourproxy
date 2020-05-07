#!/usr/bin/python
# -*- coding: UTF-8 -*-
import logging
import threading
import subprocess
import time


class SubFreelan(threading.Thread):
	def __init__(self, passphrase, maxage=1800):
		threading.Thread.__init__(self)
		self._passphrase = passphrase
		self._maxage = maxage
		self._thread_stop = False
		self._startTime = None

	def start(self):
		threading.Thread.start(self)

	def run(self):
		cmd = '/bin/freelan --security.passphrase \"' + self._passphrase + '\" '
		vpnIp = " --tap_adapter.ipv4_address_prefix_length 192.168.212.1/24"
		bandIp = " --fscp.listen_on=0.0.0.0:443"
		startcmd = cmd + vpnIp + bandIp
		self._startTime = int(time.time())
		# print(startcmd)
		subprocess.call(startcmd, shell=True)
		ret = subprocess.call("iptables -t nat -vnL POSTROUTING|grep tap0", shell=True)
		# print(ret)
		if int(ret) != 0:
			self.addrule()
		while not self._thread_stop:
			# print(int(time.time()), self._startTime)
			if (int(time.time()) - self._startTime) > self._maxage:
				break
			time.sleep(1)
		subprocess.call("pkill -9 freelan", shell=True)
		logging.warning("Close SubFreelan!")

	def addrule(self):
		rules = ["/usr/sbin/sysctl -w net.ipv4.ip_forward=1",
		         "/usr/sbin/iptables -t nat -A POSTROUTING -s 192.168.212.0/24 ! -o tap0 -j MASQUERADE",
		         "/usr/sbin/iptables -A FORWARD -i tap0 ! -o tap0 -j ACCEPT",
		         "/usr/sbin/iptables -A FORWARD -o tap0 -j ACCEPT"]
		for rule in rules:
			subprocess.call(rule, shell=True)

	def delrule(self):
		subprocess.call("iptables -t nat -F POSTROUTING", shell=True)

	def status(self):
		pid = bytes.decode(subprocess.check_output("ps -auxf|grep freelan|grep -v grep|awk '{print $2}'", shell=True))
		# pid = 22
		if pid:
			return 'running'
		else:
			return 'stopped'

	def stop(self):
		logging.warning("SubFreelan thread exit!")
		self._thread_stop = True
		self.join()
