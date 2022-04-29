from dataclasses import dataclass
from pprint import pprint
from enum import Enum
import sys
from typing import Dict, List, Tuple
import pygame
from pygame import Color, Rect

WIDTH, HEIGHT = 1600, 600
FRAMERATE = 60  # Frames per second
# How many times per second the simulation updates (simulation timestep)
PHYSICS_RATE = 2

NUM_LANES = 4
LANE_DIVIDER_WIDTH = 10

SPEED_LIMIT = 2  # 2 grid spaces per timestep


class Intent(Enum):
    """What a car plans on doing in ONE unit of time."""

    # Move forward at constant speed.
    # No accel/decel, no lane change.
    NO_CHANGE = 0
    ACCELERATE = 3  # Increase horizontal speed
    DECELERATE = 4  # Devrease horizontal speed

    LANE_CHANGE_UP = -1
    LANE_CHANGE_DOWN = 1


class CarNetwork:
    """Represents a communications network between cars. 
    Is basically a dictionary the cars all write to and read from.
    Cars will interact with the functions in this class to send and
    receive data with each other."""
    @dataclass
    class Message:
        """Information cars will send to each other in the CarNetwork."""
        id_: int
        # Horizontal coordinate (on the grid, not pix value)
        x_pos: int
        x_speed: int
        # Vertical coordinate (on the grid)
        curr_lane: int
        intent: Intent

    def __init__(self):
        # key -> car ID, val -> current intent
        self.intents: Dict[int, CarNetwork.Message] = {}

    def broadcast_msg(self, car_id: int, coords: Tuple[int, int], speed: int, intent: Intent):
        """Broadcast an Intent message to other cars."""
        x, lane = coords
        self.intents[car_id] = self.Message(car_id, x, speed, lane, intent,)

    def get_messages(self, your_id: int) -> Dict[int, Message]:
        """Retrieve messages from other cars that submitted them, excluding your own message."""
        # Return the messages dict without your id (for convenience).
        return {k: v for k, v in self.intents.items() if k != your_id}

