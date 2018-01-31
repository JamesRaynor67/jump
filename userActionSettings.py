import os
import random
import subprocess

posConf = {
	"restart" : {
		"x" : 606,
		"y" : 1568,
	}
}

config = {
	"under_game_score_y": 300,
	"press_coefficient": 1.2,
	"piece_base_height_1_2": 20,
	"piece_body_width": 70,
	"swipe": {
		"x1": 500,
		"y1": 1600,
		"x2": 500,
		"y2": 1602
	}
}

basePath = "C:\\Users\\hong\\Desktop\\playground\\WeChat\\GameAutomaton\\jump\\"

class UserAction():
	@staticmethod
	def do(action):
		if action == "restart":
			UserAction.tap("restart")
		else:
			print("***Something is wrong***")
	
	@staticmethod
	def press(timeLength):
		x = int(random.uniform(800, 1000))
		y = int(random.uniform(800, 1200))
		print("press " + str(x) + " " + str(y) + " for " + str(timeLength))
		cmd = 'adb shell input swipe {x1} {y1} {x2} {y2} {t}'.format(x1=x, y1=y, x2=x, y2=y, t=timeLength)
		subprocess.Popen(cmd).wait()

	@staticmethod
	def tap(option):
		subprocess.Popen('adb shell input tap {0} {1}'.format(posConf[option]['x'],posConf[option]['y'])).wait()

	@staticmethod
	def back():
		subprocess.Popen('adb shell input keyevent 4').wait()