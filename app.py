import math
import random
import numpy as np
import pygame
import pymunk

# Initialize Pygame and Audio
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bounce Harmony - Complete Sweep")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28, bold=True)

# Initialize Pymunk Physics Space
space = pymunk.Space()
space.gravity = (0, 650)


# Generate clean synth notes (C Major Pentatonic scale across 3 octaves)
def create_tone(freq, duration=0.55):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = (
        1.0 * np.sin(2 * np.pi * freq * t)
        + 0.35 * np.sin(2 * np.pi * (freq * 2) * t)
        + 0.12 * np.sin(2 * np.pi * (freq * 3) * t)
    )
    attack = np.minimum(t / 0.01, 1.0)
    decay = np.exp(-4.0 * t)
    audio = (wave * attack * decay * 32767 * 0.28).astype(np.int16)
    return pygame.mixer.Sound(buffer=audio)


frequencies = [
    220.00, 261.63, 329.63, 392.00, 440.00,  # A3, C4, E4, G4, A4
    523.25, 659.25, 783.99, 880.00, 1046.50  # C5, E5, G5, A5, C6
]
notes = [create_tone(f) for f in frequencies]
note_index = 0

# Create the V-shaped funnel at the bottom
funnel_body = space.static_body
left_wall = pymunk.Segment(funnel_body, (30, 550), (300, 690), 5)
right_wall = pymunk.Segment(funnel_body, (570, 550), (300, 690), 5)
left_wall.elasticity = 0.75
right_wall.elasticity = 0.75
left_wall.friction = 0.4
right_wall.friction = 0.4
space.add(left_wall, right_wall)

