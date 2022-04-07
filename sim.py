import pygame
from pygame import Color, Rect

pygame.init()

WIDTH, HEIGHT = 1200, 600

number_of_lanes = 4
lane_divider_width = 10
lane_width = (700 - (lane_divider_width * number_of_lanes)) / (number_of_lanes + 1)


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
    for i in range(number_of_lanes + 2):
        lane = Rect(0, 2 * i * road.top + road.top, WIDTH, lane_divider_width)

        pygame.draw.rect(screen, Color('white'), lane)

    temp = False
    # draw car objects
    pygame.draw.rect(screen, (255,255,255), car)

    pygame.display.update()  # Updates display buffer (redraws window)
    clock.tick(60)  # Limit to 60Hz
