# Evaluation results

Data: `D:\projects\recipe-chatbot\data\raw` - 122937 recipes loaded, skipped: {'empty record': 517, 'no title': 52, 'no ingredients': 1624, 'no instructions': 34}  
Mode: LLM parsing

**Checks passed: 26/26**  |  **LLM parses matching expected intent: 18/21**

## T1 multi-turn search + restriction

**User:** Find a penne pasta recipe

```
Search: 'penne pasta' | filters: no filters
3459 of 3459 text matches pass the filters. Top 5:

1. Creamy Penne Pasta  [ar:nvQzTEX.J7/2LmKnF8KjsR6aCqNHGxO]  (relevance 0.60, 9 ingredients, 2 steps)

2. Albino Pasta  [ar:9tzOXDImfRGmY2sLVWSfU.cHLLbdvUC]  (relevance 0.54, 4 ingredients, 2 steps)

3. Penne Pasta with Spinach and Bacon  [ar:23to8XzUux0FF.g5ZFsqnxvhByMzfJ.]  (relevance 0.51, 6 ingredients, 3 steps)

4. Bacon and Parmesan Penne Pasta  [ar:hzvAPQudIHjif5vLsP8vv.H8aTThvAq]  (relevance 0.51, 5 ingredients, 3 steps)

5. Tuna Alfredo with Penne Pasta  [ar:Ds7VCz2ZVAvWeI/YBnNcA/lzUZGjb7G]  (relevance 0.50, 6 ingredients, 2 steps)

Say 'show #N' for full ingredients and instructions.
```
_0.0s_
- PASS `has_results`: 5 results
- PASS `top_mentions`: 5/5 results mention 'penne'

**User:** I cannot have dairy

```
Search: 'penne pasta' | filters: excludes dairy
829 of 3459 text matches pass the filters. Top 5:

1. Penne Pasta with Spinach and Bacon  [ar:23to8XzUux0FF.g5ZFsqnxvhByMzfJ.]  (relevance 0.51, 6 ingredients, 3 steps)
   no dairy: checked all 6 ingredient lines, none match
   ingredients: 1 (12 ounce) package penne pasta | 2 tablespoons olive oil, divided | 6 slices bacon, chopped | 2 tablespoons minced garlic | 1 (14.5 ounce) can diced tomatoes | 1 bunch fresh spinach, rinsed and torn into bite-size pieces

2. Penne Pasta with Cannellini Beans and Escarole  [ar:zwRAInNlhnKD1jMf/HOm5a9oKhjC8Om]  (relevance 0.44, 5 ingredients, 2 steps)
   no dairy: checked all 5 ingredient lines, none match
   ingredients: 1 (16 ounce) package dry penne pasta | 1 head escarole, chopped | 1 (15.5 ounce) can cannellini beans, with liquid | 1 (14.5 ounce) can diced tomatoes with garlic and onion, drained | salt and ground black pepper to taste

3. Pat's Simple Penne  [ar:9mPiUMSt4KndASd0tYPD7iKvkRhsO2i]  (relevance 0.39, 5 ingredients, 4 steps)
   no dairy: checked all 5 ingredient lines, none match
   ingredients: 6 cups penne pasta | 1 pound bacon, cut into 1 inch pieces | 1 onion, thinly sliced | 3 1/2 (10.75 ounce) cans chicken broth | 1 pinch crushed red pepper flakes

4. Penne Pasta Salad with Sun Dried Tomatoes, Asparagus and Basil  [fn:ck/foCIv1g.W0SyPMLF5DWS/ZdeQBRi]  (relevance 0.39, 7 ingredients, 2 steps)
   no dairy: checked all 7 ingredient lines, none match
   ingredients: 1 pound penne pasta | 1 cup fresh asparagus tips | 4 garlic cloves, minced | 1/4 cup olive oil | Salt and pepper, to taste | 1 bunch basil, chopped | 1 cup sun-dried tomatoes in oil

5. Pasta and Beans  [ar:HKOP45CaBPW0XwN77bZjJtVFtXVDV..]  (relevance 0.36, 6 ingredients, 3 steps)
   no dairy: checked all 6 ingredient lines, none match
   ingredients: 1 1/2 tablespoons extra virgin olive oil | 1 onion, chopped | 2 tomatoes, chopped | 1 (15 ounce) can cannellini beans | 2 cups penne pasta | salt to taste

Say 'show #N' for full ingredients and instructions.
Active restrictions: dairy
```
_0.2s_ | parse diffs: ["query: expected None, got 'penne pasta'"]
- PASS `has_results`: 5 results
- PASS `none_violate`: all 5 results free of dairy
- PASS `query_kept`: active query = 'penne pasta'

**User:** Show me the first one

```
Penne Pasta with Spinach and Bacon  [ar:23to8XzUux0FF.g5ZFsqnxvhByMzfJ.]

Ingredients:
  - 1 (12 ounce) package penne pasta
  - 2 tablespoons olive oil, divided
  - 6 slices bacon, chopped
  - 2 tablespoons minced garlic
  - 1 (14.5 ounce) can diced tomatoes
  - 1 bunch fresh spinach, rinsed and torn into bite-size pieces

Instructions:
  1. Bring a large pot of lightly salted water to a boil. Add the penne pasta, and cook until tender, 8 to 10 minutes.
  2. Meanwhile, heat 1 tablespoon of olive oil in a skillet over medium heat. Place bacon in the skillet, and cook until browned and crisp. Add garlic, and cook for about 1 minute. Stir in the tomatoes, and cook until heated through.
  3. Place the spinach into a colander, and drain the hot pasta over it so it is wilted. Transfer to a large serving bowl, and toss with the remaining olive oil, and the bacon and tomato mixture.
```
_0.0s_

