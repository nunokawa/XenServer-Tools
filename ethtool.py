#!/usr/bin/python
# -*- coding: utf-8 -*-

import popen2
import sys

xe = "/opt/xensource/bin/xe"
ethtool = "/sbin/ethtool"

### XAPI other-configマップからethtoolコマンドの引数への変換テーブルを設定する。
###
ethtool_opts = {'ethtool-speed': 'speed', 'ethtool-duplex': 'duplex', 'ethtool-autoneg': 'autoneg'}
ethtool_offload = {'ethtool-rx': 'rx', 'ethtool-tx': 'tx', 'ethtool-sg': 'sg', 'ethtool-tso': 'tso', 'ethtool-ufo': 'ufo', 'ethtool-gso': 'gso'}


### 引数deviceで指定したPIFのother-configマップを取得し、
### キーと設定値を、引数cfgに代入する。
### 設定値"true"は"on"、"false"は"off"に変換し、ethtoolコマンドの引数にあわせる。
###
def split_other_config(cfg,device):
	cmdline = xe + " pif-list device=" + device + " params=uuid --minimal"
	(stdout, stdin) = popen2.popen2(cmdline)
	uuid = stdout.read().rstrip()
	cmdline = xe + " pif-list uuid=" + uuid + " params=other-config --minimal"
	(stdout, stdin) = popen2.popen2(cmdline)
	p = stdout.read().rstrip()
	if len(p) != 0:
		p = p.split(';')

		for str in p:
			(key, value) = str.strip().split(':')
			value = value.strip()
			if value == "true":
				value = "on"
			if value == "false":
				value = "off"
			cfg[key] = value


### 引数cfgより取得したother-configマップのキーおよび設定値を元に、
### ethtoolコマンドの引数を生成する。
### Speed,Duplex,AutoNegotiationの設定とOffload設定ではオプション指定が異なるため、
### それぞれの引数を生成する。
###
def set_ethtool_opts(cfg):
	opts = ''
	offload = ''
	for key, value in cfg.items():
		if ethtool_opts.has_key(key):
			opts = opts + ethtool_opts[key] + " " + value + " "
	for key, value in cfg.items():
		if ethtool_offload.has_key(key):
			offload = offload + ethtool_offload[key] + " " + value + " "

	return opts,offload


### コマンドライン引数に"-n"が指定された場合はデバッグモードで実行する。
###
if len(sys.argv) > 1 and sys.argv[1] == "-n":
	debug = True
else:
	debug = False


### XenServerホストのPIF(物理NIC)一覧を取得する。
###
cmdline = xe + " pif-list params=device --minimal"
(stdout, stdin) = popen2.popen2(cmdline)
devices = stdout.read().rstrip()
devices = devices.split(',')


### PIF毎に、other-configマップの取得とethtoolコマンド引数の生成を行う。
### デバッグモードの場合は、ethtoolコマンド実行の表示のみ行う。
###
for device in devices:
	other_config = {}
	split_other_config(other_config,device)
	if len(other_config) != 0:
		opts,offload =  set_ethtool_opts(other_config)
		if opts != '':
			cmdline = ethtool + " -s " + device + " " + opts
			if debug:
				print cmdline
			else:
				popen2.popen2(cmdline)
		else:
			cmdline = ethtool + " -s " + device + " autoneg on"
			if debug:
				print cmdline
			else:
				popen2.popen2(cmdline)
		if offload != '':
			cmdline = ethtool + " -K " + device + " " + offload
			if debug:
				print cmdline
			else:
				popen2.popen2(cmdline)
	else:
		cmdline = ethtool + " -s " + device + " autoneg on"
		if debug:
			print cmdline
		else:
			popen2.popen2(cmdline)
