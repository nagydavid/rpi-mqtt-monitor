# -*- coding: utf-8 -*-
# Python (runs on 2 and 3) script to check cpu load, cpu temperature and free space,
# on a Raspberry Pi computer and publish the data to a MQTT server.
# RUN pip install paho-mqtt
# RUN sudo apt-get install python-pip

from __future__ import division
import subprocess, time, socket
import speedtest
import paho.mqtt.client as paho
import json
import config
import psutil
from datetime import datetime
from getmac import get_mac_address as gma

hostname = socket.gethostname()


def check_used_space(path):
		return psutil.disk_usage('/')[3]

def check_cpu_load():
		return psutil.cpu_percent()

def check_voltage():
		full_cmd = "vcgencmd measure_volts | cut -f2 -d= | sed 's/000//'"
		voltage = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
		voltage = voltage.strip()[:-1]
		return voltage

def check_swap():
		return psutil.swap_memory()[3]

def check_memory():
		return psutil.virtual_memory()[2]

def check_cpu_temp():
		return psutil.sensors_temperatures()["cpu_thermal"][0][1]

def check_sys_clock_speed():
		return psutil.cpu_freq()[0]

def check_uptime():
	delta_time = time.time()-psutil.boot_time()
	delta = time.gmtime(delta_time)
	uptime = str(delta[2]-1) + "d " + str(delta[3]) + "h " + str(delta[4]) + "m"
	return uptime

def check_network_up():
    net_up = psutil.net_io_counters()[0]*10**-9
    return round(net_up,2)


def check_network_down():
    net_down = psutil.net_io_counters()[1]*10**-9
    return round(net_down,2)

def check_wifi_rssi():
    full_cmd = "sudo iwconfig wlan0 | grep Link"
    rssi = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
    rssi = int(rssi.decode('utf-8').split("  Signal level=")[1].split(" dBm")[0])
    return rssi

def check_speedtest_down():
    speed = speedtest.Speedtest()
    Dspeed = speed.download()/1024/1024
    return round(Dspeed,0)

def check_speedtest_up():
    speed = speedtest.Speedtest()
    Uspeed = speed.upload()/1024/1024
    return round(Uspeed,0)

def config_json(what_config):
		data = {
		    "device": {
                    "identifiers": [gma()],
                "manufacturer" : "Raspberry Pi Foundation",
                "model" : subprocess.getoutput("cat /proc/cpuinfo | grep Model").split(": ")[1],
                "name" : hostname
		    },
			"state_topic": "",
			"icon": "",
			"name": "",
			"unique_id": "",
			"unit_of_measurement": "",
		}
		
		data["state_topic"] = config.mqtt_topic_prefix+"/"+hostname+"/"+what_config
		data["unique_id"] = hostname+"_"+what_config
		if what_config == "cpuload":
			data["icon"] = "mdi:speedometer"
			data["name"] = hostname + " CPU Usage"
			data["unit_of_measurement"] = "%"
		elif what_config == "cputemp":
			data["icon"] = "hass:thermometer"
			data["name"] = hostname + " CPU Temperature"
			data["unit_of_measurement"] = "°C"
		elif what_config == "diskusage":
			data["icon"] = "mdi:harddisk"
			data["name"] = hostname + " Disk Usage"
			data["unit_of_measurement"] = "%"
		elif what_config == "voltage":
			data["icon"] = "mdi:speedometer"
			data["name"] = hostname + " CPU Voltage"
			data["unit_of_measurement"] = "V"
		elif what_config == "swap":
			data["icon"] = "mdi:harddisk"
			data["name"] = hostname + " Disk Swap"
			data["unit_of_measurement"] = "%"
		elif what_config == "memory":
			data["icon"] = "mdi:memory"
			data["name"] = hostname + " Memory Usage"
			data["unit_of_measurement"] = "%"
		elif what_config == "sys_clock_speed":
			data["icon"] = "mdi:speedometer"
			data["name"] = hostname + " CPU Clock Speed"
			data["unit_of_measurement"] = "MHz"
		elif what_config == "uptime":
			data["icon"] = "mdi:timer-outline"
			data["name"] = hostname + " Uptime"
			data["unit_of_measurement"] = ""
		elif what_config == "network_up":
			data["icon"] = "mdi:upload-network"
			data["name"] = hostname + " Network Upload"
			data["unit_of_measurement"] = "Gb"
		elif what_config == "network_down":
			data["icon"] = "mdi:download-network"
			data["name"] = hostname + " Network Download"
			data["unit_of_measurement"] = "Gb"
		elif what_config == "wifi_rssi":
			data["icon"] = "mdi:wifi"
			data["name"] = hostname + " Wifi RSSI"
			data["unit_of_measurement"] = "dBm"
		elif what_config == "speedtest_up":
			data["icon"] = "mdi:upload-network-outline"
			data["name"] = hostname + " Upload Speed"
			data["unit_of_measurement"] = "Mbit/s"
		elif what_config == "speedtest_down":
			data["icon"] = "mdi:download-network-outline"
			data["name"] = hostname + " Download Speed"
			data["unit_of_measurement"] = "Mbit/s"

		else:
			return ""
		# Return our built discovery config
		return json.dumps(data)
	