## T1 follow-ups about the results

**User:** Find a penne pasta recipe

```
Search: 'penne pasta' | filters: no filters
3459 of 3459 text matches pass the filters. Top 5:

1. Creamy Penne Pasta  [ar:nvQzTEX.J7/2LmKnF8KjsR6aCqNHGxO]  (relevance 0.60, 9 ingredients, 2 steps)

2. Albino Pasta  [ar:9tzOXDImfRGmY2sLVWSfU.cHLLbdvUC]  (relevance 0.54, 4 ingredients, 2 steps)

3. Penne Pasta with Spinach and Bacon  [ar:23to8XzUux0FF.g5ZFsqnxvhByMzfJ.]  (relevance 0.51, 6 ingredients, 3 steps)

4. Bacon and Parmesan Penne Pasta  [ar:hzvAPQudIHjif5vLsP8vv.H8aTThvAq]  (relevance 0.51, 5 ingredients, 3 steps)

5. Tuna Alfredo with Penne Pasta  [ar:Ds7VCz2ZVAvWeI/YBnNcA/lzUZGjb7G]  (relevance 0.50, 6 ingredients, 2 steps)

Say 'show #N' for full ingredients and instructions.
```
_0.0s_
- PASS `has_results`: 5 results

**User:** How many of those contain garlic?

```
Recipe count
Filters: contains garlic
Recipes analysed: 2005 (total in the search results for 'penne pasta': 3459)

Count: 2005  ->  2005 / 3459 = 57.96% of the search results for 'penne pasta'

Method: Counted recipes passing every filter. Percentage = count / total recipes in scope. Ingredient match: cleaned ingredient name contains the word (plural-insensitive, synonyms merged); different products such as 'garlic powder' do NOT count as 'garlic'.
```
_0.1s_
- PASS `says`: reply contains "the search results for 'penne pasta'"

**User:** Does the first one contain garlic?

```
Creamy Penne Pasta  [ar:nvQzTEX.J7/2LmKnF8KjsR6aCqNHGxO]  - 9 ingredients, 2 steps
garlic: yes - 1 teaspoon minced garlic
```
_0.0s_
- PASS `says`: reply contains 'garlic: '

## T1 aggregate statistics

**User:** How many recipes contain both garlic and onion? What percentage of the dataset is that?

```
Recipe count
Filters: contains garlic AND onion
Recipes analysed: 16552 (total in the dataset: 122937)

Count: 16552  ->  16552 / 122937 = 13.46% of the dataset

Method: Counted recipes passing every filter. Percentage = count / total recipes in scope. Ingredient match: cleaned ingredient name contains the word (plural-insensitive, synonyms merged); different products such as 'garlic powder' do NOT count as 'garlic'.
```
_1.7s_
- PASS `count_consistent`: both=16552, singles=[33662, 31878], re-run=16552, percent=13.46% stated with denominator

**User:** Among recipes containing tomato, which five have the fewest instruction steps?

```
Fewest instruction steps
Filters: contains tomato
Recipes analysed: 16349 (total in the dataset: 122937)

1. Melanie's Chili  [ar:..M776r8BHroHcCXw3vInfs25LDkWw2]  - 1 steps
2. Skillet Spaghetti Supper  [ar:.12bcbuKzBtUwvUDLz4SA2iPZctyzei]  - 1 steps
3. Paleo Coconut Walnut Squash  [ar:.3oN2HceZh201rfooa/WQeOsq96R/Ku]  - 1 steps
4. Everything in the Fridge Pasta Sauce  [ar:.FFTHNuM.1tpgcYtWMhP8wdZBmFtjI.]  - 1 steps
5. College Student's Saucy Chickpeas  [ar:.Je7yi3D.V.iTOFXtSmH6lIC0YtjK.q]  - 1 steps

Method: Step = one non-empty line/paragraph of the original instructions. Ties broken by recipe ID so the ranking is reproducible.
```
_0.8s_
- PASS `ranked_by_steps`: steps=[1, 1, 1, 1, 1]; global fewest=[1, 1, 1, 1, 1]

**User:** What are the 10 most common ingredients?

```
Most common ingredients
Filters: no filters
Recipes analysed: 122937 (total in the dataset: 122937)

1. garlic: 31851 recipes (25.9%)
2. egg: 24932 recipes (20.3%)
3. olive oil: 20397 recipes (16.6%)
4. butter: 19584 recipes (15.9%)
5. onion: 19096 recipes (15.5%)
6. all-purpose flour: 18853 recipes (15.3%)
7. sugar: 17466 recipes (14.2%)
8. unsalted butter: 15497 recipes (12.6%)
9. milk: 12295 recipes (10.0%)
10. vegetable oil: 10901 recipes (8.9%)

Method: Number of recipes whose cleaned ingredient names include each name (counted once per recipe). Cleaning drops quantities, units, size/prep words and text after a comma. Salt, pepper and water are left out.
```
_1.6s_

**User:** What is the average and median number of ingredients?

```
Ingredients per recipe
Filters: no filters
Recipes analysed: 122937 (total in the dataset: 122937)

mean: 10.39
median: 9
min: 1
max: 82

Method: Ingredient count = number of non-empty ingredient lines in the original record.
```
_0.1s_

## T2 ingredient matching + follow-up

