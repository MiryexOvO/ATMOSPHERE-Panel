"""持久化 Cron 调度；统一使用 UTC 时间计算。"""
import asyncio, calendar, time
from contextlib import closing
from datetime import datetime, timedelta, timezone
from ..core.database import connect
from ..core.security import can_access
from .operations import operate
from .panel_settings import audit
TASK_LOCKS={}


def cron_parts(expression):
    # 校验范围、列表与步长，星期日兼容 0 和 7。
    tokens=expression.split()
    if len(tokens)==5: tokens=['0',*tokens]
    if len(tokens)!=6: raise ValueError('Cron 需要五段或六段（可含秒），时区为 UTC')
    result=[]
    for token,(low,high) in zip(tokens,[(0,59),(0,59),(0,23),(1,31),(1,12),(0,7)]):
        values=set()
        for part in token.split(','):
            base,_,step=part.partition('/');stride=int(step) if step else 1
            if stride<1 or stride>high+1: raise ValueError('Cron 步长无效')
            if base in {'*','?'}: begin,end=low,high
            elif '-' in base: begin,end=map(int,base.split('-'))
            else: begin=int(base);end=high if step else begin
            if not low<=begin<=end<=high: raise ValueError('Cron 数值超出范围')
            values.update(range(begin,end+1,stride))
        result.append(values)
    result[-1]={value%7 for value in result[-1]}
    return result,tokens


def next_run(expression,after=None):
    parts,tokens=cron_parts(expression)
    seconds,minutes,hours,days,months,weekdays=parts
    start=datetime.fromtimestamp(after if after is not None else time.time(),timezone.utc).replace(microsecond=0)+timedelta(seconds=1)
    cursor=start.replace(hour=0,minute=0,second=0)
    # 按天跳过日期，仅枚举匹配的时分秒。
    for _ in range(366*8):
        dom=cursor.day in days;dow=(cursor.weekday()+1)%7 in weekdays
        match=(dom or dow) if tokens[3] not in {'*','?'} and tokens[5] not in {'*','?'} else dom and dow
        if cursor.month in months and match:
            for hour in sorted(hours):
                for minute in sorted(minutes):
                    candidate=cursor.replace(hour=hour,minute=minute)
                    if candidate+timedelta(seconds=59)<start: continue
                    for second in sorted(seconds):
                        candidate=candidate.replace(second=second)
                        if candidate>=start: return int(candidate.timestamp())
        cursor+=timedelta(days=1)
    raise ValueError('未来八年内没有可执行时间')


async def execute(task):
    lock=TASK_LOCKS.setdefault(task['id'],asyncio.Lock())
    if lock.locked(): return 'ERROR 任务正在执行'
    async with lock: return await _execute(task)


async def _execute(task):
    # 运行前复核任务创建者，停用或撤权后不再执行。
    with closing(connect()) as conn:
        user=conn.execute('SELECT id,role,enabled FROM users WHERE id=?',(task['owner_id'],)).fetchone()
    permission='command' if task['action']=='command' else 'backups' if task['action']=='backup' else 'power'
    try:
        if not user or not user['enabled'] or user['role']=='viewer' or not can_access(user,task['instance_id'],permission): raise ValueError('任务所有者权限失效')
        output=await operate(task['instance_id'],task['action'],task['command'])
        result='OK '+str(output)[:1000]
    except Exception as exc: result='ERROR '+str(exc)[:1000]
    with closing(connect()) as conn:
        conn.execute('UPDATE schedules SET last_run=?,last_result=? WHERE id=?',(int(time.time()),result,task['id']));conn.commit()
    audit(task['owner_id'],'schedule.run',str(task['id'])+' '+result)
    return result


async def run_scheduler():
    pending=set();running=set()
    try:
        while True:
            with closing(connect()) as conn:
                tasks=conn.execute('SELECT * FROM schedules WHERE enabled=1 AND next_run<=?',(int(time.time()),)).fetchall()
                for row in tasks:
                    task=dict(row)
                    if task['id'] in running: continue
                    # 原子认领，不补跑后端离线时错过的多次任务。
                    claimed=conn.execute('UPDATE schedules SET next_run=? WHERE id=? AND next_run=?',(next_run(task['cron']),task['id'],task['next_run'])).rowcount
                    conn.commit()
                    if claimed:
                        running.add(task['id']);job=asyncio.create_task(execute(task));pending.add(job)
                        def finished(job,task_id=task['id']): pending.discard(job);running.discard(task_id)
                        job.add_done_callback(finished)
            await asyncio.sleep(1)
    finally:
        for task in pending: task.cancel()
        if pending: await asyncio.gather(*pending,return_exceptions=True)
