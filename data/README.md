# Task 1: Weekly Data Pipeline

## What's in here

- `atd_weekly.sql`: the query that builds the weekly Mexico delivery extract
- `workflow_design.md`: rough draft of the Airflow DAG that keeps the table refreshed

## What the SQL does

Pulls trip level delivery data for Uber Eats Mexico for the previous calendar week. Output schema matches Appendix 2 of the case.

Four tables:
- `tmp.lea_trips_scope_atd_consolidation_v2`: base trips and timestamps (this is what we're analyzing)
- `delivery_matching.eats_dispatch_metrics_job_message`: distances per trip
- `dwh.dim_city`: country mapping (we need this to filter to Mexico)
- `kirby_external_data.cities_strategy_region`: territory enrichment

## The query

```sql
SELECT
  COALESCE(c.territory, 'Unspecified') AS territory,
  d.country_name,
  t.workflow_uuid,
  t.driver_uuid,
  t.delivery_trip_uuid,
  t.courier_flow,
  t.restaurant_offered_timestamp_utc,
  t.order_final_state_timestamp_local,
  t.eater_request_timestamp_local,
  t.geo_archetype,
  t.merchant_surface,

  -- Distances: convert to kilometres
  m.pickupdistance  / 1000.0 AS pickup_distance,
  m.traveldistance  / 1000.0 AS dropoff_distance,

  -- ATD: minutes between restaurant offer and final delivery state
  TIMESTAMPDIFF(
    MINUTE,
    t.restaurant_offered_timestamp_utc,
    t.order_final_state_timestamp_local
  ) AS ATD

FROM tmp.lea_trips_scope_atd_consolidation_v2 t

-- INNER JOIN: distances are required, so we drop trips without a final dispatch plan rather than carry NULLs into the analysis.
INNER JOIN delivery_matching.eats_dispatch_metrics_job_message m
  ON t.workflow_uuid = m.jobuuid
  AND m.isfinalplan = TRUE

-- INNER JOIN: country is required to filter to Mexico.
INNER JOIN dwh.dim_city d
  ON m.cityid = d.city_id

-- LEFT JOIN: territory is enrichment. Some cities aren't mapped yet and we don't want to lose those Mexican deliveries.
LEFT JOIN kirby_external_data.cities_strategy_region c
  ON d.city_id = c.city_id

WHERE d.country_name = 'Mexico'
  AND DATE(t.eater_request_timestamp_local)
        BETWEEN DATE_SUB(DATE('{{ ds }}'), 7)
            AND DATE_SUB(DATE('{{ ds }}'), 1);
```

## How the joins work, and why each one is what it is

- **INNER JOIN on dispatch metrics.** Distances are required for the model. A trip without a final dispatch plan has no usable distances, so we drop those rows at the SQL layer rather than carry NULLs into the analysis. We also filter to `m.isfinalplan = TRUE` because the source emits one row per plan revision and we only want the committed plan.
- **INNER JOIN on `dim_city`.** Country is required to filter to Mexico. Every `city_id` in the dispatch table should resolve to a country. If it doesn't, that's a data-quality issue upstream and shouldn't quietly become Mexican rows in our table.
- **LEFT JOIN on `cities_strategy_region`.** Territory is enrichment, not a filter. Some Mexican cities aren't yet classified by the strategy team, but their orders are still legitimate Mexico deliveries that belong in the analysis. The `COALESCE(c.territory, 'Unspecified')` handles the NULL safely.

The principle: inner joins where the column is required for analysis, left join only for fields that are nice-to-have.

## How the dynamic date window works

```sql
DATE(t.eater_request_timestamp_local)
  BETWEEN DATE_SUB(DATE('{{ ds }}'), 7)
      AND DATE_SUB(DATE('{{ ds }}'), 1)
```

`{{ ds }}` is the Airflow macro that gets replaced with the DAG run date at execution time. When the DAG fires on a Monday, `{{ ds }}` is that Monday's date. The query then pulls the previous Mon–Sun window.

The same query produces a different week's data on every run with no code changes. Backfilling any past week is just re-running the DAG with a different `ds`.

## Distances and units

Source distances are in meters. The query divides by 1000 to convert to kilometers, which is what the dashboard and the model both expect. Doing this at the SQL layer means every downstream consumer sees the same units.

## ATD calculation

ATD is computed inline in the SELECT as the number of minutes between `restaurant_offered_timestamp_utc` and `order_final_state_timestamp_local`. This represents the total time the eater waited from when the restaurant got the order to when it arrived, which is the customer experience metric ops cares about.

## What the workflow does

The DAG runs every Monday at 03:00 UTC. Six tasks in order:

| # | Task | What it does |
|---|------|--------------|
| 1 | Freshness check | Confirms both source tables have data for the target window. If stale, fail fast and Slack alert. Cheaper than failing after a 5 minute SQL build. |
| 2 | Build staging table | Runs the SQL into `AA_tables.atd_weekly_metrics_staging`. Staging, not prod, so we can validate before replacing what the dashboard reads. |
| 3 | Data quality checks | Four validations: duplicates on `delivery_trip_uuid`, missing values in critical columns, weekly median ATD inside a plausible band (25–50 min), and row count within ±20% of last week. If any fail, abort and alert. |
| 4 | Atomic swap | If DQ passes, rename staging to prod in a single transaction. The dashboard never reads a half built table. |
| 5 | Retrain the model | Refresh the model on a rolling 8 week window and score the new trips. Only runs after DQ passes, so the model never trains on bad data. |
| 6 | Notify | Post a one-line summary to `#aa-pipelines`: row count, median ATD, model status. Failures route to ops with pager escalation on repeat failures. |

Three things this design guarantees:

- **Reliability** through the atomic swap. The dashboard either reads last week's data or this week's, never something in between.
- **Quality** through the DQ gate. Bad weeks get caught before they become prod.
- **Recoverability** through the freshness check. We don't waste compute on stale inputs, and Slack alerts route to ops with a pager fallback.

## What about missing values

The query itself does not have `WHERE col IS NOT NULL` filters. Cleaning happens in two places:

1. **In the dashboard's data load** (`app.py`), where we coerce `\N` strings to NaN, parse timestamps, and filter ATD to the operational range of 5 to 120 minutes. This drops about 2.3% of rows that are logging artefacts (instant cancels, clock skew, stuck orders marked complete much later).
2. **In the DQ gate** of the workflow, where we check that critical columns are 100% populated before allowing the swap to prod.

Keeping the SQL minimal lets us see the raw shape of the data and catch upstream regressions in the DQ gate, instead of silently filtering them away.

## Schema (matches Appendix 2)

| Column | Type | Notes |
|---|---|---|
| `territory` | string | COALESCE'd to 'Unspecified' for unmapped cities |
| `country_name` | string | Always 'Mexico' in this scope |
| `workflow_uuid` | string | |
| `driver_uuid` | string | |
| `delivery_trip_uuid` | string | Unique key |
| `courier_flow` | string | Motorbike, Logistics, Fleet, etc. |
| `restaurant_offered_timestamp_utc` | timestamp UTC | |
| `order_final_state_timestamp_local` | timestamp local | |
| `eater_request_timestamp_local` | timestamp local | |
| `geo_archetype` | string | |
| `merchant_surface` | string | POS, Tablet, Web/Mobile, etc. |
| `pickup_distance` | float (km) | source meters / 1000 |
| `dropoff_distance` | float (km) | source meters / 1000 |
| `ATD` | float (minutes) | TIMESTAMPDIFF between restaurant offer and final delivery state |
