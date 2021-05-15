from datetime import date, time, datetime, timedelta

from . import utils

TODAY = date.today()
NOW = datetime.now()

def is_code_block_delimiter(line):
    return line.strip()=='```'

WHITESPACE = [' ','\t']

def get_initial_white(string):
    text = ''
    for char in string:
        if char in WHITESPACE:
            text += char
        else:
            return text
    return ''

def after_numerics(string):
    after = ''
    for s in string:
        if s.isnumeric():
            after = ''
        else:
            after += s
    return after

def only_numerics(string):
    return ''.join(s for s in string if s.isnumeric())

def parse_scale(scale):
    scale = scale.lower()
    if scale in ['mins', 'minutes', 'min', 'minute']:
        return 'minutes'
    elif scale in ['d', 'days', 'day']:
        return 'days'
    elif scale in ['week', 'weeks', 'wks', 'w']:
        return 'weeks'
    elif scale in ['mo', 'months', 'month']:
        return 'months'
    return 'hours'

def parse_string_and_scale(string):
    if string.strip()=='0':
        return '0', 'hours'
    numerics = [i for i in range(len(string)) if string[i].isnumeric()]
    assert numerics
    last = numerics[-1]
    return string[:last+1].strip(), parse_scale(string[last+1:].strip())

def is_range(string):
    if '-' in string:
        assert string.count('-')==1
        return True
    return False

def is_wait(string):
    return string.strip()[:4]=='wait'

TASK_MARKERS = ['*','-','#']

def is_task(line):
    # task lines must start with a marker (after any initial indent whitespace)
    line = line.strip()
    if not line:
        return False
    if line[0] in TASK_MARKERS:
        return True
    if line[0].isnumeric():
        period = line.find('.')
        if period==-1:
            return False
        before_period = line[:period]
        if all([c.isnumeric() for c in before_period]):
            return True
    return False

def parse12h(string):
    '''
    Parses a string like "12 pm", "1130am", "1:15pm" to hour, minute, ampm
    '''
    numerics = only_numerics(string)
    assert len(numerics)<=4
    if len(numerics)<3:
        hour = int(numerics)
        minute = 0
    else:
        hour, minute = int(numerics[:-2]), int(numerics[-2:])
    ampm = after_numerics(string).strip().lower()
    if not (ampm in ['am','pm']):
        ampm = None
    return hour, minute, ampm

def is_deadline(string):
    return string.strip()[:2]=='by'

def get_deadline(string):
    brackets = utils.find_groups(string, '[]')
    having_by = [b for b in brackets if b.strip()[:2]=='by']
    if having_by:
        assert len(having_by)==1, f"More than one deadline found in line '{string}'"
        string = having_by[0]
        index = string.index('by')
        deadline = string[index+2:].strip()
        return deadline
    return None

def is_measurement(bracket_string):
    return bracket_string.strip()[0].isnumeric()

def is_interval(string):
    return '-' in string

def parse_time_interval(string):
    """Returns the number of hours represented in a time interval, parsed forgivingly.

    E.g.
        parse_time_interval("1030-1") -> 2.5
        parse_time_interval("5-6pm") -> 1
        parse_time_interval("5am-5:30") -> 0.5
    """
    times = string.split('-')
    assert len(times)==2
    first = parse12h(times[0])
    second = parse12h(times[1])
    if has24(first) and has24(second):
        return hour_diff(first, second)
    if second[2] is None:
        assert first[2] is None
        second = (second[0], second[1], 'pm')
    if not (first[2] is None):
        return hour_diff(first, second)
    else:
        first = (first[0], first[1], 'pm')
        diff1 = hour_diff(first, second)
        first = (first[0], first[1], 'am')
        diff2 = hour_diff(first, second)
        return min(diff1, diff2)

def has24(triplet):
    return not (triplet[2] is None)

def hour_diff(trip1, trip2):
    t1 = time_to_float(trip1)
    t2 = time_to_float(trip2)
    if t2>=t1:
        return t2-t1
    else:
        return 24-(t1-t2)

def time_to_float(triplet):
    h, m, ampm = triplet
    twelve = (h+m/60.0) % 12
    return twelve+12*(ampm=='pm')

def get_dependencies(string):
    groups = utils.find_groups(string, ['@(',')'])
    if not groups:
        return []
    assert len(groups)==1
    string = groups[0]
    splits = string.split(',')
    return [split.strip() for split in splits]

def closest_date(string):
    month, day = string.split('-')
    month = int(month.strip())
    day = int(day.strip())
    curr_year = TODAY.year
    years = [curr_year-1, curr_year, curr_year+1]
    base = date.fromisoformat('2000-{:02d}-{:02d}'.format(month, day))
    options = [base.replace(year) for year in years]
    return min(options, key=lambda d: abs(d-TODAY))