def publish_to_mqtt (cpu_load = 0, cpu_temp = 0, used_space = 0, voltage = 0,
 sys_clock_speed = 0, swap = 0, memory = 0, uptime = "", network_up = 0 , 
 network_down = 0, wifi_rssi = 0,speedtest_up = 0, speedtest_down = 0):
		# connect to mqtt server
		client = paho.Client()
		client.username_pw_set(config.mqtt_user, config.mqtt_password)
		client.connect(config.mqtt_host, int(config.mqtt_port))

		# publish monitored values to MQTT
		if config.cpu_load:
			if config.discovery_messages:
				client.publish("homeassistant/sensor/"+config.mqtt_topic_prefix+"/"+hostname+"_cpuload/config", config_json('cpuload'), qos=0)
				time.sleep(config.sleep_time)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/cpuload", cpu_load, qos=1)
			time.sleep(config.sleep_time)

		if config.cpu_temp:
			if config.discovery_messages:
				client.publish("homeassistant/sensor/"+config.mqtt_topic_prefix+"/"+hostname+"_cputemp/config", config_json('cputemp'), qos=0)
				time.sleep(config.sleep_time)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/cputemp", cpu_temp, qos=1)
			time.sleep(config.sleep_time)

		if config.used_space:
			if config.discovery_messages:
				client.publish("homeassistant/sensor/"+config.mqtt_topic_prefix+"/"+hostname+"_diskusage/config", config_json('diskusage'), qos=0)
				time.sleep(config.sleep_time)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/diskusage", used_space, qos=1)
			time.sleep(config.sleep_time)

		if config.voltage:
			if config.discovery_messages:
				client.publish("homeassistant/sensor/"+config.mqtt_topic_prefix+"/"+hostname+"_voltage/config", config_json('voltage'), qos=0)
				time.sleep(config.sleep_time)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/voltage", voltage, qos=1)
			time.sleep(config.sleep_time)

		if config.swap:
			if config.discovery_messages:
				client.publish("homeassistant/sensor/"+config.mqtt_topic_prefix+"/"+hostname+"_swap/config", config_json('swap'), qos=0)
				time.sleep(config.sleep_time)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/swap", swap, qos=1)
			time.sleep(config.sleep_time)

		if config.memory:
			if config.discovery_messages:
				client.publish("homeassistant/sensor/"+config.mqtt_topic_prefix+"/"+hostname+"_memory/config", config_json('memory'), qos=0)
				time.sleep(config.sleep_time)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/memory", memory, qos=1)
			time.sleep(config.sleep_time)

		if config.sys_clock_speed:
			if config.discovery_messages:
				client.publish("homeassistant/sensor/"+config.mqtt_topic_prefix+"/"+hostname+"_sys_clock_speed/config", config_json('sys_clock_speed'), qos=0)
				time.sleep(config.sleep_time)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/sys_clock_speed", sys_clock_speed, qos=1)
			time.sleep(config.sleep_time)

		if config.uptime:
			if config.discovery_messages:
				client.publish("homeassistant/sensor/"+config.mqtt_topic_prefix+"/"+hostname+"_uptime/config", config_json('uptime'), qos=0)
				time.sleep(config.sleep_time)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/uptime", uptime, qos=1)
			time.sleep(config.sleep_time)

		if config.network_up:
			if config.discovery_messages:
				client.publish("homeassistant/sensor/"+config.mqtt_topic_prefix+"/"+hostname+"_network_up/config", config_json('network_up'), qos=0)
				time.sleep(config.sleep_time)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/network_up", network_up, qos=1)
			time.sleep(config.sleep_time)

		if config.network_down:
			if config.discovery_messages:
				client.publish("homeassistant/sensor/"+config.mqtt_topic_prefix+"/"+hostname+"_network_down/config", config_json('network_down'), qos=0)
				time.sleep(config.sleep_time)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/network_down", network_down, qos=1)
			time.sleep(config.sleep_time)

		if config.wifi_rssi:
			if config.discovery_messages:
				client.publish("homeassistant/sensor/"+config.mqtt_topic_prefix+"/"+hostname+"_wifi_rssi/config", config_json('wifi_rssi'), qos=0)
				time.sleep(config.sleep_time)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/wifi_rssi", wifi_rssi, qos=1)
			time.sleep(config.sleep_time)

		if config.speedtest_up:
			if config.discovery_messages:
				client.publish("homeassistant/sensor/"+config.mqtt_topic_prefix+"/"+hostname+"_speedtest_up/config", config_json('speedtest_up'), qos=0)
				time.sleep(config.sleep_time)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/speedtest_up", speedtest_up, qos=1)
			time.sleep(config.sleep_time)

		if config.speedtest_down:
			if config.discovery_messages:
				client.publish("homeassistant/sensor/"+config.mqtt_topic_prefix+"/"+hostname+"_speedtest_down/config", config_json('speedtest_down'), qos=0)
				time.sleep(config.sleep_time)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/speedtest_down", speedtest_down, qos=1)
			time.sleep(config.sleep_time)
		
		# disconect from mqtt server
		client.disconnect()

