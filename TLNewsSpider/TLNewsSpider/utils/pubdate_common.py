import re
import pytz
import time
import datetime
import traceback
from collections import OrderedDict

tz = pytz.timezone(pytz.country_timezones('cn')[0])

def _pack_with_year(match_res_tuple, need_detail_time=False, need_ms=False):
    year = match_res_tuple[0]
    if len(year) == 2:
        ymd = '20{}-'.format(year)
        fmt_ymd = ['0{}'.format(x) if len(str(x)) == 1 else x for x in match_res_tuple[1:3]]
        ymd += '-'.join(fmt_ymd)
    else:
        fmt_ymd = ['0{}'.format(x) if len(str(x)) == 1 else x for x in match_res_tuple[:3]]
        ymd = '-'.join(fmt_ymd)

    return _pack_hms(match_res_tuple=match_res_tuple[3:], ymd=ymd,
                     need_detail_time=need_detail_time, need_ms=need_ms)


def _pack_without_year(match_res_tuple, need_detail_time=False, need_ms=False):
    now = datetime.datetime.now(tz=tz)
    year = now.year
    raw_month = int(match_res_tuple[0])
    raw_day = int(match_res_tuple[1])
    if raw_month >= now.month:
        if raw_month > now.month:
            year = int(year) - 1
        elif raw_day > now.day:
            year = int(year) - 1

    ymd = '{}-'.format(year)
    fmt_md = ['0{}'.format(x) if len(str(x)) == 1 else x for x in match_res_tuple[:2]]
    ymd += '-'.join(fmt_md)

    return _pack_hms(match_res_tuple=match_res_tuple[2:], ymd=ymd,
                     need_detail_time=need_detail_time, need_ms=need_ms)


def _pack_hms(match_res_tuple, ymd='', need_detail_time=False, need_ms=False):
    now = datetime.datetime.now(tz=tz)
    if not ymd:
        ymd = now.strftime(_pack_fmt())

    hms = ' '
    match_res_tuple_len = len(match_res_tuple)
    if need_detail_time:
        if match_res_tuple_len >= 3:
            rest = match_res_tuple
        else:
            rest = match_res_tuple + ('00',) * (3 - match_res_tuple_len)

        rest = ['0{}'.format(x) if len(str(x)) == 1 else x for x in rest[:3]]
        hms += ':'.join(rest[:3])

    if need_ms:
        if match_res_tuple_len >= 4 and int(match_res_tuple[4]) != 0:
            hms += '.{}'.format(match_res_tuple[4])
        else:
            hms += '.{}'.format(now.microsecond)

    return ymd + hms


time_reg_dict = OrderedDict()
time_reg_dict['(\d+)[年\.\-/](\d+)[月\.\-/](\d+).*?(\d+)[:,:](\d+)[:,:](\d+)\.(\d+)'] = (7, _pack_with_year) # 年月日 时分秒 毫秒
time_reg_dict['(\d+)[年\.\-/](\d+)[月\.\-/](\d+).*?(\d+)[:,:](\d+)[:,:](\d+)'] = (6, _pack_with_year)  # 年月日 时分秒
time_reg_dict['(\d+)[年\.\-/](\d+)[月\.\-/](\d+).*?(\d+)[:,:](\d+)'] = (5, _pack_with_year)  # 年月日 时分
time_reg_dict['(\d+)[月\.\-/](\d+).*?(\d+)[:,:](\d+)[:,:](\d+)'] = (5, _pack_without_year)  # 月日 时分秒
time_reg_dict['(\d+)[月\.\-/](\d+).*?(\d+)[:,:](\d+)'] = (4, _pack_without_year)  # 月日 时分
time_reg_dict['(\d+)[:,:](\d+)[:,:](\d+)'] = (3, _pack_hms)  # 时分秒
time_reg_dict['(\d+)[:,:](\d+)'] = (2, _pack_hms)  # 时分
time_reg_dict['(\d+)[年\.\-/](\d+)[月\.\-/](\d+)'] = (3, _pack_with_year)  # 年月日
time_reg_dict['(\d+)[月\.\-/](\d+)'] = (2, _pack_without_year)  # 月日


