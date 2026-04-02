import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchEvalDatasets, fetchEvalRuns } from "../../api/client";
import { ErrorState } from "../../components/ErrorState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { StatusBadge } from "../../components/StatusBadge";

function formatTimestamp(value: string | null) {
  if (!value) {
    return "Not completed";
  }

  return new Date(value).toLocaleString();
}

function asNumber(value: unknown) {
  return typeof value === "number" ? value : null;
}

function formatMetric(value: unknown) {
  if (typeof value !== "number") {
    return "n/a";
  }

  return Number.isInteger(value) ? `${value}` : value.toFixed(4);
}

function latestRunsByDataset(runs: Awaited<ReturnType<typeof fetchEvalRuns>>) {
  const seen = new Map<string, (typeof runs)[number]>();

  for (const run of runs) {
    if (!seen.has(run.eval_dataset_slug)) {
      seen.set(run.eval_dataset_slug, run);
    }
  }

  return Array.from(seen.values());
}

function thresholdFailures(
  thresholdResults: Record<string, unknown>,
): string[] {
  return Object.entries(thresholdResults)
    .filter(([, value]) => {
      if (!value || typeof value !== "object") {
        return false;
      }

      const candidate = value as { passed?: unknown };
      return candidate.passed === false;
    })
    .map(([metricName]) => metricName);
}