def bulk_publish_to_mqtt (cpu_load = 0, cpu_temp = 0, used_space = 0, voltage = 0,
 sys_clock_speed = 0, swap = 0, memory = 0, uptime = "", network_up = 0 , 
 network_down = 0, wifi_rssi = 0,speedtest_up = 0, speedtest_down = 0):
		# compose the CSV message containing the measured values
		values = cpu_load, float(cpu_temp), used_space, float(voltage), int(sys_clock_speed), swap, memory, uptime, network_up, network_down, wifi_rssi, speedtest_up, speedtest_down
		values = str(values)[1:-1]

		# connect to mqtt server
		client = paho.Client()
		client.username_pw_set(config.mqtt_user, config.mqtt_password)
		client.connect(config.mqtt_host, int(config.mqtt_port))

		# publish monitored values to MQTT
		client.publish(config.mqtt_topic_prefix+"/"+hostname, values, qos=1)

		# disconect from mqtt server
		client.disconnect()

if __name__ == '__main__':
		# set all monitored values to False in case they are turned off in the config
		cpu_load = cpu_temp = used_space = voltage = sys_clock_speed = swap = memory = uptime = network_up = network_down = wifi_rssi = speedtest_up = speedtest_down = False

		# delay the execution of the script
		time.sleep(config.random_delay)

		# collect the monitored values
		if config.cpu_load:
			cpu_load = check_cpu_load()
		if config.cpu_temp:
			cpu_temp = check_cpu_temp()
		if config.used_space:
			used_space = check_used_space('/')
		if config.voltage:
			voltage = check_voltage()
		if config.sys_clock_speed:
			sys_clock_speed = check_sys_clock_speed()
		if config.swap:
			swap = check_swap()
		if config.memory:
			memory = check_memory()
		if config.uptime:
			uptime = check_uptime()
		if config.network_up:
			network_up = check_network_up()
		if config.network_down:
			network_down = check_network_down()
		if config.wifi_rssi:
			wifi_rssi = check_wifi_rssi()
		if datetime.now().minute in list(range(0,60,config.speedtest_freq)):
			if config.speedtest_up:
				speedtest_up = check_speedtest_up()		
			if config.speedtest_down:
				speedtest_down = check_speedtest_down()
			speed_dict = {'speed_down':speedtest_down,'speed_up':speedtest_up}
			with open("/home/pi/rpi-mqtt-monitor/speedtest.json", "w") as outfile:
				json.dump(speed_dict, outfile)
			outfile.close()		
		else:
			f = open('/home/pi/rpi-mqtt-monitor/speedtest.json',)
			data = json.load(f)
			if config.speedtest_up:
				speedtest_up = data['speed_up']
			if config.speedtest_down:
				speedtest_down = data['speed_down']
			f.close()
					
		# Publish messages to MQTT
		if config.group_messages:
			bulk_publish_to_mqtt(cpu_load, cpu_temp, used_space, voltage, sys_clock_speed, swap, memory, uptime,network_up,network_down, wifi_rssi, speedtest_up,speedtest_down)
		else:
			publish_to_mqtt(cpu_load, cpu_temp, used_space, voltage, sys_clock_speed, swap, memory, uptime, network_up,network_down, wifi_rssi, speedtest_up,speedtest_down)