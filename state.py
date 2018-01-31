import os
import time
import random
import math
import subprocess
import shutil
from userActionSettings import UserAction
from userActionSettings import posConf
from userActionSettings import config
from userActionSettings import basePath
from PIL import Image

class GameState():
	def __init__(self, initState):
		# This list must be set by hand in code according to different games,
		# and rest state classes are the same.
		# It denotes the state of game and controls the flow of operation,
		# which is extremly important.
		# Usually it contains: 'Start', 'InGame', 'End', etc.
		# We can also define sub-state in a high-level state.abs
		# For example, we can define 'GetInput', 'PostAction' in 'InGame'
		self.stateList = ['InGame', 'End']
		self.currentState = initState
	
	def getMessage(self, message):
		# message is also different according to different games.
		# subState can be inside xxxStrategy or yyyStrategy etc.
		# response is the result gives to same level, usually it's None.
		# reply is the result gives to higher level.

		# do something with message
		#
		# if currentState is 'xxx':
		#     response, nextState = xxxStrategy(message)
		# elif currentState is 'yyy':
		#     response, nextState = yyyStrategy(message)
		# elif currentState is 'zzz':
		#     response, nextState = zzzStrategy(message)
		# 
		# do something with response
		# currentState = nextState
		# return replyMessage

		# In this exact program, message is an integer from 0 to indicate 
		# the screenshot of device. And only two states exist.
		if self.currentState == 'InGame':
			response, nextState = self.inGameStrategy(message)
		elif self.currentState == 'End':
			response, nextState = self.endStrategy(message)
		self.currentState = nextState

		# reply message is simply, just keeping request next image
		replyMessage = "request next image"
		return replyMessage

	def inGameStrategy(self, message):

		print("State: InGame")
		imgIndex = message
		image = readImg(imgIndex)

		if isGameEnd(image):
			nextState = "End"
		else:
			currentPos, nextPos = getCurAndNextPos(image)
			pressTime = calculatePressTime(currentPos, nextPos)
			UserAction.press(pressTime)
			nextState = "InGame"
		
		print("Next state: " + nextState + '\n')
		response = None
		return response, nextState
	
	def endStrategy(self, message):

		print('本局结束，开始下局')
		time.sleep(15)
		UserAction.do('restart')

		response = None
		nextState = "InGame"
		return response, nextState

def readImg(index):
	global basePath
	image = Image.open(basePath + str(index) + '.png')
	return image

def isGameEnd(image):
	# if gray value of top right corner becomes too dark, we think game is end
	width, height = image.size
	topRightPixel = image.getpixel((width-1, 0))
	if topRightPixel[0] + topRightPixel[0] + topRightPixel[0] < 180:
		return True
	else:
		return False

def calculatePressTime(currentPos, nextPos):
	distance = math.sqrt((currentPos[0] - nextPos[0]) ** 2 + (currentPos[1] - nextPos[1]) ** 2)
	press_time = distance * config['press_coefficient']
	press_time = max(press_time, 200)   # 设置 200ms 是最小的按压时间
	press_time = int(press_time)
	return press_time

