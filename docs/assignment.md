# Assignment: Reinforcement Learning Final Project

English translation of the assignment the course published on the campus site (in Spanish),
limited to what applies to this project. Where they differ, the original prevails.

## Groups and topic

- Groups of up to 4 students.
- The topic is either one suggested by the course or one agreed upon with the professors. The
  agreed minimum objectives must be met without exception; the work may go beyond them, on the
  group's own initiative or by agreement with the professors.
- Existing RL libraries may be used (SB3, CleanRL, PufferLib, etc.).
- **Chosen topic:** optimal allocation with a known solution (Merton/Kelly). See
  [the topic section](#topic-optimal-allocation-with-a-known-solution-mertonkelly).

## Deadlines

| Milestone                                                           | Date               |
| ------------------------------------------------------------------- | ------------------ |
| Submission of the written report, the code, and supporting material | Nov 29, 23:59      |
| 15-minute oral defense                                              | TBD, around Dec 10 |

In the defense, the professors question each member about the report, including the diagnostic
case study, and assign the final grade.

## Report

Up to 10 pages, presenting the techniques and decisions made throughout the project. The AI use
declaration does not count toward the limit. Recommended structure:

1. **Objectives:** the project topic and its specific objectives. About half a page.
2. **Introduction:** the background needed to understand the topic and all the summarized
   information relevant to follow the development, including the specification of the learning
   environment. Between half a page and one page.
3. **Development:** a chronological account of the work, including dead ends, implementation
   problems, experiments with different training parameters, limitations of the algorithm in
   the chosen environment, etc.
4. **Diagnostic case study:** within Development or as its own section. See
   [below](#diagnostic-case-study).
5. **Conclusions:** key points of the development, main results, and possible future work.
6. **AI use declaration:** see [below](#ai-use-declaration).

Also:

- If the environment was built for the project, the report must describe it, as well as the
  behaviors learned by the policy.
- The report may include Drive links to videos of the learned behaviors.

## Deliverable

- The report.
- The source code used to solve the problem.
- Links or references to any external resource used.

If the deliverable exceeds the campus storage limit, upload only the report, and include in its
text a Google Drive link to the complete deliverable.

## Diagnostic case study

About one page on a concrete problem the group had to diagnose during the project, with this
structure:

- **Symptom:** what was observed, with the specific curve or metric (for example, "entropy
  collapsed before 50k steps and the return plateaued at 30% of the analytical optimum").
- **Hypotheses:** at least two plausible explanations considered before changing anything.
- **Discriminating experiment:** the run designed to tell the hypotheses apart, and why it was
  expected to do so.
- **Evidence and solution:** results before and after, referencing the corresponding runs or
  commits.
- **Lesson:** what to look at from the start next time.

The diagnosis can be of a failure (a bug, an instability, an agent that doesn't learn) or of a
learned behavior (for example, why the no-trade band turns out narrower than theory predicts).
Grading focuses mainly on the quality of the reasoning and of the discriminating experiment. In
the oral defense, any member may be asked about the case.

## AI use declaration

The goal of the project is not to write code, but to formulate the problem, diagnose training,
and analyze the learned behaviors. That's why AI tools are allowed, but the group is
responsible for everything submitted and every member must be able to explain it in the oral
defense.

The report ends with a declaration of the AI tools used (model and version) and their purpose:
writing code, debugging, writing the report, literature search, etc. This section does not
count toward the 10-page limit.

## Topic: optimal allocation with a known solution (Merton/Kelly)

An environment for allocating between a simulated risky asset and a risk-free one, where the
agent maximizes the logarithmic utility of terminal wealth.

1. Verify that the learned policy recovers Merton's analytical optimal fraction.
2. Add proportional transaction costs: a case with no simple closed-form solution but with a
   known structure (a no-trade band). Analyze whether the agent learns that band and how its
   width changes with the cost level.

### In plain words

You have money to split between something safe (a bond with a fixed yield) and something risky
(a stock that rises on average but fluctuates). Put too little in the stock and you grow
slowly. Put too much and a bad streak sinks you, and recovering takes a long time. There's an
optimal fraction in between, and for logarithmic utility it has a formula:

$$\pi^* = \frac{\mu - r}{\sigma^2} = \frac{\text{expected return} - \text{risk-free rate}}{\text{variance}}$$

It's the same idea as the Kelly criterion in betting.

### The project in three steps

1. **The environment:** at each step the agent chooses what fraction of its wealth to put in the
   simulated stock, and the rest stays in the bond. The reward is the log-return of wealth over
   that step; summed, they give the log of terminal wealth, so the reward is dense without any
   shaping.
2. **Validation:** without costs, the optimal policy always holds that fraction constant, so
   it's possible to check directly whether the agent finds it.
3. **The interesting part:** trading costs are added. Rebalancing all the time gets expensive,
   and the optimum becomes a **band**: if the current fraction is within a range around the
   optimum, do nothing, and trade only when it leaves the range. The question is whether the
   agent discovers that band on its own, and whether it widens as costs rise, as theory
   predicts.
