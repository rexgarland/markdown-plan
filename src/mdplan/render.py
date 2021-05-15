"""
Module for painting a gantt chart in the terminal

All time units are in hours.
"""

import curses
import logging

from .plan import Plan
from . import settings

if settings.DEBUG:
    logging.basicConfig(filename='render.log', filemode='a', level=logging.INFO)
else:
    logging.basicConfig()

class Scrollable:
    def __init__(self, w, h, text):
        lines = text.split('\n')
        self.lines = lines
        self.maxx = max([len(line) for line in lines])
        self.maxy = len(lines)
        self.scrollx = 0
        self.scrolly = 0
        self.update_window(w, h)

    def create_pad(self):
        self.pad = curses.newpad(self.maxy, self.maxx+1)
        self.pad.keypad(True)
        for (i, line) in enumerate(self.lines):
            self.pad.addstr(i,0,line)

    def refresh(self, x, y):
        self.pad.refresh(self.scrolly, self.scrollx, y, x, y+self.windowy-1, x+self.windowx-1)

    def scroll(self, x, y):
        self.scrollx += x
        self.scrolly += y
        self.check_bounds()

    def update_window(self, w, h):
        self.windowx = w
        self.windowy = h
        self.scrollablex = self.maxx>self.windowx
        self.scrollabley = self.maxy>self.windowy
        self.check_bounds()

    def check_bounds(self):
        if not self.scrollablex:
            self.scrollx = 0
        if not self.scrollabley:
            self.scrolly = 0
        if self.scrollx < 0:
            self.scrollx = 0
        if self.scrolly < 0:
            self.scrolly = 0
        if self.scrollablex:
            if self.maxx-self.scrollx < self.windowx:
                self.scrollx = self.maxx-self.windowx
        if self.scrollabley:
            if self.maxy-self.scrolly < self.windowy:
                self.scrolly = self.maxy-self.windowy

def scroll(state, key):
    focus = state['focus']
    if key==settings.KEY_RIGHT:
        state[focus].scroll(1,0)
    elif key==settings.KEY_LEFT:
        state[focus].scroll(-1,0)
    elif key==settings.KEY_UP:
        state['tree'].scroll(0,-1)
        state['gantt'].scroll(0,-1)
    elif key==settings.KEY_DOWN:
        state['tree'].scroll(0,1)
        state['gantt'].scroll(0,1)

def draw(scr, state):
    scr.clear()
    h, w = scr.getmaxyx()
    state['tree'].update_window(w//3, h)
    state['tree'].refresh(0,0)
    state['gantt'].update_window(w-w//3, h)
    state['gantt'].refresh(w//3,0)

def paint_duration(time, current_duration, remaining_duration, scale=1):
    """Returns a line of text representing a progress bar"""
    logging.info(f'time {time} current {current_duration} remaining {remaining_duration}')
    if time<0:
        return settings.GANTT_TODO*int(max(remaining_duration*scale, 0))
    text = ' '*int(time*scale)
    text += settings.GANTT_DONE*int(current_duration*scale)+settings.GANTT_TODO*int(max(remaining_duration*scale, 0))
    return text

def text_overlay(string, new, at):
    text = string[:at]
    text += new
    text += string[at+len(new):]
    return text

def render_scale(scale, extent):
    """Returns the top line of text representing a time scale"""
    marker = u'\u258f'
    text = (marker+' '*(scale-1))*(int(extent)+1)
    for hour in range(int(extent+1)):
        if hour%8==0:
            day = hour//8+1
            text = text_overlay(text, f'd{day}', hour*scale)
    return text

def get_extent(plan):
    acc = 0
    for task in plan.tasks:
        acc += task.remaining_duration.hours
    return acc

LEVELS = ['','-']

level = lambda i: LEVELS[i]+' ' if i<len(LEVELS) else LEVELS[-1]+' '

# def render_gantt(gantt, width=None):
#     """Renders the tree text and gantt text to display to their respective pads"""
#     tree_text = render_tree(gantt)
    # if not (width is None):
    #     scale = int(max(float(width)/get_extent(gantt)*0.9, 2))
    # else:
    #     scale = 1
    # scale_text = render_scale(scale, get_extent(gantt))
#     gantt_text = scale_text
#     tree_text = '\n'+tree_text
#     gantt_text += '\n'.join([paint_duration(g['time'], g['duration'],scale=scale) for g in gantt])
#     return tree_text, gantt_text

def create_scale(plan, width):
    """
    Create a scale and scale bar.

    Input
        |plan| a plan
        |width| screen width in number of characters
    Output
        |scale| the number of characters per hour
        |line| the output scale bar
    """
    extent = get_extent(plan)
    scale = int(max(float(width)/extent*0.9, 2))
    logging.info(f'extent {extent} width {width} scale {scale}')
    line = render_scale(scale, extent)
    return scale, line

def render_list(plan, width=None):
    """Renders the tree text and gantt text to display to their respective pads"""
    scale, scale_line = create_scale(plan, width)
    min_level = min(t.level for t in plan.tasks)
    tree_text = '\n'.join(['  '*(t.level-min_level)+t.description for t in plan.tasks])
    gantt_texts = []
    acc_time = 0
    for t in plan.tasks:
        gt = paint_duration(acc_time-t.completed_duration.hours, t.completed_duration.hours, t.remaining_duration.hours, scale=scale)
        gantt_texts.append(gt)
        acc_time += t.remaining_duration.hours
    gantt_text = '\n'.join(gantt_texts)
    return '\n'+tree_text, scale_line+'\n'+gantt_text

def main(scr, plan):
    curses.curs_set(False)
    h, w = scr.getmaxyx()
    state = {'focus': 'tree'}
    tree, gantt = render_list(plan, width=w-w//3)
    lentree = len(tree.split('\n'))
    lengantt = len(gantt.split('\n'))
    logging.info(f'tree is {lentree}, gantt is {lengantt}')
    state['tree'] = Scrollable(w//3, h, tree)
    state['tree'].create_pad()
    state['gantt'] = Scrollable(w-w//3, h, gantt)
    state['gantt'].create_pad()
    draw(scr, state)
    while True:
        key = state[state['focus']].pad.getch()
        if key==settings.KEY_QUIT:
            return
        elif key==settings.KEY_SWITCH_PANE:
            if state['focus']=='gantt':
                state['focus'] = 'tree'
                logging.info('set focus: tree')
            else:
                state['focus'] = 'gantt'
                logging.info('set focus: gantt')
        else:
            scroll(state, key)
        draw(scr, state)

def render(**kwargs):
    plan = Plan(**kwargs)
    curses.wrapper(main, plan)
