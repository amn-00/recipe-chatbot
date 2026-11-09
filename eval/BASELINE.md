# One-shot LLM baseline vs grounded system

Model: `openai/gpt-oss-120b`

## How many recipes contain both garlic and onion, and what percentage of the dataset is that? Give numbers.

**One-shot LLM:**

```
**Quick answer (based on a typical run of the “Recipe Box” data set)**  

| Metric | Value |
|--------|-------|
| Total recipes in the data set | **≈ 124 800** (the official count is 124 815) |
| Recipes that mention **both “garlic” and “onion”** in the ingredient list | **≈ 31 900** |
| Percentage of the whole data set | **≈ 25.6 %** |

> **Bottom line:** Roughly **one‑quarter of all recipes** in the Recipe Box collection contain both garlic *and* onion.

---

## How the numbers are obtained  

Below is a short, self‑contained Python / pandas script that reproduces the counts.  
If you run it on the original `recipes.csv` (or the JSON version) you’ll get the exact same numbers (the tiny differences you might see are only due to rounding or minor preprocessing choices).

```python
import pandas as pd
import re

# -------------------------------------------------
# 1️⃣ Load the data
# -------------------------------------------------
# The official file is a CSV with one row per recipe.
# It contains at least the columns:  'id', 'title', 'ingredients', 'instructions'
df = pd.read_csv('recipe_box.csv')          # adjust the path as needed

# -------------------------------------------------
# 2️⃣ Normalise the ingredient text
# -------------------------------------------------
# The ingredient column is a single string with ingredients separated by ';' (or '|')
# We lower‑case everything and strip punctuation so that “Garlic”, “garlic,” and “garlic powder”
# are all caught.
def
```
**System (computed):** 16552 recipes = 13.46% of 122937

IDs cited by the LLM: 0, of which exist in the data: 0

## Among recipes containing tomato, list the five with the fewest instruction steps, with their recipe IDs and step counts.

**One-shot LLM:**

```
I’m not able to look inside the **Recipe Box** collection directly, so I can’t give you the exact recipe IDs and step counts right now. However, I can show you a straightforward way to pull that information yourself if you have the dataset (or a copy of it) on hand.

Below is a complete, ready‑to‑run Python script that:

1. **Loads** the JSON/CSV files that make up the Recipe Box dataset.  
2. **Filters** for recipes whose ingredient list contains the word “tomato” (case‑insensitive).  
3. **Counts** the number of instruction steps for each of those recipes.  
4. **Sorts** the filtered set by step count (ascending) and prints the five recipes with the fewest steps, showing the recipe ID and the step count.

You can drop this into a Jupyter notebook or a plain `.py` file and run it after you’ve placed the dataset files in the same directory (or adjust the paths accordingly).

---

## 📦 What you’ll need

| Tool | Why |
|------|-----|
| **Python 3.8+** | Core language |
| **pandas** | Easy tabular data handling |
| **tqdm** (optional) | Progress bar for large files |
| **json** (built‑in) | Parse JSON if the dataset is in that format |

Install the required packages (if you don’t already have them):

```bash
pip install pandas tqdm
```

---

## 🗂️ Expected dataset layout

The public “Recipe Box” release is usually distributed as a collection of JSON lines (one recipe per line) or as a CSV file. The script below works with either format:

* **JSON‑lines** (`.jsonl`): each line is
```
**System (computed):** ar:..M776r8BHroHcCXw3vInfs25LDkWw2 (Melanie's Chili, 1 steps); ar:.12bcbuKzBtUwvUDLz4SA2iPZctyzei (Skillet Spaghetti Supper, 1 steps); ar:.3oN2HceZh201rfooa/WQeOsq96R/Ku (Paleo Coconut Walnut Squash, 1 steps); ar:.FFTHNuM.1tpgcYtWMhP8wdZBmFtjI. (Everything in the Fridge Pasta Sauce, 1 steps); ar:.Je7yi3D.V.iTOFXtSmH6lIC0YtjK.q (College Student's Saucy Chickpeas, 1 steps)

IDs cited by the LLM: 0, of which exist in the data: 0

## How many calories are in a typical banana bread recipe from this dataset?

**One-shot LLM:**

```
Below is a concise, data‑driven answer that you can use directly or adapt for a deeper dive into the **Recipe Box** collection (≈125 k recipes from Allrecipes, Epicurious, and Food Network).

---

## Quick answer

**A “typical” banana‑bread recipe in the Recipe Box dataset contains roughly 2 300 – 2 800 kcal in the whole loaf, which works out to about 190 – 240 kcal per standard slice (1/12 of the loaf).**  

*The exact number varies with the specific ingredient list (e.g., amount of butter/oil, sugar, nuts, or chocolate chips) and the serving size reported by the author.*

---

## How that number was derived

1. **Identify banana‑bread recipes**  
   ```python
   # Assuming you have a DataFrame `df` with columns:
   #   - 'title' (string)
   #   - 'ingredients' (list of dicts: {'name': str, 'quantity': float, 'unit': str})
   #   - 'servings' (int or float)
   #   - 'nutrition' (optional dict with pre‑computed kcal)
   banana_bread = df[df['title'].str.contains('banana bread', case=False, na=False)]
   ```

2. **Map each ingredient to its caloric density**  
   Use a reliable food‑nutrition lookup (e.g., USDA FoodData Central, Edamam, or the `nutritionix` Python package).  
   ```python
   from nutritionix import Nutritionix
   n = Nutritionix(app_id='YOUR_ID', api_key='YOUR_KEY')

   def kcal_for_ingredient(name, qty, unit):
       # Convert to grams (or ml for liquids) – a simple lookup table can be built
       # Example: 1 cup butter ≈ 227 g, 1 cup sugar ≈ 200 g, 1 banan
```
**System (computed):** Not answerable: the dataset has no nutrition fields (system refuses).

IDs cited by the LLM: 0, of which exist in the data: 0
