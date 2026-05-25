import math
import logging
import arcade
import pymunk

from game_object import Bird, Column, Pig, YellowBird, BlueBird
from game_logic import get_impulse_vector, Point2D, get_distance

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("arcade").setLevel(logging.WARNING)
logging.getLogger("pymunk").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

logger = logging.getLogger("main")

WIDTH = 1800
HEIGHT = 800
TITLE = "Angry birds"
GRAVITY = -900


class App(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture("assets/img/background3.png")
        # crear espacio de pymunk
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)

        # agregar piso
        floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        floor_shape = pymunk.Segment(floor_body, [0, 15], [WIDTH, 15], 0.0)
        floor_shape.collision_type = 999
        floor_shape.friction = 10
        self.space.add(floor_body, floor_shape)

        self.sprites = arcade.SpriteList()
        self.birds = arcade.SpriteList()
        self.world = arcade.SpriteList()

        self.current_bird_type = "red"

        #self.add_columns()
        #self.add_pigs()
        self.level = 1
        self.score = 0
        self.load_level()

        self.start_point = Point2D()
        self.end_point = Point2D()
        self.distance = 0
        self.draw_line = False

        # agregar un collision handler
        self.handler = self.space.add_default_collision_handler()
        self.handler.post_solve = self.collision_handler


    def load_level(self):

        # limpiar mundo anterior
        for obj in self.world:
            obj.remove_from_sprite_lists()

            if obj.body in self.space.bodies:
                self.space.remove(obj.body, obj.shape)

        self.world.clear()

        # LEVEL 1
        if self.level == 1:

            for x in range(WIDTH // 2, WIDTH, 400):

                column = Column(x, 50, self.space)

                self.sprites.append(column)
                self.world.append(column)

            pig = Pig(WIDTH / 2, 100, self.space)

            self.sprites.append(pig)
            self.world.append(pig)

            self.target_score = 100

        # LEVEL 2
        elif self.level == 2:

            for x in range(WIDTH // 2, WIDTH, 250):

                column = Column(x, 50, self.space)

                self.sprites.append(column)
                self.world.append(column)

            pig1 = Pig(WIDTH / 2, 100, self.space)
            pig2 = Pig(WIDTH / 2 + 250, 100, self.space)

            self.sprites.append(pig1)
            self.sprites.append(pig2)

            self.world.append(pig1)
            self.world.append(pig2)

            self.target_score = 300

        # LEVEL 3
        elif self.level == 3:

            for x in range(WIDTH // 2, WIDTH, 180):

                column = Column(x, 50, self.space)

                self.sprites.append(column)
                self.world.append(column)

            for i in range(4):

                pig = Pig(WIDTH / 2 + i * 200, 100, self.space)

                self.sprites.append(pig)
                self.world.append(pig)

            self.target_score = 1000

    def get_active_bird(self):
        if len(self.birds) == 0:
            return None

        bird = self.birds[-1]

        # si tocó el suelo
        if bird.has_touched_ground:
            return None

        # si salió de la pantalla
        if (
            bird.center_x < 0
            or bird.center_x > WIDTH
            or bird.center_y < 0
            or bird.center_y > HEIGHT
        ):
            return None

        return bird

    
    def on_key_press(self, symbol, modifiers):

        if symbol == arcade.key.R:
            self.current_bird_type = "red"

        elif symbol == arcade.key.A:
            self.current_bird_type = "yellow"

        elif symbol == arcade.key.B:
            self.current_bird_type = "blue"
            

    def collision_handler(self, arbiter, space, data):
        shapes = arbiter.shapes

        # detectar contacto con el suelo
        for bird in self.birds:

            if bird.shape in shapes:

                for shape in shapes:

                    if shape.collision_type == 999:
                        bird.has_touched_ground = True

        impulse_norm = arbiter.total_impulse.length
        if impulse_norm < 100:
            return True
        logger.debug(impulse_norm)
        if impulse_norm > 1200:
            for obj in self.world:
                if obj.shape in arbiter.shapes:
                    if isinstance(obj, Pig):
                        self.score += 100

                    elif isinstance(obj, Column):
                        self.score += 25
                    obj.remove_from_sprite_lists()
                    self.space.remove(obj.shape, obj.body)

        return True

    def add_columns(self):
        for x in range(WIDTH // 2, WIDTH, 400):
            column = Column(x, 50, self.space)
            self.sprites.append(column)
            self.world.append(column)

    def add_pigs(self):
        pig1 = Pig(WIDTH / 2, 100, self.space)
        self.sprites.append(pig1)
        self.world.append(pig1)

    def on_update(self, delta_time: float):
        self.space.step(1 / 60.0)  # actualiza la simulacion de las fisicas
        self.sprites.update(delta_time)
        if self.score >= self.target_score:

            self.level += 1

            self.load_level()

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        active_bird = self.get_active_bird()

        # si hay un pajaro volando se activar poder
        if active_bird is not None:

            if isinstance(active_bird, YellowBird):
                active_bird.activate_power()

            elif isinstance(active_bird, BlueBird):

                new_birds = active_bird.activate_power()

                for bird in new_birds:
                    self.sprites.append(bird)
                    self.birds.append(bird)

            return

        # si no hay pajaro volando se inicia arrastre
        self.start_point = Point2D(x, y)
        self.end_point = Point2D(x, y)

        self.draw_line = True

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        if buttons == arcade.MOUSE_BUTTON_LEFT:
            self.end_point = Point2D(x, y)
            logger.debug(f"Dragging to: {self.end_point}")

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # evitar disparar si no estabamos arrastrando
        if not self.draw_line:
            return


        self.draw_line = False

        impulse_vector = get_impulse_vector(
            self.start_point,
            self.end_point
        )

        if self.current_bird_type == "red":

            bird = Bird(
                "assets/img/red-bird3.png",
                impulse_vector,
                x,
                y,
                self.space
            )

        elif self.current_bird_type == "yellow":

            bird = YellowBird(
                impulse_vector,
                x,
                y,
                self.space
            )

        else:

            bird = BlueBird(
                impulse_vector,
                x,
                y,
                self.space
            )

        self.sprites.append(bird)
        self.birds.append(bird)

    def on_draw(self):
        self.clear()
        # arcade.draw_lrwh_rectangle_textured(0, 0, WIDTH, HEIGHT, self.background)
        arcade.draw_texture_rect(self.background, arcade.LRBT(0, WIDTH, 0, HEIGHT))
        self.sprites.draw()
        if self.draw_line:
            arcade.draw_line(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y,
                             arcade.color.BLACK, 3)
        
        arcade.draw_text(
            "Key R: Red Bird   Key A: Yellow Bird   Key B: Blue Bird",
            20,
            HEIGHT - 40,
            arcade.color.BLACK,
            20,
            bold=True
        )
        
        arcade.draw_text(
            f"Nivel: {self.level}",
            20,
            HEIGHT - 75,
            arcade.color.BLACK,
            20,
            bold=True
        )
        arcade.draw_text(
            f"Puntaje: {self.score}",
            20,
            HEIGHT - 110,
            arcade.color.BLACK,
            20,
            bold=True
        )


def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    game = App()
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()