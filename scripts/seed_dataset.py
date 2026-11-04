"""Deterministic synthetic B2B SaaS data warehouse generator (100k+ rows).

Generates realistic, temporally coherent columnar Parquet datasets:
- dim_customers.parquet (10,000 customers)
- dim_plans.parquet (5 plan tiers)
- fct_subscriptions.parquet (15,000 subscriptions)
- fct_invoices.parquet (60,000 invoices)
- fct_mrr_movements.parquet (30,000 MRR movements)
Total records: 115,005 rows.
"""

from __future__ import annotations

import datetime
import os
import random
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

SEED = 42
random.seed(SEED)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "seed"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INDUSTRIES = ["Healthcare", "Fintech", "DevTools", "E-commerce", "Cybersecurity", "EdTech"]
TIERS = ["Startup", "Mid-Market", "Enterprise"]
COUNTRIES = ["USA", "GBR", "DEU", "FRA", "CAN", "IND", "AUS", "SGP"]
COMPANIES_BASE = [
    "Acme Corp", "Alphabet Inc.", "TechFlow", "CloudScale", "NovaData", "Apex AI",
    "StripeLink", "Quantico", "HyperGrowth", "CyberShield", "DataForge", "OmniNet",
    "PulseAnalytics", "Synapse Bio", "Vortex Labs", "ByteCraft", "AeroSystems", "NexusTech"
]

PLANS = [
    {"plan_id": "PLAN-01", "plan_name": "Free Tier", "tier": "Free", "base_price_usd": 0.0, "billing_interval": "monthly"},
    {"plan_id": "PLAN-02", "plan_name": "Starter", "tier": "Basic", "base_price_usd": 49.0, "billing_interval": "monthly"},
    {"plan_id": "PLAN-03", "plan_name": "Growth Pro", "tier": "Pro", "base_price_usd": 199.0, "billing_interval": "monthly"},
    {"plan_id": "PLAN-04", "plan_name": "Enterprise Plus", "tier": "Enterprise", "base_price_usd": 999.0, "billing_interval": "monthly"},
    {"plan_id": "PLAN-05", "plan_name": "Scale Ultra", "tier": "Scale", "base_price_usd": 2499.0, "billing_interval": "annual"},
]


def generate_dim_customers(n: int = 10_000) -> pa.Table:
    """Generate dim_customers."""
    base_date = datetime.datetime(2023, 1, 1, 0, 0, 0)
    customer_ids = [f"CUST-{i:05d}" for i in range(1, n + 1)]
    company_names = [f"{random.choice(COMPANIES_BASE)} {i:04d}" for i in range(1, n + 1)]
    industries = [random.choice(INDUSTRIES) for _ in range(n)]
    tiers = [random.choices(TIERS, weights=[0.55, 0.35, 0.10])[0] for _ in range(n)]
    countries = [random.choices(COUNTRIES, weights=[0.45, 0.12, 0.10, 0.08, 0.08, 0.07, 0.05, 0.05])[0] for _ in range(n)]
    created_ats = [base_date + datetime.timedelta(days=random.randint(0, 1000), hours=random.randint(0, 23)) for _ in range(n)]
    is_deleted = [random.random() < 0.02 for _ in range(n)]

    schema = pa.schema([
        ("customer_id", pa.string()),
        ("company_name", pa.string()),
        ("industry", pa.string()),
        ("company_tier", pa.string()),
        ("country", pa.string()),
        ("created_at", pa.timestamp("ms")),
        ("is_deleted", pa.bool_()),
    ])

    return pa.Table.from_arrays([
        pa.array(customer_ids),
        pa.array(company_names),
        pa.array(industries),
        pa.array(tiers),
        pa.array(countries),
        pa.array(created_ats),
        pa.array(is_deleted),
    ], schema=schema)


def generate_dim_plans() -> pa.Table:
    """Generate dim_plans."""
    schema = pa.schema([
        ("plan_id", pa.string()),
        ("plan_name", pa.string()),
        ("tier", pa.string()),
        ("base_price_usd", pa.float64()),
        ("billing_interval", pa.string()),
    ])
    return pa.Table.from_pydict({
        "plan_id": [p["plan_id"] for p in PLANS],
        "plan_name": [p["plan_name"] for p in PLANS],
        "tier": [p["tier"] for p in PLANS],
        "base_price_usd": [p["base_price_usd"] for p in PLANS],
        "billing_interval": [p["billing_interval"] for p in PLANS],
    }, schema=schema)


