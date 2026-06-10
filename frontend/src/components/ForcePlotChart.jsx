import React, { useMemo } from "react";

/**
 * ForcePlotChart — SHAP force plot visualisation.
 *
 * Props:
 *   data: ForcePlotData {
 *     base_value: number,
 *     output_value: number,
 *     positive_features: ForceFeatureItem[],   // push toward higher risk (red)
 *     negative_features: ForceFeatureItem[],   // push toward lower risk (blue)
 *     features: ForceFeatureItem[],
 *   }
 */

const LABEL_MAP = {
  upi_txn_count_6m: "UPI Volume",
  upi_consistency_score: "UPI Consistency",
  upi_merchant_diversity: "Merchant Diversity",
  upi_failed_rate: "UPI Fail Rate",
  upi_avg_txn_value: "Avg Txn Value",
  upi_night_txn_share: "Night Txns",
  upi_income_regularity: "Income Regularity",
  utility_streak_length: "Utility Streak",
  utility_days_before_due_avg: "Utility Payment Timing",
  utility_lapse_count_12m: "Utility Lapses",
  utility_reinstatement_count: "Utility Reinstatements",
  mobile_plan_tier: "Mobile Plan Tier",
  mobile_recharge_streak: "Recharge Streak",
  mobile_plan_trend: "Plan Trend",
  mobile_lapse_count: "Mobile Lapses",
  gst_filing_regularity: "GST Regularity",
  gst_turnover_trend: "Turnover Trend",
  gst_penalty_count: "GST Penalties",
  "Other features": "Other features",
};

function featureLabel(name) {
  return LABEL_MAP[name] || name.replace(/_/g, " ");
}

function formatVal(v) {
  if (v === null || v === undefined) return "";
  if (typeof v === "boolean") return v ? "Yes" : "No";
  if (typeof v === "number") return Number.isInteger(v) ? v : v.toFixed(3);
  return String(v);
}

export default function ForcePlotChart({ data }) {
  if (!data) {
    return (
      <div className="force-plot-empty">
        Force plot data unavailable for this applicant.
      </div>
    );
  }

  const { base_value, output_value, positive_features, negative_features } = data;

  // Total absolute SHAP mass for scaling bar widths
  const allFeatures = [...positive_features, ...negative_features];
  const totalMass = useMemo(
    () => allFeatures.reduce((sum, f) => sum + Math.abs(f.shap_value), 0),
    [allFeatures]
  );

  // Width of each bar as % of the chart width (min 4% so tiny bars stay visible)
  const barWidth = (f) =>
    Math.max(4, (Math.abs(f.shap_value) / (totalMass || 1)) * 100);

  return (
    <div className="force-plot-container">
      {/* Header */}
      <div className="force-plot-header">
        <span className="force-plot-label">Force Plot</span>
        <span className="force-plot-subtitle">
          How each feature pushed this applicant's score away from the average
        </span>
      </div>

      {/* Score bar */}
      <div className="force-plot-score-row">
        <div className="force-plot-score-item">
          <span className="force-plot-score-title">Base value</span>
          <span className="force-plot-score-value neutral">
            {base_value.toFixed(3)}
          </span>
        </div>
        <div className="force-plot-arrow">→</div>
        <div className="force-plot-score-item">
          <span className="force-plot-score-title">Model output</span>
          <span
            className={`force-plot-score-value ${
              output_value > base_value ? "risk-higher" : "risk-lower"
            }`}
          >
            {output_value.toFixed(3)}
          </span>
        </div>
      </div>

      {/* Bar chart area */}
      <div className="force-plot-bars-wrapper">
        {/* Negative (blue) bars — push LEFT (lower risk) */}
        <div className="force-plot-col negative-col">
          <div className="force-plot-col-label negative-label">
            ← Lower risk
          </div>
          <div className="force-plot-bars negative-bars">
            {[...negative_features]
              .sort((a, b) => a.shap_value - b.shap_value)
              .map((f, i) => (
                <div key={i} className="force-bar-row">
                  <div
                    className="force-bar negative-bar"
                    style={{ width: `${barWidth(f)}%` }}
                    title={`SHAP: ${f.shap_value.toFixed(4)}, value: ${formatVal(f.feature_value)}`}
                  />
                  <span className="force-bar-label">
                    {featureLabel(f.name)}
                    {f.feature_value !== null && f.feature_value !== undefined
                      ? ` = ${formatVal(f.feature_value)}`
                      : ""}
                  </span>
                </div>
              ))}
          </div>
        </div>

        {/* Centre baseline */}
        <div className="force-plot-baseline" />

        {/* Positive (red) bars — push RIGHT (higher risk) */}
        <div className="force-plot-col positive-col">
          <div className="force-plot-col-label positive-label">
            Higher risk →
          </div>
          <div className="force-plot-bars positive-bars">
            {[...positive_features]
              .sort((a, b) => b.shap_value - a.shap_value)
              .map((f, i) => (
                <div key={i} className="force-bar-row">
                  <div
                    className="force-bar positive-bar"
                    style={{ width: `${barWidth(f)}%` }}
                    title={`SHAP: +${f.shap_value.toFixed(4)}, value: ${formatVal(f.feature_value)}`}
                  />
                  <span className="force-bar-label">
                    {featureLabel(f.name)}
                    {f.feature_value !== null && f.feature_value !== undefined
                      ? ` = ${formatVal(f.feature_value)}`
                      : ""}
                  </span>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="force-plot-legend">
        <span className="legend-dot negative-dot" /> Lower risk contributors
        <span className="legend-dot positive-dot" style={{ marginLeft: "1.5rem" }} /> Higher risk contributors
      </div>
    </div>
  );
}