class Car:

    CAR_WIDTH = 100
    CAR_HEIGHT = 50

    CAR_X_START = 0

    # Static class variable for getting an ID
    __car_ids = 0

    @classmethod
    def get_id(cls) -> int:
        """Get a unique car ID."""
        retval = cls.__car_ids
        cls.__car_ids += 1
        return retval

    def __init__(
        self, current_lane: int, goal_lane: int, color: str, network: CarNetwork
    ):
        # Save arguments passed to this object for resetting later
        self.__initial_state = locals()
        del self.__initial_state["self"]  # Don't need self for the reset().

        # ID of this car for network (basically a MAC address for this car)
        self.ID = self.get_id()  # TODO need to save in initial_state!!!

        # Current lane (y-position on the coordinate grid)
        self.current_lane = current_lane

        # Lane this Car wants to be in in the future
        self.goal_lane = goal_lane

        # X-position on the coordinate grid
        self.x_pos = self.CAR_X_START

        # X-coordinate points per time unit
        # (how quickly the car advances forward per timestep)
        self.x_speed = SPEED_LIMIT
        
        self.color_name = color
        self.COLOR = Color(color)
        self.network = network

        self.intent = Intent.NO_CHANGE  # Default: Just keep moving straight ahead.

    def reset(self):
        """Reset all variables for this car, returning
        it to its initial state when first constructed."""
        self.__init__(**self.__initial_state)

    def send_intent(self):
        """Send this car's intent into the network. All cars
        will do this step first before taking any actions."""
        # Choose what to do
        
        # Drive at the speed limit unless you were performing a maneuver
        if self.x_speed > SPEED_LIMIT:
            self.intent = Intent.DECELERATE
        elif self.x_speed < SPEED_LIMIT:
            self.intent = Intent.ACCELERATE
        
        # Change lanes if you need to
        elif self.current_lane == self.goal_lane:
            self.intent = Intent.NO_CHANGE

        elif self.current_lane > self.goal_lane:
            # You're "below" your goal lane
            self.intent = Intent.LANE_CHANGE_UP

        elif self.current_lane < self.goal_lane:
            # You're "above" your goal lane
            self.intent = Intent.LANE_CHANGE_DOWN

        # Broadcast this to others
        self.network.broadcast_msg(
            self.ID, (self.x_pos, self.current_lane), self.x_speed, self.intent
        )

    def resolve_conflicts(self):
        """Review intents of other vehicles on the network.
        If any conflicts are detected, change this Car's intent
        according to the agreed upon protocol."""
        other_cars_intents = self.network.get_messages(self.ID)
        # Determine if your intent is feasible/safe given others' intents, change intent if conflicts are detected.

        other_cars = other_cars_intents.values()
        
        print(f"{self.color_name} car (x={self.x_pos}): {other_cars=}")

        # Helper functions

        def calc_future_position(intent: Intent, curr_lane: int, curr_x: int, curr_speed: int) -> Tuple[int, int]:
            if intent == Intent.LANE_CHANGE_DOWN:
                new_lane = curr_lane + 1
            elif intent == Intent.LANE_CHANGE_UP:
                new_lane = curr_lane - 1
            else:
                new_lane = curr_lane
            
            # Calculate new x
            new_x = curr_x + curr_speed
            return new_x, new_lane

        # Helper functions for car logic
        above = lambda a, b: a < b
        below = lambda a, b: a > b

        my_future_position = calc_future_position(self.intent, self.current_lane, self.x_pos, self.x_speed)
        
        # Do any overlap?
        conflicting_cars = [car for car in other_cars if calc_future_position(car.intent, car.curr_lane, car.x_pos, car.x_speed) == my_future_position]
        # TODO this probably shouldn't be a list, there is only ever 1 scenario where this could happen, right?
        
        pprint(f"{self.color_name} car: {conflicting_cars=}")

        if conflicting_cars:
            # Change intent to avoid a collision!
            # In this scenario, two cars intend on moving into the same lane.
            # Choose next intent based on predefined rules: Left car accelerates, right car decelerates.
            if above(self.current_lane, conflicting_cars[0].curr_lane):
                # We are above them. Speed up.
                self.intent = Intent.ACCELERATE
            else:
                # We are beneath them. Slow down
                self.intent = Intent.DECELERATE
            

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

            if self.x_speed <= 0: raise AssertionError(f"self.x_speed = {self.x_speed}, should be > 0")
            
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
        pygame.draw.rect(surf, self.COLOR, rect)

    def draw_intent(self, surf: pygame.surface.Surface):
        """Draw a line showing where the car intends to move"""           
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
        # Get new x and y pixel values to draw the line
        
        # X
        if self.intent == Intent.DECELERATE:
            new_x_pix = X_GRIDSIZE * (self.x_pos + self.x_speed - 1)
        elif self.intent == Intent.ACCELERATE:
            new_x_pix = X_GRIDSIZE * (self.x_pos + self.x_speed + 1)
        else:
            # In all other cases (including lane changes), the car will move forward one unit.
            new_x_pix = X_GRIDSIZE * (self.x_pos + self.x_speed)

        # Y
        
        if self.intent == Intent.LANE_CHANGE_DOWN:
            new_y_pix = lane_heights[self.current_lane + 1]
        elif self.intent == Intent.LANE_CHANGE_UP:
            new_y_pix = lane_heights[self.current_lane - 1]
        else:
            new_y_pix = y_pix

        # Center lines 
        x_pix += self.CAR_WIDTH // 2
        new_x_pix += self.CAR_WIDTH // 2
        y_pix += self.CAR_HEIGHT // 2
        new_y_pix += self.CAR_HEIGHT // 2
        
        pygame.draw.line(surf, self.COLOR, (x_pix, y_pix), (new_x_pix, new_y_pix), width=3)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    
    # Define objects on the screen
    network = CarNetwork()

    font = pygame.font.SysFont('calibri', 32)

    # Car spawner: At a timestep (key), spawn the list of cars (value)
    # Index is each scenario, selected with number input.
    # TODO refactor into a class or something. Not great impl here
    car_spawner = [
        {
            0: [Car(1, 4, "green", network), Car(2, 5, "blue", network)],
            1: [Car(3, 3, "red", network)],
            3: [Car(5, 2, "brown", network)],
            5: [
                Car(2, 4, "white", network),
                Car(1, 5, "orange", network),
            ],
        },
        {0: [Car(2, 3, "blue", network), Car(4, 3, "orange", network)]},
    ]
    # Which scenario will be selected from the car spawner?
    try:
        scenario = int(sys.argv[1])
    except IndexError:
        scenario = 1
    

    cars_on_road: List[Car] = []

    road = Rect(0, 50, WIDTH, HEIGHT - 100)
    lanes = [
        Rect(0, 2 * i * road.top + road.top, WIDTH, LANE_DIVIDER_WIDTH)
        for i in range(NUM_LANES + 2)
    ]

    simtime = 0  # Keeps track of simulation timestep

    show_intent_lines = True

    physics_clock = FRAMERATE / PHYSICS_RATE  # Start at max value for first draw
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

                # Toggle intent lines
                elif event.key == pygame.K_d:
                    show_intent_lines = not show_intent_lines
                    if show_intent_lines:
                        print("Showing intent lines")
                    else:
                        print("Hiding intent lines")

                # Handle different scenarios
                elif event.key == pygame.K_1:
                    # Reset simulation
                    cars_on_road.clear()
                    simtime = 0
                    scenario = 0
                    physics_clock = FRAMERATE / PHYSICS_RATE  # Start at max value for first draw
                    # Reset cars
                    for cars in car_spawner[scenario].values():
                        for car in cars:
                            car.reset()
                        
                    print(f"Switching to scenario {scenario+1}")


                elif event.key == pygame.K_2:
                    cars_on_road.clear()
                    simtime = 0
                    scenario = 1
                    physics_clock = FRAMERATE / PHYSICS_RATE  # Start at max value for first draw
                    # Reset cars
                    for cars in car_spawner[scenario].values():
                        for car in cars:
                            car.reset()
                    
                    print(f"Switching to scenario {scenario+1}")

        # Draw new frame
        if physics_clock == FRAMERATE / PHYSICS_RATE:
            # physics_clock = 0

            screen.fill(Color("darkgreen"))  # Draw grass

            # Draw road
            pygame.draw.rect(screen, Color("black"), road)

            # Draw lanes
            for lane in lanes:
                pygame.draw.rect(screen, Color("white"), lane)
            
            # Display sim stats
            text = font.render(f"{len(cars_on_road)} cars on road | {simtime=}", True, Color("white"))
            text_rect = text.get_rect()
            text_rect.topleft = (0, 0)
            screen.blit(text, text_rect)

            # Spawn in new cars, if any.
            try:
                cars_on_road += car_spawner[scenario][simtime]
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
            
            if show_intent_lines:
                for car in cars_on_road:
                    car.draw_intent(screen)
        
        # Second sim stage
        elif physics_clock == FRAMERATE / PHYSICS_RATE * 2:
            physics_clock = 0
            
            # Cars resolve conflicts with each other.
            for car in cars_on_road:
                car.resolve_conflicts()
            
            if show_intent_lines:
                for car in cars_on_road:
                    car.draw_intent(screen)

            # Cars move to new position.
            for car in cars_on_road:
                try:
                    car.drive()
                except Exception as e:
                    paused = True
                    text = font.render("Error!", True, Color("white"))
                    text_rect = text.get_rect()
                    text_rect.center = WIDTH // 2, HEIGHT // 2
                    screen.blit(text, text_rect)
                    print("\n\n\nERROR")
                    print(f"{cars_on_road=}")
                    # raise e



            print(f"Current simulation time: {simtime}")
            simtime += 1


        pygame.display.update()  # Update display buffer (redraw window)
        clock.tick(FRAMERATE)  # Limit framerate

        if not paused:
            physics_clock += 1


if __name__ == "__main__":
    main()
