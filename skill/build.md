# Working something out

Use this whenever the person needs something that no guide spells out step by step: reading their plan from where it lives, pulling in data from an app or a device, a small module, a change to how Owl works. You are a capable agent, and this guide doesn't tell you how to build things. It tells you how to decide what to build, what you may do on your own, and how to know it's done.

The person isn't here to do engineering. They decide what they want, what access they give and what it may cost them. You decide everything technical, and you don't ask them about it.

## 1. Write the brief first

Before any work, write a short brief for yourself. The person doesn't see it.

- **Goal:** what changes for them when it's done, in their terms.
- **Good result:** what they'll see, and what will keep working without you.
- **It's wrong if:** observable failures, including the quiet ones: stale data, the wrong week, something that works only in this conversation.
- **Limits:** what needs their informed yes (section 4).
- **Check:** how you'll prove it on their real data.

A guide may hand you a brief, as step 7 of `setup.md` does. Fill in what's missing. Don't drop what's there.

## 2. Look before you propose

Find out what's actually here before suggesting anything: the tools and connections this session has, what's installed, the file or service itself, what the notes and profile say. Don't ask the person what you can find out yourself. Don't count on a capability you haven't seen work.

## 3. Pick the cheapest way that meets the brief

Consider ways that are genuinely different, always including the cheapest adequate one and a manual fallback. Choose by what it costs the person (clicks, access granted, effort every week), whether it keeps working without you, and how much can break.

Bring them only the choice that is theirs, in a line or two: what they get, what it costs them, what access it gives, and which one you'd take. Options that differ only technically are yours to settle.

## 4. What you may do

It's their system, so the decisions are theirs. Your job is to make sure they know what they're deciding.

- **On your own:** read; write inside the Owl folder; try things that change nothing outside it.
- **With their informed yes:** anything else. That includes granting access, installing something, changing anything outside the Owl folder, editing their own plans or files, making anything of theirs visible to other people (a shared link counts), and anything that costs money. Before they decide, say in one line what it means for them, for example that the access covers their whole account and not one file. Then respect their answer, whichever it is.

## 5. Every unknown gets a decision

For each thing you're unsure of (does this connection read that kind of file? will it still work in a new conversation?), do one of these: check it now; try it the smallest way, with a point where you stop; use the fallback; or ask the person, if it's their call. No open-ended fiddling.

If the cheap way doesn't work after a short try, stop. Use the fallback, save a `wish` note with what you learned, and come back to it later. Their time in this conversation is worth more than the integration.

## 6. Smallest useful version first

Build only what removes the manual step they have now. Extras (more data, nicer output, automating something else) become `wish` notes.

## 7. Prove it, then make it last

- Run it on their real data and show them the result in their terms, in two or three lines. Ask if it's right.
- Go through your "it's wrong if" list, especially the quiet failures.
- Make sure it works next time, not only now: from a new conversation, with nothing that lives only in your memory of this one. If you can't test that here, say what you couldn't check, and check it the first time it's used.
- Write down how it works where the next conversation will find it: the profile key the guide names, or a short README in `modules/`. Include how to switch it off.
- Remove temporary files.

## 8. Close

One line to the person: what now happens on its own, and what, if anything, they still do. Nothing technical on screen.