def handle_pubdate(pubdate_str, timestamp=None, need_detail_time=False, need_ms=False):

    """
    处理常见的时间格式
    pubdate_str: 常见的时间格式,可以只有年月日或时分秒的信息,也可以同时包含有年月日与时分秒的信息,
                        但一旦包含年月日的信息,则至少需要有月和日, 一旦包含时分秒的信息.则至少要有时和分,
                        否则解析会得不到预期的结果;还可以包含"刚刚", "n秒/分钟/小时/天/周前", "今天",
                        "昨天", "前天" 等日期信息 
    timestamp: 当pubdate_str所代表的不是具体的时间信息时(如 今天 昨天 n小时前等)时,若在解析时再
                    调用此方法时,会默认使用系统当前时间,若指定timestamp时,则会将timestamp转换为当前时间,
                    再来进行时间的偏移处理.例如:今天获取的日期信息(格式为 1小时前),当第二天再来解析时,若指定
                    timestamp为bbd_uptime,则可以将时间还原到数据抓取时的1小时前
    need_detail_time: 是否需要"时分秒"的信息,默认为False
    need_ms: 是否需要"毫秒"的信息,默认为False
    status: 是否正确处理日期, bool
            result: 当status为True时,result为根据need_detail_time和need_ms参数返回对应的时间格式, 
                    如"2019-01-01"或"2019-01-01 01:01:01";
                    当status为False时,result为错误信息
    """
    try:
        if not re.sub('\s', '', pubdate_str):
            return False, 'pubdate is {}, can not be formatted'.format(pubdate_str)

        _assert_params(need_detail_time=need_detail_time, need_ms=need_ms)
        t = ''.join(re.findall('刚刚', pubdate_str))
        if t:
            return  _pubdate_just_now(timestamp=timestamp,
                                     need_detail_time=need_detail_time, need_ms=need_ms)
        t = ''.join(re.findall('(\d+)秒钟*以*前*', pubdate_str))
        if t:
            return _pubdate_s(before_s=float(t), timestamp=timestamp, need_detail_time=need_detail_time, need_ms=need_ms)

        t = ''.join(re.findall('(\d+)分钟以*前*', pubdate_str))
        if t:
            return _pubdate_m(before_m=float(t), timestamp=timestamp, need_detail_time=need_detail_time, need_ms=need_ms)

        t = ''.join(re.findall('(\d+)小时以*前*', pubdate_str))
        if t:
            return _pubdate_h(before_h=float(t), timestamp=timestamp, need_detail_time=need_detail_time, need_ms=need_ms)

        t = ''.join(re.findall('(\d+)天以*前*', pubdate_str))
        if t:
            return _pubdate_d(before_d=float(t), timestamp=timestamp, need_detail_time=need_detail_time, need_ms=need_ms)

        t = ''.join(re.findall('(\d+)周以*前*', pubdate_str))
        if t:
            return _pubdate_w(before_w=float(t), timestamp=timestamp, need_detail_time=need_detail_time, need_ms=need_ms)

        t = ''.join(re.findall('今天', pubdate_str))
        if t:
            today_time = ''.join(re.findall('今天.*?([\d+:]{0,6}\d+)', pubdate_str))
            return _pubdate_today(today_time=today_time, timestamp=timestamp, need_detail_time=need_detail_time, need_ms=need_ms)

        t = ''.join(re.findall('昨天', pubdate_str))
        if t:
            yesterday_time = ''.join(re.findall('昨天.*?([\d+:]{0,6}\d+)', pubdate_str))
            return _pubdate_yesterday(yesterday_time=yesterday_time, timestamp=timestamp, need_detail_time=need_detail_time,
                                      need_ms=need_ms)

        t = ''.join(re.findall('前天', pubdate_str))
        if t:
            daysago_time = ''.join(re.findall('前天.*?([\d+:]{0,6}\d+)', pubdate_str))
            return _pubdate_daysago(daysago_time=daysago_time, timestamp=timestamp, need_detail_time=need_detail_time,
                                    need_ms=need_ms)

        return _pack_time_str(time_str=pubdate_str, need_detail_time=need_detail_time, need_ms=need_ms)
    except Exception:
        err_msg = traceback.format_exc()
        return False, err_msg


def _assert_params(need_detail_time, need_ms):
    if not need_detail_time and need_ms:
        raise Exception("Can not set need detail time to False while need ms is True!")


def _pack_fmt(need_detail_time=False, need_ms=False):
    tm_fmt = '%Y-%m-%d'

    if need_detail_time:
        tm_fmt += ' %H:%M:%S'

    if need_ms:
        tm_fmt += '.%f'

    return tm_fmt


def _str_2_timestamp(time_str, fmt='%Y-%m-%d'):
    time_str = re.sub('\+\d+:\d+', '', time_str)
    time_str = time_str.strip()
    dt = datetime.datetime.strptime(time_str, fmt)
    res = time.mktime(dt.timetuple())
    if dt.microsecond:
        res = float('{}.{}'.format(int(res), dt.microsecond))
    return res


def _timestamp_2_str(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, tz=tz).strftime(_pack_fmt(need_detail_time=True, need_ms=True))


def _pack_timestamp(timestamp=None, need_detail_time=False, need_ms=False):
    if not timestamp:
        timestamp = time.time()

    tm_str = _timestamp_2_str(timestamp)
    tm_str = _pack_time_str(time_str=tm_str, need_detail_time=need_detail_time, need_ms=need_ms)
    tm_fmt = _pack_fmt(need_detail_time, need_ms)
    return _str_2_timestamp(tm_str, tm_fmt)