def generate_fct_subscriptions(customer_ids: list[str], n: int = 15_000) -> pa.Table:
    """Generate fct_subscriptions."""
    sub_ids = [f"SUB-{i:05d}" for i in range(1, n + 1)]
    sub_cust_ids = [random.choice(customer_ids) for _ in range(n)]
    plan_choices = [random.choices(PLANS, weights=[0.20, 0.40, 0.25, 0.12, 0.03])[0] for _ in range(n)]
    plan_ids = [p["plan_id"] for p in plan_choices]
    
    statuses = []
    started_ats = []
    ended_ats = []
    mrr_amounts = []

    base_date = datetime.datetime(2023, 1, 1)

    for p in plan_choices:
        start = base_date + datetime.timedelta(days=random.randint(0, 800))
        status = random.choices(["active", "canceled", "past_due", "paused"], weights=[0.70, 0.20, 0.06, 0.04])[0]
        ended = None
        if status == "canceled":
            ended = start + datetime.timedelta(days=random.randint(30, 300))
        
        # calculate MRR
        base_val = p["base_price_usd"]
        if p["billing_interval"] == "annual":
            mrr = round(base_val / 12.0, 2)
        else:
            mrr = base_val
        
        # add random volume seat variance
        if base_val > 0:
            seats = random.choice([1, 1, 2, 5, 10, 25]) if p["tier"] in ["Pro", "Enterprise"] else 1
            mrr = round(mrr * seats, 2)
        
        statuses.append(status)
        started_ats.append(start)
        ended_ats.append(ended)
        mrr_amounts.append(mrr)

    schema = pa.schema([
        ("subscription_id", pa.string()),
        ("customer_id", pa.string()),
        ("plan_id", pa.string()),
        ("status", pa.string()),
        ("started_at", pa.timestamp("ms")),
        ("ended_at", pa.timestamp("ms")),
        ("mrr_amount_usd", pa.float64()),
    ])

    return pa.Table.from_arrays([
        pa.array(sub_ids),
        pa.array(sub_cust_ids),
        pa.array(plan_ids),
        pa.array(statuses),
        pa.array(started_ats),
        pa.array(ended_ats),
        pa.array(mrr_amounts),
    ], schema=schema)


