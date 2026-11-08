"""终端品牌输出；日志文件与 systemd 自动去掉颜色。"""
import logging, os, platform, sys
from loguru import logger
from .core.config import CREDENTIALS_PATH


def colors():
    return not os.getenv('NO_COLOR') and (sys.stderr.isatty() or os.getenv('ATMOSPHERE_COLOR')=='always')


def configure_logs():
    # 保留异常堆栈，用紧凑格式区分事件与来源。
    # Windows 重定向日志统一为 UTF-8，保留终端字符。
    if os.name=='nt':
        for stream in (sys.stdout,sys.stderr):
            if hasattr(stream,'reconfigure'): stream.reconfigure(encoding='utf-8',errors='backslashreplace')
    logger.remove()
    logger.add(sys.stderr,colorize=colors(),level=os.getenv('ATMOSPHERE_LOG_LEVEL','INFO'),format='<dim>{time:HH:mm:ss}</dim>  <level>{level: <7}</level>  {message}  <dim>{name}:{line}</dim>')


def show_banner():
    accent='\033[38;5;180m' if colors() else '';dim='\033[2m' if colors() else '';reset='\033[0m' if colors() else ''
    port=os.getenv('ATMOSPHERE_BACKEND_PORT','27777')
    lines=['ATMOSPHERE  /  CONTROL PLANE','Minecraft server operations · v0.2.0',f'{platform.system()} {platform.machine()}  ·  Python {platform.python_version()}',f'API  {os.getenv("ATMOSPHERE_BIND","0.0.0.0")}:{port}','Java / Bedrock / MCDR  ·  PROCESS ENGINE','Ready · Ctrl+C to close the panel']
    print('\n'+accent+'┌'+'─'*62+'┐'+reset,file=sys.stderr)
    for index,line in enumerate(lines): print(accent+'│  '+(accent if index==0 else dim)+line.ljust(59)+accent+' │'+reset,file=sys.stderr)
    print(accent+'└'+'─'*62+'┘'+reset+'\n',file=sys.stderr,flush=True)
    # 初始密码未被替换时提示凭据文件位置，方便重新查看。
    if CREDENTIALS_PATH.exists():
        print('  初始凭据 / CREDENTIALS  '+str(CREDENTIALS_PATH)+'\n',file=sys.stderr,flush=True)


class TerminalFormatter(logging.Formatter):
    def format(self,record):
        color='\033[38;5;180m' if colors() else '';reset='\033[0m' if colors() else ''
        record.levelname=record.levelname.replace('WARNING','WARN')
        return f'{color}{self.formatTime(record,"%H:%M:%S")}  {record.levelname:<7}{reset}  {record.getMessage()}'+ ('\n'+self.formatException(record.exc_info) if record.exc_info else '')
