from dataclasses import dataclass
import enum
from typing import Dict, NewType, Tuple
import pygame
from pygame import Color, Rect

pygame.init()

WIDTH, HEIGHT = 1600, 600
FRAMERATE = 60  # Frames per second
# How many times per second the simulation updates (simulation timestep)
PHYSICS_RATE = 2

NUM_LANES = 4
LANE_DIVIDER_WIDTH = 10


screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


class Intent(enum.Enum):
    """What a car plans on doing in ONE unit of time."""

    # Move forward at constant speed.
    # No accel/decel, no lane change.
    NO_CHANGE = 0
    ACCELERATE = 3  # Increase horizontal speed
    DECELERATE = 4  # Devrease horizontal speed

    LANE_CHANGE_UP = 1
    LANE_CHANGE_DOWN = 2


class CarNetwork:
    @dataclass
    class Message:
        # Horizontal coordinate (on the grid, not pix value)
        x: int
        # Vertical coordinate (on the grid)
        curr_lane: int
        intent: Intent

    def __init__(self):
        # key -> car ID, val -> current intent
        self.intents: Dict[int, CarNetwork.Message] = {}

    def broadcast_msg(self, car_id: int, coords: Tuple[int, int], intent: Intent):
        """Broadcast an Intent message to other cars."""
        x, lane = coords
        self.intents[car_id] = self.Message(x, lane, intent)

    def get_messages(self, your_id: int):
        """Retrieve messages from other cars that submitted them, excluding your own message."""
        # Return the messages dict without your id (for convenience).
        return {k: v for k, v in self.intents.items() if k != your_id}


class Car:

    CAR_WIDTH = 100
    CAR_HEIGHT = 50

    CAR_X_START = 0

    # Static class variable, shared across instances, for getting an ID
    __car_ids = 0

    @classmethod
    def get_id(cls) -> int:
        retval = cls.__car_ids
        cls.__car_ids += 1
        return retval

    def __init__(
        self, current_lane: int, goal_lane: int, color: Color, network: CarNetwork
    ):
        # ID of this car for network (basically a MAC address for this car)
        self.id = self.get_id()

        # Current lane (y-position on the coordinate grid)
        self.current_lane = current_lane

        # Lane this Car wants to be in in the future
        self.goal_lane = goal_lane

        # X-position on the coordinate grid
        self.x_pos = self.CAR_X_START

        # X-coordinate points per time unit
        # (how quickly the car advances forward per timestep)
        self.x_speed = 1

        self.color = color
        self.network = network

        self.intent = Intent.NO_CHANGE  # Default: Just keep moving straight ahead.

    def send_intent(self):
        """Send this car's intent into the network. All cars
        will do this step first before taking any actions."""
        # Choose what to do
        if self.current_lane == self.goal_lane:
            self.intent = Intent.NO_CHANGE

        elif self.current_lane > self.goal_lane:
            # You're "below" your goal lane
            self.intent = Intent.LANE_CHANGE_UP

        elif self.current_lane < self.goal_lane:
            # You're "above" your goal lane
            self.intent = Intent.LANE_CHANGE_DOWN

        # Broadcast this to others
        self.network.broadcast_msg(
            self.id, (self.x_pos, self.current_lane), self.intent
        )

    def resolve_conflicts(self):
        """Review intents of other vehicles on the network.
        If any conflicts are detected, change this Car's intent
        according to the agreed upon protocol."""
        other_cars_intents = self.network.get_messages(self.id)
        # TODO determine if your intent is feasible/safe given others' intents
        # TODO change intent if issues arise (e.g., collision):
        # WARNING: Be careful how the simulator handles this, cars may not be able
        # to move yet if conflicts need to be resolved. But, it would be cool if
        # our algorithm resolved conflicts without any additional information/message passing,
        # Which now that I think about it, probably could as long as protocols are defined for
        # different types of conflicts and their solutions are deterministic (non-random)
        # E.g., if the conflict is that a Car in lane 3 and a Car in lane 1 both want to merge
        # to lane 2 but have the same x position, the leftmost car always accelerates and the
        # rightmost car decelerates. If this always happens, then we should be able to resolve the conflict
        # this cycle, and next cycle perform the lane change. Just push back the lane change til next
        # cycle and perform the accelerate/decelerate now.
        pass

    def drive(self):
        """Move the vehicle accoording to its intent (after conflict resolution)"""
        if self.intent == Intent.NO_CHANGE:
            # Drive forward at your current velocity.
            self.x_pos += self.x_speed

        elif self.intent == Intent.LANE_CHANGE_UP:
            self.x_pos += self.x_speed
            self.current_lane -= 1

        elif self.intent == Intent.LANE_CHANGE_DOWN:
            self.x_pos += self.x_speed
            self.current_lane += 1

        elif self.intent == Intent.ACCELERATE:
            self.x_speed += 1
            self.x_pos += self.x_speed

        elif self.intent == Intent.DECELERATE:
            self.x_speed -= 1
            self.x_pos += self.x_speed

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

    network = CarNetwork()

    # Car spawner: At a timestep (key), spawn the list of cars (value)
    car_spawner = {
        0: [Car(1, 4, Color("green"), network), Car(2, 5, Color("blue"), network)],
        1: [Car(3, 3, Color("red"), network)],
        3: [Car(5, 2, Color("brown"), network)],
        5: [Car(2, 4, Color("white"), network), Car(1, 5, Color("orange"), network)],
    }

    cars_on_road = []

    road = Rect(0, 50, WIDTH, HEIGHT - 100)
    lanes = [
        Rect(0, 2 * i * road.top + road.top, WIDTH, LANE_DIVIDER_WIDTH)
        for i in range(NUM_LANES + 2)
    ]

    simtime = 0  # Keeps track of simulation timestep

    physics_clock = FRAMERATE // PHYSICS_RATE  # Start at max value for first draw
    paused = False  # Whether the sim is paused (pauses physics_clock)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return  # From main()
            elif event.type == pygame.KEYDOWN:
                # Handle spacebar press to pause sim
                if event.key == pygame.K_SPACE:
                    paused = not paused
                    print(f"{paused=}")

        # Draw new frame
        if physics_clock == FRAMERATE // PHYSICS_RATE:
            physics_clock = 0

            screen.fill(Color("darkgreen"))  # Draw grass

            # Draw road
            pygame.draw.rect(screen, Color("black"), road)

            # Draw lanes
            for lane in lanes:
                pygame.draw.rect(screen, Color("white"), lane)

            # Spawn in new cars, if any.
            try:
                cars_on_road += car_spawner[simtime]
            except KeyError:
                pass

            # Draw cars to screen.
            # Draw before everything else, because it makes it easier
            # to see the initial state of the cars at t=0.
            for car in cars_on_road:
                car.draw(screen)

            # Each car sends its intent into the network.
            for car in cars_on_road:
                car.send_intent()

            # Cars resolve conflicts with each other.
            for car in cars_on_road:
                car.resolve_conflicts()

            # Cars move to new position.
            for car in cars_on_road:
                car.drive()

            print(f"Current simulation time: {simtime}")
            simtime += 1

        pygame.display.update()  # Update display buffer (redraw window)
        clock.tick(FRAMERATE)  # Limit framerate

        if not paused:
            physics_clock += 1


if __name__ == "__main__":
    main()
