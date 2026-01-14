# journal #4: diamond challenge, innovation, and manim

## january 14, 2026

been working on the diamond challenge with kingdom and got pretty deep into it. also watched this innovation video that made a lot of things click, and started messing around with manim for visualizing stuff. figured i'd document all of this properly since it's interconnected.

## part 1: the diamond challenge & kingdom

### what we're doing
kingdom is basically our attempt to solve a real problem that people actually face. the diamond challenge format forces you to think systematically—identify the problem, understand who's affected, sketch out a solution that scales.

### the problem space
started with a lot of user conversations. like actually sitting down and asking people what frustrates them. the real pain points aren't always obvious at first—people complain about symptoms, not root causes. had to dig deeper and ask "why" a bunch of times until the actual problem emerged.

### what we're building
kingdom is designed to be:
- simple enough that people get it immediately
- flexible enough to adapt as we learn more
- actually feasible with the resources we have
- built to survive long-term, not just a one-off thing

we're looking at the tech stack, the user experience, how it scales, and whether we can sustain it without burning out or going broke.

### how we're approaching it
- start with the absolute minimum version. ship something rough and real.
- get people using it and listen to what they actually do vs. what they say they'll do
- iterate like crazy. the first version will be wrong in ways we can't predict
- measure what matters. not vanity metrics, but actual impact

### what i've learned so far
- you can't predict what users will do. you have to watch them
- constraints are actually useful—they force better thinking
- talking to lots of different people is crucial. one person's perspective is always incomplete
- it's okay to build something imperfect if it solves a real problem

## part 2: the innovation video

watched this video about innovation frameworks and it basically tied together a bunch of half-formed thoughts i had. innovation isn't just about new tech—it's about rethinking systems to actually solve problems better.

### key ideas that stuck

**design thinking is about empathy first.** the whole framework is empathize → define → ideate → prototype → test. nothing revolutionary but damn if people don't skip the empathize part constantly. you gotta actually understand what someone's trying to accomplish, not what you *think* they want.

**lean startup's build-measure-learn loop** is basically how we're approaching kingdom. don't spend six months planning. build something minimal and dumb, ship it, see what breaks.

**constraints force better thinking.** sounds counterintuitive but when you can't do everything, you get creative about what actually matters.

**failure is information.** if your hypothesis is wrong, that's valuable. you just saved time by not building the wrong thing at scale.

### applying this to kingdom

we're literally doing all this with kingdom. user research (empathy). clear problem statement (define). multiple solution sketches (ideate). working prototype (prototype). throwing it at actual users (test). it's all there.

the video also talked about how most organizations kill innovation accidentally by:
- treating it like a separate department instead of a way of thinking
- needing everything approved before it starts (kills speed)
- not letting people fail
- optimizing for efficiency instead of learning

we're trying not to do any of that. keeping the team small, moving fast, being okay with being wrong.

### what it made me think

a lot of "innovation" is really just paying attention. like, actually watching how people work instead of assuming you know. then building something that fits how they actually think, not how you think they should think.

## part 3: manim—visualizing math stuff

started playing with manim because we need to actually *show* what kingdom does. static descriptions are boring. animations make things click in ways words don't.

### why manim?

grant sanderson (3blue1brown) built this tool because he got tired of making math videos the hard way. it's a python library that lets you write code to animate mathematical concepts. honestly it's perfect for what we need—communicate complex ideas in a way that's actually engaging.

### the basics

every manim animation is a scene. you define objects (mobjects), you animate them, and boom you have a video.

```python
from manim import *

class SimpleScene(Scene):
    def construct(self):
        circle = Circle()
        self.play(Create(circle))
        self.wait(2)
```

that's literally it. create object, animate it, wait so people can see it.

### building blocks

**mobjects** are the visual elements:
- shapes: `Circle()`, `Square()`, `Rectangle()`, `Triangle()`
- text: `Text()` for regular text, `TeX()` for fancy math notation
- plots: if you want to graph a function
- arrows and vectors for showing direction
- basically anything visual