**User:** I have eggs, onions, tomatoes, and rice. Suggest five recipes using as many of these as possible, with no peanuts and at most six instruction steps. Prefer recipes that need the fewest additional ingredients.

```
Your ingredients: egg, onion, tomato, rice
Hard constraints: excludes peanut; at most 6 steps
Ranking: most_matched > fewest_extra > fewest_steps > recipe ID (salt, pepper, water assumed in pantry)
No quantities given: name-level match only; quantity sufficiency was not verified.
66608 recipes use at least one of your ingredients; 54430 pass the constraints.

1. Fiesta Egg Skillet  [ar:QyVarQzRar/zTLW7ExZpc6qbYC1xQF6]  - 5 steps
   matched: egg, onion, tomato, rice
   not used from your list: -
   missing / extra required: 2 tablespoons olive oil; 1/4 cup heavy cream; 1 cup diced ham; 1 (4 ounce) can diced green chiles, drained; 1 1/2 cups shredded Cheddar cheese, divided
   pantry (assumed): 1/2 teaspoon salt; 1/4 teaspoon ground black pepper
   why here: uses 4/4 of yours, needs 5 extra, 5 steps

2. Curried Rice With Smoked Trout  [fn:Akk/zqCo1n3wzwavH0..w6QIF5363M2]  - 3 steps
   matched: egg, onion, tomato, rice
   not used from your list: -
   missing / extra required: 1 1/2 tablespoons extra-virgin olive oil; 2 teaspoons curry powder; 1/4 cup chopped fresh cilantro; 4 cups mixed greens or baby spinach; Juice of 1/2 lemon; 4 ounces smoked trout, flaked
   pantry (assumed): Kosher salt and freshly ground pepper
   why here: uses 4/4 of yours, needs 6 extra, 3 steps

3. Omelet for Leftovers (Omurice)  [ar:ylwbZEdf8zK8ZA6pqy15Wll6YtZyG2G]  - 2 steps
   matched: egg, onion, tomato, rice
   not used from your list: -
   missing / extra required: 1 1/2 teaspoons butter; 1/2 red bell pepper, sliced; 1/4 zucchini, sliced; 1 ounce sliced mushrooms; 1 tablespoon ketchup, or to taste; 1 slice cooked bacon, chopped, or more to taste; 1/2 teaspoon paprika
   pantry (assumed): salt and ground black pepper to taste
   why here: uses 4/4 of yours, needs 7 extra, 2 steps

4. Turkey Meatball Vindaloo  [fn:Z8iATJKOvt1aLJVdw1DFqPxUlKbxwe.]  - 3 steps
   matched: egg, onion, tomato, rice
   not used from your list: -
   missing / extra required: 1 1/4 pounds ground turkey; 1/4 cup breadcrumbs; 3/4 cup chopped fresh cilantro; 1 tablespoon grated peeled ginger; 2 tablespoons extra-virgin olive oil; 1 red bell pepper, chopped; 2 to 3 teaspoons hot Madras curry powder (or regular curry powder mixed with 1/4 teaspoon cayenne)
   pantry (assumed): Kosher salt
   why here: uses 4/4 of yours, needs 7 extra, 3 steps

5. Baked Eggplant with Ground Beef  [ar:4hdBHLI11MpSoJtnXn/vZjwb5Coetb2]  - 6 steps
   matched: egg, onion, tomato, rice
   not used from your list: -
   missing / extra required: 1/4 cup bread crumbs; 2 tablespoons vegetable oil, or more to taste; 1/2 pound ground beef; 1 clove garlic, chopped; 1 eggplant, halved lengthwise and pulp scooped from peel leaving two shells; 1/4 cup shredded Italian cheese blend; 1/4 teaspoon dried basil
   pantry (assumed): 1 pinch salt and ground black pepper to taste
   why here: uses 4/4 of yours, needs 7 extra, 6 steps
Active restrictions: peanut
```
_5.5s_
- PASS `has_results`: 5 results
- PASS `match_valid`: 5 results, constraint breaks: none, sorted: True

**User:** Exclude eggs too

```
Your ingredients: onion, tomato, rice
Hard constraints: excludes peanut, egg; at most 6 steps
Ranking: most_matched > fewest_extra > fewest_steps > recipe ID (salt, pepper, water assumed in pantry)
No quantities given: name-level match only; quantity sufficiency was not verified.
Removed from your ingredients because they are now excluded: egg
40970 recipes use at least one of your ingredients; 28253 pass the constraints.

1. Mark's Quick Beef Spanish Rice  [ar:2SrtKig3ojWd/bADwTMfSHHEpdrwnvG]  - 3 steps
   matched: onion, tomato, rice
   not used from your list: -
   missing / extra required: 1 1/2 pounds ground beef; 1/3 cup chopped green bell pepper
   pantry (assumed): 1 cup water; 1/2 teaspoon salt; salt and black pepper to taste
   why here: uses 3/3 of yours, needs 2 extra, 3 steps

2. Spanish Rice Soup  [ar:1Pxb9wyEXP7.LTDd7BAJP.FyGppXeC.]  - 1 steps
   matched: onion, tomato, rice
   not used from your list: -
   missing / extra required: 1 pound ground turkey; 1 clove crushed garlic; 2 (8 ounce) cans tomato sauce
   pantry (assumed): 4 1/2 cups water
   why here: uses 3/3 of yours, needs 3 extra, 1 steps

3. Easy Red Rice  [ar:HEANjerxzzD5N/d0QMF7jOsTplW.f1K]  - 1 steps
   matched: onion, tomato, rice
   not used from your list: -
   missing / extra required: 1 tablespoon olive oil; 2 cups chicken broth; 1/2 teaspoon dried basil
   why here: uses 3/3 of yours, needs 3 extra, 1 steps

4. Zucchini Saute  [ar:J/illFyDAANk7X1GwnmkQ4iMZPDTBmO]  - 2 steps
   matched: onion, tomato, rice
   not used from your list: -
   missing / extra required: 1 tablespoon vegetable oil; 2 pounds zucchini, peeled and cut into 1 inch thick slices; 1 green bell pepper, chopped
   pantry (assumed): salt to taste; ground black pepper to taste; 1/2 cup water
   why here: uses 3/3 of yours, needs 3 extra, 2 steps

5. Spanish Rice II  [ar:nwtx08KExuRUl4LHekRYuJ3Y9EsHE.m]  - 2 steps
   matched: onion, tomato, rice
   not used from your list: -
   missing / extra required: 2 tablespoons vegetable oil; 1/2 green bell pepper, chopped; 2 teaspoons chili powder, or to taste
   pantry (assumed): 2 cups water; 1 teaspoon salt
   why here: uses 3/3 of yours, needs 3 extra, 2 steps
Active restrictions: peanut, egg
```
_3.8s_
- PASS `has_results`: 5 results
- PASS `have_dropped`: have now = ['onion', 'tomato', 'rice']
- PASS `match_valid`: 5 results, constraint breaks: none, sorted: True

