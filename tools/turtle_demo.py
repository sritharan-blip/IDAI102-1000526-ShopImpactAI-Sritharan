"""Play a desktop Turtle animation of the ShopImpactAI Decision lab flow."""

import turtle


STEPS = (
    (-240, "Check budget", "Will it fit this month?"),
    (0, "Estimate cost per use", "How often will I use it?"),
    (240, "Save a pause plan", "When will I revisit it?"),
)


def main() -> None:
    screen = turtle.Screen()
    screen.title("ShopImpactAI | Decision lab")
    screen.setup(width=760, height=360)
    screen.bgcolor("#101c25")
    screen.tracer(0)

    heading = turtle.Turtle(visible=False)
    heading.penup()
    heading.color("#edf7f4")
    heading.goto(0, 100)
    heading.write("Decision lab", align="center", font=("Arial", 28, "bold"))
    heading.goto(0, -125)
    heading.write("Space to play or replay   |   Esc to close", align="center",
                  font=("Arial", 12, "normal"))

    route = turtle.Turtle(shape="turtle", visible=False)
    route.color("#64e2b0")
    route.pensize(4)
    labels = turtle.Turtle(visible=False)
    labels.penup()
    labels.color("#edf7f4")
    playing = False

    def arrive(index: int) -> None:
        nonlocal playing
        x, title, prompt = STEPS[index]
        route.dot(13)
        labels.goto(x, -34)
        labels.write(title, align="center", font=("Arial", 15, "bold"))
        labels.goto(x, -59)
        labels.write(prompt, align="center", font=("Arial", 11, "normal"))
        screen.update()
        if index + 1 < len(STEPS):
            screen.ontimer(lambda: advance(index + 1), 650)
        else:
            playing = False

    def advance(index: int) -> None:
        # Move a few pixels per frame so Tk can still process the close key.
        remaining = STEPS[index][0] - route.xcor()
        route.forward(min(8, remaining))
        screen.update()
        if remaining <= 8:
            arrive(index)
        else:
            screen.ontimer(lambda: advance(index), 16)

    def play() -> None:
        nonlocal playing
        if playing:
            return
        playing = True
        labels.clear()
        route.clear()
        route.penup()
        route.goto(STEPS[0][0], 10)
        route.pendown()
        route.showturtle()
        arrive(0)

    screen.onkey(play, "space")
    screen.onkey(screen.bye, "Escape")
    screen.listen()
    screen.update()
    screen.mainloop()


if __name__ == "__main__":
    main()