def _pack_time_str(time_str='', need_detail_time=False, need_ms=False):
    if not time_str:
        time_str = _timestamp_2_str(time.time())

    for time_reg, cnt_cb in time_reg_dict.items():
        cnt, cb = cnt_cb
        match_res_tuple = re.findall(time_reg, time_str)
        if not match_res_tuple:
            continue
        if len(match_res_tuple[0]) != int(cnt):
            continue

        return cb(match_res_tuple=match_res_tuple[0], need_detail_time=need_detail_time,
                  need_ms=need_ms)
    else:
        raise Exception('Can not handle pubdate {}'.format(time_str))


def _pubdate_just_now(timestamp=None, need_detail_time=False, need_ms=False):
    if timestamp is not None:
        timestamp = _pack_timestamp(timestamp=timestamp, need_detail_time=need_detail_time, need_ms=need_ms)
    else:
        timestamp = _pack_timestamp(need_detail_time=need_detail_time, need_ms=need_ms)

    return _timestamp_2_str(timestamp)


def _pubdate_s(before_s: float, timestamp=None, need_detail_time=False, need_ms=False):
    if not timestamp:
        now = datetime.datetime.now(tz=tz)
    else:
        now = datetime.datetime.fromtimestamp(timestamp, tz)

    real_dt = now - datetime.timedelta(seconds=float(before_s))
    dt_fmt = _pack_fmt(need_detail_time=need_detail_time, need_ms=need_ms)
    return real_dt.strftime(dt_fmt)


def _pubdate_m(before_m: float, timestamp=None, need_detail_time=False, need_ms=False):
    if not timestamp:
        now = datetime.datetime.now(tz=tz)
    else:
        now = datetime.datetime.fromtimestamp(timestamp, tz)

    real_dt = now - datetime.timedelta(minutes=float(before_m))
    dt_fmt = _pack_fmt(need_detail_time=need_detail_time, need_ms=need_ms)
    return real_dt.strftime(dt_fmt)


def _pubdate_h(before_h: float, timestamp=None, need_detail_time=False, need_ms=False):
    if not timestamp:
        now = datetime.datetime.now(tz=tz)
    else:
        now = datetime.datetime.fromtimestamp(timestamp, tz)

    real_dt = now - datetime.timedelta(hours=float(before_h))
    dt_fmt = _pack_fmt(need_detail_time=need_detail_time, need_ms=need_ms)
    return real_dt.strftime(dt_fmt)


def _pubdate_d(before_d: float, timestamp=None, need_detail_time=False, need_ms=False):
    if not timestamp:
        now = datetime.datetime.now(tz=tz)
    else:
        now = datetime.datetime.fromtimestamp(timestamp, tz)

    real_dt = now - datetime.timedelta(days=float(before_d))
    dt_fmt = _pack_fmt(need_detail_time=need_detail_time, need_ms=need_ms)
    return real_dt.strftime(dt_fmt)


def _pubdate_w(before_w: float, timestamp=None, need_detail_time=False, need_ms=False):
    if not timestamp:
        now = datetime.datetime.now(tz=tz)
    else:
        now = datetime.datetime.fromtimestamp(timestamp, tz)

    real_dt = now - datetime.timedelta(weeks=float(before_w))
    dt_fmt = _pack_fmt(need_detail_time=need_detail_time, need_ms=need_ms)
    return real_dt.strftime(dt_fmt)


def _pubdate_today(today_time='', timestamp=None, need_detail_time=False, need_ms=False):
    if timestamp:
        ymd = datetime.datetime.fromtimestamp(timestamp, tz).strftime(_pack_fmt())
        today_time = ymd + ' ' + today_time

    return _pack_time_str(time_str=today_time, need_detail_time=need_detail_time, need_ms=need_ms)


def _pubdate_yesterday(yesterday_time='', timestamp=None, need_detail_time=False, need_ms=False):
    if not timestamp:
        now = datetime.datetime.now(tz=tz)
    else:
        now = datetime.datetime.fromtimestamp(timestamp, tz)

    real_dt = now - datetime.timedelta(days=1)
    ymd = real_dt.strftime(_pack_fmt())
    return _pack_time_str(time_str='{} {}'.format(ymd, yesterday_time),
                          need_detail_time=need_detail_time, need_ms=need_ms)


def _pubdate_daysago(daysago_time='', timestamp=None, need_detail_time=False, need_ms=False):
    if not timestamp:
        now = datetime.datetime.now(tz=tz)
    else:
        now = datetime.datetime.fromtimestamp(timestamp, tz)

    real_dt = now - datetime.timedelta(days=2)
    ymd = real_dt.strftime(_pack_fmt())
    return _pack_time_str(time_str='{} {}'.format(ymd, daysago_time),
                          need_detail_time=need_detail_time, need_ms=need_ms)


