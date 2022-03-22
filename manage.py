#!/usr/bin/env python3

__author__ = "AFCM"

r"""
Main script of the Hyclone Minetest server
"""

import os
import time
import signal
import subprocess
import requests
import tarfile
import fire
import pathlib
from typing import *
from termcolor import cprint

minetest_path = pathlib.Path("./server/minetest/bin/minetestserver")
mineclone2_path = pathlib.Path("./games/MineClone2")
multiserver_path = pathlib.Path("./multiserver/mt-multiserver-proxy")


###########
#  Utils  #
###########

#print(os.getenv("GOBIN"))


def check_bin_exists(path: pathlib.Path):
	if path.exists() and path.is_file():
		return
	else:
		cprint(str(path) + " doesn't exist!", "red")
		exit(1)


def download_tar(url: str, path: pathlib.Path):
	response = requests.get(url, stream = True)
	file = tarfile.open(fileobj = response.raw, mode = "r|gz")
	file.extractall(path = path)


def _start_world(world: str, out: Optional[int] = None) -> subprocess.Popen:
	return subprocess.Popen(["./server/minetest/bin/minetestserver", "--world", f"./worlds/{world}", "--config", f"./worlds/{world}/minetest.conf", "--logfile", f"./worlds/{world}/debug.txt"], stdout=out, stderr=out)


###############
#  Functions  #
###############

def start(debug: bool = False, monitoring: bool = False):
	"""
	Start multiserver, all minetest instances and monitoring if enabled.
	Exit all process normally then receiving SIGTERM or SIGINT.
	"""
	# TODO: check if all required binaries are installed first

	redis_process: Optional[subprocess.Popen] = None
	multiserver_process: Optional[subprocess.Popen] = None
	minetest_processes: Dict[str, subprocess.Popen] = {}
	prometheus_process: Optional[subprocess.Popen] = None
	grafana_process: Optional[subprocess.Popen] = None

	out = None
	if debug:
		out = None
	else:
		out = subprocess.DEVNULL

	# Signals Handling
	def _on_exit(a,b):
		if multiserver_process:
			cprint("Exiting Multiserver....", "yellow")
			multiserver_process.terminate()
		
		for world in minetest_processes:
			cprint(f"Exiting world {world}....", "yellow")
			minetest_processes[world].terminate()
		
		if prometheus_process:
			cprint("Exiting Prometheus....", "yellow")
			prometheus_process.terminate()
		
		if grafana_process:
			cprint("Exiting Grafana....", "yellow")
			grafana_process.terminate()
		
		if redis_process:
			cprint("Exiting Redis Server....", "yellow")
			subprocess.run(["./database/redis-stable/src/redis-cli", "shutdown"])

		exit(0)

	signal.signal(signal.SIGTERM, _on_exit)
	signal.signal(signal.SIGINT, _on_exit)

	# Starting Redis
	cprint("Starting Redis...", "green")

	redis_process = subprocess.Popen(["./redis-stable/src/redis-server", "./redis.conf"], cwd="./database", stdout=out, stderr=out)

	time.sleep(2)


	# Starting Multiserver
	cprint("Starting Multiserver...", "green")

	multiserver_process = subprocess.Popen(["./multiserver/mt-multiserver-proxy"])


	# Starting individual Minetest worlds
	for world in os.listdir("./worlds"):
		cprint(f"Starting world {world}...", "green")
		minetest_processes[world] = _start_world(world, out)


	# Starting Prometheus and Grafana servers
	if monitoring:
		cprint("Starting Prometheus...", "green")
		prometheus_process = subprocess.Popen(["./prometheus", "--config.file=../prometheus.yml"], cwd="./monitoring/prometheus-2.34.0.linux-amd64/", stdout=out, stderr=out)
		
		cprint("Starting Grafana...", "green")
		grafana_process = subprocess.Popen(["./bin/grafana-server", "--config", "../grafana.ini"], cwd="./monitoring/grafana-8.4.4/", stdout=out, stderr=out)


	while True:
		time.sleep(1)
		if multiserver_process.poll():
			cprint("Multiserver Crashed!", "red")
			exit(1)
		
		for world in minetest_processes:
			r = minetest_processes[world].poll()
			if r != None:
				if r == 0:
					cprint(f"Restarting world {world}...", "green")
					minetest_processes[world] = _start_world(world, out)
					time.sleep(5)
				else:
					cprint(f"World {world} crashed! Restarting...", "red")
					minetest_processes[world] = _start_world(world, out)
					time.sleep(5)
		

