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

def _start_world(name: str):
	pass

def _start_worlds():
	for world in os.listdir("./worlds"):
		print(world)
		subprocess.run(f"minetest --server --world worlds/{world}")
		

def start():
	"""
	Start all minetest instances and multiserver.
	Exit all process normally then receiving SIGTERM.
	"""
	multiserver_process: Optional[subprocess.Popen] = None
	minetest_processes: List[subprocess.Popen] = {}

	def _on_exit(a,b):
		if multiserver_process:
			multiserver_process.terminate()
		exit(0)

	signal.signal(signal.SIGTERM, _on_exit)
	signal.signal(signal.SIGINT, _on_exit)

	multiserver_process = subprocess.Popen(["./multiserver/mt-multiserver-proxy"])
	print(type(multiserver_process))


git_minetest = "https://github.com/minetest/minetest"
git_irrlicht = "https://github.com/minetest/irrlicht"


def _remove_old_files_server():
	cprint("Removing Old Files....", "green")

	subprocess.run(["rm", "-rf", "./server/minetest"])
	subprocess.run(["rm", "-rf", "./server/irrlichtmt"])


def _hard_build_server():
	cprint("Cloning Minetest....", "green")

	r = subprocess.run(["git", "clone", git_minetest, "./server/minetest"])
	if r != 0:
		cprint("Cloning Failed!", "red")
		exit(1)
	
	cprint("Cloning IrrlichtMT....", "green")

	r = subprocess.run(["git", "clone", git_irrlicht, "./server/irrlicht"])
	if r != 0:
		cprint("Cloning Failed!", "red")
		exit(1)
	
	cprint("Linking IrrlichtMT to Minetest....", "green")

	r = subprocess.run(["ln", "-s", "./server/irrlicht", "./server/minetest/lib/irrlichtmt"])
	if r != 0:
		cprint("Linking failed!", "red")
		exit(1)


def _update_build_server():
	cprint("Updating Minetest....", "green")

	r = subprocess.run(["git", "pull"], cwd="./server/minetest")
	if r != 0:
		cprint("Updating Failed!", "red")
		exit(1)
	
	cprint("Updating IrrlichtMT....", "green")

	r = subprocess.run(["git", "clone", git_irrlicht, "./server/irrlicht"])
	if r != 0:
		cprint("Updating Failed!", "red")
		exit(1)


def _compile_server():
	cprint("Building Minetest....", "green")

	r1 = subprocess.run(["cmake", "./server/minetest -DRUN_IN_PLACE=TRUE"])
	r2 = subprocess.run(["make", "--directory=./server/minetest"])

	if r1 != 0 or r2 != 0:
		cprint("Building Failed!", "red")
		exit(1)

def build_server(update: bool = True):
	if update:
		if os.path.exists("./server/minetest") and os.path.exists("./server/irrlicht"):
			print("update")
			_update_build_server()
			#_compile_server()
		else:
			print("hard")
			_hard_build_server()
			#_compile_server
	else:
		#_remove_old_files_server()
		#_hard_build_server()
		
		_compile_server()
	



fire.Fire({
	"build_server": build_server,
	"start": start,
})