def parse_date_only(string, method='nearest'):
    dividers = string.count('-')
    assert dividers in [1, 2]
    if dividers==1:
        if method=='nearest':
            return closest_date(string)
        elif method=='before':
            month, day = string.split('-')
            year = TODAY.year
            d = date(year, int(month), int(day))
            if d<=TODAY:
                return d
            else:
                return date(year-1, int(month), int(day))
    else:
        year, month, day = string.split('-')
        return date(int(year), int(month), int(day))

def parse_time_only(string):
    hour, minute, ampm = parse12h(string.strip())
    return time(hour=hour+12*(ampm=='pm'), minute=minute)

def parse_time(string, method='nearest'):
    '''
    Parses text to return a date, time, or datetime object, whichever is appropriate
    '''
    num_hyphens = string.count('-')
    if num_hyphens==0:
        # time
        return parse_time_only(string)
    elif num_hyphens in [1,2]:
        at = string.find('at')
        if at==-1:
            # date
            return parse_date_only(string, method=method)
        else:
            # datetime
            date_part = string[:at].strip()
            d = parse_date_only(date_part, method=method)
            time_part = string[at+2:].strip()
            t = parse_time_only(time_part)
            return datetime.combine(d, t)
    else:
        raise Exception(f'Could not determine type of time event in string {string}')

def parse_deadline(string):
    """Returns a datetime for the provided date. Only supports ISO date format right now."""
    by = string.index('by')
    string = string[by+2:].strip()
    return parse_time(string)

def get_start(line):
    starts = [parse_start(b) for b in utils.find_groups(line, '[]') if is_start(b)]
    assert len(starts)<2, f"Multiple start directives found in line '{line}'"
    if not starts:
        return None
    return starts[0]

def get_finish(line):
    finishes = [parse_finish(b) for b in utils.find_groups(line, '[]') if is_finish(b)]
    assert len(finishes)<2, f"Multiple finish directives found in line '{line}'"
    if not finishes:
        return None
    return finishes[0]

def is_start(string):
    return ('began' in string) or ('started' in string)

def parse_start(string):
    if 'began' in string:
        kw = 'began'
    elif 'started' in string:
        kw = 'started'
    string = string[string.index(kw)+len(kw):].strip()
    return parse_time(string, method='before')

def is_finish(string):
    return ('finished' in string) or ('ended' in string)

def parse_finish(string):
    if 'ended' in string:
        kw = 'ended'
    elif 'finished' in string:
        kw = 'finished'
    string = string[string.index(kw)+len(kw):].strip()
    return parse_time(string, method='before')

def get_measurements(string):
    brackets = utils.find_groups(string, '[]')
    measurements = []
    for bracket in brackets:
        for sub in bracket.split(','):
            sub = sub.strip()
            if is_measurement(sub):
                measurements.append(sub)
    return measurements

def is_completed(line):
    for bracket in utils.find_groups(line, '[]'):
        if bracket.strip().lower()=='done':
            return True
    return False

def get_estimate(line):
    groups = utils.find_groups(line, '{}')
    if not groups:
        return None
    assert len(groups)==1
    return groups[0].strip()

def get_level(line, indent='\t'):
    first = line.strip()[0]
    if first=='#':
        line = line.strip()
        num = 0
        for char in line:
            if char!='#':
                break
            num += 1
        level = -1*0.5**(num-1)
        return level
    else:
        first_index = line.index(first)
        level = line[:first_index].count(indent)
        return level

def is_ordered(line):
    return line.strip()[0].isnumeric()

def get_description(content):
    """Description is everything before the special symbols for {estimate} and [status], after task markers"""
    bracket = content.find('[')
    bracket = bracket if bracket>-1 else len(content)
    brace = content.find('{')
    brace = brace if brace>-1 else len(content)
    paren = content.find('@(')
    paren = paren if paren>-1 else len(content)
    special = min(bracket, brace, paren)
    before_special = content[:special].strip()
    if before_special[0] in TASK_MARKERS:
        return before_special[1:].strip()
    if before_special[0].isnumeric():
        period = before_special.find('.')
        if period>=len(before_special)-1:
            return ''
        return before_special[period+1:].strip()
    return ''

def infer_indent(text):
    lines = text.split('\n')
    indents = [get_initial_white(line) for line in lines if is_task(line)]
    indents = [indent for indent in indents if indent]
    if not indents:
        return '\t' # default
    chartype = indents[0][0]
    together = ''.join(indents)
    assert together.count(chartype)==len(together), "Indentation must be consistent"
    counts = {len(indent) for indent in indents}
    return utils.gcd(*counts)*chartype