## T2 quantities

**User:** I have 2 cups rice and 3 eggs, what can I make?

```
Your ingredients: 2 cup rice, 3 egg
Hard constraints: no filters
Ranking: most_matched > fewest_extra > fewest_steps > recipe ID (salt, pepper, water assumed in pantry)
36392 recipes use at least one of your ingredients; 36392 pass the constraints.

1. Portuguese Sweet Rice  [ar:DSWxOyo5nIMV6kTVmUYSDD81/WVaLxy]  - 2 steps
   matched: rice, egg
   not used from your list: -
   missing / extra required: 1 1/2 quarts milk; 1 cup white sugar
   qty: rice: you have 2 cup rice, recipe uses '1 cup uncooked white rice' -> enough
   qty: egg: you have 3 egg, recipe uses '2 eggs, beaten' -> enough
   why here: uses 2/2 of yours, needs 2 extra, 2 steps

2. Egg and Pesto Sushi  [ar:2WeDEiGPrPJMFddJhI76CKsxYhVhl8i]  - 3 steps
   matched: rice, egg
   not used from your list: -
   missing / extra required: 6 sheets nori (dry seaweed); 1/4 cup basil pesto
   pantry (assumed): 4 cups water; salt and pepper to taste
   qty: rice: you have 2 cup rice, recipe uses '2 cups uncooked glutinous white rice' -> enough
   qty: egg: you have 3 egg, recipe uses '6 eggs, beaten' -> NOT enough (recipe needs 6)
   why here: uses 2/2 of yours, needs 2 extra, 3 steps

3. Vegetarian Lemon-Rice Soup  [ar:dBWk7S.seP3R8GUJ3j0BxSZ8BUHndKS]  - 3 steps
   matched: rice, egg
   not used from your list: -
   missing / extra required: 4 cups vegetable broth; 2 lemons, juiced
   pantry (assumed): salt and ground black pepper to taste
   qty: rice: quantity not verified (recipe line '2 1/2 ounces rice' uses a different or no unit)
   qty: egg: you have 3 egg, recipe uses '3 eggs' -> enough
   why here: uses 2/2 of yours, needs 2 extra, 3 steps

4. R is for Rich Rice Pudding  [epi:HFPFk9VuI6u2QqDt0Kd4XLu4LiOOdZS]  - 3 steps
   matched: rice, egg
   not used from your list: -
   missing / extra required: 1 1/2 cups whole milk, plus more if desired; 2 tablespoons sugar
   qty: rice: quantity not verified ('2 cups cooked rice' is cooked, yours is not, or vice versa)
   qty: egg: you have 3 egg, recipe uses '2 large eggs, beaten' -> enough
   why here: uses 2/2 of yours, needs 2 extra, 3 steps

5. Egyptian Rice Cooked in a Clay Bram  [fn:6zutMq3CPKBpD8xIWgHc1fZGvatm5/2]  - 3 steps
   matched: rice, egg
   not used from your list: -
   missing / extra required: 3 tablespoons unsalted butter; 3 cups whole milk
   pantry (assumed): 1 teaspoon sea salt
   qty: rice: you have 2 cup rice, recipe uses '1 1/2 cups short-grain rice (I use paella rice, but arborio or even sushi rice would work wonderfully)' -> enough
... (2 more lines)
```
_3.0s_
- PASS `has_results`: 5 results

## T2 no-match case

**User:** I have saffron, durian and quinoa. Only recipes that use all three, at most 3 steps.

