export const DAD_JOKES = [
  { question: "Why did the scarecrow win an award?", punchline: "Because he was outstanding in his field." },
  { question: "What do you call a bear with no teeth?", punchline: "A gummy bear." },
  { question: "Why can't a bicycle stand up on its own?", punchline: "Because it's two-tyred." },
  { question: "What do you call cheese that isn't yours?", punchline: "Nacho cheese." },
  { question: "Why did the maths book look sad?", punchline: "It had too many problems." },
  { question: "How do you organise a space party?", punchline: "You planet." },
  { question: "What do you call a fish wearing a bow tie?", punchline: "Sofishticated." },
  { question: "Why don't eggs tell jokes?", punchline: "They'd crack each other up." },
  { question: "What do you call a sleeping dinosaur?", punchline: "A dino-snore." },
  { question: "Why did the golfer bring two pairs of trousers?", punchline: "In case he got a hole in one." },
  { question: "How does the moon cut its hair?", punchline: "Eclipse it." },
  { question: "What did one wall say to the other?", punchline: "I'll meet you at the corner." },
  { question: "What do you call a factory that makes okay products?", punchline: "A satisfactory." },
  { question: "Why did the tomato turn red?", punchline: "Because it saw the salad dressing." },
  { question: "What do you call a boomerang that doesn't come back?", punchline: "A stick." },
  { question: "Why couldn't the pony sing?", punchline: "It was a little hoarse." },
  { question: "What do you call an alligator in a waistcoat?", punchline: "An investigator." },
  { question: "What kind of shoes do ninjas wear?", punchline: "Sneakers." },
  { question: "Why did the orange stop halfway up the hill?", punchline: "It ran out of juice." },
  { question: "What do you call a dog that does magic?", punchline: "A labracadabrador." },
  { question: "How do trees get online?", punchline: "They log in." },
  { question: "What did the ocean say to the beach?", punchline: "Nothing. It just waved." },
  { question: "Why don't skeletons fight each other?", punchline: "They don't have the guts." },
  { question: "What do you call a pile of cats?", punchline: "A meowtain." },
] as const

// Every other joke has the same chance; the current joke is never selected.
export function randomJokeIndex(current: number, random = Math.random()) {
  const pick = Math.floor(random * (DAD_JOKES.length - 1))
  return pick >= current ? pick + 1 : pick
}
