def numeric_accuracy(reference_numbers, hypothesis_text):
    if not reference_numbers:
        return 1.0

    hyp = hypothesis_text.lower()
    correct = 0

    for num in reference_numbers:
        if str(num) in hyp:
            correct += 1

    return correct / len(reference_numbers)


def negation_accuracy(reference_negations, hypothesis_text):
    if not reference_negations:
        return 1.0

    hyp = hypothesis_text.lower()
    correct = 0

    for neg in reference_negations:
        if neg.lower() in hyp:
            correct += 1

    return correct / len(reference_negations)