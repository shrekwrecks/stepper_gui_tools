import pygame
from . import modelviewcontroller
import sys

# Initialize pygame and joystick module
pygame.init()
pygame.joystick.init()

# Check for joystick(s)
if pygame.joystick.get_count() == 0:
    print("No joystick detected. Connect your Bluetooth Xbox controller and try again.")
    sys.exit(1)

# Use the first joystick
joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Joystick initialized: {joystick.get_name()}")

try:
    while True:
        # Pump pygame events
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                axis = event.axis
                value = event.value
                print(f"Axis {axis} moved to {value:.3f}")
            elif event.type == pygame.JOYBUTTONDOWN:
                button = event.button
                print(f"Button {button} pressed")
            elif event.type == pygame.JOYBUTTONUP:
                button = event.button
                print(f"Button {button} released")
            elif event.type == pygame.JOYHATMOTION:
                hat = event.hat
                value = event.value  # tuple like (x, y)
                print(f"Hat {hat} moved to {value}")

        # Add a small delay to reduce CPU load
        pygame.time.wait(10)

except KeyboardInterrupt:
    print("\nExiting...")
finally:
    joystick.quit()
    pygame.quit()
