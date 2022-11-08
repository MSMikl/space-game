import asyncio
import curses
import os
import random
import time

from itertools import cycle
from os.path import isfile, join

from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed
from space_garbage import fly_garbage


EVENT_LOOP = []


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol='*', offset_tics=1):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(offset_tics*20)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(offset_tics*3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(offset_tics*5)

        canvas.addstr(row, column, symbol)
        await sleep(offset_tics*3)


async def fire(canvas, start_row, start_column, rows_speed=0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep(1)

    canvas.addstr(round(row), round(column), 'O')
    await sleep(1)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await sleep(1)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def fill_orbit_with_garbage(canvas, garbage_frames):
    max_y = canvas.getmaxyx()[1] - 1
    global EVENT_LOOP
    while True:
        EVENT_LOOP.append(fly_garbage(canvas, random.randint(0, max_y), random.choice(garbage_frames), speed=0.2))
        await sleep(10)



async def render_spaceship(canvas, column, row, frames):
    size = canvas.getmaxyx()
    # Максимальные координаты окна на единицу меньше размера, поскольку нумерация начинается с 0
    max_y = size[0] - 1
    max_x = size[1] - 1
    ship_length, ship_width = get_frame_size(frames[0])
    row_speed = column_speed = 0
    exit = False
    for frame in cycle(frames):
        step_y, step_x, _, exit = read_controls(canvas)
        row_speed, column_speed = update_speed(row_speed, column_speed, step_y, step_x)
        if exit:
            break
        column = min(column + column_speed, max_x - ship_width) if column_speed >= 0 else max(column + column_speed, 0)
        row = min(row + row_speed, max_y - ship_length) if row_speed >= 0 else max(row + row_speed, 0)
        draw_frame(canvas, row, column, frame)
        await sleep(1)
        draw_frame(canvas, row, column, frame, negative=True)


def load_frames(path):
    frames = []
    for filename in os.listdir(path):
        full_path = join(path, filename)
        if isfile(full_path):
            with open(full_path) as file:
                frames.append(file.read())
    return frames


def draw(canvas):
    canvas.nodelay(True)
    base_path = os.getcwd()
    rocket_frames = load_frames(join(base_path, 'pics', 'rocket'))
    garbage_frames = load_frames(join(base_path, 'pics', 'garbage'))
    y, x = canvas.getmaxyx()
    curses.curs_set(False)
    global EVENT_LOOP
    EVENT_LOOP += [blink(
        canvas,
        row=random.randint(1, y-1),
        column=random.randint(1, x-1),
        symbol=random.choice('+*.:'),
        offset_tics=random.randint(1, 3),
        ) for _ in range(random.randint(50, 100))]

    multipled_rocket_frames = [frame for frame in rocket_frames for _ in range(2)]
    # shot = fire(canvas, y//2, x//2)
    EVENT_LOOP.append(render_spaceship(canvas, 5, 5, multipled_rocket_frames))
    EVENT_LOOP.append(fill_orbit_with_garbage(canvas, garbage_frames))
    while True:
        for coroutine in EVENT_LOOP.copy():
            try: 
                coroutine.send(None)
            except StopIteration:
                if coroutine.__name__ == 'render_spaceship':
                    break
                EVENT_LOOP.remove(coroutine)
        canvas.refresh()
        time.sleep(0.1)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
