"""跨平台启动入口，与开发用 uvicorn 入口兼容。"""
import argparse, os, sys
from pathlib import Path
import uvicorn


def main():
    if getattr(sys, 'frozen', False):
        data = Path(os.getenv('ATMOSPHERE_DATA_DIR') or Path(sys.executable).parent / 'data')
        data.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault('ATMOSPHERE_DATA_DIR', str(data))
        os.environ.setdefault('ATMOSPHERE_DB_PATH', str(data / 'panel.sqlite3'))
        os.environ.setdefault('ATMOSPHERE_WEB_DIR', str(Path(sys._MEIPASS) / 'web'))
    parser=argparse.ArgumentParser(description='ATMOSPHERE · Minecraft server operations')
    parser.add_argument('--host',default=os.getenv('ATMOSPHERE_BIND','0.0.0.0'))
    parser.add_argument('--port',type=int,default=int(os.getenv('ATMOSPHERE_BACKEND_PORT','27777')))
    parser.add_argument('--no-access-log',action='store_true')
    args=parser.parse_args()
    if not 1<=args.port<=65535: parser.error('port must be between 1 and 65535')
    os.environ['ATMOSPHERE_BACKEND_PORT']=str(args.port);os.environ['ATMOSPHERE_BIND']=args.host
    # 统一 Uvicorn 启动、访问与异常日志的终端格式。
    config={'version':1,'disable_existing_loggers':False,'formatters':{'terminal':{'()':'app.terminal.TerminalFormatter'}},'handlers':{'console':{'class':'logging.StreamHandler','formatter':'terminal','stream':'ext://sys.stderr'}},'loggers':{'uvicorn':{'handlers':['console'],'level':'INFO','propagate':False},'uvicorn.access':{'handlers':['console'],'level':'INFO','propagate':False}}}
    uvicorn.run('app.main:app',host=args.host,port=args.port,log_config=config,access_log=not args.no_access_log)


if __name__=='__main__': main()
