#!/usr/bin/env python3
"""Vitra Lance — neon stained-glass harpoon arcade for ElbowOS."""
import argparse, math, os, random, subprocess, sys

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "VITRA LANCE"
HANDLE = "x.com/ElbowOS"
PAL = {
    "bg": (12, 6, 22),
    "bg2": (28, 8, 36),
    "teal": (46, 230, 200),
    "rose": (255, 77, 141),
    "amber": (255, 193, 77),
    "violet": (155, 107, 255),
    "slag": (255, 64, 72),
    "white": (240, 236, 255),
    "dim": (90, 70, 120),
}
HUES = [PAL["teal"], PAL["rose"], PAL["amber"], PAL["violet"]]


def lerp(a, b, t):
    return a + (b - a) * t


class Orb:
    __slots__ = ("x", "y", "r", "vy", "col", "wob", "phase", "alive", "slag")

    def __init__(self, y=None):
        self.x = random.uniform(90, W - 90)
        self.y = y if y is not None else random.uniform(-200, 80)
        self.r = random.choice((34, 40, 46, 52))
        self.vy = random.uniform(1.6, 3.4)
        self.slag = random.random() < 0.16
        self.col = PAL["slag"] if self.slag else random.choice(HUES)
        self.wob = random.uniform(0.6, 1.8)
        self.phase = random.random() * 6.28
        self.alive = True

    def step(self, t):
        self.y += self.vy
        self.x += math.sin(t * self.wob + self.phase) * 1.15
        self.x = max(70, min(W - 70, self.x))


