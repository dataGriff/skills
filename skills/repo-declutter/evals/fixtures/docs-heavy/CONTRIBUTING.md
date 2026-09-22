# Contributing

Thank you for your interest in contributing to ledger-api. It is worth
noting that we try to keep the process as lightweight as we possibly can,
but there are, needless to say, a few things that we would ask of you.

First of all, please note that we would like you to branch from `main`. We
have found over time that branching from other branches tends to cause
confusion, so in order to keep things simple, `main` it is. Branch names
should, generally speaking, follow the pattern `la-<ticket>-<slug>`.

Secondly, and this is basically the most important thing, please make sure
that `make test` passes before you open a pull request. CI will run it in
any case, but it is just much faster for everybody if it is green already.

Thirdly, commit messages: we would ask that you write them in the
imperative mood, keep the first line under 72 characters, and reference the
ticket. This is, as you may know, the conventional style and it makes the
history considerably easier to read.

Fourthly, every pull request needs a review from someone on the ledger team.
This is not negotiable, as the ledger is, needless to say, the system of
record for money.

Finally, it is worth noting that we squash-merge, so the pull request title
becomes the commit message. Please make it a good one.
