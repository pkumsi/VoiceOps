def domain_keyword_accuracy(reference_keywords, hypothesis_text):
    if not reference_keywords:
        return 1.0

    correct = 0
    hyp = hypothesis_text.lower()

    for kw in reference_keywords:
        if kw.lower() in hyp:
            correct += 1

    return correct / len(reference_keywords)