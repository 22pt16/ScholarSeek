from typing import Set, Optional, Tuple

class SpellChecker:
    """
    Dynamic Programming based Levenshtein Distance Spell Checker.
    Provides 'Did you mean?' suggestions for query terms.
    """

    def __init__(self, vocabulary: Set[str]):
        self.vocabulary = vocabulary

    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """
        Computes the minimum edit distance (insertions, deletions, substitutions)
        between s1 and s2 using DP matrix.
        """
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],      # Deletion
                        dp[i][j - 1],      # Insertion
                        dp[i - 1][j - 1]   # Substitution
                    )

        return dp[m][n]

    def suggest(self, word: str, max_distance: int = 2) -> Optional[str]:
        """
        Finds the closest matching word in the index vocabulary.
        """
        word_lower = word.lower()
        if word_lower in self.vocabulary:
            return None  # Word is already spelled correctly in index

        best_match = None
        min_dist = float('inf')

        for candidate in self.vocabulary:
            # Quick length check filter optimization
            if abs(len(candidate) - len(word_lower)) > max_distance:
                continue

            dist = self.levenshtein_distance(word_lower, candidate)
            if dist < min_dist and dist <= max_distance:
                min_dist = dist
                best_match = candidate

        return best_match

    def suggest_query(self, query: str) -> Tuple[str, bool]:
        """
        Checks a full multi-word query and suggests corrections if needed.
        Returns (corrected_query_string, was_corrected_flag).
        """
        words = query.split()
        corrected_words = []
        has_correction = False

        for word in words:
            suggestion = self.suggest(word)
            if suggestion:
                corrected_words.append(suggestion)
                has_correction = True
            else:
                corrected_words.append(word)

        return " ".join(corrected_words), has_correction