def setup(multiserver: bool = False, multiserver_plugins: bool = False, minetest: bool = False, monitoring: bool = False, redis: bool = False, force: bool = False):
	"""
	Setup the server environment
	"""

	if not multiserver and not multiserver_plugins and not minetest and not monitoring and not redis:
		cprint("You must specify which services to setup (see ./manage.py setup --help)", "red")
		exit(1)
	

	if multiserver:
		cprint("Installing Multiserver....", "green")

		r = subprocess.run(["go", "install", "github.com/HimbeerserverDE/mt-multiserver-proxy/cmd/mt-multiserver-proxy@latest"])
		if r.returncode != 0:
			cprint("Installing multiserver failed!", "red")
			exit(1)
	
		#cprint("Linking Multiserver binary....", "green")
		#try:
		#	print(pathlib.Path("~/go/bin/mt-multiserver-proxy").absolute())
		#	multiserver_path.symlink_to(pathlib.Path("~/go/bin/mt-multiserver-proxy").absolute())
		#except FileExistsError:
		#	cprint("The link seems to already exist", "yellow")


	if multiserver_plugins:
		for plugin in os.listdir("./multiserver/plugins_src"):
			cprint(f"Building {plugin} plugin...", "green")

			r = subprocess.run(["go", "build", "-buildmode=plugin", "-o", pathlib.Path("./multiserver/plugins/").absolute()], cwd=f"./multiserver/plugins_src/{plugin}")
			if r.returncode != 0:
				cprint(f"Build of {plugin} failed!", "red")


	if minetest:
		if pathlib.Path("./server/minetest").exists():
			if force:
				cprint("Removing old files...", "yellow")
				subprocess.run(["rm", "-rf", "./server/minetest"])
			else:
				cprint("Minetest 5.4.1 Server is already installed! Force the reinstallation with the --force flag if you really need it.", "red")
				exit(1)
		
		cprint("Installing Minetest dependencies....", "green")

		minetest_depends = [
			"git", "g++", "make", "cmake", "build-essential",
			"libjpeg8-dev", "libpng-dev", "zlib1g-dev", "libopengl-dev",
			"libglx-dev", "libgl1-mesa-dev", "libx11-dev", "libxxf86vm-dev",
			"libvorbis-dev", "libopenal-dev", "libsqlite3-dev", "libluajit-5.1-dev",
			"libjsoncpp-dev", "libgmp-dev", "libcurl4-gnutls-dev", "libfreetype6-dev", "libzstd-dev"
		]
		r = subprocess.run(["sudo", "apt", "install", "-y"] + minetest_depends)
		if r.returncode != 0:
			cprint("Installing dependencies failed!", "red")
			exit(1)
		
		cprint("Cloning Minetest....", "green")

		git_minetest = "https://github.com/minetest/minetest"
		r1 = subprocess.run(["git", "clone", git_minetest, "./server/minetest"])
		r2 = subprocess.run(["git", "checkout", "5.4.1"], cwd="./server/minetest")
		if r1.returncode != 0 or r2.returncode != 0:
			cprint("Cloning Failed!", "red")
			exit(1)

		cprint("Building Minetest....", "green")

		# TODO: enable Prometheus client
		r1 = subprocess.run(["cmake", "-DRUN_IN_PLACE=TRUE", "-DBUILD_SERVER=TRUE", "-DBUILD_CLIENT=FALSE"], cwd="./server/minetest")
		r2 = subprocess.run(["make", "-j$(nproc)"], cwd="./server/minetest", shell=True)

		if r1.returncode != 0 or r2.returncode != 0:
			cprint("Building Failed!", "red")
			exit(1)
		
		cprint("Linking MineClone2...", "green")
		pathlib.Path("./server/minetest/games/MineClone2").symlink_to(mineclone2_path.absolute())

		for mod in os.listdir("./mods"):
			link_path = pathlib.Path(f"./server/minetest/mods/{mod}")
			cprint(f"Linking {mod} mod...", "green")
			link_path.symlink_to(pathlib.Path(f"./mods/{mod}").absolute())



	if monitoring:
		prometheus_url = "https://github.com/prometheus/prometheus/releases/download/v2.34.0/prometheus-2.34.0.linux-amd64.tar.gz"
		grafana_url = "https://dl.grafana.com/oss/release/grafana-8.4.4.linux-amd64.tar.gz"
		monitoring_path = pathlib.Path("./monitoring/")

		if pathlib.Path("./monitoring/prometheus-2.34.0.linux-amd64").exists():
			if force:
				cprint("Old Prometheus files will be overiden...", "yellow")
			else:
				cprint("Prometheus 3.34 is already installed! Force the reinstallation with the --force flag if you are sure this wont cause any data loss.", "red")
				exit(1)
		
		if pathlib.Path("./monitoring/grafana-8.4.4.linux-amd64").exists():
			if force:
				cprint("Old Grafana files will be overiden...", "yellow")
			else:
				cprint("Grafana 8.4.4 is already installed! Force the reinstallation with the --force flag if you are sure this wont cause any data loss.", "red")
				exit(1)


		cprint("Installing Prometheus 2.34....", "green")
		download_tar(prometheus_url, monitoring_path)

		cprint("Installing Grafana 8.4.4....", "green")
		download_tar(grafana_url, monitoring_path)


	if redis:
		redis_url = "http://download.redis.io/redis-stable.tar.gz"
		database_path = pathlib.Path("./database/")

		if pathlib.Path("./database/redis-stable").exists():
			if force:
				cprint("Old Redis files will be overiden...", "yellow")
			else:
				cprint("Redis Stable is already installed! Force the reinstallation with the --force flag if you are sure this wont cause any data loss.", "red")
				exit(1)

		cprint("Installing Redis Stable....", "green")
		download_tar(redis_url, database_path)

		# We put a prefix to not conflict with the system installation
		cprint("Building Redis Stable....", "green")
		subprocess.run(["make"], cwd="./database/redis-stable")

		# https://grafana.com/grafana/plugins/redis-datasource/
		if pathlib.Path("./monitoring/grafana-8.4.4").exists():
			cprint("Grafana found, installing grafana-redis", "green")
			subprocess.run(["./bin/grafana-cli", "--pluginsDir", "./plugins", "plugins", "install", "redis-datasource"], cwd="./monitoring/grafana-8.4.4/")


fire.Fire({
	"setup": setup,
	"start": start,
})