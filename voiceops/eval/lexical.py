from jiwer import wer, cer


def compute_wer(reference, hypothesis):
    return wer(reference, hypothesis)


def compute_cer(reference, hypothesis):
    return cer(reference, hypothesis)