```
Your ingredients: saffron, durian, quinoa
Hard constraints: contains saffron AND durian AND quinoa; at most 3 steps
Ranking: most_matched > fewest_extra > fewest_steps > recipe ID (salt, pepper, water assumed in pantry)
No quantities given: name-level match only; quantity sufficiency was not verified.
1324 recipes use at least one of your ingredients; 0 pass the constraints.

NO MATCH: no recipe satisfies all hard constraints.
Closest alternatives - each one VIOLATES a constraint, shown only for reference:

1. Saffron Quinoa with Dried Cherries and Almonds  [epi:VQuGf4kHU2t1/bK3uE7CCdBWP5JjiSy]  VIOLATES: has 8 steps (max 3); does not contain 'durian'
   matched: saffron, quinoa
   not used from your list: durian
   missing / extra required: 3 tablespoons coconut oil or olive oil, divided; 1 1/2 cups sliced almonds; 1 teaspoon ground cinnamon; Pinch of cayenne pepper; 1 medium onion, chopped; 1 1/2 cups dried cherries
   pantry (assumed): 1 3/4 teaspoons kosher salt, divided

2. Shrimp and Mushroom Quinoa Risotto  [epi:JGImspXF.r1128LgtqOntgLt9jCE2u.]  VIOLATES: has 12 steps (max 3); does not contain 'durian'
   matched: saffron, quinoa
   not used from your list: durian
   missing / extra required: 2 lb small hard-shell clams (2 to 2 1/2 inches in diameter); 1 celery rib, coarsely chopped; 1 large carrot, coarsely chopped; 1/2 large red onion, coarsely chopped; 1 Turkish or 1/2 California bay leaf; 2 lb medium shrimp in shell (31 to 35 per pound), peeled and deveined; 1/3 cup vegetable oil; 1 tablespoon achiote (annatto) seeds; 1/2 stick (1/4 cup) unsalted butter; 1/2 lb cremini or button mushrooms, trimmed and sliced (3/4 inch thick; 3 cups); 1/2 lb oyster mushrooms, trimmed and large caps halved lengthwise (2 3/4 cups); 1 (5- to 6-oz) portabella mushroom cap, sliced (1/4 inch thick); 2 tablespoons olive oil; 1/2 large red onion, thinly sliced; 2 garlic cloves, thinly sliced; 2 tablespoons bottled aj amarillo purée; 1 cup dry white wine; 1/2 cup heavy cream; 1/4 lb finely grated Parmigiano-Reggiano (2 cups); 3 tablespoons chopped fresh basil
   pantry (assumed): 8 cups cold water; 1/4 teaspoon black pepper; 1 1/2 teaspoons salt; 1/2 teaspoon black pepper

3. Quinoa with Moroccan Winter Squash and Carrot Stew  [epi:kerFupGW7CxPX9FnMgUdYIqpXf0N7bu]  VIOLATES: has 7 steps (max 3); does not contain 'durian'
   matched: saffron, quinoa
   not used from your list: durian
   missing / extra required: 2 tablespoons olive oil; 1 cup chopped onion; 3 garlic cloves, chopped; 2 teaspoons Hungarian sweet paprika; 1/2 teaspoon ground coriander; 1/2 teaspoon ground cumin; 1/2 teaspoon turmeric; 1/2 teaspoon ground ginger; 1/2 teaspoon cayenne pepper; 1 14 1/2-ounce can diced tomatoes, drained; 2 tablespoons fresh lemon juice; 3 cups 1-inch cubes peeled butternut squash (from 1 1/2-pound squash); 2 cups 3/4-inch cubes peeled carrots; 1 tablespoon butter; 1 tablespoon olive oil; 1/2 cup finely chopped onion; 1/4 cup finely chopped peeled carrot; 2 garlic cloves, minced; 1/2 teaspoon turmeric; 1/2 cup chopped fresh cilantro, divided; 2 teaspoons chopped fresh mint, divided
   pantry (assumed): 1 teaspoon salt; 1/2 teaspoon ground black pepper; 1 cup water; 1/2 teaspoon salt; 2 cups water
```
_1.7s_
- PASS `no_match_reported`: no-match stated: True; closest alternatives shown (each labelled VIOLATES): 4

## T3 egg-free banana bread

**User:** Take this banana bread recipe and remove eggs. Use only ingredients that appear in the dataset. What replacements have evidence from related baked recipes, and how might the texture change?

