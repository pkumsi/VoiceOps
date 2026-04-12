# VoiceOps-HealthBench Failure Taxonomy v0.1

## Overview

This taxonomy defines the primary failure modes targeted by VoiceOps-HealthBench, a benchmark for evaluating speech-to-text robustness on healthcare telephony audio.

The benchmark focuses on failure modes that are:
- common in degraded 8kHz telephony conditions,
- safety-relevant in healthcare communication,
- measurable beyond standard WER alone.

---

## F1. Domain Term Substitution

### Definition
A healthcare-specific term, especially a medication name, is replaced by a phonetically plausible but clinically incorrect word or phrase.

### Why it happens
General-purpose STT systems are often weak on rare or specialized medical vocabulary, especially under telephony degradation or accented pronunciation.

### Examples
- lisinopril -> listen april
- hydroxyzine -> hydro design
- amlodipine -> am low dipping

### Why it matters
Medication mistranscription can alter clinical meaning and cause downstream extraction failures.

### Evaluation focus
- domain keyword accuracy
- safety-critical error rate

---

## F2. Numeric Instability

### Definition
A dosage, quantity, or timing-related number is mistranscribed.

### Why it happens
Number words are acoustically similar under low-fidelity audio and noisy environments.

### Examples
- fifteen -> fifty
- ten milligrams -> two milligrams
- twenty five -> seventy five

### Why it matters
Dose errors are clinically dangerous even when the rest of the transcript is correct.

### Evaluation focus
- numeric accuracy
- safety-critical error rate

---

## F3. Negation Loss

### Definition
A negation marker is omitted, altered, or inverted, changing the clinical meaning of the statement.

### Why it happens
Short function words such as no, not, or denies are vulnerable to deletion in noise and conversational speech.

### Examples
- no insulin -> insulin
- denies dizziness -> dizziness
- no fever -> fever

### Why it matters
Negation errors can reverse patient status and create unsafe summaries or interventions.

### Evaluation focus
- negation preservation accuracy
- safety-critical error rate

---

## F4. Accent-Induced Misrecognition

### Definition
Accent variation in English leads to consistent or repeated misrecognition of words, especially domain-specific and low-frequency terms.

### Why it happens
The STT model may be underexposed to certain accent patterns, and telephony degradation worsens recognition.

### Examples
- accented pronunciation of medication names becoming unrelated terms
- repeated confusion on dosage phrases under accented English

### Why it matters
Healthcare systems must generalize across speaker populations rather than overfit to one accent profile.

### Evaluation focus
- subgroup accuracy by accent
- domain keyword accuracy by accent
- safety-critical error rate by accent

---

## Notes on Annotation

Each benchmark sample should include:
- one primary failure mode
- optional secondary failure mode
- target keywords
- target numerics
- target negations
- risk flag for safety-critical interpretation

This structure supports:
- per-failure-mode evaluation
- correction ablations
- future benchmark expansion