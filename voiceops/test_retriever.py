from voiceops.models.retriever.rank_candidates import rank_medical_candidates

print("Testing lisinapril:")
print(rank_medical_candidates("lisinapril"))

print("\nTesting hydroxazine:")
print(rank_medical_candidates("hydroxazine"))