```
Using 'Banana Bread' (ar:BoBTO3QUO3Ci.0kayPs8.CfDU5oEXuu) as the recipe. Give an ID to use a different one.
Adapting: Banana Bread  [ar:BoBTO3QUO3Ci.0kayPs8.CfDU5oEXuu]
Change requested: remove egg; restrictions: none

- Line: '2 eggs, beaten'
  Role (general knowledge): binding and structure, moisture, some leavening in baking
  Local evidence pool: 1500 most similar recipes (164 without it, 1336 with it)
    > plain yogurt: supported - in 6 similar recipes without it (4%) vs 2% of those with it; e.g. fn:p174TykunvO./PLjDpl03RBTaXiOEdu, ar:zDXYTtHNZiB/zBsPG4GYb4clr3Q4FYy, ar:D3bGqZWu5sNEPFq9WybOYagumQF9Ur6, fn:TZXLNcRBN2fCsW0JR1zWrxyhopvBHca, fn:M/7pnvPz8Wb6PH5rciq9gjzoncgVj9q ...
      direct (title says made without it): fn:p174TykunvO./PLjDpl03RBTaXiOEdu, fn:TZXLNcRBN2fCsW0JR1zWrxyhopvBHca
      buttermilk: supported - in 29 similar recipes without it (18%) vs 13% of those with it; e.g. ar:hP4bs4Hnuqh3nV2YRsDMbFz/d5GZR0i, epi:y6T13hIM/WW0IPK2tg/PC.ZuQWQ0I.W, epi:t1Xjyz0oHDWZ7/NckuPwPEbJZS2Z93G, ar:/4//SYLvmdSzHBaKS.BG7u8RvC6EM12, ar:aIKcPNUSv1I93wOhNVpcQHXAnCVLI5K ...
      direct (title says made without it): ar:0QJ0Ix.sMt/qvuYxW8DQki2lKMcClmS
      silken tofu, blended: weak - in 1 similar recipes without it (1%) vs 0% of those with it; e.g. ar:5S4TJwjeeH.L/gDoUxUR0jfxC/8Vd4u
      mashed banana: conflicting - in 76 similar recipes without it (46%) vs 33% of those with it; e.g. ar:PhnAKrjQUJ7cNju0QrQQd7ZX6wp5g5y, ar:TJFqS5qmSUVcBw7c2Da99BzhmvnbgCm, fn:p174TykunvO./PLjDpl03RBTaXiOEdu, ar:ij6QwLu2zgfChlFpoKA2KqoLRZiXb.6, ar:5S4TJwjeeH.L/gDoUxUR0jfxC/8Vd4u ...
      direct (title says made without it): fn:p174TykunvO./PLjDpl03RBTaXiOEdu, ar:ij6QwLu2zgfChlFpoKA2KqoLRZiXb.6, ar:.GLWQH0bkiU3fRzwc68PqTCqGHJj2fy, ar:3w6xjW7R3yxf46eRNeTeERSCdaGwAMa, ar:ASoUPVV1LvfjKR4QSR8F/sESL58SbW2
      note: already in this recipe, so its evidence is confounded
      applesauce: conflicting - in 5 similar recipes without it (3%) vs 3% of those with it; e.g. ar:.GLWQH0bkiU3fRzwc68PqTCqGHJj2fy, ar:cHlllf8nAZGzy9zEQxH8t03PgFdbdAu, ar:BPzywWaTryMtzEPllE5AWYBZtieyGFm, ar:aJGOqBVXj9rKJuKMQPsiMYsPg043Tsu, fn:1kqAvZDBqNXVrtlPBQ2bBivLQ2VO57y
      direct (title says made without it): ar:.GLWQH0bkiU3fRzwc68PqTCqGHJj2fy, ar:BPzywWaTryMtzEPllE5AWYBZtieyGFm
      ground flaxseed + water: conflicting - in 1 similar recipes without it (1%) vs 1% of those with it; e.g. ar:BPzywWaTryMtzEPllE5AWYBZtieyGFm
      direct (title says made without it): ar:BPzywWaTryMtzEPllE5AWYBZtieyGFm
  Includes direct evidence: similar recipes whose titles say they are made without it. Evidence is split: 'buttermilk' is almost as well supported.
  Predicted effect (not verified): tender and moist; slight tang

Updated ingredients:
  - 1 1/2 cups all-purpose flour
  - 1 teaspoon baking soda
  - 1/2 teaspoon salt
  - 1 cup white sugar
  - plain yogurt - 1/4 cup per egg   [replaces: 2 eggs, beaten]
  - 1/4 cup butter, melted
  - 3 bananas, mashed

Revised instructions:
  1. Grease and flour two 7x3 inch loaf pans. Preheat oven to 350 degrees F (175 degrees C).
  2. [changed] In one bowl, whisk together flour, soda, salt, and sugar. Mix in slightly beaten plain yogurt, melted butter, and mashed bananas. Stir in nuts if desired. Pour into prepared pans.
  3. Bake at 350 degrees F (175 degrees C) for 1 hour, or until a wooden toothpick inserted in the center comes out clean.

Notes: ratios and roles are general cooking knowledge; evidence is local recipe co-occurrence, not tested outcomes. No internet search was used. This is not a medical/allergy safety guarantee - check product labels.
```
_0.1s_
- PASS `substitution_grounded`: adapted=True, refused=False, cited 33 ids (missing from data: []; still containing egg: []), 'egg' left in new lines: none
- PASS `evidence_labelled`: uncertainty labels present: ['conflicting', 'confounded', 'split']

## T3 dairy-free cream pasta

**User:** Find a creamy penne alfredo with heavy cream

```
Search: 'penne alfredo' | filters: contains heavy cream
112 of 824 text matches pass the filters. Top 5:

1. Alfredo Sauce  [ar:cu.PPkdTeAWw3KrgheaUv6DcKvR61hO]  (relevance 0.32, 5 ingredients, 1 steps)
   contains heavy cream: 1 cup heavy cream
   ingredients: 1/4 cup butter | 1 cup heavy cream | 1 clove garlic, crushed | 1 1/2 cups freshly grated Parmesan cheese | 1/4 cup chopped fresh parsley

2. Jalapeno Rosemary Alfredo  [ar:LWiUaNaVIXmAJrG8DOIsv1JLfS.R3yC]  (relevance 0.32, 7 ingredients, 1 steps)
   contains heavy cream: 1 cup heavy cream
   ingredients: 2 tablespoons olive oil | 2 cloves garlic, minced | 1 jalapeno pepper, seeded and minced | 1 cup heavy cream | 1/2 cup grated Parmesan cheese | 1 teaspoon dried rosemary | 1 pinch salt and ground black pepper to taste

3. Alfredo Mostaccioli  [ar:.KJWMy4viiWA8/yF9lnp00kkjePF2ZO]  (relevance 0.29, 8 ingredients, 2 steps)
   contains heavy cream: 1 cup heavy cream
   ingredients: 1 (16 ounce) package mostaccioli | 1 cup heavy cream | 1/2 cup butter | 1/2 cup grated Parmesan cheese | 1 cup chopped fresh parsley | 1 teaspoon salt | 1/4 teaspoon freshly ground black pepper | 1/8 teaspoon garlic powder

4. Alfredo Sauce  [fn:JDMkMyVpT0iGnta0qW/L03U5j4PlC9u]  (relevance 0.28, 5 ingredients, 2 steps)
   contains heavy cream: 1 cup heavy cream
   ingredients: 1 stick butter | 1 cup heavy cream | Salt and freshly ground black pepper | 2 cups freshly grated Parmesan | Pasta cooking water, as needed

5. Alfredo Blue  [ar:1bRhYQuxwFO.bEop0etFBG1cKpTkrBC]  (relevance 0.28, 8 ingredients, 4 steps)
   contains heavy cream: 2 cups heavy cream
   ingredients: 1 (16 ounce) package fettuccini pasta | 1 tablespoon olive oil | 1 clove garlic, sliced | 4 ounces blue cheese, crumbled | 1/4 cup grated Parmesan cheese | 2 cups heavy cream | 1 tablespoon Italian seasoning | salt and pepper to taste

Say 'show #N' for full ingredients and instructions.
```
_0.0s_ | parse diffs: ["query: expected 'creamy penne alfredo heavy cream', got 'penne alfredo'", "include: expected ['cream'], got ['heavy cream']"]
- PASS `has_results`: 5 results

