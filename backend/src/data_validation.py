"""
data_validation.py — Great Expectations data quality checks for CreditBridge.

Validates synthetic applicant profiles before they enter the training pipeline,
catching schema drift, out-of-range values, and null leakage early.

Usage:
    python src/data_validation.py
    python src/data_validation.py --input data/synthetic/profiles.parquet
"""

import argparse
import json
import os
import sys

import pandas as pd


def load_data(input_path: str) -> pd.DataFrame:
    if input_path.endswith(".parquet"):
        return pd.read_parquet(input_path)
    return pd.read_csv(input_path)


def build_expectation_suite(df: pd.DataFrame) -> dict:
    """
    Runs Great Expectations validations on the profiles DataFrame.
    Returns a summary dict: {"passed": bool, "results": [...], "stats": {...}}.
    """
    try:
        import great_expectations as gx
    except ImportError:
        print("[GE] great_expectations not installed. Run: pip install great_expectations")
        sys.exit(1)

    # Create an in-memory GE data context (no filesystem config needed)
    context = gx.get_context(mode="ephemeral")

    # Create a datasource from the pandas DataFrame
    data_source = context.data_sources.add_pandas("synthetic_profiles")
    data_asset = data_source.add_dataframe_asset("profiles")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("full_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    # Build expectation suite
    suite = context.suites.add(
        gx.ExpectationSuite(name="creditbridge_profile_suite")
    )

    # ── Schema & completeness ────────────────────────────────────────────
    EXPECTED_COLS = [
        "applicant_id", "gender", "geography", "income_proxy", "is_msme",
        "default_label",
        "upi_count", "upi_failed_count", "upi_amount",
        "upi_merchant_count", "upi_night_count", "upi_income_deposits",
        "utility_status", "utility_days_late",
        "mobile_recharge_status", "mobile_plan_value",
        "gst_status", "gst_turnover", "gst_penalties",
        "income_shock_job_loss", "income_shock_health",
    ]
    suite.add_expectation(
        gx.expectations.ExpectTableColumnsToMatchSet(
            column_set=EXPECTED_COLS,
            exact_match=False,          # allow extra columns
        )
    )

    # ── Row count ────────────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectTableRowCountToBeBetween(min_value=100, max_value=None)
    )

    # ── applicant_id uniqueness ──────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeUnique(column="applicant_id")
    )

    # ── Gender values ────────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="gender", value_set=["M", "F"]
        )
    )

    # ── Geography values ─────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="geography", value_set=["urban", "semi-urban", "rural"]
        )
    )

    # ── Income proxy values ──────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="income_proxy", value_set=["high", "mid", "low"]
        )
    )

    # ── Target label is binary ───────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="default_label", value_set=[0, 1]
        )
    )

    # ── No nulls on key columns ──────────────────────────────────────────
    for col in ["applicant_id", "gender", "geography", "income_proxy",
                "default_label", "is_msme"]:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(column=col)
        )

    # ── Default rate sanity check (between 2% and 60%) ───────────────────
    default_rate = df["default_label"].mean()
    suite.add_expectation(
        gx.expectations.ExpectColumnMeanToBeBetween(
            column="default_label", min_value=0.02, max_value=0.60
        )
    )

    # ── Boolean shock columns ────────────────────────────────────────────
    for shock_col in ["income_shock_job_loss", "income_shock_health"]:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeInSet(
                column=shock_col, value_set=[True, False, 0, 1]
            )
        )

    # ── Run validation ───────────────────────────────────────────────────
    validation_definition = context.validation_definitions.add(
        gx.ValidationDefinition(
            name="profile_validation",
            data=batch_definition,
            suite=suite,
        )
    )
    results = validation_definition.run(batch_parameters={"dataframe": df})

    # Parse results into a plain summary
    passed_count = sum(1 for r in results.results if r.success)
    failed_count = sum(1 for r in results.results if not r.success)
    overall_pass = results.success

    summary = {
        "passed": overall_pass,
        "stats": {
            "total_checks": len(results.results),
            "passed": passed_count,
            "failed": failed_count,
            "row_count": len(df),
            "default_rate": round(float(default_rate), 4),
        },
        "results": [
            {
                "expectation": str(r.expectation_config.type),
                "column": r.expectation_config.kwargs.get("column", "table"),
                "success": r.success,
                "observed": str(r.result.get("observed_value", "")) if r.result else "",
            }
            for r in results.results
        ],
    }
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Run Great Expectations data quality validation on synthetic profiles."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/synthetic/profiles.parquet",
        help="Path to the profiles file (.parquet or .csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="models/data_validation_report.json",
        help="Path to write the JSON validation report",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[GE] Input file not found: {args.input}")
        print("  Run: python data/synthetic/generate_profiles.py first.")
        sys.exit(1)

    print(f"[GE] Loading profiles from {args.input}...")
    df = load_data(args.input)
    print(f"[GE] Loaded {len(df):,} rows × {len(df.columns)} columns.")

    print("[GE] Running expectation suite...")
    summary = build_expectation_suite(df)

    # Save report
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(summary, f, indent=2)

    # Print result
    print()
    print("=" * 50)
    print(f"  Data Validation {'PASSED ✓' if summary['passed'] else 'FAILED ✗'}")
    print(f"  Checks: {summary['stats']['passed']}/{summary['stats']['total_checks']} passed")
    print(f"  Rows validated: {summary['stats']['row_count']:,}")
    print(f"  Default rate: {summary['stats']['default_rate']:.2%}")
    print(f"  Report saved to: {args.output}")
    print("=" * 50)

    if summary["stats"]["failed"] > 0:
        print("\nFailed checks:")
        for r in summary["results"]:
            if not r["success"]:
                print(f"  ✗ [{r['column']}] {r['expectation']} — observed: {r['observed']}")

    sys.exit(0 if summary["passed"] else 1)


if __name__ == "__main__":
    main()
