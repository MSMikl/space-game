import asyncio
import curses
import random
import time

from itertools import cycle

from curses_tools import draw_frame, read_controls


async def blink(canvas, row, column, symbol='*'):
    while True:
        for _ in range (random.randint(5, 20)):
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await asyncio.sleep(0)

        for _ in range (random.randint(2, 5)):
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await asyncio.sleep(0)

        for _ in range (random.randint(4, 12)):
            canvas.addstr(row, column, symbol, curses.A_BOLD)
            await asyncio.sleep(0)

        for _ in range (random.randint(3, 9)):
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


async def spaceship(canvas, column, row, frames):
    iterator = cycle(frames)
    frame = next(iterator)
    space = False
    max_y, max_x = canvas.getmaxyx()
    while not space:
        draw_frame(canvas, row, column, frame)
        move_x = 0
        move_y = 0
        for _ in range(2):
            (y, x, space) = read_controls(canvas)
            move_x += x
            move_y += y
            await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)
        column = min(column + move_x, max_x - 6) if move_x >= 0 else max(column + move_x, 1)
        row = min(row + move_y, max_y - 10) if move_y >= 0 else max(row + move_y, 1)
        frame = next(iterator)


def draw(canvas):
    canvas.nodelay(True)
    with open('./pics/rocket_frame_1.txt') as file:
        frame1 = file.read()
    print(frame1)
    with open('./pics/rocket_frame_2.txt') as file:
        frame2 = file.read()
    print(frame2)
    frames = [frame1, frame2]
    curses.curs_set(False)
    y, x = canvas.getmaxyx()
    shot = fire(canvas, y//2, x//2)
    animation = spaceship(canvas, 5, 5, frames)
    coroutines = [blink(
        canvas,
        row=random.randint(1, y-1),
        column=random.randint(1, x-1),
        symbol=random.choice('+*.:'),
        ) for _ in range (random.randint(50, 100))]
    is_shot = True
    while True:
        for coroutine in coroutines:
            coroutine.send(None)
        if is_shot:
            try:
                shot.send(None)
            except StopIteration:
                is_shot = False
        animation.send(None)

        canvas.refresh()
        time.sleep(0.1)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)