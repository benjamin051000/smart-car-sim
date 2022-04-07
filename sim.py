import pygame
from pygame import Color, Rect

pygame.init()

WIDTH, HEIGHT = 1200, 600

NUM_LANES = 4
LANE_DIVIDER_WIDTH = 10
LANE_WIDTH = (700 - (LANE_DIVIDER_WIDTH * NUM_LANES)) / (NUM_LANES + 1)


screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Define objects on the screen
car = Rect(WIDTH/2, HEIGHT/2, 20, 20)
road = Rect(0, 50, WIDTH, HEIGHT - 100)


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

    screen.fill(Color('darkgreen'))  # Draw grass
    

    # draw our road here
    pygame.draw.rect(screen, Color('black'), road)

    # draw lanes
    for i in range(NUM_LANES + 2):
        lane = Rect(0, 2 * i * road.top + road.top, WIDTH, LANE_DIVIDER_WIDTH)

        pygame.draw.rect(screen, Color('white'), lane)

    temp = False
    # draw car objects
    pygame.draw.rect(screen, (255,255,255), car)

    pygame.display.update()  # Updates display buffer (redraws window)
    clock.tick(60)  # Limit to 60Hz
