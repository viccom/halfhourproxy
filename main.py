#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os, sys, platform, time
import re
import chardet
import logging
import subprocess
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI
from starlette.responses import FileResponse, RedirectResponse, PlainTextResponse
from starlette.staticfiles import StaticFiles
# from api.freelan import apiFreelan
# from api.v1 import apiv1
from app.freelan import SubFreelan
from app.gost import SubGostlan
import uuid
import uvicorn

formatter = "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s"
log_level = 'INFO'
log_filenum = 9
log_maxsize = 4
level = logging.getLevelName(log_level)
logging.basicConfig(level=level, format=formatter)
if not os.path.exists("logs"):
	os.mkdir("logs")
log = logging.getLogger()
# 输出到文件
fh = RotatingFileHandler('./logs/freelan_service.log', mode='a+', maxBytes=log_maxsize * 1024 * 1024,
                         backupCount=log_filenum, delay=True)
fh.setFormatter(logging.Formatter(formatter))
log.addHandler(fh)

# app = FastAPI(openapi_url="/api/v1/openapi.json", docs_url="/api/v1/docs")
app = FastAPI()
app.mount('/dl', StaticFiles(directory='dl'), name='dl')
# app.broker = MQTTBroker()
# mqttConfig = {"host": "localhost", "port": "3883", "user": "viccom", "pwd": "Pa88word"}
# app.mqttmicro = MQTTPubBase('micro', mqttConfig)
app.passphrase = str(uuid.uuid1())
app.subfreelan = SubFreelan(app.passphrase)
app.gostpassword = str(uuid.uuid1())
app.subgostlan = SubGostlan(app.gostpassword)


def turnfile(file):
	with open(file, 'rb') as f:
		data = f.read()
		encoding = chardet.detect(data)['encoding']
		data_str = data.decode(encoding)
		tp = 'LF'
		if '\r\n' in data_str:
			tp = 'CRLF'
			data_str = data_str.replace('\r\n', '\n')
		if encoding not in ['utf-8', 'ascii'] or tp == 'CRLF':
			with open(file, 'w', newline='\n', encoding='utf-8') as f:
				f.write(data_str)


def alter(file, newfile, old_str, new_str):
	if os.path.exists(newfile):
		os.remove(newfile)
	with open(file, "r", newline='\n', encoding="utf-8") as f1, open(newfile, "w", encoding="utf-8") as f2:
		for line in f1:
			f2.write(re.sub(old_str, new_str, line))
	turnfile(newfile)


@app.on_event("startup")
async def startup():
	pass


# logging.info("Staring hbmqtt broker..")
# app.broker.start()
# logging.info("Staring mqtt client..")
# app.mqttmicro.start()


@app.on_event("shutdown")
async def shutdown():
	pass


# app.mqttmicro.stop()


@app.get("/")
async def index():
	response = PlainTextResponse(
		' curl -L -s freelan.freeioe.org/goststart|bash\n')
	return response


@app.get("/proxysh")
def proxysh():
	alter("app/freelan/freeproxy.sh", "app/freelan/new-freeproxy.sh", "freelan.passphrase", app.passphrase)
	response = FileResponse("app/freelan/new-freeproxy.sh")
	response.media_type = "application/octet-stream"
	response.filename = "freeproxy.sh"
	return response


@app.get("/start")
def api_start():
	if app.subfreelan.is_alive():
		logging.info("subfreelan is running")
		status = app.subfreelan.status()
		if status == "running":
			logging.info("freelan is running")
			response = FileResponse("app/freelan/error1.sh")
			response.media_type = "application/octet-stream"
			response.filename = "error1.sh"
			return response
		else:
			logging.error("freelan is stopped")
			app.subfreelan.stop()
			response = FileResponse("app/freelan/error2.sh")
			response.media_type = "application/octet-stream"
			response.filename = "error2.sh"
			return response
	else:
		logging.info("subfreelan is starting")
		app.passphrase = str(uuid.uuid1())
		app.subfreelan = SubFreelan(app.passphrase)
		app.subfreelan.start()
		return RedirectResponse("/proxysh?" + str(int(time.time())))


@app.get("/status")
def api_status():
	pid = bytes.decode(subprocess.check_output("ps -auxf|grep freelan|grep -v grep|awk '{print $2}'", shell=True))
	if pid:
		return {"result": True, "message": "running"}
	else:
		return {"result": True, "message": "stopped"}


@app.post("/stop")
def api_stop(key):
	if key:
		if key == app.passphrase or key == "admin@freeioe.org":
			if app.subfreelan.is_alive():
				app.subfreelan.stop()
			return {"result": True, "message": "stop"}
	return {"result": False, "message": "key error"}


@app.get("/gostsh")
def gostsh():
	alter("app/gost/gostproxy.sh", "app/gost/new-gostproxy.sh", "gostpassword.passphrase", app.gostpassword)
	response = FileResponse("app/gost/new-gostproxy.sh")
	response.media_type = "application/octet-stream"
	response.filename = "gostproxy.sh"
	return response


@app.get("/goststart")
def api_goststart():
	if app.subgostlan.is_alive():
		logging.info("subgostlan is running")
		status = app.subgostlan.status()
		if status == "running":
			logging.info("gostlan is running")
			response = FileResponse("app/gost/error1.sh")
			response.media_type = "application/octet-stream"
			response.filename = "error1.sh"
			return response
		else:
			logging.error("gostlan is stopped")
			app.subgostlan.stop()
			response = FileResponse("app/gost/error2.sh")
			response.media_type = "application/octet-stream"
			response.filename = "error2.sh"
			return response
	else:
		logging.info("subgostlan is starting")
		app.gostpassword = str(uuid.uuid1())
		app.subgostlan = SubGostlan(app.gostpassword)
		app.subgostlan.start()
		return RedirectResponse("/gostsh?" + str(int(time.time())))


@app.get("/goststatus")
def api_goststatus():
	pid = bytes.decode(subprocess.check_output("ps -auxf|grep gost|grep -v grep|awk '{print $2}'", timeout=2, shell=True))
	if pid:
		return {"result": True, "message": "running"}
	else:
		return {"result": True, "message": "stopped"}


@app.post("/goststop")
def api_goststop(key):
	if key:
		if key == app.gostpassword or key == "admin@freeioe.org":
			if app.subgostlan.is_alive():
				app.subgostlan.stop()
			return {"result": True, "message": "stop"}
	return {"result": False, "message": "key error"}

# app.include_router(apiv1, prefix='/api/v1/micro', tags=['apiv1'])
# app.include_router(apiFreelan, prefix='/api/v1/freelan', tags=['apiFreelan'])

if __name__ == '__main__':
	debug = False
	if len(sys.argv) > 1 and sys.argv[1] == '--debug':
		debug = True
	if (platform.system() != "Linux"):
		debug = True
	logging.info("当前工作路径：" + str(os.getcwd()) + ",启动参数:debug=" + str(debug))
	time.sleep(1)
	(filename, extension) = os.path.splitext(os.path.basename(__file__))
	appStr = filename + ':app'
	uvicorn.run(appStr, host="127.0.0.1", port=8081, reload=debug)