**User:** Replace the cream in #1 without dairy. Prefer examples from recipes already in the database.

```
Adapting: Alfredo Sauce  [ar:cu.PPkdTeAWw3KrgheaUv6DcKvR61hO]
Change requested: remove heavy cream; restrictions: dairy

- Line: '1/4 cup butter'
  Role (general knowledge): fat for flavour, tenderness and browning
  Local evidence pool: 1500 most similar recipes (574 without it, 926 with it)
    > olive oil: supported - in 265 similar recipes without it (46%) vs 21% of those with it; e.g. fn:W/avyZ.harLyYn5tRT.2YGmKcsHNjCG, ar:LWiUaNaVIXmAJrG8DOIsv1JLfS.R3yC, ar:1bRhYQuxwFO.bEop0etFBG1cKpTkrBC, ar:odoTGzUuCAM5PzcANCaT4LH.XhuPPF., ar:l6/.hHUF4.D.uSwxaWCWW8ARbdaCb8G ...
      direct (title says made without it): fn:TJ408r4TI1kRXjTXg7E36YS1jxY2bwm, epi:SX4WUn7soISKA9E..uPhdLIJ6L/J4Fy, ar:sb1Unxe/KM1D3BbqKHz27h8tfgRVPUa
      vegetable oil: supported - in 36 similar recipes without it (6%) vs 3% of those with it; e.g. ar:yjU5yQ.qUitLsJdvrdGVUpAXLaMRpim, ar:S3NUbLZYczH2.kKDcopjw/yVUymO2ea, ar:yp7A2KE3xS77jQF7cUbFIhspvnoy71S, ar:FzY7/p3h9aOTrxI7XZRg8uYRaBR8Oti, ar:PL.UkQmanxhk44.rWyERF5Dv3dzpI.a ...
      applesauce: conflicting - in 1 similar recipes without it (0%) vs 0% of those with it; e.g. ar:ENyb2AL18Vds8UzGi6YGdVwsd8l81SO
      coconut oil: none - in 0 similar recipes without it (0%) vs 0% of those with it
  Includes direct evidence: similar recipes whose titles say they are made without it.
  Predicted effect (not verified): fruity flavour; fine for savoury dishes

- Line: '1 cup heavy cream'
  Role (general knowledge): fat, richness and body; thickens sauces when reduced
  Local evidence pool: 1500 most similar recipes (902 without it, 598 with it)
    > olive oil + reserved pasta water: supported - in 334 similar recipes without it (37%) vs 21% of those with it; e.g. ar:ssvvt2OLwZOBX5VNQ/FgJmQgeNG1BmS, fn:X.DRpucWfUzQ14AOBAyfAbhwaGUqhAm, ar:L7A8jrXlCUnKxvPVHb/ZX0jVyjiSjNa, fn:W/avyZ.harLyYn5tRT.2YGmKcsHNjCG, ar:NUpdmG6kbXVfFSZ63ZSVrXRp6hYA2rG ...
      direct (title says made without it): fn:TJ408r4TI1kRXjTXg7E36YS1jxY2bwm, epi:SX4WUn7soISKA9E..uPhdLIJ6L/J4Fy, ar:sb1Unxe/KM1D3BbqKHz27h8tfgRVPUa
      cashews blended with water: supported - in 3 similar recipes without it (0%) vs 0% of those with it; e.g. ar:sb1Unxe/KM1D3BbqKHz27h8tfgRVPUa, ar:rHSxuLLRxICFxPNYxu13eoAtzie2XwS, ar:kiV/KLgx4O6YJ8mDQib/US/wSDTsDES
      direct (title says made without it): ar:sb1Unxe/KM1D3BbqKHz27h8tfgRVPUa
      vegetable broth: conflicting - in 5 similar recipes without it (1%) vs 1% of those with it; e.g. epi:SX4WUn7soISKA9E..uPhdLIJ6L/J4Fy, ar:HE8HQHpsPQB56MY8XzULLh7ZRyTMYKS, ar:sb1Unxe/KM1D3BbqKHz27h8tfgRVPUa, epi:hUzLHvpSiD.xwKjWzCWAA2yw/CxplL6, ar:uYarG1kkCD25wTkhatMGAFYRCR.XMLe
      direct (title says made without it): epi:SX4WUn7soISKA9E..uPhdLIJ6L/J4Fy, ar:sb1Unxe/KM1D3BbqKHz27h8tfgRVPUa
      coconut milk: conflicting - in 1 similar recipes without it (0%) vs 0% of those with it; e.g. fn:8aDT41R8AXAqRbt6e.bGfZFW6VuRZE.
  Includes direct evidence: similar recipes whose titles say they are made without it.
  Predicted effect (not verified): much lighter, glossy rather than creamy

- Line: '1 1/2 cups freshly grated Parmesan cheese'
  Role (general knowledge): salty, savoury flavour; melting/binding when heated
  Local evidence pool: 1500 most similar recipes (655 without it, 845 with it)
    > nutritional yeast: supported - in 4 similar recipes without it (1%) vs 0% of those with it; e.g. ar:I5nEPw6EqeC.oyqhvHmASSU2bX/KGIe, fn:TJ408r4TI1kRXjTXg7E36YS1jxY2bwm, ar:0NlVwTqCT.E/2N3jybL9ayKVpIDhIzq, ar:sb1Unxe/KM1D3BbqKHz27h8tfgRVPUa
      direct (title says made without it): ar:I5nEPw6EqeC.oyqhvHmASSU2bX/KGIe, fn:TJ408r4TI1kRXjTXg7E36YS1jxY2bwm, ar:0NlVwTqCT.E/2N3jybL9ayKVpIDhIzq, ar:sb1Unxe/KM1D3BbqKHz27h8tfgRVPUa
      toasted breadcrumbs: conflicting - in 3 similar recipes without it (0%) vs 4% of those with it; e.g. epi:c7/fDVsMKkvJGa9z/b1A2wKfrYtoZo6, fn:fpEjRD8ZgUE10j6EooQAvBaN9EahWjS, fn:X2Z0sArdjOFaTlKS59IT/oUxhaXiOM.
  Includes direct evidence: similar recipes whose titles say they are made without it.
  Predicted effect (not verified): savoury, cheesy-ish flavour; does not melt

Updated ingredients:
  - olive oil - 3/4 the amount of butter   [replaces: 1/4 cup butter]
  - olive oil + reserved pasta water - 2 tbsp oil + 1/2 cup pasta water per cup   [replaces: 1 cup heavy cream]
  - 1 clove garlic, crushed
  - nutritional yeast - about 1/2 the amount   [replaces: 1 1/2 cups freshly grated Parmesan cheese]
  - 1/4 cup chopped fresh parsley

Revised instructions:
  1. [changed] Melt olive oil in a medium saucepan over medium low heat. Add olive oil + reserved pasta water and simmer for 5 minutes, then add garlic and nutritional yeast and whisk quickly, heating through. Stir in parsley and serve.
... (3 more lines)
```
_0.2s_ | parse diffs: ["remove: expected 'cream', got 'heavy cream'"]
- PASS `restriction_respected`: silent violations: none; unresolved lines flagged: True
- PASS `evidence_labelled`: uncertainty labels present: ['conflicting']

