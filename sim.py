import enum
import pygame
from pygame import Color, Rect

pygame.init()

WIDTH, HEIGHT = 1200, 600
FRAMERATE = 60  # Frames per second
# How many times per second the simulation updates (simulation timestep)
PHYSICS_RATE = 2

NUM_LANES = 4
LANE_DIVIDER_WIDTH = 10


screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()



class Car:
    class Intent(enum.Enum):
        NO_CHANGE = 0
        LANE_CHANGE_UP = 1
        LANE_CHANGE_DOWN = 2
        ACCELERATE = 3
        DECELERATE = 4
        
    CAR_WIDTH = 100
    CAR_HEIGHT = 50

    CAR_X_START = 0

    def __init__(self, current_lane: int, goal_lane: int, color: Color, network: CarNetwork):
        # Current lane (y-position on the coordinate grid)
        self.current_lane = current_lane

        # Lane this Car wants to be in in the future
        self.goal_lane = goal_lane

        # X-position on the coordinate grid
        self.x_pos = self.CAR_X_START

        self.color = color
        self.network = network

    def change_lanes(self, new_lane: int):
        """Update grahpics of car to new lane, also store new lane in self.current_lane"""
        # self.rect.top = Car.lane_heights[new_lane]
        self.current_lane = new_lane

    def drive(self):
        """Move car forward CAR_X_SPEED pixels."""
        self.x_pos += 1  # drive forward one space on the grid

        # Choose whether or not to change lanes
        if self.current_lane != self.goal_lane:
            # Express intent here
            # if self.current_lane < self.goal_lane:
            #     self.intent = Car.Intent.LANE_CHANGE_UP
            # elif self.current_lane > self.goal_lane:
            #     self.intent = Car.Intent.LANE_CHANGE_DOWN
            # else:
            #     self.intent = Car.Intent.NO_CHANGE
            # Figure out if safe/smart to change lane (smart part of all this)

            # perform algorithms here

            # Actually change lanes
            if self.current_lane < self.goal_lane:
                # TODO express intent to other cars!
                self.change_lanes(self.current_lane + 1)
            else:
                self.change_lanes(self.current_lane - 1)

    def draw(self, surf: pygame.surface.Surface):
        """Convert coordinate grid points to pixel values
        and draw the rectangle on the surface."""
        X_GRIDSIZE = self.CAR_WIDTH

        x_pix = X_GRIDSIZE * self.x_pos
        lane_heights = {  # TODO make function
            1: HEIGHT // 2 - self.CAR_HEIGHT // 2 + 5 - 200,
            2: HEIGHT // 2 - self.CAR_HEIGHT // 2 + 5 - 100,
            3: HEIGHT // 2 - self.CAR_HEIGHT // 2 + 5,
            4: HEIGHT // 2 - self.CAR_HEIGHT // 2 + 5 + 100,
            5: HEIGHT // 2 - self.CAR_HEIGHT // 2 + 5 + 200,
        }
        y_pix = lane_heights[self.current_lane]
        # Create rect
        rect = Rect(x_pix, y_pix, self.CAR_WIDTH, self.CAR_HEIGHT)
        # Draw that bih
        pygame.draw.rect(surf, self.color, rect)


def main():
    # Define objects on the screen

    # On-screen objects (mostly rectangles)
    cars = [
        Car(1, 4, Color("green"), network),
        Car(2, 5, Color("blue"), network),
        Car(3, 3, Color("red"), network),
        # Car(4, 4),
        # Car(5, 1)
    ]

    road = Rect(0, 50, WIDTH, HEIGHT - 100)
    lanes = [
        Rect(0, 2 * i * road.top + road.top, WIDTH, LANE_DIVIDER_WIDTH)
        for i in range(NUM_LANES + 2)
    ]

    physics_clock = FRAMERATE // PHYSICS_RATE  # Start at max value for first draw

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return  # From main()

        # Draw new frame
        if physics_clock == FRAMERATE // PHYSICS_RATE:
            physics_clock = 0

            screen.fill(Color("darkgreen"))  # Draw grass

            # Draw road
            pygame.draw.rect(screen, Color("black"), road)

            # Draw lanes
            for lane in lanes:
                pygame.draw.rect(screen, Color("white"), lane)

            # Draw cars
            for car in cars:
                car.draw(screen)
                car.drive()

        pygame.display.update()  # Update display buffer (redraw window)
        clock.tick(FRAMERATE)  # Limit framerate
        physics_clock += 1


if __name__ == "__main__":
    main()
