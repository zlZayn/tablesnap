# Design Philosophy

## Debugging for Generality

Every debug session answers the same question: **does this change make all images better?**

If the answer is "only fixes this one image" — the direction is wrong. Patching one image with regex is fast but adds a new edge case that will surface elsewhere. Every extra rule is more to maintain.

The correct approach — counter-intuitive at first — is to **go back to the prompt** and make the model understand better rather than cleaning up after it.

## VLM Pipeline: AI as Reader, Not Formatter

The PSV extraction pipeline rests on one assumption:

The VLM can *see* the table. It understands "columns" as easily as a human does. Telling it what to do is enough — it will do it correctly.

Do not teach it *how to format* — quoting rules, escaping conventions, regex cleanup. Those are things the model is not good at. A model that understands the data will produce correct delimiters on its own. A model that doesn't understand the data won't be saved by more rules.

### What This Means in Practice

| Scenario | Wrong approach | Right approach |
| :--- | :--- | :--- |
| Quoted cells mis-paired | Add regex to detect and clean | Remove quoting rule, let model use pipe-only delimiters |
| Column count misaligned   | Add column-fill logic              | Prompt: strictly require equal columns per row |
| Extra noise rows          | Add filtering rule                 | Prompt: strictly require only table rows |

Every right approach is the same direction: **a clearer prompt and a model trained to understand, not a post-processing layer for syntax errors.**

## Why This Is Not Idealism

Three practical reasons — not philosophical:

1. **Every regex is a hidden bug.** The edge case you fix today reappears tomorrow with a different image format. A prompt fix, once right, is done.
2. **Prompt improvements benefit all images.** One better rule improves 6 images, 60 images, 600 images simultaneously. A regex patch covers only the case you wrote a condition for.
3. **VLMs are getting better.** Stronger models mean better comprehension, and prompt improvements compound over time. Regex benefits are fixed; model upgrades don't make regex smarter.

## Boundary

This philosophy is not absolute. If a problem is impossible to solve at the prompt level — for example, the VLM output is syntactically unparseable — a fallback is needed. But:

- The fallback must be **generic** (no conditions keyed to specific images)
- The fallback must be **simple** (strip, split — no semantic reasoning)
- After adding a fallback, revisit the prompt with the goal of removing it

## One Line

**"Fixes" at the code level are an admission of prompt failure. Prompt-level improvements are real debugging.**