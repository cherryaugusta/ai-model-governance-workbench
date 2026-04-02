import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  approveApproval,
  fetchApprovals,
  rejectApproval,
  requestApprovalChanges,
} from "../../api/client";
import type { ApprovalDecision, ApprovalRecord } from "../../schemas/approvals";
import { ErrorState } from "../../components/ErrorState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { StatusBadge } from "../../components/StatusBadge";

const decisionOptions: Array<{
  label: string;
  value: "all" | ApprovalDecision;
}> = [
  { label: "All decisions", value: "all" },
  { label: "Pending", value: "pending" },
  { label: "Approved", value: "approved" },
  { label: "Rejected", value: "rejected" },
  { label: "Changes requested", value: "changes_requested" },
];

const approvalTypeOptions = [
  { label: "All approval types", value: "all" },
  { label: "Technical", value: "technical" },
  { label: "Product", value: "product" },
  { label: "Risk", value: "risk" },
  { label: "Governance", value: "governance" },
] as const;

function formatApprovalType(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "Not decided";
  }

  return new Date(value).toLocaleString();
}

function ApprovalActions({
  record,
  onActionComplete,
}: {
  record: ApprovalRecord;
  onActionComplete: () => void;
}) {
  const [comment, setComment] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async ({
      action,
      approvalId,
      payload,
    }: {
      action: "approve" | "reject" | "request_changes";
      approvalId: number;
      payload: { comment: string };
    }) => {
      if (action === "approve") {
        return approveApproval(approvalId, payload);
      }

      if (action === "reject") {
        return rejectApproval(approvalId, payload);
      }

      return requestApprovalChanges(approvalId, payload);
    },
    onSuccess: async () => {
      setErrorMessage("");
      setComment("");
      await queryClient.invalidateQueries({ queryKey: ["approvals"] });
      onActionComplete();
    },
    onError: () => {
      setErrorMessage(
        "Approval action failed. Check the backend terminal and the browser network response.",
      );
    },
  });

  const isPending = record.decision === "pending";
  const isWorking = mutation.isPending;

  return (
    <div className="panel" style={{ marginTop: "1rem" }}>
      <div className="field-grid">
        <label className="field">
          <span>Review comment</span>
          <textarea
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            rows={3}
            placeholder="Add review context for this decision"
            disabled={!isPending || isWorking}
          />
        </label>
      </div>
      {errorMessage ? <ErrorState message={errorMessage} /> : null}
      <div className="button-row">
        <button
          type="button"
          onClick={() =>
            mutation.mutate({
              action: "approve",
              approvalId: record.id,
              payload: { comment },
            })
          }
          disabled={!isPending || isWorking}
        >
          Approve
        </button>
        <button
          type="button"
          onClick={() =>
            mutation.mutate({
              action: "reject",
              approvalId: record.id,
              payload: { comment },
            })
          }
          disabled={!isPending || isWorking}
        >
          Reject
        </button>
        <button
          type="button"
          onClick={() =>
            mutation.mutate({
              action: "request_changes",
              approvalId: record.id,
              payload: { comment },
            })
          }
          disabled={!isPending || isWorking}
        >
          Request changes
        </button>
      </div>
    </div>
  );
}

