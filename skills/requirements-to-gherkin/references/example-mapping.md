# Running an example mapping session with stakeholders

For when the user is facilitating a live session (in person or a call)
with the people who hold the requirements — a product owner, a domain
expert, a tester — rather than answering questions themselves. Give them
this structure to run the room; the output slots straight into the
discovery board.

## The setup

Four colours of card (physical index cards, or four columns in a shared
doc/whiteboard):

- **Yellow — the story.** One card, on top. The thing being discussed.
- **Blue — rules.** The constraints and decisions, one per card.
- **Green — examples.** Concrete cases, each placed under the blue rule it
  illustrates. Named people, real values.
- **Red — questions.** Anything nobody in the room can answer. Write it,
  park it, move on — red cards are the point of the session, not a
  failure of it.

Timebox to 25–30 minutes per story. Three to five people; more than that
and it becomes a meeting.

## How the conversation runs

1. Read the story aloud. Ask "what must be true for this to be done?" —
   each answer becomes a blue card.
2. For every blue card, ask for a real case: "give me an actual example —
   a person, a number, a day." Write it green. Push for at least one
   example where the rule says *no*.
3. When people disagree or hesitate, don't debate for more than a minute:
   write a red card with the question and whose call it is, and move on.
4. When someone proposes an example that doesn't fit any rule, that's a
   discovered rule — write the blue card it implies.
5. Stop at the timebox and read the table.

## Reading the table at the end

- **Lots of red** — the story isn't ready to build. That's a cheap and
  valuable discovery; the red cards are the follow-up list, each with an
  owner and a deadline.
- **One blue card with many greens** — probably several rules hiding in
  one; try to split it.
- **A blue card with no green** — nobody could produce an example, so the
  rule is folklore; either find an example or question the rule.
- **Little red, every rule exampled** — ready. Feed the cards into the
  discovery board and convert (SKILL.md step 4).

## Remote / async variant

When there's no shared session to be had, invert it: draft the blue and
green cards yourself from what's known, mark every guess, and send the
stakeholder only the red cards plus the guessed cards with "correct
anything wrong here". People are far better at correcting a wrong concrete
example than at answering an open question — a deliberately checkable
guess ("I've assumed day 30 is still refundable") often gets an answer a
question wouldn't.
