import argparse
import logging
import os
from typing import List, Tuple, Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, udf, countDistinct
from pyspark.sql.types import FloatType, StringType
import json

# Try to import evaluation helpers from voiceops.eval, else define minimal versions
try:
    from voiceops.eval.lexical import wer, cer
    from voiceops.eval.domain import keyword_accuracy, numeric_accuracy, negation_accuracy
except ImportError:
    # Minimal fallback implementations
    def wer(ref: str, hyp: str) -> float:
        r, h = ref.split(), hyp.split()
        d = [[0] * (len(h)+1) for _ in range(len(r)+1)]
        for i in range(len(r)+1): d[i][0] = i
        for j in range(len(h)+1): d[0][j] = j
        for i in range(1, len(r)+1):
            for j in range(1, len(h)+1):
                d[i][j] = min(
                    d[i-1][j] + 1,
                    d[i][j-1] + 1,
                    d[i-1][j-1] + (r[i-1] != h[j-1])
                )
        return d[-1][-1] / max(1, len(r))
    def cer(ref: str, hyp: str) -> float:
        r, h = list(ref), list(hyp)
        d = [[0] * (len(h)+1) for _ in range(len(r)+1)]
        for i in range(len(r)+1): d[i][0] = i
        for j in range(len(h)+1): d[0][j] = j
        for i in range(1, len(r)+1):
            for j in range(1, len(h)+1):
                d[i][j] = min(
                    d[i-1][j] + 1,
                    d[i][j-1] + 1,
                    d[i-1][j-1] + (r[i-1] != h[j-1])
                )
        return d[-1][-1] / max(1, len(r))
    def keyword_accuracy(ref: str, hyp: str) -> float:
        ref_set = set(ref.split())
        hyp_set = set(hyp.split())
        return len(ref_set & hyp_set) / max(1, len(ref_set))
    def numeric_accuracy(ref: str, hyp: str) -> float:
        import re
        ref_nums = set(re.findall(r"\\d+", ref))
        hyp_nums = set(re.findall(r"\\d+", hyp))
        return len(ref_nums & hyp_nums) / max(1, len(ref_nums))
    def negation_accuracy(ref: str, hyp: str) -> float:
        return int(("no " in ref) == ("no " in hyp))

def get_logger() -> logging.Logger:
    logger = logging.getLogger("spark_eval")
    if not logger.hasHandlers():
        logging.basicConfig(level=logging.INFO)
    return logger

def read_input(spark: SparkSession, input_path: str) -> DataFrame:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    ext = os.path.splitext(input_path)[-1].lower()
    if ext == ".csv":
        df = spark.read.option("header", True).csv(input_path)
    elif ext == ".json":
        df = spark.read.json(input_path)
    else:
        raise ValueError(f"Unsupported input file type: {ext}")
    return df

def validate_columns(df: DataFrame, required: List[str]):
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

def main():
    parser = argparse.ArgumentParser(description="Spark batch evaluation for VoiceOps transcripts.")
    parser.add_argument("--input", required=True, help="Input CSV or JSON file with predictions and references.")
    parser.add_argument("--output-dir", required=True, help="Directory to write output reports.")
    args = parser.parse_args()

    logger = get_logger()
    spark = SparkSession.builder.appName("VoiceOpsSparkEval").getOrCreate()

    try:
        df = read_input(spark, args.input)
    except Exception as e:
        logger.error(f"Failed to read input: {e}")
        return

    required_cols = ["sample_id", "condition", "reference_text", "predicted_text", "baseline_name"]
    try:
        validate_columns(df, required_cols)
    except Exception as e:
        logger.error(str(e))
        return

    if df.count() == 0:
        logger.error("Input dataset is empty.")
        return

    logger.info(f"Loaded {df.count()} rows from {args.input}")
    baselines = [row[0] for row in df.select("baseline_name").distinct().collect()]
    conditions = [row[0] for row in df.select("condition").distinct().collect()]
    logger.info(f"Baselines found: {baselines}")
    logger.info(f"Conditions found: {conditions}")

    # Register UDFs
    spark.udf.register("wer", wer, FloatType())
    spark.udf.register("cer", cer, FloatType())
    spark.udf.register("keyword_accuracy", keyword_accuracy, FloatType())
    spark.udf.register("numeric_accuracy", numeric_accuracy, FloatType())
    spark.udf.register("negation_accuracy", negation_accuracy, FloatType())

    df_eval = df.withColumn("WER", udf(wer, FloatType())(col("reference_text"), col("predicted_text"))) \
               .withColumn("CER", udf(cer, FloatType())(col("reference_text"), col("predicted_text"))) \
               .withColumn("KeywordAcc", udf(keyword_accuracy, FloatType())(col("reference_text"), col("predicted_text"))) \
               .withColumn("NumericAcc", udf(numeric_accuracy, FloatType())(col("reference_text"), col("predicted_text"))) \
               .withColumn("NegationAcc", udf(negation_accuracy, FloatType())(col("reference_text"), col("predicted_text")))

    # Grouped summary
    summary = df_eval.groupBy("baseline_name", "condition").agg(
        {"WER": "avg", "CER": "avg", "KeywordAcc": "avg", "NumericAcc": "avg", "NegationAcc": "avg", "sample_id": "count"}
    ).withColumnRenamed("avg(WER)", "WER") \
     .withColumnRenamed("avg(CER)", "CER") \
     .withColumnRenamed("avg(KeywordAcc)", "KeywordAcc") \
     .withColumnRenamed("avg(NumericAcc)", "NumericAcc") \
     .withColumnRenamed("avg(NegationAcc)", "NegationAcc") \
     .withColumnRenamed("count(sample_id)", "NumSamples")

    os.makedirs(args.output_dir, exist_ok=True)
    summary_path = os.path.join(args.output_dir, "spark_eval_report.csv")
    error_path = os.path.join(args.output_dir, "error_patterns.csv")

    summary.coalesce(1).write.option("header", True).csv(summary_path, mode="overwrite")
    logger.info(f"Wrote summary report to {summary_path}")

    # Error pattern mining: output rows with high WER or CER
    error_df = df_eval.filter((col("WER") > 0.3) | (col("CER") > 0.3))
    error_df.coalesce(1).write.option("header", True).csv(error_path, mode="overwrite")
    logger.info(f"Wrote error patterns to {error_path}")

    spark.stop()

if __name__ == "__main__":
    main()
