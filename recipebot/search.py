"""Task 1 retrieval: TF-IDF over title + ingredient names, hard filters on the full corpus.

Why TF-IDF and not embeddings: queries here are dish names and ingredients, which
are lexical. TF-IDF is fast, deterministic, needs no model download, and every
score can be explained. Filters (exclusions, required ingredients, max steps)
are applied to every scored recipe, not to a small top-k, so a restriction can
never be silently lost.
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .constraints import Constraints
from .data import Recipe


def _doc(r: Recipe) -> str:
    # Title counted twice: a match on the dish name matters more than on one ingredient.
    return f"{r.title} {r.title} " + " ".join(r.names)


class SearchIndex:
    def __init__(self, recipes: list[Recipe], min_df: int = 2):
        self.recipes = recipes
        self.by_id = {r.id: r for r in recipes}
        self.pos = {r.id: i for i, r in enumerate(recipes)}
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2),
                                          sublinear_tf=True, min_df=min_df)
        self.matrix = self.vectorizer.fit_transform(_doc(r) for r in recipes)

    def scores(self, text: str) -> np.ndarray:
        q = self.vectorizer.transform([text])
        return (self.matrix @ q.T).toarray().ravel()   # rows are L2-normalised -> cosine

    def search(self, query: str, constraints: Constraints, limit: int = 5):
        """Returns (results, n_candidates, n_eligible). results = [(recipe, score)]."""
        if query:
            s = self.scores(query)
            order = [i for i in np.argsort(-s, kind="stable") if s[i] > 0]
        else:  # ingredient-only search: every recipe is a candidate
            s = np.zeros(len(self.recipes))
            order = range(len(self.recipes))
        results, eligible = [], 0
        for i in order:
            r = self.recipes[i]
            if constraints.ok(r):
                eligible += 1
                if len(results) < limit:
                    results.append((r, float(s[i])))
        return results, len(order), eligible

    def similar(self, recipe: Recipe, top: int = 2000) -> list[tuple[Recipe, float]]:
        s = (self.matrix @ self.matrix[self.pos[recipe.id]].T).toarray().ravel()
        order = np.argsort(-s, kind="stable")[: top + 1]
        return [(self.recipes[i], float(s[i])) for i in order if self.recipes[i].id != recipe.id and s[i] > 0]
