# Lessons from the LenAI rollout

> A note from someone who was on the floor at Marsh McLennan during the rollout of LenAI the firm's enterprise generative AI assistant, used across 90,000+ employees and independently credited (Oliver Wyman, Rubrik) with saving over 1 million team hours in its first year.

LenAI is Marsh McLennan's enterprise generative AI assistant. I contributed to its rollout during my final two years at Marsh McLennan as a Claims Analyst, including delivering training to Claims Ops in Norwich while still carrying my own caseload.

These are four observations from that vantage point. They are not Marsh McLennan's official position, and they are not a complete picture of the programme. They are the things I noticed from a seat that was close enough to the rollout to help shape it, and close enough to the floor to see what wasn't landing.

---

## 1. Adoption is harder than capability

On the Norwich claims floor, LenAI was used eagerly in the first weeks and then dropped off sharply. Speaking with the team, the picture was consistent: people thought it was helpful but they hadn't built it into their daily work.

Two things were happening underneath. First, the team were prompting badly asking for whole-policy breakdowns rather than the specific question they actually needed answering (an exclusion, a limit, a date). The tool's answers were technically correct but too long to be useful inside a working day. Second and less obviously, there was a risk-mindset hangover. In the months before LenAI launched, the firm had allowed public ChatGPT use *only* on the strict condition that no internal or client data could ever be entered. By the time LenAI arrived with the right trust scaffolding in place, colleagues were still in the old mindset. The tool that *could* take their data was being treated like the tool that couldn't.

By that point I'd been pulled into the development team's training workstream while still carrying my claims caseload, which gave me an unusual vantage point close enough to the rollout to help shape the response, close enough to the floor to see what wasn't landing. The fix that worked was hand-holding: walking colleagues through uploading their own working documents in the GenAI Academy sessions, and following up with internal comms that made the changed rules explicit. Uptake recovered.

The takeaway: the hardest part of an enterprise GenAI rollout isn't shipping the tool. It's un-learning the rules from before. The harder the prior compliance posture, the more deliberate the relearning has to be and a lot of that work happens in the gap between training and lived practice, where people decide whether the new rules really apply to them.

---

## 2. The use cases that mattered weren't always the ones we predicted

The teams we expected to adopt LenAI fastest did. Anywhere with high-volume, data-heavy work that pulled from multiple documents picked the tool up quickly and used it. That was the easy bit and it matched the rollout prediction.

What surprised us was where the deeper return-on-time was happening. The standout was aviation certification. Every aircraft, spare engine, and certain other parts are required to have an insurance certificate before flight, and some aviation clients renew thousands of certificates a year. The Norwich aviation cert team was small but their document output across operations was second only to one team roughly ten times their size. With LenAI integrated into their workflow, that gap narrowed fast.

The pattern became clear in retrospect: high-volume teams were using LenAI for many small tasks across the day. Smaller teams were using it for one or two tasks every few minutes, and that compounded. A focused, disciplined use of the tool produced more output per head than a broad, exploratory one.

The takeaway: the most valuable uses don't appear in any pre-rollout deck because they aren't visible until people have lived with the tool for a few weeks and stopped using it the way the rollout assumed they would. Measuring adoption by raw usage misses the teams that have figured out one thing and got disciplined about it.

---

## 3. Power users and casual users are two different products

The fastest LenAI power users were the ones already using ChatGPT before the rollout. They saved prompts when they noticed themselves reusing a phrasing, and they concentrated on one or two big time-saving tasks rather than spraying the tool across many small ones. The discipline wasn't technical, it was workflow-shaped they'd identified where LenAI made the biggest difference and built a routine around it. The same users were quickest to outgrow chatbot-mode and start asking for LenAI to have access to the systems they used every day, to pull data directly rather than have it pasted in. They didn't want a better assistant; they wanted a platform.

Casual users were a different problem. Their barrier wasn't compliance or workflow it was the blank box. Opening LenAI to an empty prompt with no hint of what to ask left a lot of colleagues unsure where to start, and a fair number never came back. A landing screen with a few example prompts, framed around the kind of work the user actually did, dropped the threshold significantly. Casual users don't want to learn prompt-craft; they want a starting point.

Two social patterns mattered as much as anything in the product. Peer teaching outpaced formal training quickly colleagues who'd figured the tool out became the people their team turned to for prompt help, faster and more useful than the next academy session. And the younger or less confident colleagues found there was no social cost to asking LenAI things they wouldn't have asked a senior basic policy questions, "is this how I'd phrase this", "what's the difference between X and Y" the kind of question someone in their first claims job hesitates to take up a senior's time with. The tool was, for that population, an unjudgemental colleague.

---

## 4. Training is not education

The first thing I found myself teaching that wasn't in the deck was the most basic and the most overlooked: 'treat LenAI like a tool, not a person.' Colleagues writing prompts like emails "Hi, could you possibly help me with…" were getting answers that were polite but slow to surface the useful bit. Drop the niceties. Be direct. Say what you want, in the order you want it. I'd been using LLMs for years before the rollout and even I had to be told this the social instinct to be polite to something that talks back is stronger than people realise. The training deck assumed people would arrive understanding the tool was software. Most didn't.

The second thing was a harder lesson: **the data is only as good as what the colleague puts in.** The clearest example I saw on the floor was a colleague who uploaded the wrong policy document and got back a confident, accurate answer to the wrong question. The output was technically correct; it just had nothing to do with the claim they were actually working on. The tool didn't flag the mismatch because it couldn't know there was one. What it *did* do, several prompts later, was pick up from context that the user was referring to a different policy than the one they'd uploaded which is impressive, but is exactly the kind of behaviour that builds false confidence in users who don't yet understand its limits.

That second example is the whole training-vs-education distinction in one moment. Training would have shown that colleague how to upload a document. Education is teaching them to ask, before trusting the answer, *did I give it the right document?* and to keep asking that even when the answer sounds right. The first is a slide. The second is built over weeks of use, peer conversation, and watching the tool be confidently wrong about something you happen to know well. The GenAI Academy got better at this over time, partly because the rollout team got better at noticing where colleagues were getting tripped up. But the gap between "knows the buttons" and "knows when to trust the output" is the one that determined whether someone became a useful long-term user or a sporadic one.

The takeaway: training gets people across the threshold. Education is what makes the difference between a tool that produces hours-saved and a tool that produces hours-saved-without-introducing-new-risk. The first is measurable on day one; the second only becomes visible after the system has been in regulated hands for a while, and it doesn't transfer through a slide deck.

---

— Leon
