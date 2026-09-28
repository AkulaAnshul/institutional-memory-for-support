"""Generate a realistic, deterministic support dataset.

The data tells one coherent story so the demo has a payoff:
  1. A CSV-export timeout appears in Jan, spreads, and is "believed fixed in v2.3".
  2. After v2.4 ships the export fails again as a 504 regression, which directly
     contradicts the "fixed" belief stored in memory.
  3. Smaller recurring issues (SSO loop, duplicate billing seats, slow dashboards)
     plus feature-request clusters (dark mode, Slack alerts).

History tickets (Jan–Mar 2026) are seeded into memory. The demo stream
(Apr–May 2026) is replayed live to show the agent learning.
"""
from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

PRODUCT = "Acme Cloud"
HISTORY_END = datetime(2026, 3, 31, 23, 59, 59)

CUSTOMERS = [
    ("c01", "Priya Nair", "Northwind Analytics", "Enterprise", "India", "Snowflake warehouse, 240 seats, SSO via Okta", "Ravi K."),
    ("c02", "Marcus Bell", "Bellwether Retail", "Growth", "United States", "BigQuery, 60 seats", "Dana P."),
    ("c03", "Sofia Rossi", "Rossi Logistics", "Enterprise", "Italy", "Redshift, 180 seats, SSO via Azure AD", "Ravi K."),
    ("c04", "Daniel Osei", "Accra Fintech", "Starter", "Ghana", "Postgres source, 12 seats", "Dana P."),
    ("c05", "Hannah Kim", "Kim & Park Legal", "Growth", "South Korea", "Snowflake, 45 seats, strict data residency", "Mei L."),
    ("c06", "Tomas Novak", "Novak Manufacturing", "Enterprise", "Czechia", "Databricks, 300 seats", "Ravi K."),
    ("c07", "Aisha Rahman", "Rahman Health", "Growth", "UAE", "BigQuery, 80 seats, HIPAA mode", "Mei L."),
    ("c08", "Liam O'Connor", "Shamrock Media", "Starter", "Ireland", "CSV uploads, 8 seats", "Dana P."),
    ("c09", "Chen Wei", "Lantern Commerce", "Enterprise", "Singapore", "Snowflake, 210 seats, SSO via Okta", "Mei L."),
    ("c10", "Fatima Zahra", "Atlas Education", "Growth", "Morocco", "Postgres source, 55 seats", "Dana P."),
    ("c11", "Erik Larsen", "Fjord Shipping", "Enterprise", "Norway", "Databricks, 160 seats", "Ravi K."),
    ("c12", "Grace Mwangi", "Nairobi Agritech", "Starter", "Kenya", "BigQuery, 10 seats", "Dana P."),
    ("c13", "Julien Moreau", "Moreau Fashion", "Growth", "France", "Snowflake, 70 seats, GDPR mode", "Mei L."),
    ("c14", "Isabella Santos", "Santos Energy", "Enterprise", "Brazil", "Redshift, 320 seats, SSO via Azure AD", "Ravi K."),
    ("c15", "Noah Fischer", "Fischer Robotics", "Growth", "Germany", "Databricks, 90 seats", "Mei L."),
]

EXPORTS = ["exports/2026-0{m}-revenue.csv", "monthly-report.csv", "customer-export.csv", "usage-dump.csv"]


