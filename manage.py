#!/usr/bin/env python3

__author__ = "AFCM"

r"""
Main script of the Hyclone Minetest server
"""

import os
import signal
import subprocess
import fire
import pathlib
from typing import *
from termcolor import cprint

minetest_path = pathlib.Path("server/minetest/bin/minetest")

def _start_world(name: str):
	pass

def _start_worlds():
	if not minetest_path.exists():
		cprint("Minetest Server isn't build yet!", "red")
		exit(1)
	for world in os.listdir("./worlds"):
		print(world)
		subprocess.run(f"{minetest_path} --server --world worlds/{world}")
		

def start():
	"""
	Start all minetest instances and multiserver.
	Exit all process normally then receiving SIGTERM.
	"""
	multiserver_process: Optional[subprocess.Popen] = None
	minetest_processes: List[subprocess.Popen] = {}

	def _on_exit(a,b):
		cprint("Exiting Multiserver....", "yellow")
		if multiserver_process:
			multiserver_process.terminate()
		exit(0)

	signal.signal(signal.SIGTERM, _on_exit)
	signal.signal(signal.SIGINT, _on_exit)

	multiserver_process = subprocess.Popen(["./multiserver/mt-multiserver-proxy"])
	while True:
		if multiserver_process.poll():
			exit(1)


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

	r = subprocess.run(["git", "clone", git_irrlicht, "./server/irrlicht"])
	if r.returncode != 0:
		cprint("Updating Failed!", "red")
		exit(1)

def _link_game_server():
	subprocess.run(["ln", "-s", "./games/MineClone2", "./server/minetest/games/MineClone2"])

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
		if os.path.exists("./server/minetest") and os.path.exists("./server/irrlicht"):
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
})