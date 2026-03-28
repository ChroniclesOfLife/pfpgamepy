# client/input.py
import pygame

class InputHandler:
    def __init__(self):
        # Current logic state for local predictive rendering and sending to server
        self.state = {"up": False, "down": False, "left": False, "right": False}
        
    def process_events(self, events):
        # We process key down/up immediately
        changed = False
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w: self.state["up"] = True; changed = True
                if event.key == pygame.K_s: self.state["down"] = True; changed = True
                if event.key == pygame.K_a: self.state["left"] = True; changed = True
                if event.key == pygame.K_d: self.state["right"] = True; changed = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_w: self.state["up"] = False; changed = True
                if event.key == pygame.K_s: self.state["down"] = False; changed = True
                if event.key == pygame.K_a: self.state["left"] = False; changed = True
                if event.key == pygame.K_d: self.state["right"] = False; changed = True
        return changed # Return True if state changed so we can network it
        
    def get_state(self):
        return self.state