def generate_fct_invoices(subscriptions: pa.Table, n: int = 60_000) -> pa.Table:
    """Generate fct_invoices."""
    sub_pydict = subscriptions.to_pydict()
    sub_count = len(sub_pydict["subscription_id"])

    inv_ids = [f"INV-{i:06d}" for i in range(1, n + 1)]
    inv_cust_ids = []
    inv_sub_ids = []
    inv_dates = []
    due_dates = []
    paid_ats = []
    total_amounts = []
    tax_amounts = []
    statuses = []

    for i in range(n):
        idx = i % sub_count
        c_id = sub_pydict["customer_id"][idx]
        s_id = sub_pydict["subscription_id"][idx]
        mrr = sub_pydict["mrr_amount_usd"][idx]
        start_date = sub_pydict["started_at"][idx]

        # invoice every 30 days
        month_offset = (i // sub_count) * 30
        inv_date = start_date + datetime.timedelta(days=month_offset + random.randint(0, 5))
        due_date = inv_date + datetime.timedelta(days=14)

        status = random.choices(["paid", "open", "void", "uncollectible"], weights=[0.88, 0.07, 0.03, 0.02])[0]
        paid_at = None
        if status == "paid":
            paid_at = inv_date + datetime.timedelta(days=random.randint(0, 10))

        total_amount = max(0.0, round(mrr + random.uniform(-5.0, 15.0), 2))
        tax = round(total_amount * 0.08, 2)

        inv_cust_ids.append(c_id)
        inv_sub_ids.append(s_id)
        inv_dates.append(inv_date)
        due_dates.append(due_date)
        paid_ats.append(paid_at)
        total_amounts.append(total_amount)
        tax_amounts.append(tax)
        statuses.append(status)

    schema = pa.schema([
        ("invoice_id", pa.string()),
        ("customer_id", pa.string()),
        ("subscription_id", pa.string()),
        ("invoice_date", pa.timestamp("ms")),
        ("due_date", pa.timestamp("ms")),
        ("paid_at", pa.timestamp("ms")),
        ("total_amount_usd", pa.float64()),
        ("tax_usd", pa.float64()),
        ("status", pa.string()),
    ])

    return pa.Table.from_arrays([
        pa.array(inv_ids),
        pa.array(inv_cust_ids),
        pa.array(inv_sub_ids),
        pa.array(inv_dates),
        pa.array(due_dates),
        pa.array(paid_ats),
        pa.array(total_amounts),
        pa.array(tax_amounts),
        pa.array(statuses),
    ], schema=schema)


def generate_fct_mrr_movements(customer_ids: list[str], n: int = 30_000) -> pa.Table:
    """Generate fct_mrr_movements."""
    mov_ids = [f"MOV-{i:06d}" for i in range(1, n + 1)]
    cust_ids = [random.choice(customer_ids) for _ in range(n)]
    mov_types = [random.choices(["new", "expansion", "contraction", "churn"], weights=[0.35, 0.35, 0.18, 0.12])[0] for _ in range(n)]

    base_date = datetime.datetime(2023, 1, 1)
    dates = [base_date + datetime.timedelta(days=random.randint(0, 1000), hours=random.randint(0, 23)) for _ in range(n)]

    prior_mrrs = []
    deltas = []
    new_mrrs = []

    for m_type in mov_types:
        if m_type == "new":
            prior = 0.0
            delta = round(random.uniform(49.0, 999.0), 2)
            new_m = delta
        elif m_type == "expansion":
            prior = round(random.uniform(99.0, 2500.0), 2)
            delta = round(random.uniform(50.0, 800.0), 2)
            new_m = round(prior + delta, 2)
        elif m_type == "contraction":
            prior = round(random.uniform(200.0, 3000.0), 2)
            delta = -round(random.uniform(30.0, min(prior * 0.7, 500.0)), 2)
            new_m = round(prior + delta, 2)
        else:  # churn
            prior = round(random.uniform(49.0, 1500.0), 2)
            delta = -prior
            new_m = 0.0

        prior_mrrs.append(prior)
        deltas.append(delta)
        new_mrrs.append(new_m)

    schema = pa.schema([
        ("movement_id", pa.string()),
        ("customer_id", pa.string()),
        ("movement_type", pa.string()),
        ("movement_date", pa.timestamp("ms")),
        ("mrr_delta_usd", pa.float64()),
        ("prior_mrr_usd", pa.float64()),
        ("new_mrr_usd", pa.float64()),
    ])

    return pa.Table.from_arrays([
        pa.array(mov_ids),
        pa.array(cust_ids),
        pa.array(mov_types),
        pa.array(dates),
        pa.array(deltas),
        pa.array(prior_mrrs),
        pa.array(new_mrrs),
    ], schema=schema)


def main():
    print(f"Generating synthetic B2B SaaS dataset into {DATA_DIR}...")
    
    customers_table = generate_dim_customers(10_000)
    pq.write_table(customers_table, DATA_DIR / "dim_customers.parquet")
    print(f"✓ Generated dim_customers.parquet ({len(customers_table):,} rows)")

    plans_table = generate_dim_plans()
    pq.write_table(plans_table, DATA_DIR / "dim_plans.parquet")
    print(f"✓ Generated dim_plans.parquet ({len(plans_table):,} rows)")

    customer_ids = customers_table["customer_id"].to_pylist()

    subs_table = generate_fct_subscriptions(customer_ids, 15_000)
    pq.write_table(subs_table, DATA_DIR / "fct_subscriptions.parquet")
    print(f"✓ Generated fct_subscriptions.parquet ({len(subs_table):,} rows)")

    invoices_table = generate_fct_invoices(subs_table, 60_000)
    pq.write_table(invoices_table, DATA_DIR / "fct_invoices.parquet")
    print(f"✓ Generated fct_invoices.parquet ({len(invoices_table):,} rows)")

    movements_table = generate_fct_mrr_movements(customer_ids, 30_000)
    pq.write_table(movements_table, DATA_DIR / "fct_mrr_movements.parquet")
    print(f"✓ Generated fct_mrr_movements.parquet ({len(movements_table):,} rows)")

    total_rows = len(customers_table) + len(plans_table) + len(subs_table) + len(invoices_table) + len(movements_table)
    print(f"\n🎉 Successfully seeded analytical data lakehouse: {total_rows:,} total rows.")


if __name__ == "__main__":
    main()
