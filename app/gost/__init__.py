#!/usr/bin/python
# -*- coding: UTF-8 -*-
import logging
import threading
import subprocess
import time


class SubGostlan(threading.Thread):
	def __init__(self, passphrase, maxage=1800):
		threading.Thread.__init__(self)
		self._passphrase = passphrase
		self._maxage = maxage
		self._thread_stop = False
		self._startTime = None

	def start(self):
		threading.Thread.start(self)

	def run(self):
		startcmd = 'nohup gost -L tun://AEAD_CHACHA20_POLY1305:' + self._passphrase + '@:8421?net=192.168.212.1/24 &'
		self._startTime = int(time.time())
		# print(startcmd)
		subprocess.call(startcmd, timeout=3, shell=True)
		ret = subprocess.call("iptables -t nat -vnL POSTROUTING|grep tun0", shell=True)
		# print(ret)
		if int(ret) != 0:
			self.addrule()
		while not self._thread_stop:
			# logging.info(str(int(time.time())-self._startTime))
			if (int(time.time()) - self._startTime) > self._maxage:
				break
			time.sleep(1)
		logging.info("kill gost!")
		subprocess.call("pkill -9 gost", timeout=1, shell=True)
		logging.warning("Close SubGostlan!")

	def addrule(self):
		logging.info("add iptables rule!")
		rules = ["/usr/sbin/sysctl -w net.ipv4.ip_forward=1",
		         "/usr/sbin/iptables -t nat -A POSTROUTING -s 192.168.212.0/24 ! -o tun0 -j MASQUERADE",
		         "/usr/sbin/iptables -A FORWARD -i tun0 ! -o tun0 -j ACCEPT",
		         "/usr/sbin/iptables -A FORWARD -o tun0 -j ACCEPT"]
		for rule in rules:
			subprocess.call(rule, timeout=2, shell=True)

	def delrule(self):
		subprocess.call("iptables -t nat -F POSTROUTING", timeout=2, shell=True)

	def status(self):
		pid = bytes.decode(subprocess.check_output("ps -auxf|grep gost|grep -v grep|awk '{print $2}'", timeout=2, shell=True))
		# pid = 22
		if pid:
			return 'running'
		else:
			return 'stopped'

	def stop(self):
		logging.warning("SubGostlan thread exit!")
		self._thread_stop = True
		self.join()
