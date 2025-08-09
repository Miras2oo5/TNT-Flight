import random
import math
import os
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.uix.button import Button

Window.size = (800, 600)  # Только для ПК

class Plane(Image):
    def __init__(self, **kwargs):
        self.target = kwargs.pop('target', Window.center)
        super().__init__(**kwargs)
        self.dragging = False
        self.speed = 2
        self.angle = 0

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dragging = True
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.dragging:
            self.center_x = touch.x
            self.center_y = touch.y
            return True

    def on_touch_up(self, touch):
        if self.dragging:
            self.dragging = False

    def move_towards_target(self):
        if not self.dragging:
            dx = self.target[0] - self.center_x
            dy = self.target[1] - self.center_y
            dist = math.hypot(dx, dy)
            if dist > 1:
                self.center_x += self.speed * dx / dist
                self.center_y += self.speed * dy / dist

                angle_rad = math.atan2(dy, dx)
                self.angle = math.degrees(angle_rad)
                # Если картинка смотрит вверх, замени на:
                # self.angle = math.degrees(angle_rad) - 90
            else:
                pass


class Game(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        bg_path = os.path.join(os.path.dirname(__file__), "assets", "background.png")
        self.background = Image(
            source=bg_path,
            size=Window.size,
            pos=(0, 0),
            size_hint=(None, None)
        )
        self.background.allow_stretch = True
        self.background.keep_ratio = False

        self.add_widget(self.background, index=0)

        self.planes = []
        self.game_over = False
        self.time_alive = 0
        self.best_time = 0
        self.restart_button = None

        self.best_label = Label(
            text="Best Score: 0",
            font_size=20,
            color=(1, 1, 0, 1),
            size_hint=(None, None),
            pos=(Window.width - 150, Window.height - 40)
        )
        self.add_widget(self.best_label)
 
        Clock.schedule_interval(self.update, 1/60)
        Clock.schedule_interval(self.spawn_plane, 2)
        Clock.schedule_interval(self.update_timer, 1)

        Window.bind(on_resize=self.update_best_label_pos)

    def update_best_label_pos(self, *args):
        self.best_label.pos = (Window.width - 150, Window.height - 40)

    def spawn_plane(self, dt):
        if self.game_over:
            return

        side = random.choice(["top", "bottom", "left", "right"])
        path = os.path.join(os.path.dirname(__file__), "assets", "plane.png")

        if side == "top":
            x = random.randint(0, Window.width)
            y = Window.height + 50
            target = (random.randint(0, Window.width), -50)
        elif side == "bottom":
            x = random.randint(0, Window.width)
            y = -50
            target = (random.randint(0, Window.width), Window.height + 50)
        elif side == "left":
            x = -50
            y = random.randint(0, Window.height)
            target = (Window.width + 50, random.randint(0, Window.height))
        elif side == "right":
            x = Window.width + 50
            y = random.randint(0, Window.height)
            target = (-50, random.randint(0, Window.height))

        plane = Plane(source=path, size_hint=(None, None), size=(64, 64), target=target)
        plane.center_x = x
        plane.center_y = y

        self.planes.append(plane)
        self.add_widget(plane)

    def update(self, dt):
        if self.game_over:
            return

        for plane in self.planes:
            plane.move_towards_target()

        self.planes = [p for p in self.planes if
                       -50 <= p.center_x <= Window.width + 50 and
                       -50 <= p.center_y <= Window.height + 50]

        for child in self.children[:]:
            if isinstance(child, Plane) and child not in self.planes:
                self.remove_widget(child)

        self.check_collisions()

    def check_collisions(self):
        visible_planes = [p for p in self.planes if
                          0 <= p.center_x <= Window.width and
                          0 <= p.center_y <= Window.height]

        for i in range(len(visible_planes)):
            for j in range(i + 1, len(visible_planes)):
                p1 = visible_planes[i]
                p2 = visible_planes[j]
                dist = math.hypot(p1.center_x - p2.center_x, p1.center_y - p2.center_y)
                if dist < 50:
                    explosion_pos = ((p1.center_x + p2.center_x) / 2, (p1.center_y + p2.center_y) / 2)
                    self.end_game(explosion_pos=explosion_pos)

    def update_timer(self, dt):
        if not self.game_over:
            self.time_alive += 1

    def end_game(self, explosion_pos=None):
        self.game_over = True

        # Обновляем лучший рекорд, если нужно
        if self.time_alive > self.best_time:
            self.best_time = self.time_alive
            self.best_label.text = f"Best Score: {self.best_time}"

        if explosion_pos:
            explosion_path = os.path.join(os.path.dirname(__file__), "assets", "explosion.png")
            explosion = Image(source=explosion_path, size=(128, 128), size_hint=(None, None))
            explosion.center = explosion_pos
            self.add_widget(explosion)

            anim = Animation(opacity=0, duration=1.0)
            anim.bind(on_complete=lambda *args: self.show_game_over_label())
            anim.start(explosion)
        else:
            self.show_game_over_label()

    def show_game_over_label(self):
        label = Label(
            text=f"GAME OVER\nTime: {self.time_alive} sec",
            font_size=32,
            color=(1, 0, 0, 1),
            center=Window.center
        )
        self.add_widget(label)

        self.restart_button = Button(
            text="Restart",
            size_hint=(None, None),
            size=(200, 60),
            pos=(Window.width/2 - 100, Window.height/2 - 100)
        )
        self.restart_button.bind(on_release=self.on_restart_pressed)
        self.add_widget(self.restart_button)

    def on_restart_pressed(self, instance):
        if self.restart_button:
            self.remove_widget(self.restart_button)
            self.restart_button = None

        # Удаляем все надписи Game Over
        for child in self.children[:]:
            if isinstance(child, Label):
                self.remove_widget(child)

        self.reset_game()

    def reset_game(self):
        # Удаляем все самолеты
        for plane in self.planes[:]:
            if plane in self.children:
                self.remove_widget(plane)
        self.planes.clear()

        self.time_alive = 0
        self.game_over = False


class AirTrafficApp(App):
    def build(self):
        return Game()


if __name__ == "__main__":
    AirTrafficApp().run()
