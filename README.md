# README

This is a little personal project I wrote that uses NLTK to tokenize and mutate the text of Jorge Luis Borges' short story "The Library of Babel" to mimic biological descent with modification. The project is currently running [on Heroku](https://botched-replication.herokuapp.com/). Note: the project is currently (as of 12/14/19) running on a Heroku free tier, which means it gets shut off every 30 minutes, at which point the whole thing is reloaded from the original text and starts mutating again from scratch. It's also a very simple web app that doesn't refresh any part of the page automatically.

## Implementation

How the mutation works: the entire text is tokenized. A random word is then pulled out of the list of tokens. The random word's part of speech is identified. The main `Corpus` class then also builds a dictionary (in #pos_dictionary()) where each key is a part of speech and each value is yet another list of _every_ word from the text (including repeats, these are not sets) that is that part of speech. One is chosen at random and the original random word is replaced with the new word.

The part of speech dictionary is noteworthy in that it's not saved as an attribute, but instead is a method and is reevaluated on every mutation. This is obviously significantly more computation-intensive, but allows for real-time responses to things like "extinction events" (ex: replacing a word now means that word no longer exists in the modified text).

There are some fun and somewhat arbitrary decisions made here. The primary one is the rate of mutation, which is currently set at one mutation every 204 seconds. You can see my loose justification of that in the code [here](https://github.com/macroscopicentric/botched_replication/blob/master/botched_replication.py#L12-L22).

Another is that I chose to mutate at the level of whole words (and specifically matching parts of speech). This was largely for the logistical reason, which is that it would have mutated too quickly into gibberish without some ground rules. But I also partially justify my choice this way: People frequently refer to DNA bases as a genetic alphabet. If you extend this metaphor, proteins are effectively the words built by the alphabet. This works pretty well since proteins, like words, have different functions but those functions can be categorized loosely, almost like "parts of speech." Also like in language and communication, the coding parts of our DNA are fairly strictly regulated simply because most mutations causing protein changes would be fatal (to life, or to communication). As a result, most sustainable protein changes are from one type of protein to a similarly functioning protein. This is admittedly a pretty handwavey explanation but I think we can all agree that random letter insertions would be boring because so rarely would they allow for _meaningful_ changes. (I'm not totally sure the guy who wrote a short story that included an entire book of a's would fully agree with me skipping the boring parts but in my defense he never actually implemented the library he just wrote like ten pages about the library and then called it good, so we clearly have similar attention spans at least.)

## Running It Locally

The mutation happens in `botched_replication.py` using NLTK, and the web app is in `web_app.py` and relies on Flask. You'll also need a local redis instance running if you want to try running this locally, and you'll want to uncomment the relevant line in `web_app.py` using that one instead of the Heroku-redis.

## Todos

So many. Things it might be fun to do:
- Use the stuff I put in the `ajax-experiment` branch to actually do live client-side updates of individual word changes. (Think of the animation potential! So fun!)
- Slow this down so it's not 1000x the fastest living bacterial mutation rate and make it a long-running thing on Heroku.
- Changelog of mutations! Right now you can only see the most recent at a second endpoint and I don't even do anything with that info. Boring.
- Find a wonderful new handwavey way to add new words into the text! Right now words can only go extinct, new words cannot spontaneously appear in the text, which is VERY anti-genetics.

Literally none of these will ever get done. That's fine. Life happens, move on.