def _body(key: str, month: int) -> str:
    if key == "export_timeout":
        f = random.choice(EXPORTS).format(m=month)
        return (
            f"Our finance team has been pulling a large CSV export and it never finishes. "
            f"It has hung for over {random.choice([20, 25, 30, 45])} minutes on {f}. "
            f"Anything above roughly {random.choice([40000, 50000, 60000])} rows just times out. "
            f"We need this before month end."
        )
    if key == "export_504":
        return (
            "Since the weekend every large export now fails almost immediately with "
            "'504 Gateway Timeout'. It used to at least run for a while; now it dies in seconds. "
            "We are blocked on reporting."
        )
    if key == "sso_loop":
        return (
            "After a routine password reset our users get stuck in an SSO redirect loop and "
            "cannot reach the dashboard. Clearing cookies helps for one login, then it loops again."
        )
    if key == "duplicate_seats":
        return (
            "Our latest invoice appears to bill for more seats than we have active. The totals "
            "do not match the admin console. Please check seat counts before we pay."
        )
    if key == "dark_mode":
        return "Several analysts work late and have asked for a dark mode theme. Is this on the roadmap?"
    if key == "slack_alerts":
        return "We would love to route alert notifications into Slack instead of email. Do you support that?"
    if key == "slow_dashboard":
        return "Dashboards with more than about 10 charts take 15-20 seconds to load. It is slowing the team down."
    if key == "api_429":
        return "Our integration suddenly gets HTTP 429 from the Public API though our volume is unchanged. What is the limit?"
    if key == "sync_skip":
        return "Our scheduled sync finished with a green check but a chunk of recent rows is missing. We only noticed by accident."
    if key == "webhook_retry":
        return "Webhooks stopped retrying after our endpoint was briefly down. Events look dropped rather than retried."
    raise KeyError(key)


ARCHETYPES = [
    dict(key="export_timeout", module="Data Export", issue="performance",
         subject="Large CSV export times out",
         resolution="Confirmed timeout above ~50k rows. Workaround: use a scheduled export or narrow the date range. Tracked as ENG-4471; believed fixed in v2.3.",
         versions=["v2.1", "v2.2"], history=6, stream=0),
    dict(key="export_504", module="Data Export", issue="regression",
         subject="Exports now fail with 504 Gateway Timeout",
         resolution="Escalated to on-call as a suspected regression in v2.4. Interim: scheduled exports still succeed.",
         versions=["v2.4"], history=0, stream=6),
    dict(key="sso_loop", module="Authentication", issue="bug",
         subject="SSO redirect loop after password reset",
         resolution="Clearing the Acme session cookie resolves it once; tracked as ENG-4502. Workaround: sign in from a private window.",
         versions=["v2.2", "v2.3", "v2.4"], history=3, stream=2),
    dict(key="duplicate_seats", module="Billing", issue="billing",
         subject="Invoice shows duplicate seat count",
         resolution="Billing corrected the seat count and issued a revised invoice. Monitor next cycle.",
         versions=["v2.2", "v2.3", "v2.4"], history=2, stream=2),
    dict(key="dark_mode", module="Dashboards", issue="feature_request",
         subject="Feature request: dark mode",
         resolution="Logged as a feature request. No workaround.",
         versions=["v2.2", "v2.3", "v2.4"], history=4, stream=3),
    dict(key="slack_alerts", module="Webhooks", issue="feature_request",
         subject="Feature request: Slack alerts",
         resolution="Logged as a feature request; the generic webhook integration is a workaround.",
         versions=["v2.2", "v2.3", "v2.4"], history=3, stream=2),
    dict(key="slow_dashboard", module="Dashboards", issue="performance",
         subject="Slow dashboard load with many charts",
         resolution="Confirmed slow rendering above ~10 charts. Workaround: split into multiple dashboards.",
         versions=["v2.1", "v2.2", "v2.3"], history=3, stream=2),
    dict(key="api_429", module="Public API", issue="how_to",
         subject="Unexpected 429 from the Public API",
         resolution="Documented limit is 120 requests/minute per token. Recommended exponential backoff.",
         versions=["v2.1", "v2.2", "v2.3", "v2.4"], history=2, stream=1),
    dict(key="sync_skip", module="Scheduled Sync", issue="bug",
         subject="Scheduled sync silently skipped rows",
         resolution="Known race in the sync scheduler; fix scheduled. Workaround: re-run the sync manually.",
         versions=["v2.3", "v2.4"], history=1, stream=2),
    dict(key="webhook_retry", module="Webhooks", issue="bug",
         subject="Webhooks do not retry after failures",
         resolution="Retry policy only fires twice; engineering reviewing. Workaround: poll the events API.",
         versions=["v2.3", "v2.4"], history=1, stream=2),
]