# Double Pendulum initial parameters (high-energy chaotic start)
pivot = (WIDTH // 2, 230)
L1, L2 = 95, 115
a1, a2 = 2.8, 2.3  # Near-inverted angles create chaotic full-circle sweeps
v1, v2 = 0.15, -0.25
m1, m2 = 10, 10
g = 0.45

# Create the 3 rings of frozen blocks around the pendulum
blocks = []
block_size = 16
colors = [
    (255, 80, 80),
    (255, 165, 0),
    (255, 220, 0),
    (80, 220, 100),
    (0, 180, 255),
]

for radius in [135, 170, 205]:
    for deg in range(-200, 25, 15):
        rad = math.radians(deg)
        bx = pivot[0] + radius * math.cos(rad)
        by = pivot[1] + radius * math.sin(rad)

        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = (bx, by)
        shape = pymunk.Poly.create_box(body, (block_size, block_size))
        shape.elasticity = 0.6
        shape.friction = 0.5
        space.add(body, shape)

        blocks.append({
            "body": body,
            "shape": shape,
            "frozen": True,
            "color": (160, 200, 225),
            "hit_color": random.choice(colors),
        })


# Helper: shortest distance from point (px, py) to line segment (ax, ay)-(bx, by)
def point_to_segment_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return math.hypot(px - proj_x, py - proj_y)


game_complete = False
settle_timer = 0
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    frozen_blocks = [b for b in blocks if b["frozen"]]
    remaining_count = len(frozen_blocks)

    if remaining_count > 0:
        # Sub-step double pendulum physics for numerical stability
        sub_steps = 12
        dt = 0.11 / sub_steps

        for _ in range(sub_steps):
            num1 = -g * (2 * m1 + m2) * math.sin(a1)
            num2 = -m2 * g * math.sin(a1 - 2 * a2)
            num3 = -2 * math.sin(a1 - a2) * m2
            num4 = v2 * v2 * L2 + v1 * v1 * L1 * math.cos(a1 - a2)
            den = L1 * (2 * m1 + m2 - m2 * math.cos(2 * a1 - 2 * a2))
            acc1 = (num1 + num2 + num3 * num4) / den

            num1 = 2 * math.sin(a1 - a2)
            num2 = v1 * v1 * L1 * (m1 + m2)
            num3 = g * (m1 + m2) * math.cos(a1)
            num4 = v2 * v2 * L2 * m2 * math.cos(a1 - a2)
            den = L2 * (2 * m1 + m2 - m2 * math.cos(2 * a1 - 2 * a2))
            acc2 = (num1 * (num2 + num3 + num4)) / den

            v1 += acc1 * dt
            v2 += acc2 * dt
            a1 += v1 * dt
            a2 += v2 * dt

        # Maintain lively chaotic energy so it reaches top and inner blocks
        speed = abs(v1) + abs(v2)
        if speed < 0.45:
            v1 *= 1.02
            v2 *= 1.02
        elif speed > 1.1:
            v1 *= 0.99
            v2 *= 0.99

        # Gentle homing bias if <= 8 blocks remain so it never gets stuck missing the last few
        if remaining_count <= 8:
            target = frozen_blocks[0]["body"].position
            desired_angle = math.atan2(
                target.x - pivot[0], target.y - pivot[1]
            )
            diff = (desired_angle - a1 + math.pi) % (2 * math.pi) - math.pi
            v1 += diff * 0.008

        v1 = max(-1.6, min(1.6, v1))
        v2 = max(-1.8, min(1.8, v2))
        a1 %= 2 * math.pi
        a2 %= 2 * math.pi
    else:
        # All blocks knocked down: smoothly slow pendulum to a halt
        v1 *= 0.92
        v2 *= 0.92
        a1 += v1 * 0.1
        a2 += v2 * 0.1
        settle_timer += 1
        if settle_timer > 150:  # ~2.5 seconds after last block drops
            game_complete = True

    # Calculate joint and tip coordinates
    x1 = pivot[0] + L1 * math.sin(a1)
    y1 = pivot[1] + L1 * math.cos(a1)
    x2 = x1 + L2 * math.sin(a2)
    y2 = y1 + L2 * math.cos(a2)

    # Check collision along the ENTIRE outer arm (joint to tip) so middle blocks never get skipped
    for b in frozen_blocks:
        bx, by = b["body"].position
        dist_outer_arm = point_to_segment_dist(bx, by, x1, y1, x2, y2)
        dist_inner_arm = point_to_segment_dist(
            bx, by, pivot[0], pivot[1], x1, y1
        )

        if dist_outer_arm < 16 or dist_inner_arm < 16:
            b["frozen"] = False
            b["color"] = b["hit_color"]

            # Convert static frozen block into a falling dynamic physics body
            space.remove(b["body"], b["shape"])
            dyn_body = pymunk.Body(
                1, pymunk.moment_for_box(1, (block_size, block_size))
            )
            dyn_body.position = (bx, by)
            dyn_body.velocity = (
                random.uniform(-50, 50),
                random.uniform(-30, 40),
            )
            dyn_shape = pymunk.Poly.create_box(
                dyn_body, (block_size, block_size)
            )
            dyn_shape.elasticity = 0.55
            dyn_shape.friction = 0.5
            space.add(dyn_body, dyn_shape)

            b["body"] = dyn_body
            b["shape"] = dyn_shape

            # Play next musical note
            notes[note_index % len(notes)].play()
            note_index += 1

    # Step physics until complete
    if not game_complete:
        space.step(1 / 60.0)

    # Render everything
    screen.fill((12, 12, 16))

    # Draw V-Funnel
    pygame.draw.line(screen, (255, 255, 255), (30, 550), (300, 690), 4)
    pygame.draw.line(screen, (255, 255, 255), (570, 550), (300, 690), 4)

    # Draw Blocks
    for b in blocks:
        pos = b["body"].position
        angle = b["body"].angle
        surf = pygame.Surface((block_size, block_size), pygame.SRCALPHA)
        surf.fill(b["color"])
        rotated = pygame.transform.rotate(surf, -math.degrees(angle))
        rect = rotated.get_rect(center=(int(pos.x), int(pos.y)))
        screen.blit(rotated, rect.topleft)

    # Draw Double Pendulum
    pygame.draw.line(screen, (220, 220, 220), pivot, (x1, y1), 4)
    pygame.draw.line(screen, (220, 220, 220), (x1, y1), (x2, y2), 4)
    pygame.draw.circle(screen, (255, 255, 255), pivot, 6)
    pygame.draw.circle(screen, (255, 255, 255), (int(x1), int(y1)), 6)
    pygame.draw.circle(screen, (100, 200, 255), (int(x2), int(y2)), 7)

    # Status HUD
    if game_complete:
        done_text = font.render(
            "ALL BLOCKS DROPPED - COMPLETE!", True, (100, 255, 140)
        )
        screen.blit(
            done_text, (WIDTH // 2 - done_text.get_width() // 2, 45)
        )
    else:
        count_text = font.render(
            f"Remaining: {remaining_count}", True, (180, 180, 195)
        )
        screen.blit(
            count_text, (WIDTH // 2 - count_text.get_width() // 2, 45)
        )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()