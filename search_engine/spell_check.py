import re
import string
from typing import Dict, List, Optional, Set, Tuple


class SpellChecker:
    """Lightweight spelling suggestions over the unstemmed corpus vocabulary."""

    def __init__(self, vocabulary: Set[str]):
        self.vocabulary = vocabulary
        self._vocabulary_size = -1
        self._words_by_length: Dict[int, List[str]] = {}
        self._words_by_first_char: Dict[str, List[str]] = {}

    @staticmethod
    def levenshtein_distance(s1: str, s2: str, max_distance: Optional[int] = None) -> int:
        """Compute edit distance, using a bounded diagonal band when possible."""
        if s1 == s2:
            return 0
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        m, n = len(s1), len(s2)
        if max_distance is not None and m - n > max_distance:
            return max_distance + 1

        previous = list(range(n + 1))
        for i in range(1, m + 1):
            if max_distance is None:
                start, end = 1, n
                sentinel = m + n + 1
            else:
                start = max(1, i - max_distance)
                end = min(n, i + max_distance)
                sentinel = max_distance + 1
            current = [sentinel] * (n + 1)
            current[0] = i
            row_min = current[0] if start == 1 else sentinel
            for j in range(start, end + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                current[j] = min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + cost,
                )
                row_min = min(row_min, current[j])
            if max_distance is not None and row_min > max_distance:
                return max_distance + 1
            previous = current
        return previous[n]

    def _refresh_vocabulary_index(self) -> None:
        # The corpus vocabulary only grows during normal use, so size is a
        # sufficient invalidation signal for this append-only index.
        if len(self.vocabulary) == self._vocabulary_size:
            return
        by_length: Dict[int, List[str]] = {}
        by_first: Dict[str, List[str]] = {}
        for word in self.vocabulary:
            by_length.setdefault(len(word), []).append(word)
            if word:
                by_first.setdefault(word[0], []).append(word)
        self._words_by_length = {length: sorted(words) for length, words in by_length.items()}
        self._words_by_first_char = {first: sorted(words) for first, words in by_first.items()}
        self._vocabulary_size = len(self.vocabulary)

    def prepare(self) -> None:
        """Build the vocabulary buckets during startup instead of on first typo."""
        self._refresh_vocabulary_index()

    def suggest(self, word: str, max_distance: int = 2) -> Optional[str]:
        word_lower = word.lower()
        if not word_lower or word_lower in self.vocabulary:
            return None

        self._refresh_vocabulary_index()
        candidates = []
        for length in range(max(1, len(word_lower) - max_distance), len(word_lower) + max_distance + 1):
            candidates.extend(self._words_by_length.get(length, ()))

        # Prefer candidates with the same first character. This keeps typo
        # suggestions fast on a large vocabulary and covers common typos.
        same_first = [candidate for candidate in candidates if candidate.startswith(word_lower[0])]
        search_pool = same_first if same_first else candidates

        best_match = None
        best_key = (max_distance + 1, 0, 0, "")
        for candidate in search_pool:
            distance = self.levenshtein_distance(word_lower, candidate, max_distance)
            if distance > max_distance:
                continue
            common_prefix = 0
            for left, right in zip(word_lower, candidate):
                if left != right:
                    break
                common_prefix += 1
            common_suffix = 0
            for left, right in zip(word_lower[::-1], candidate[::-1]):
                if left != right:
                    break
                common_suffix += 1
            key = (distance, -common_prefix, -common_suffix, candidate)
            if key < best_key:
                best_key = key
                best_match = candidate
        return best_match

    def suggest_query(
        self,
        query: str,
        tokenizer=None,
        indexed_vocabulary: Optional[Set[str]] = None,
    ) -> Tuple[str, bool]:
        """Suggest corrections only for words absent after index normalization."""
        corrected_words = []
        has_correction = False

        for word in query.split():
            match = re.match(r"^(\W*)([\w]+)(\W*)$", word, flags=re.UNICODE)
            if not match:
                corrected_words.append(word)
                continue

            leading, surface_word, trailing = match.groups()
            normalized = tokenizer.tokenize(surface_word) if tokenizer else [surface_word.lower()]
            if not normalized:
                corrected_words.append(word)
                continue

            # A word such as "learning" is valid if its normalized form
            # exists in the index; don't compare its surface form to stems.
            if indexed_vocabulary is not None and any(token in indexed_vocabulary for token in normalized):
                corrected_words.append(word)
                continue

            suggestion = self.suggest(surface_word)
            if suggestion and suggestion.lower() != surface_word.lower():
                corrected_words.append(f"{leading}{suggestion}{trailing}")
                has_correction = True
            else:
                corrected_words.append(word)

        return " ".join(corrected_words), has_correction
