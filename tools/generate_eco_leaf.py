"""Draw a leaf with Python Turtle and save the pen strokes for the web app."""
from pathlib import Path
from turtle import TNavigator, Turtle, done
import argparse


class RecordingTurtle(TNavigator):
    """Record the standard Turtle movement on an SVG canvas without opening Tk."""

    def __init__(self):
        super().__init__()
        self.strokes = []
        self.stroke = None

    def penup(self):
        self.stroke = None

    def pendown(self):
        self.stroke = [self.position()]
        self.strokes.append(self.stroke)

    def _goto(self, end):
        super()._goto(end)
        if self.stroke is not None:
            self.stroke.append(self.position())


def draw_leaf(pen):
    """Use two matching arcs for the outline and shorter strokes for the veins."""
    pen.penup()
    pen.goto(-55, -45)
    pen.setheading(3)
    pen.pendown()
    for _ in range(2):
        pen.left(3.75)
        for segment in range(14):
            pen.forward(9.4)
            if segment < 13:
                pen.left(7.5)
        pen.left(78.75)
    for x, y, heading, length in [(-55, -45, 55.5, 114), (-26, -3, 8, 16),
                                  (-11, 20, 145, 12), (-3, 31, 5, 12)]:
        pen.penup()
        pen.goto(x, y)
        pen.setheading(heading)
        pen.pendown()
        pen.forward(length)


def export_svg(path):
    pen = RecordingTurtle()
    draw_leaf(pen)
    strokes = []
    for index, stroke in enumerate(pen.strokes):
        points = " ".join(f"{118 + x:.1f},{86 - y:.1f}" for x, y in stroke)
        strokes.append(f'  <polyline points="{points}" pathLength="1" style="--delay:{index * 130}ms"/>')
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 190 150">\n'
        '  <title>Leaf drawn with Python Turtle</title>\n'
        '  <style>\n'
        '    polyline {fill:none;stroke:#237457;stroke-width:4;stroke-linecap:round;stroke-linejoin:round}\n'
        '    @media (prefers-reduced-motion: no-preference) {\n'
        '      polyline {stroke-dasharray:1;animation:draw .85s ease-out var(--delay) both}\n'
        '    }\n'
        '    @keyframes draw {from {stroke-dashoffset:1} to {stroke-dashoffset:0}}\n'
        '  </style>\n'
        '  <rect x="1" y="1" width="188" height="148" rx="20" fill="#ecf8ef"/>\n'
        + "\n".join(strokes) + "\n</svg>\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", help="Watch the same strokes in the Turtle desktop window.")
    if parser.parse_args().preview:
        turtle = Turtle()
        turtle.pensize(4)
        turtle.pencolor("#237457")
        draw_leaf(turtle)
        done()
    else:
        export_svg(Path(__file__).resolve().parents[1] / "shopimpact" / "assets" / "eco-leaf.svg")