**animations** make them move:
- `FadeIn()` / `FadeOut()`: appears and disappears
- `Create()` / `Write()`: draws something onscreen
- `MoveTo()`: moves to a position
- `Rotate()`: spins it
- `Scale()`: makes it bigger or smaller
- `ReplacementTransform()`: morphs one thing into another

you can stack animations together to happen at the same time or one after another.

### practical stuff

the coordinate system is pretty standard:
- center of screen is (0, 0)
- x increases to the right
- y increases upward
- think like a math graph

colors are easy to work with. can use names or hex codes.

```python
circle = Circle(color=BLUE_C, stroke_width=2, fill_color=RED_C, fill_opacity=0.5)
```

timing matters. `self.play()` runs animations, `self.wait()` pauses, `self.add()` just puts stuff on screen without animation.

### what we can use it for with kingdom

- visualize how kingdom works. flow charts that actually animate.
- show user journeys step by step
- create impact visualizations. graphs that build themselves as you watch
- explain core concepts in a way that's memorable
- make pitches way more compelling

instead of saying "our system connects users and resources," you *show* circles appearing and linking together. people get it instantly.

### next steps with manim

- set everything up properly (there's dependencies to deal with)
- make a simple test animation just to get comfortable
- create kingdom-specific scenes
- use them in presentations
- maybe make it part of the onboarding experience

the nice thing about manim is it's reproducible. everything is code. if you want to change something, you just edit the code and regenerate. no clicking around in some gui.

### going deeper

there's a lot more to manim—custom animations, complex graphs, 3d stuff. but for kingdom we probably don't need anything super advanced. clear, clean visualizations that help people understand what we're doing. that's the goal.

## part 4: how it all connects

diamond challenge = figuring out what problem exists and how to solve it
innovation frameworks = how to think about solving it smartly  
manim = how to actually communicate what you built

they're not separate things. they're different pieces of the same process.

the whole cycle is:
1. deep dive into understanding the problem (diamond challenge methodology)
2. think systematically about solutions using proven frameworks (innovation principles)
3. execute and communicate clearly (manim for visualization)
4. iterate based on real feedback from real users

### why this matters

most people skip steps. they have an idea, jump straight to building, and hope users will magically understand. or they understand the problem perfectly but build something ugly that nobody wants to use because they can't communicate it.

we're trying to do all three things right. that's harder but it's why kingdom actually has a shot.

### communication changes everything

here's the thing: two products can solve the exact same problem. one succeeds, one fails. the difference is often just in how well it's communicated.

kingdom is solving a real problem with a thoughtful approach. but if we can't *show* people what we're doing and why it matters, they won't get on board. manim lets us do that in a way that's memorable and engaging.

videos beat demos beat screenshots beat descriptions. we're putting work into the visualization layer because it matters.

## what i'm actually learning

### about problem-solving
- most problems aren't what people first describe them as
- talking to lots of people is the only way to really understand something
- solutions that work are usually simpler than you expect
- but getting to that simplicity takes a lot of iteration

### about communication
- clarity is hard. saying something simply requires understanding it deeply
- visuals are powerful. showing is always better than telling
- rhythm and pacing matter. how you present something is as important as what you're presenting

### about myself
- i like building things that solve real problems
- i like tools that let me think better and communicate clearer
- i'm good at asking questions and listening
- i'm still learning how to move fast without being reckless

## what's next

need to:
- actually finish the kingdom prototype so we have something real to show
- set up manim and make some kingdom-specific animations
- get the prototype in front of users and listen to what breaks
- refine based on feedback
- prepare for the next stage of the diamond challenge

also just keep thinking about this stuff. reading about innovation, watching how other people solve problems, staying curious about what makes some projects succeed and others fail.

the interesting part isn't going to be the final polished product. it's the process of getting there.
