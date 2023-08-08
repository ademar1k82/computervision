import tkinter as tk
from enum import Enum

import cv2
import cv2 as cv
import numpy as np


class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1]
        # increase the below value to increase the speed of ball
        self.speed = 5
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#FFB643')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item,
                                   fill=Brick.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#D6D1F5',
                                width=self.width,
                                height=self.height, )
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 326)
        self.items[self.paddle.item] = self.paddle

        self.move_detection = MoveJoystick()

        # adding brick with different hit capacities - 3,2 and 1
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None
        self.setup_game()
        self.canvas.focus_set()
        # self.canvas.bind('<Left>', lambda _: self.paddle.move(-10))
        # self.canvas.bind('<Right>', lambda _: self.paddle.move(10))

    def setup_game(self):
        self.move_detection.destroy_window()
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(300, 200,
                                   'Click Mouse to start')
        self.canvas.bind('<Button-1>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40'):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text,
                                       font=font)

    def update_lives_text(self):
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):

        self.move_detection.open_window()

        self.canvas.unbind('<Button-1>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):

        screen_move = self.move_detection.on_move_detection

        if screen_move == Screen.LEFT:
            self.paddle.move(-15)
        elif screen_move == Screen.RIGHT:
            self.paddle.move(15)

        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.ball.speed = None
            self.draw_text(300, 200, 'You win! You the Breaker of Bricks.')
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = None
            self.lives -= 1
            if self.lives < 0:
                self.move_detection.destroy_window()
                self.draw_text(300, 200, 'You Lose! Game Over!')
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)


class MoveJoystick:

    def __init__(self):
        self.next_gray = None
        self.previous_gray = None
        self.cap = cv2.VideoCapture()
        self.window_name = "Motion Play!"

    def open_window(self):

        if not self.cap.isOpened():
            self.cap.open(0)

        ret, frame1 = self.cap.read()
        frame1 = cv2.flip(frame1, 1)
        blur1 = cv2.GaussianBlur(frame1, (25, 25), 0)

        #cv2.imshow("Gaussian blur", blur1)

        self.previous_gray = cv2.cvtColor(blur1, cv.COLOR_BGR2GRAY)

    @property
    def on_move_detection(self):
        cap = self.cap

        ret, frame2 = cap.read()
        frame2 = cv2.flip(frame2, 1)
        blur2 = cv2.cvtColor(frame2, cv.COLOR_BGR2GRAY)

        self.next_gray = cv2.GaussianBlur(blur2, (25, 25), 0)

        farneback = cv2.calcOpticalFlowFarneback(prev=self.previous_gray, next=self.next_gray, flow=None,
                                                 pyr_scale=0.5,  # 0.5,
                                                 levels=1,  # 3,
                                                 winsize=10,  # 15,
                                                 iterations=1,  # 3,
                                                 poly_n=5,
                                                 poly_sigma=1.1,
                                                 flags=0)
        threshold = 2.0

        # flow_norm = np.sqrt(farneback[:, :, 0] ** 2 + farneback[:, :, 1] ** 2)
        # flow_norm_norm = cv2.normalize(flow_norm, None, 0.0, 1.0, cv2.NORM_MINMAX)
        # cv2.imshow("Flow", flow_norm_norm)

        flow_xx = farneback[:, :, 0]

        left_move = np.count_nonzero(flow_xx < -threshold)
        right_move = np.count_nonzero(flow_xx > threshold)

        cv2.imshow(self.window_name, frame2)

        # print("Going left: " + str(left_move))
        # print("Going right: " + str(right_move))

        if left_move < 300:
            left_move = 0

        if right_move < 300:
            right_move = 0

        self.previous_gray = self.next_gray

        if left_move > right_move:
            return Screen.LEFT
        elif left_move < right_move:
            return Screen.RIGHT
        else:
            return Screen.CENTER

    def destroy_window(self):
        cap = self.cap

        if cap.isOpened():
            cap.release()
            cv2.destroyWindow(self.window_name)


class Screen(Enum):
    LEFT = 0
    RIGHT = 1
    CENTER = 2


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break those Bricks!')
    game = Game(root)
    game.mainloop()
