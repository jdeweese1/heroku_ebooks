from datetime import datetime


def parse_time(string_time):
    day_of_week, month, month_day, time_str, _, year_str = string_time.split(' ')
    month_map = {
        'january': 1,
        'february': 2,
        'march': 3,
        'april': 4,
        'may': 5,
        'june': 6,
        'july': 7,
        'august': 8,
        'september': 9,
        'october': 10,
        'november': 11,
        'december': 12
    }
    month = month.lower()
    month_num = 0
    for key in month_map.keys():
        if month.lower() in key:
            month_num = month_map[key]
            break
    month_day_int = int(month_day)
    hour_str, minute_str, second_str = time_str.split(':')

    kwargs = {
        'month': month_num,
        'day': month_day_int,
        'hour': int(hour_str),
        'minute': int(minute_str),
        'second': int(second_str),
        'year': int(year_str),
    }
    d = datetime(**kwargs)
    return d
