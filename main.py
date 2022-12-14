import asyncio
import curses
import os
import random
import time

from itertools import cycle
from os.path import isfile, join

from curses_tools import draw_frame, read_controls, get_frame_size
from explosion import explode
from game_scenario import get_garbage_delay_tics, PHRASES
from obstacles import Obstacle, show_obstacles, has_collision
from physics import update_speed
from space_garbage import fly_garbage


event_loop = []
obstacles = []
year = 1957


class GameOverException(Exception):
    pass


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def change_year():
    global year
    while True:
        await sleep(15)
        year += 1


async def show_text(canvas):
    current_year = year
    text = f"{year} {PHRASES.get(year, '')}"
    while True:
        if current_year != year:
            current_year = year
            text = f"{year} {PHRASES.get(year, '')}"
        canvas.addnstr(text, len(text))
        canvas.refresh()
        await sleep(1)
        canvas.clear()


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
        for obstacle in obstacles.copy():
            if has_collision((obstacle.row, obstacle.column), (obstacle.rows_size, obstacle.columns_size), (row, column)):
                obstacle.row = -1
                obstacles.remove(obstacle)
                event_loop.append(explode(canvas, row, column))
                return
        canvas.addstr(round(row), round(column), symbol)
        await sleep(1)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def fill_orbit_with_garbage(canvas, garbage_frames):
    max_row, max_column = canvas.getmaxyx()
    while True:
        if not get_garbage_delay_tics(year):
            await sleep(15)
            continue
        for obstacle in obstacles.copy():
            if obstacle.row >= max_row:
                obstacles.remove(obstacle)
        start_column = random.randint(0, max_column - 1)
        frame = random.choice(garbage_frames)
        frame_height, frame_width = get_frame_size(frame)
        obstacle = Obstacle(0, start_column, frame_height, frame_width)
        obstacles.append(obstacle)
        event_loop.append(fly_garbage(canvas, start_column, frame, speed=0.2, obstacle=obstacle))
        await sleep(get_garbage_delay_tics(year))


async def game_over(canvas, row, column, frames):
    while True:
        draw_frame(canvas, row, column, frames[0])
        await sleep(1)


async def render_spaceship(canvas, column, row, frames):
    global event_loop
    size = canvas.getmaxyx()
    # ???????????????????????? ???????????????????? ???????? ???? ?????????????? ???????????? ??????????????, ?????????????????? ?????????????????? ???????????????????? ?? 0
    max_y = size[0] - 1
    max_x = size[1] - 1
    ship_length, ship_width = get_frame_size(frames[0])
    row_speed = column_speed = 0
    game_exit = False
    for frame in cycle(frames):
        step_y, step_x, space, game_exit = read_controls(canvas)
        row_speed, column_speed = update_speed(row_speed, column_speed, step_y, step_x)
        if game_exit:
            raise GameOverException()
        column = min(column + column_speed, max_x - ship_width) if column_speed >= 0 else max(column + column_speed, 0)
        row = min(row + row_speed, max_y - ship_length) if row_speed >= 0 else max(row + row_speed, 0)
        draw_frame(canvas, row, column, frame)
        for obstacle in obstacles:
            if has_collision((obstacle.row, obstacle.column), (obstacle.rows_size, obstacle.columns_size), (row, column), (ship_length, ship_width)):
                draw_frame(canvas, row, column, frame, negative=True)
                raise GameOverException()
        if space and year >= 2020:
            event_loop.append(fire(canvas, row, column + ship_width//2, rows_speed = -2 + row_speed))
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
    global event_loop
    canvas.nodelay(True)
    base_path = os.getcwd()
    rocket_frames = load_frames(join(base_path, 'pics', 'rocket'))
    garbage_frames = load_frames(join(base_path, 'pics', 'garbage'))
    gameover_frame = load_frames(join(base_path, 'pics', 'gameover'))
    y, x = canvas.getmaxyx()
    year_window = canvas.derwin(2, 26, y - 2, x//2 - 13)
    curses.curs_set(False)
    event_loop += [blink(
        canvas,
        row=random.randint(1, y-1),
        column=random.randint(1, x-1),
        symbol=random.choice('+*.:'),
        offset_tics=random.randint(1, 3),
        ) for _ in range(random.randint(50, 100))]

    multipled_rocket_frames = [frame for frame in rocket_frames for _ in range(2)]
    event_loop.append(render_spaceship(canvas, 5, 5, multipled_rocket_frames))
    event_loop.append(fill_orbit_with_garbage(canvas, garbage_frames))
    # event_loop.append(show_obstacles(canvas, obstacles))
    event_loop.append(change_year())
    event_loop.append(show_text(year_window))
    while True:
        for coroutine in event_loop.copy():
            try: 
                coroutine.send(None)
            except StopIteration:
                event_loop.remove(coroutine)
            except GameOverException:
                event_loop = [game_over(canvas, 10, 10, gameover_frame)]

        canvas.refresh()
        time.sleep(0.1)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