# Month per version.
VERSION_MONTH = {"v2.1": 1, "v2.2": 2, "v2.3": 3, "v2.4": 4}


def generate() -> None:
    rng = random.Random(20260529)

    customers = [
        dict(id=cid, name=name, company=company, plan=plan, region=region,
             environment=env, csm=csm)
        for (cid, name, company, plan, region, env, csm) in CUSTOMERS
    ]
    with (DATA / "customers.jsonl").open("w") as fh:
        for c in customers:
            fh.write(json.dumps(c) + "\n")

    history: list[dict] = []
    stream: list[dict] = []
    n = 0
    for arc in ARCHETYPES:
        for version in arc["versions"]:
            month = VERSION_MONTH[version]
            for bucket, weight in (("history", arc["history"]), ("stream", arc["stream"])):
                for _ in range(weight):
                    n += 1
                    cust = rng.choice(CUSTOMERS)
                    cid = cust[0]
                    if bucket == "history":
                        day = rng.randint(1, 27)
                        when = datetime(2026, month, day, rng.randint(8, 18), rng.randint(0, 59))
                        # keep history strictly in Jan-Mar
                        when = min(when, HISTORY_END)
                    else:
                        day = rng.randint(1, 28)
                        when = datetime(2026, month, day, rng.randint(8, 18), rng.randint(0, 59))
                    resolved = rng.random() < 0.75
                    ticket = dict(
                        id=f"T{n:04d}",
                        customer_id=cid,
                        created_at=when.isoformat(),
                        product=PRODUCT,
                        version=version,
                        module=arc["module"],
                        issue_type=arc["issue"],
                        subject=arc["subject"],
                        body=_body(arc["key"], when.month),
                        status="resolved" if resolved else "open",
                        resolution=arc["resolution"] if resolved else None,
                        archetype=arc["key"],
                        phase=bucket,
                    )
                    (history if bucket == "history" else stream).append(ticket)

    history.sort(key=lambda t: (t["created_at"], t["id"]))
    stream.sort(key=lambda t: (t["created_at"], t["id"]))

    with (DATA / "seed_tickets.jsonl").open("w") as fh:
        for t in history:
            fh.write(json.dumps(t) + "\n")
    with (DATA / "demo_stream.jsonl").open("w") as fh:
        for t in stream:
            fh.write(json.dumps(t) + "\n")

    kb = [
        dict(id="KB-1", product=PRODUCT, module="Data Export",
             title="Large exports and the 504/timeout error",
             body="Exports above ~50k rows can time out. Use scheduled exports or split by date range. After v2.3 this was believed resolved; if you see immediate 504s on v2.4, treat it as a regression and escalate to on-call."),
        dict(id="KB-2", product=PRODUCT, module="Authentication",
             title="SSO redirect loop after password reset",
             body="Clear the Acme session cookie, or sign in from a private window. Resolves a single session; tracked as ENG-4502."),
        dict(id="KB-3", product=PRODUCT, module="Public API",
             title="Public API rate limits",
             body="Default limit is 120 requests/minute per token. Use exponential backoff on 429."),
        dict(id="KB-4", product=PRODUCT, module="Billing",
             title="Seat count mismatches on invoices",
             body="Duplicate seat counts have been reported around version upgrades. Billing can issue a corrected invoice."),
    ]
    with (DATA / "kb_articles.jsonl").open("w") as fh:
        for a in kb:
            fh.write(json.dumps(a) + "\n")

    print(f"wrote {len(history)} history tickets, {len(stream)} demo tickets, {len(customers)} customers")


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    generate()
