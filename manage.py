#!/usr/bin/env python3

__author__ = "AFCM"

r"""
Main script of the Hyclone Minetest server
"""

import os
import time
import signal
import subprocess
import fire
import pathlib
from typing import *
from termcolor import cprint

minetest_path = pathlib.Path("./server/minetest/bin/minetestserver")
mineclone2_path = pathlib.Path("./games/MineClone2")


def _start_world(world: str) -> subprocess.Popen:
	return subprocess.Popen(["minetest","--server", "--world", f"./worlds/{world}", "--config", f"./worlds/{world}/minetest.conf", "--logfile", f"./worlds/{world}/debug.txt"])


def start():
	"""
	Start all minetest instances and multiserver.
	Exit all process normally then receiving SIGTERM or SIGINT.
	"""
	multiserver_process: Optional[subprocess.Popen] = None
	minetest_processes: Dict[str, subprocess.Popen] = {}

	def _on_exit(a,b):
		cprint("Exiting Multiserver....", "yellow")
		if multiserver_process:
			multiserver_process.terminate()
		
		for world in minetest_processes:
			cprint(f"Exiting world {world}....", "yellow")
			minetest_processes[world].terminate()

		exit(0)

	signal.signal(signal.SIGTERM, _on_exit)
	signal.signal(signal.SIGINT, _on_exit)

	cprint("Starting Multiserver...", "green")

	multiserver_process = subprocess.Popen(["./multiserver/mt-multiserver-proxy"])

	for world in os.listdir("./worlds"):
		cprint(f"Starting world {world}...", "green")
		minetest_processes[world] = _start_world(world)

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
					minetest_processes[world] = _start_world(world)
					time.sleep(5)
				else:
					cprint(f"World {world} crashed! Restarting...", "red")
					minetest_processes[world] = _start_world(world)
					time.sleep(5)
		

git_minetest = "https://github.com/minetest/minetest"
git_irrlicht = "https://github.com/minetest/irrlicht"


def _remove_old_files_server():
	cprint("Removing Old Files....", "green")

	subprocess.run(["rm", "-rf", "./server/minetest"])
	subprocess.run(["rm", "-rf", "./server/irrlicht"])


def _hard_build_server():
	cprint("Cloning Minetest....", "green")

	r = subprocess.run(["git", "clone", git_minetest, "./server/minetest"])
	if r.returncode != 0:
		cprint("Cloning Failed!", "red")
		exit(1)
	
	cprint("Cloning IrrlichtMT....", "green")

	r = subprocess.run(["git", "clone", git_irrlicht, "./server/minetest/lib/irrlichtmt"])
	if r.returncode != 0:
		cprint("Cloning Failed!", "red")
		exit(1)


def _update_build_server():
	cprint("Updating Minetest....", "green")

	r = subprocess.run(["git", "pull"], cwd="./server/minetest")
	if r.returncode != 0:
		cprint("Updating Failed!", "red")
		exit(1)
	
	cprint("Updating IrrlichtMT....", "green")

	r = subprocess.run(["git", "pull"], cwd="./server/minetest/lig/irrlichtmt")
	if r.returncode != 0:
		cprint("Updating Failed!", "red")
		exit(1)

	subprocess.run(["git", "checkout", "5.5.0"], cwd="./server/minetest")


def _link_game_server():
	link_minetest = pathlib.Path("./server/minetest/games/MineClone2")
	link_multiserver = pathlib.Path("./multiserver/games/MineClone2")

	if not link_minetest.exists():
		pathlib.Path("./server/minetest/games/MineClone2").symlink_to(mineclone2_path.absolute())
	#if not link_multiserver.exists():
	#	pathlib.Path("./multiserver/games/MineClone2").symlink_to(mineclone2_path.absolute())
	# TODO: link mods


def _compile_server():
	"""
	Compile the files contained in ./server/minetest
	"""
	cprint("Building Minetest....", "green")

	r1 = subprocess.run(["cmake", "-DRUN_IN_PLACE=TRUE", "-DBUILD_SERVER=TRUE", "-DBUILD_CLIENT=FALSE"], cwd="./server/minetest")
	r2 = subprocess.run(["make", "-j$(nproc)"], cwd="./server/minetest", shell=True)

	if r1.returncode != 0 or r2.returncode != 0:
		cprint("Building Failed!", "red")
		exit(1)


def build_server(update: bool = True):
	"""
	Build the Minetest server
	"""
	if update:
		if os.path.exists("./server/minetest") and os.path.exists("./server/minetest/lib/irrlichtmt"):
			_update_build_server()
			_compile_server()
		else:
			_hard_build_server()
			_compile_server
	else:
		_remove_old_files_server()
		_hard_build_server()
		
		_compile_server()
	



fire.Fire({
	"build_server": build_server,
	"start": start,
	"link": _link_game_server, # TEMP
})