## T3 weak / unsupported substitution

**User:** Remove the saffron from a saffron paella

```
Using 'Shrimp Paella' (ar:ln0kBgBPb0fDxHp6mpgsyULU.agdyvq) as the recipe. Give an ID to use a different one.
Adapting: Shrimp Paella  [ar:ln0kBgBPb0fDxHp6mpgsyULU.agdyvq]
Change requested: remove saffron; restrictions: none

- Line: '4 saffron threads'
  No substitute candidates are known for this ingredient, so no adaptation is proposed.

I can't support a reliable adaptation from the local data, so I'm not giving one.
```
_0.1s_
- PASS `evidence_labelled`: uncertainty labels present: ["can't support", 'No substitute candidates']

## Unsupported attribute

**User:** Find a banana bread recipe

```
Search: 'banana bread' | filters: no filters
12200 of 12200 text matches pass the filters. Top 5:

1. Banana Bread  [ar:BoBTO3QUO3Ci.0kayPs8.CfDU5oEXuu]  (relevance 0.61, 7 ingredients, 3 steps)

2. Banana Banana Bread  [ar:kq.naD.8G19M4UU9dVvJgHtpfo.l/eC]  (relevance 0.55, 7 ingredients, 3 steps)

3. Country Banana Bread  [ar:LCKlIJX8Jjf51FQPJqTQGydT1/m4zRi]  (relevance 0.54, 4 ingredients, 3 steps)

4. 4H Banana Bread  [ar:DcIUE5ijDjaMmoh59TJiyafZCvChIji]  (relevance 0.54, 10 ingredients, 3 steps)

5. Banana Bread  [fn:J9d89klHetj.4b5OKiASicRh8tfXK6m]  (relevance 0.52, 10 ingredients, 2 steps)

Say 'show #N' for full ingredients and instructions.
```
_0.0s_
- PASS `has_results`: 5 results

**User:** How many calories are in the first one?

```
The dataset doesn't contain calories. Each recipe only has a title, ingredient lines and instruction text - no nutrition, timing, rating or price fields - so I won't estimate it.
```
_0.0s_
- PASS `says_missing`: states the field is missing, no estimate

**User:** What's its total cooking time?

```
The dataset doesn't contain cooking time. Each recipe only has a title, ingredient lines and instruction text - no nutrition, timing, rating or price fields - so I won't estimate it.

What the instructions of 'Banana Bread' say, as written (not a total time):
  - Bake at 350 degrees F (175 degrees C) for 1 hour, or until a wooden toothpick inserted in the center comes out clean.
```
_0.0s_
- PASS `says_missing`: states the field is missing, no estimate