class Shard:
    __slots__ = ("x", "y", "vx", "vy", "life")

    def __init__(self, x, y, ang, spd=28):
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(ang) * spd, math.sin(ang) * spd
        self.life = 55

    def step(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        return self.life > 0 and -40 < self.x < W + 40 and -40 < self.y < H + 40


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "sz")

    def __init__(self, x, y, col):
        a = random.random() * 6.28
        s = random.uniform(2, 11)
        self.x, self.y, self.vx, self.vy = x, y, math.cos(a) * s, math.sin(a) * s
        self.life = random.randint(10, 22)
        self.col, self.sz = col, random.randint(2, 6)

    def step(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.18
        self.life -= 1
        return self.life > 0


class Game:
    def __init__(self, auto=False):
        self.auto = auto
        self.t = 0
        self.score = 0
        self.chain = 0
        self.px = W * 0.5
        self.aim = -math.pi / 2
        self.cool = 0
        self.orbs = [Orb(y=random.uniform(180, 1100)) for _ in range(10)]
        self.shards, self.sparks = [], []
        self.stars = [(random.randrange(W), random.randrange(H), random.randint(1, 3)) for _ in range(70)]
        self.flash = 0
        self.lives = 3

    def spawn(self):
        if len(self.orbs) < 14 and random.random() < 0.22:
            self.orbs.append(Orb())

    def fire(self):
        if self.cool > 0:
            return
        self.cool = 10
        ox = self.px + math.cos(self.aim) * 70
        oy = H - 210 + math.sin(self.aim) * 70
        self.shards.append(Shard(ox, oy, self.aim))
        for _ in range(6):
            self.sparks.append(Spark(ox, oy, PAL["white"]))

    def pop(self, orb, chain=0):
        orb.alive = False
        self.flash = 6
        pts = 40 + chain * 25
        if orb.slag:
            pts = 8
            self.chain = 0
        else:
            self.chain += 1
            pts += self.chain * 10
        self.score += pts
        for _ in range(18):
            self.sparks.append(Spark(orb.x, orb.y, orb.col))
        if not orb.slag:
            for o in self.orbs:
                if o.alive and not o.slag and o.col == orb.col:
                    if (o.x - orb.x) ** 2 + (o.y - orb.y) ** 2 < (orb.r + o.r + 86) ** 2:
                        self.pop(o, chain + 1)

    def autoplay(self):
        live = [o for o in self.orbs if o.alive and o.y < H - 280]
        targets = [o for o in live if not o.slag] or live
        if not targets:
            self.aim += 0.04
            return
        best, bestn = targets[0], -1
        for o in targets:
            n = sum(
                1
                for q in targets
                if q is not o and q.col == o.col and (q.x - o.x) ** 2 + (q.y - o.y) ** 2 < 220 ** 2
            )
            score = n * 3 + (1 if o.y > 700 else 0)
            if score > bestn:
                best, bestn = o, score
        ang = math.atan2(best.y - (H - 210), best.x - self.px)
        da = (ang - self.aim + math.pi) % (2 * math.pi) - math.pi
        self.aim += max(-0.13, min(0.13, da))
        self.px += max(-10, min(10, best.x - self.px)) * 0.08
        self.px = max(120, min(W - 120, self.px))
        if abs(da) < 0.12 and self.cool == 0:
            self.fire()

    def step(self, keys=None):
        self.t += 1
        self.cool = max(0, self.cool - 1)
        self.flash = max(0, self.flash - 1)
        if self.auto:
            self.autoplay()
        else:
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.px -= 14
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.px += 14
            self.px = max(90, min(W - 90, self.px))
            if keys[pygame.K_q]:
                self.aim -= 0.09
            if keys[pygame.K_e]:
                self.aim += 0.09
            mx, my = pygame.mouse.get_pos()
            self.aim = math.atan2(my - (H - 210), mx - self.px)
            if keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]:
                self.fire()
        self.aim = max(-math.pi + 0.25, min(-0.25, self.aim))
        self.spawn()
        for o in self.orbs:
            if o.alive:
                o.step(self.t * 0.08)
                if o.y - o.r > H - 160:
                    o.alive = False
                    if o.slag:
                        self.lives = max(0, self.lives - 1)
                        self.flash = 8
                    self.chain = 0
        self.orbs = [o for o in self.orbs if o.alive]
        live_shards = []
        for s in self.shards:
            if not s.step():
                continue
            hit = False
            for o in self.orbs:
                if o.alive and (s.x - o.x) ** 2 + (s.y - o.y) ** 2 < (o.r + 10) ** 2:
                    self.pop(o)
                    hit = True
                    break
            if not hit:
                live_shards.append(s)
        self.shards = live_shards
        self.sparks = [p for p in self.sparks if p.step()]
        if self.lives <= 0:
            self.lives = 3
            self.chain = 0

    def draw(self, surf, font, small):
        surf.fill(PAL["bg"])
        for i in range(18):
            y = int((i * 140 + self.t * 3) % (H + 140) - 140)
            c = 16 + (i % 3) * 6
            pygame.draw.rect(surf, (c, 8, 28 + i), (0, y, W, 70), 0)
        for x, y, r in self.stars:
            yy = (y + self.t) % H
            pygame.draw.circle(surf, PAL["dim"], (x, yy), r)
        pygame.draw.rect(surf, (40, 16, 58), (0, 0, 36, H))
        pygame.draw.rect(surf, (40, 16, 58), (W - 36, 0, 36, H))
        pygame.draw.line(surf, PAL["violet"], (36, 0), (36, H), 3)
        pygame.draw.line(surf, PAL["teal"], (W - 36, 0), (W - 36, H), 3)
        pygame.draw.polygon(surf, (32, 12, 48), [(0, H - 150), (W, H - 150), (W, H), (0, H)])
        pygame.draw.line(surf, PAL["amber"], (40, H - 150), (W - 40, H - 150), 4)
        for o in self.orbs:
            if not o.alive:
                continue
            pygame.draw.circle(surf, o.col, (int(o.x), int(o.y)), o.r)
            pygame.draw.circle(surf, PAL["white"], (int(o.x - o.r * 0.28), int(o.y - o.r * 0.32)), max(4, o.r // 5))
            pygame.draw.circle(surf, PAL["bg"], (int(o.x), int(o.y)), o.r, 3)
            if o.slag:
                pygame.draw.line(surf, PAL["white"], (o.x - 10, o.y - 10), (o.x + 10, o.y + 10), 3)
        for s in self.shards:
            pygame.draw.circle(surf, PAL["white"], (int(s.x), int(s.y)), 8)
            pygame.draw.circle(surf, PAL["amber"], (int(s.x), int(s.y)), 4)
            tx, ty = s.x - s.vx * 1.4, s.y - s.vy * 1.4
            pygame.draw.line(surf, PAL["teal"], (s.x, s.y), (tx, ty), 5)
        for p in self.sparks:
            pygame.draw.circle(surf, p.col, (int(p.x), int(p.y)), p.sz)
        base = (self.px, H - 210)
        tip = (self.px + math.cos(self.aim) * 118, H - 210 + math.sin(self.aim) * 118)
        pygame.draw.circle(surf, (48, 20, 70), (int(self.px), H - 168), 54)
        pygame.draw.circle(surf, PAL["teal"], (int(self.px), H - 168), 54, 4)
        pygame.draw.line(surf, PAL["amber"], base, tip, 10)
        pygame.draw.circle(surf, PAL["rose"], (int(tip[0]), int(tip[1])), 12)
        pygame.draw.circle(surf, PAL["white"], (int(self.px), H - 210), 16)
        if self.flash:
            veil = pygame.Surface((W, H), pygame.SRCALPHA)
            veil.fill((255, 200, 230, 28 * self.flash))
            surf.blit(veil, (0, 0))
        banner = pygame.Surface((W, 150), pygame.SRCALPHA)
        banner.fill((8, 2, 16, 170))
        surf.blit(banner, (0, 0))
        surf.blit(font.render(TITLE, True, PAL["amber"]), (48, 22))
        surf.blit(small.render(HANDLE, True, PAL["teal"]), (48, 88))
        sc = font.render(f"{self.score:05d}", True, PAL["white"])
        surf.blit(sc, (W - 48 - sc.get_width(), 22))
        ch = small.render(f"CHAIN {self.chain}   HEARTS {self.lives}", True, PAL["rose"])
        surf.blit(ch, (W - 48 - ch.get_width(), 92))


def record(path):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.font.init()
    surf = pygame.Surface((W, H))
    font = pygame.font.SysFont("DejaVu Sans", 64, bold=True)
    small = pygame.font.SysFont("DejaVu Sans", 36, bold=True)
    g = Game(auto=True)
    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    frames = FPS * 15
    try:
        for _ in range(frames):
            g.step()
            g.draw(surf, font, small)
            proc.stdin.write(pygame.image.tostring(surf, "RGB"))
        proc.stdin.close()
        err = proc.stderr.read()
        rc = proc.wait(timeout=60)
    except Exception:
        proc.kill()
        raise
    if rc != 0:
        raise RuntimeError(err.decode("utf-8", "ignore")[-800:])
    print("wrote", path)


def play():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("DejaVu Sans", 64, bold=True)
    small = pygame.font.SysFont("DejaVu Sans", 36, bold=True)
    g = Game(auto=False)
    run = True
    while run:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                run = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                run = False
        g.step(pygame.key.get_pressed())
        g.draw(screen, font, small)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--record", action="store_true")
    p.add_argument("--play", action="store_true")
    p.add_argument("--out", default="/home/workdir/artifacts/vitra_lance_ElbowOS.mp4")
    a = p.parse_args()
    if a.record or not a.play:
        record(a.out)
        if a.play:
            play()
    else:
        play()


if __name__ == "__main__":
    main()
