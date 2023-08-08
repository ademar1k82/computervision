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

        self.objectDetection = ObjectJoystick()

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
        self.objectDetection.destroy_window()
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(300, 200,
                                   'Click mouse to start')
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

        self.objectDetection.open_window()

        self.canvas.unbind('<Button-1>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):

        self.objectDetection.detect_camera_object()

        screen_side = self.objectDetection.side

        if screen_side == Screen.LEFT:
            self.paddle.move(-15)
        elif screen_side == Screen.RIGHT:
            self.paddle.move(15)

        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.objectDetection.destroy_window()
            self.ball.speed = None
            self.draw_text(300, 200, 'You win! You the Breaker of Bricks.')
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = None
            self.lives -= 1
            if self.lives < 0:
                self.objectDetection.destroy_window()
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


class ObjectJoystick:

    def __init__(self):
        self.cap = cv2.VideoCapture()
        self.side = Screen.MIDDLE
        self.windowName = "Play!"

    def open_window(self):
        if not self.cap.isOpened():
            self.cap.open(0)

    def get_mask(self, image):

        blur = cv2.GaussianBlur(image, (25, 25), 0)
        # cv2.imshow("Blur", blur)

        hsv = cv2.cvtColor(blur, cv.COLOR_BGR2HSV)

        # threshold blue

        # blue testing

        # blueBGR = np.uint8([[[255, 0, 0]]])
        # hsv_blue = cv2.cvtColor(blueBGR, cv2.COLOR_BGR2HSV)
        # print(hsv_blue)

        light_blue = np.array([90, 80, 0])
        dark_blue = np.array([130, 255, 255])

        # mask = cv2.inRange(hsv, light_blue, dark_blue)
        # cv2.imshow("mask", mask)

        return cv2.inRange(hsv, light_blue, dark_blue)

    def detect_camera_object(self):
        cap = self.cap
        _, image = cap.read()
        image = cv2.flip(image, 1)

        mask = self.get_mask(image)

        contours, _ = cv2.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
        contourIdx = self.get_contourIdx(contours)

        cv2.drawContours(image=image, contours=contours, contourIdx=contourIdx, color=(0, 255, 0), thickness=-1)
        cv2.imshow(self.windowName, image)

        if contourIdx > -1:
            self.side = self.get_screen_position(image, contours[contourIdx])
        else:
            self.side = Screen.MIDDLE

    def get_contourIdx(self, contours):

        countourIdx = -1
        max_area = 0

        for i in range(len(contours)):

            current_contour = contours[i]
            countour_area = cv2.contourArea(current_contour)

            if countour_area > max_area:
                max_area = countour_area
                countourIdx = i

        return countourIdx

    def get_contour_center(self, contour):

        moment = cv2.moments(contour)
        x = int(moment["m10"] / moment["m00"])
        y = int(moment["m01"] / moment["m00"])
        return [x, y]

    def get_screen_position(self, image, contour):
        side = Screen.MIDDLE
        contour_center = self.get_contour_center(contour)

        image_point_o = image.shape[0] / 2

        if image_point_o - 25 > contour_center[0]:
            side = Screen.LEFT
        elif image_point_o - 25 < contour_center[0]:
            side = Screen.RIGHT

        return side

    def destroy_window(self):
        cap = self.cap

        if cap.isOpened():
            cap.release()
            cv2.destroyWindow(self.windowName)


class Screen(Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break those Bricks!')
    game = Game(root)
    game.mainloop()
