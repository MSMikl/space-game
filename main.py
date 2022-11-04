import asyncio
import curses
import os
import random
import time

from itertools import cycle
from os.path import isfile, join

from curses_tools import draw_frame, read_controls


async def blink(canvas, row, column, symbol='*', offset_tics=1):
    while True:
        for _ in range(offset_tics*20):
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await asyncio.sleep(0)

        for _ in range(offset_tics*3):
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await asyncio.sleep(0)

        for _ in range(offset_tics*5):
            canvas.addstr(row, column, symbol, curses.A_BOLD)
            await asyncio.sleep(0)

        for _ in range(offset_tics*3):
            canvas.addstr(row, column, symbol)
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def render_spaceship(canvas, column, row, frames):
    space = False
    size = canvas.getmaxyx()
    # Максимальные координаты окна на единицу меньше размера, поскольку нумерация начинается с 0
    max_y = size[0] - 1
    max_x = size[1] - 1
    ship_width = 6
    ship_length = 8
    for frame in cycle(frames):
        if space:
            break
        draw_frame(canvas, row, column, frame)
        (step_y, step_x, space) = read_controls(canvas)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)
        column = min(column + step_x, max_x - ship_width) if step_x >= 0 else max(column + step_x, 1)
        row = min(row + step_y, max_y - ship_length) if step_y >= 0 else max(row + step_y, 1)


def draw(canvas):
    canvas.nodelay(True)
    base_path = os.getcwd()
    frames = []
    for filename in os.listdir(join(base_path, 'pics')):
        full_path = join(base_path, 'pics', filename)
        if isfile(full_path):
            with open(full_path) as file:
                frames.append(file.read())
    y, x = canvas.getmaxyx()
    coroutines = [blink(
        canvas,
        row=random.randint(1, y-1),
        column=random.randint(1, x-1),
        symbol=random.choice('+*.:'),
        offset_tics=random.randint(1, 3),
        ) for _ in range (random.randint(50, 100))]
    
    multipled_frames = [frame for frame in frames for _ in range(2)]
    print(multipled_frames)
    curses.curs_set(False)
    shot = fire(canvas, y//2, x//2)
    coroutines.append(shot)
    coroutines.append(render_spaceship(canvas, 5, 5, multipled_frames))
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(shot)
        canvas.refresh()
        time.sleep(0.1)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)