export function ApprovalQueuePage() {
  const [decisionFilter, setDecisionFilter] =
    useState<"all" | ApprovalDecision>("pending");
  const [approvalTypeFilter, setApprovalTypeFilter] = useState<
    "all" | "technical" | "product" | "risk" | "governance"
  >("all");
  const [activeRecordId, setActiveRecordId] = useState<number | null>(null);

  const query = useQuery({
    queryKey: ["approvals", decisionFilter, approvalTypeFilter],
    queryFn: () =>
      fetchApprovals({
        decision: decisionFilter === "all" ? undefined : decisionFilter,
        approval_type:
          approvalTypeFilter === "all" ? undefined : approvalTypeFilter,
      }),
  });

  const approvals = query.data ?? [];

  const summary = useMemo(() => {
    return approvals.reduce(
      (accumulator, record) => {
        accumulator.total += 1;

        if (record.decision === "pending") {
          accumulator.pending += 1;
        }

        if (record.decision === "approved") {
          accumulator.approved += 1;
        }

        if (record.decision === "rejected") {
          accumulator.rejected += 1;
        }

        if (record.decision === "changes_requested") {
          accumulator.changesRequested += 1;
        }

        return accumulator;
      },
      {
        total: 0,
        pending: 0,
        approved: 0,
        rejected: 0,
        changesRequested: 0,
      },
    );
  }, [approvals]);

  if (query.isLoading) {
    return <LoadingSpinner label="Loading approval queue" />;
  }

  if (query.isError) {
    return (
      <ErrorState message="Approval queue could not be loaded. Check the backend terminal and verify the approvals API is reachable." />
    );
  }

  return (
    <section className="page-section">
      <div className="page-header">
        <p className="eyebrow">Approvals</p>
        <h2>Risk-tier approval queue</h2>
        <p>
          Review release candidate approvals driven by system risk tier. This
          queue supports approve, reject, and request changes actions against
          governed release candidates.
        </p>
      </div>

      <div className="stats-grid">
        <div className="panel">
          <p className="eyebrow">Total records</p>
          <h3>{summary.total}</h3>
        </div>
        <div className="panel">
          <p className="eyebrow">Pending</p>
          <h3>{summary.pending}</h3>
        </div>
        <div className="panel">
          <p className="eyebrow">Approved</p>
          <h3>{summary.approved}</h3>
        </div>
        <div className="panel">
          <p className="eyebrow">Rejected</p>
          <h3>{summary.rejected}</h3>
        </div>
        <div className="panel">
          <p className="eyebrow">Changes requested</p>
          <h3>{summary.changesRequested}</h3>
        </div>
      </div>

      <div className="panel">
        <div className="field-grid">
          <label className="field">
            <span>Decision</span>
            <select
              value={decisionFilter}
              onChange={(event) =>
                setDecisionFilter(event.target.value as "all" | ApprovalDecision)
              }
            >
              {decisionOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Approval type</span>
            <select
              value={approvalTypeFilter}
              onChange={(event) =>
                setApprovalTypeFilter(
                  event.target.value as
                    | "all"
                    | "technical"
                    | "product"
                    | "risk"
                    | "governance",
                )
              }
            >
              {approvalTypeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {approvals.length === 0 ? (
        <div className="panel">
          <p>No approval records match the current filters.</p>
        </div>
      ) : (
        <div className="stack-lg">
          {approvals.map((record) => {
            const isExpanded = activeRecordId === record.id;

            return (
              <article key={record.id} className="panel">
                <div className="page-header" style={{ marginBottom: "1rem" }}>
                  <p className="eyebrow">Release candidate</p>
                  <h3>{record.release_candidate_name}</h3>
                </div>

                <div className="detail-grid">
                  <div>
                    <strong>Approval type</strong>
                    <p>{formatApprovalType(record.approval_type)}</p>
                  </div>
                  <div>
                    <strong>Decision</strong>
                    <p>
                      <StatusBadge value={record.decision} />
                    </p>
                  </div>
                  <div>
                    <strong>Reviewer</strong>
                    <p>{record.reviewer_username ?? "Unassigned"}</p>
                  </div>
                  <div>
                    <strong>Decided at</strong>
                    <p>{formatDateTime(record.decided_at)}</p>
                  </div>
                </div>

                <div style={{ marginTop: "1rem" }}>
                  <strong>Comment</strong>
                  <p>{record.comment || "No review comment recorded."}</p>
                </div>

                <div className="button-row" style={{ marginTop: "1rem" }}>
                  <button
                    type="button"
                    onClick={() =>
                      setActiveRecordId(isExpanded ? null : record.id)
                    }
                  >
                    {isExpanded ? "Hide actions" : "Review actions"}
                  </button>
                </div>

                {isExpanded ? (
                  <ApprovalActions
                    record={record}
                    onActionComplete={() => setActiveRecordId(null)}
                  />
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}