# This function is copied from 
# https://github.com/wangshub/wechat_jump_game/blob/master/wechat_jump_auto.py
# It should be able to be refined
def getCurAndNextPos(im):
	"""
	寻找关键坐标
	"""
	w, h = im.size

	piece_x_sum = 0
	piece_x_c = 0
	piece_y_max = 0
	board_x = 0
	board_y = 0
	scan_x_border = int(w / 8)  # 扫描棋子时的左右边界
	scan_start_y = 0  # 扫描的起始 y 坐标
	im_pixel = im.load()
	# 以 50px 步长，尝试探测 scan_start_y
	for i in range(int(h / 3), int(h*2 / 3), 50):
		last_pixel = im_pixel[0, i]
		for j in range(1, w):
			pixel = im_pixel[j, i]
			# 不是纯色的线，则记录 scan_start_y 的值，准备跳出循环
			if pixel != last_pixel:
				scan_start_y = i - 50
				break
		if scan_start_y:
			break
	print('scan_start_y: {}'.format(scan_start_y))

	# 从 scan_start_y 开始往下扫描，棋子应位于屏幕上半部分，这里暂定不超过 2/3
	for i in range(scan_start_y, int(h * 2 / 3)):
		# 横坐标方面也减少了一部分扫描开销
		for j in range(scan_x_border, w - scan_x_border):
			pixel = im_pixel[j, i]
			# 根据棋子的最低行的颜色判断，找最后一行那些点的平均值，这个颜
			# 色这样应该 OK，暂时不提出来
			if (50 < pixel[0] < 60) \
					and (53 < pixel[1] < 63) \
					and (95 < pixel[2] < 110):
				piece_x_sum += j
				piece_x_c += 1
				piece_y_max = max(i, piece_y_max)

	if not all((piece_x_sum, piece_x_c)):
		return 0, 0, 0, 0
	piece_x = int(piece_x_sum / piece_x_c)
	piece_y = piece_y_max - config["piece_base_height_1_2"]  # 上移棋子底盘高度的一半

	# 限制棋盘扫描的横坐标，避免音符 bug
	if piece_x < w/2:
		board_x_start = piece_x
		board_x_end = w
	else:
		board_x_start = 0
		board_x_end = piece_x

	for i in range(int(h / 3), int(h * 2 / 3)):
		last_pixel = im_pixel[0, i]
		if board_x or board_y:
			break
		board_x_sum = 0
		board_x_c = 0

		for j in range(int(board_x_start), int(board_x_end)):
			pixel = im_pixel[j, i]
			# 修掉脑袋比下一个小格子还高的情况的 bug
			if abs(j - piece_x) < config["piece_body_width"]:
				continue

			# 修掉圆顶的时候一条线导致的小 bug，这个颜色判断应该 OK，暂时不提出来
			if abs(pixel[0] - last_pixel[0]) \
					+ abs(pixel[1] - last_pixel[1]) \
					+ abs(pixel[2] - last_pixel[2]) > 10:
				board_x_sum += j
				board_x_c += 1
		if board_x_sum:
			board_x = board_x_sum / board_x_c
	last_pixel = im_pixel[board_x, i]

	# 从上顶点往下 +274 的位置开始向上找颜色与上顶点一样的点，为下顶点
	# 该方法对所有纯色平面和部分非纯色平面有效，对高尔夫草坪面、木纹桌面、
	# 药瓶和非菱形的碟机（好像是）会判断错误
	for k in range(i+274, i, -1):  # 274 取开局时最大的方块的上下顶点距离
		pixel = im_pixel[board_x, k]
		if abs(pixel[0] - last_pixel[0]) \
				+ abs(pixel[1] - last_pixel[1]) \
				+ abs(pixel[2] - last_pixel[2]) < 10:
			break
	board_y = int((i+k) / 2)

	# 如果上一跳命中中间，则下个目标中心会出现 r245 g245 b245 的点，利用这个
	# 属性弥补上一段代码可能存在的判断错误
	# 若上一跳由于某种原因没有跳到正中间，而下一跳恰好有无法正确识别花纹，则有
	# 可能游戏失败，由于花纹面积通常比较大，失败概率较低
	for j in range(i, i+200):
		pixel = im_pixel[board_x, j]
		if abs(pixel[0] - 245) + abs(pixel[1] - 245) + abs(pixel[2] - 245) == 0:
			board_y = j + 10
			break

	if not all((board_x, board_y)):
		return 0, 0, 0, 0
	return (piece_x, piece_y), (board_x, board_y)

def getScreenshot(imgIndex):
	subprocess.Popen("adb shell screencap -p /sdcard/screen.png").wait()
	subprocess.Popen("adb pull /sdcard/screen.png").wait()
	subprocess.Popen("adb shell rm /sdcard/screen.png").wait()
	os.rename(basePath + "screen.png", basePath + str(imgIndex)+".png")
	shutil.copyfile(basePath + str(imgIndex)+".png", basePath + str(imgIndex)+"_backup.png")
	if os.path.exists(basePath + str((imgIndex+1)%20)+"_backup.png"):
		os.remove(basePath + str((imgIndex+1)%20)+"_backup.png")
		time.sleep(0.3)
	time.sleep(0.3)	

def initialize():
	global basePath
	rootDir = os.listdir(basePath)
	for item in rootDir:
		if item.endswith(".png"):
			os.remove(os.path.join(basePath, item))

if __name__ == '__main__':
	initialize()
	gameState = GameState("InGame")
	
	imgIndex = 0
	getScreenshot(imgIndex)
	reply = gameState.getMessage(imgIndex)
	
	while reply == "request next image":
		os.remove(basePath + str(imgIndex)+".png")
		time.sleep(max(random.gammavariate(2, 2), 0.9))
		imgIndex += 1
		imgIndex %= 20
		getScreenshot(imgIndex)
		reply = gameState.getMessage(imgIndex)
		if(random.uniform(1, 500) < 100):
			t = random.uniform(3, 10)
			print("模拟不规则长时间间隔，停止操作" + str(t) + "秒")
			time.sleep(t)