export function EvalDashboardPage() {
  const datasetsQuery = useQuery({
    queryKey: ["eval-datasets"],
    queryFn: fetchEvalDatasets,
  });

  const runsQuery = useQuery({
    queryKey: ["eval-runs"],
    queryFn: fetchEvalRuns,
  });

  const latestRuns = useMemo(() => {
    return latestRunsByDataset(runsQuery.data ?? []);
  }, [runsQuery.data]);

  const latestRunSummary = useMemo(() => {
    const runs = latestRuns;

    const passCount = runs.filter((run) => run.status === "passed").length;
    const failCount = runs.filter((run) => run.status === "failed").length;

    const accuracyValues = runs
      .map((run) => asNumber(run.summary_metrics.accuracy))
      .filter((value): value is number => value !== null);

    const latencyValues = runs
      .map((run) => asNumber(run.summary_metrics.p95_latency_ms))
      .filter((value): value is number => value !== null);

    const costValues = runs
      .map((run) => asNumber(run.summary_metrics.mean_cost_estimate))
      .filter((value): value is number => value !== null);

    return {
      passCount,
      failCount,
      meanAccuracy:
        accuracyValues.length > 0
          ? accuracyValues.reduce((sum, value) => sum + value, 0) / accuracyValues.length
          : null,
      meanP95Latency:
        latencyValues.length > 0
          ? latencyValues.reduce((sum, value) => sum + value, 0) / latencyValues.length
          : null,
      meanCost:
        costValues.length > 0
          ? costValues.reduce((sum, value) => sum + value, 0) / costValues.length
          : null,
    };
  }, [latestRuns]);

  if (datasetsQuery.isLoading || runsQuery.isLoading) {
    return <LoadingSpinner label="Loading evaluation dashboard..." />;
  }

  if (datasetsQuery.isError) {
    return <ErrorState message="Eval datasets could not be loaded from the backend API." />;
  }

  if (runsQuery.isError) {
    return <ErrorState message="Eval runs could not be loaded from the backend API." />;
  }

  const datasets = datasetsQuery.data ?? [];
  const runs = runsQuery.data ?? [];

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">Evals</p>
          <h2>Evaluation dashboard</h2>
          <p className="muted">
            Deterministic release-gate results for governed AI change management.
          </p>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">Active eval datasets</span>
          <strong className="stat-value">{datasets.filter((dataset) => dataset.is_active).length}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">Latest passing suites</span>
          <strong className="stat-value">{latestRunSummary.passCount}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">Latest failing suites</span>
          <strong className="stat-value">{latestRunSummary.failCount}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">Recorded eval runs</span>
          <strong className="stat-value">{runs.length}</strong>
        </div>
      </div>

      <div className="summary-grid">
        <div className="panel">
          <h3>Current release-gate posture</h3>
          <div className="stats-grid">
            <div className="stat-card compact">
              <span className="stat-label">Mean accuracy</span>
              <strong className="stat-value">
                {latestRunSummary.meanAccuracy === null
                  ? "n/a"
                  : latestRunSummary.meanAccuracy.toFixed(4)}
              </strong>
            </div>
            <div className="stat-card compact">
              <span className="stat-label">Mean p95 latency</span>
              <strong className="stat-value">
                {latestRunSummary.meanP95Latency === null
                  ? "n/a"
                  : `${latestRunSummary.meanP95Latency.toFixed(0)} ms`}
              </strong>
            </div>
            <div className="stat-card compact">
              <span className="stat-label">Mean cost estimate</span>
              <strong className="stat-value">
                {latestRunSummary.meanCost === null
                  ? "n/a"
                  : latestRunSummary.meanCost.toFixed(4)}
              </strong>
            </div>
            <div className="stat-card compact">
              <span className="stat-label">Threshold basis</span>
              <strong className="stat-value">Static v1</strong>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>Dataset inventory</h3>
          {datasets.length === 0 ? (
            <p className="muted">No eval datasets have been discovered yet.</p>
          ) : (
            <div className="list-stack">
              {datasets.map((dataset) => (
                <div key={dataset.id} className="list-card">
                  <div className="card-header">
                    <div>
                      <strong>{dataset.name}</strong>
                      <div className="table-subtext">
                        {dataset.ai_system_name} | {dataset.slug}
                      </div>
                    </div>
                    <StatusBadge value={dataset.is_active ? "active" : "retired"} />
                  </div>
                  <div className="table-subtext">Scenario type: {dataset.scenario_type}</div>
                  <div className="table-subtext">Cases: {dataset.case_count}</div>
                  <div className="table-subtext">{dataset.description}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="panel">
        <h3>Latest run by dataset</h3>
        {latestRuns.length === 0 ? (
          <p className="muted">No eval runs have been recorded yet.</p>
        ) : (
          <div className="list-stack">
            {latestRuns.map((run) => {
              const failures = thresholdFailures(run.threshold_results);

              return (
                <div key={run.id} className="list-card">
                  <div className="card-header">
                    <div>
                      <strong>{run.eval_dataset_name}</strong>
                      <div className="table-subtext">
                        Candidate {run.release_candidate} | {run.release_candidate_name}
                      </div>
                      <div className="table-subtext">Run label: {run.run_label}</div>
                    </div>
                    <StatusBadge value={run.status} />
                  </div>

                  <div className="stats-grid">
                    <div className="stat-card compact">
                      <span className="stat-label">Accuracy</span>
                      <strong className="stat-value">
                        {formatMetric(run.summary_metrics.accuracy)}
                      </strong>
                    </div>
                    <div className="stat-card compact">
                      <span className="stat-label">Schema valid rate</span>
                      <strong className="stat-value">
                        {formatMetric(run.summary_metrics.schema_valid_rate)}
                      </strong>
                    </div>
                    <div className="stat-card compact">
                      <span className="stat-label">p95 latency</span>
                      <strong className="stat-value">
                        {formatMetric(run.summary_metrics.p95_latency_ms)}
                      </strong>
                    </div>
                    <div className="stat-card compact">
                      <span className="stat-label">Mean cost estimate</span>
                      <strong className="stat-value">
                        {formatMetric(run.summary_metrics.mean_cost_estimate)}
                      </strong>
                    </div>
                  </div>

                  <div className="spacer-sm" />

                  {failures.length === 0 ? (
                    <p className="muted">All configured thresholds passed for this suite.</p>
                  ) : (
                    <div className="list-stack">
                      {failures.map((failure) => (
                        <div key={failure} className="list-card">
                          <StatusBadge value={failure} />
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="spacer-sm" />
                  <div className="table-subtext">
                    Completed: {formatTimestamp(run.completed_at)}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="panel">
        <h3>Recent per-case execution samples</h3>
        {latestRuns.length === 0 ? (
          <p className="muted">Per-case execution logs will appear once eval runs exist.</p>
        ) : (
          <div className="list-stack">
            {latestRuns.flatMap((run) =>
              run.case_results.slice(0, 2).map((caseResult) => (
                <div key={`${run.id}-${caseResult.id}`} className="list-card">
                  <div className="card-header">
                    <div>
                      <strong>{caseResult.case_id}</strong>
                      <div className="table-subtext">
                        {run.eval_dataset_slug} | candidate {run.release_candidate}
                      </div>
                    </div>
                    <StatusBadge value={caseResult.execution_status} />
                  </div>
                  <div className="table-subtext">
                    Expected: {caseResult.expected_label || "n/a"}
                  </div>
                  <div className="table-subtext">
                    Predicted: {caseResult.predicted_label || "n/a"}
                  </div>
                  <div className="table-subtext">
                    Failure reason: {caseResult.failure_reason || "none"}
                  </div>
                  <div className="spacer-sm" />
                  <pre className="code-block">
                    {JSON.stringify(caseResult.metric_log, null, 2)}
                  </pre>
                </div>
              )),
            )}
          </div>
        )}
      </div>
    </section>
  );
}
