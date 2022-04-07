import enum
import pygame
from pygame import Color, Rect

pygame.init()

WIDTH, HEIGHT = 1200, 600

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

    CAR_X_SPEED = CAR_WIDTH
    CAR_X_START = 0

    lane_heights = {
        1: HEIGHT // 2 - CAR_HEIGHT // 2 + 5 - 200,
        2: HEIGHT // 2 - CAR_HEIGHT // 2 + 5 - 100,
        3: HEIGHT // 2 - CAR_HEIGHT // 2 + 5,
        4: HEIGHT // 2 - CAR_HEIGHT // 2 + 5 + 100,
        5: HEIGHT // 2 - CAR_HEIGHT // 2 + 5 + 200,
    }

    def __init__(self, current_lane: int, goal_lane: int):
        # rect for drawing
        self.rect = Rect(Car.CAR_X_START, Car.lane_heights[current_lane], Car.CAR_WIDTH, Car.CAR_HEIGHT)
        self.color = Color('white')

        self.current_lane = current_lane
        self.goal_lane = goal_lane
        
        self.intent: Car.Intent = Car.Intent.NO_CHANGE  # TODO broadcast via a @property

        self.intent_messages = []
    
    def change_lanes(self, new_lane: int):
        """Update grahpics of car to new lane, also store new lane in self.current_lane"""
        self.rect.top = Car.lane_heights[new_lane]
        self.current_lane = new_lane

    def drive(self):
        """Move car forward CAR_X_SPEED pixels."""
        self.rect.move_ip(Car.CAR_X_SPEED, 0)  # drive forward

        # Choose whether or not to change lanes
        if self.current_lane != self.goal_lane:
            # Express intent here
            if self.current_lane < self.goal_lane:
                self.intent = Car.Intent.LANE_CHANGE_UP
            elif self.current_lane > self.goal_lane:
                self.intent = Car.Intent.LANE_CHANGE_DOWN
            else:
                self.intent = Car.Intent.NO_CHANGE
            # Figure out if safe/smart to change lane (smart part of all this)

            #perform algorithms here

            # Actually change lanes
            if(self.current_lane < self.goal_lane):
                # TODO express intent to other cars!
                self.change_lanes(self.current_lane + 1)
            else:
                self.change_lanes(self.current_lane - 1)
    
    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect)

# Define objects on the screen


# On-screen objects (mostly rectangles)
cars = [
    Car(1, 4),
    Car(2, 5),
    #Car(3, 3),
    #Car(4, 4),
    # Car(5, 1)
]

road = Rect(0, 50, WIDTH, HEIGHT - 100)
lanes = [Rect(0, 2 * i * road.top + road.top, WIDTH, LANE_DIVIDER_WIDTH) for i in range(NUM_LANES + 2)]


physics_count = 60
first_draw = True

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # draw lanes
    if physics_count == 60:
        screen.fill(Color("darkgreen"))  # Draw grass

        # draw our road here
        pygame.draw.rect(screen, Color("black"), road)

        for car in cars:
            car.draw(screen)
            car.drive()

        for lane in lanes:
            pygame.draw.rect(screen, Color("white"), lane)

        physics_count = 0

    pygame.display.update()  # Updates display buffer (redraws window)
    clock.tick(60)  # Limit framerate
    physics_count += 1

