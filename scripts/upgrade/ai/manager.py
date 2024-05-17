class AIManager:
    def rate(self, term, definition):
        resp = ""
        score = self.extract_score(resp)
        culture = self.extract_culture(resp)
        return [False, score, culture]

    def extract_score(self, str):
        pass

    def extract_culture(self, str):
        pass
