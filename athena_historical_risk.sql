-- ============================================================================
-- NASA Planetary Defense Risk Intelligence Platform — Phase 7 Historical Sentry
-- AWS Athena / Trino DDL: Sentry Snapshot Coverage & Risk Metric History
-- ============================================================================
-- Architecture: Serverless Lakehouse (S3 + Athena SQL Views)
-- Grain:
--   v_sentry_snapshot_coverage:     (snapshot_key)
--   v_sentry_risk_metric_history:    (snapshot_key, sentry_id)
-- Scientific Safety: Strictly linear arithmetic deltas; no Palermo percentage
--                   change; zero composite danger scores; zero causal claims.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS nasa_asteroids;

-- ----------------------------------------------------------------------------
-- 1. External Table DDL: Sentry Risk Snapshots (Phase 4 Ingestion)
-- ----------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS nasa_asteroids.fact_sentry_risk_snapshot (
    snapshot_key STRING,
    run_id STRING,
    snapshot_time STRING,
    sentry_id STRING,
    designation STRING,
    fullname STRING,
    absolute_magnitude DOUBLE,
    estimated_diameter_km DOUBLE,
    impact_probability DOUBLE,
    potential_impacts_count BIGINT,
    palermo_scale_cum DOUBLE,
    palermo_scale_max DOUBLE,
    torino_scale_max BIGINT,
    v_infinity_km_s DOUBLE,
    impact_year_range STRING,
    last_obs_date STRING,
    last_obs_jd DOUBLE
)
PARTITIONED BY (
    year STRING,
    month STRING,
    day STRING
)
STORED AS PARQUET
LOCATION 's3://nasa-asteroid-intelligence/processed/sentry/risk_snapshot/'
TBLPROPERTIES (
    'parquet.compression'='SNAPPY',
    'projection.enabled'='true',
    'projection.year.type'='integer',
    'projection.year.range'='2020,2030',
    'projection.year.digits'='4',
    'projection.month.type'='integer',
    'projection.month.range'='1,12',
    'projection.month.digits'='2',
    'projection.day.type'='integer',
    'projection.day.range'='1,31',
    'projection.day.digits'='2',
    'storage.location.template'='s3://nasa-asteroid-intelligence/processed/sentry/risk_snapshot/year=${year}/month=${month}/day=${day}/'
);

-- ----------------------------------------------------------------------------
-- 2. External Table DDL: Canonical Asteroid Crosswalk Bridge (Phase 6 Resolution)
-- ----------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS nasa_asteroids.bridge_asteroid_identifier (
    asteroid_key STRING,
    source_system STRING,
    identifier_name STRING,
    identifier_value STRING,
    is_primary_pivot BOOLEAN,
    created_at STRING,
    updated_at STRING
)
PARTITIONED BY (
    year STRING,
    month STRING,
    day STRING
)
STORED AS PARQUET
LOCATION 's3://nasa-asteroid-intelligence/reference/asteroid_crosswalk/bridge_asteroid_identifier/'
TBLPROPERTIES (
    'parquet.compression'='SNAPPY',
    'projection.enabled'='true',
    'projection.year.type'='integer',
    'projection.year.range'='2020,2030',
    'projection.year.digits'='4',
    'projection.month.type'='integer',
    'projection.month.range'='1,12',
    'projection.month.digits'='2',
    'projection.day.type'='integer',
    'projection.day.range'='1,31',
    'projection.day.digits'='2',
    'storage.location.template'='s3://nasa-asteroid-intelligence/reference/asteroid_crosswalk/bridge_asteroid_identifier/year=${year}/month=${month}/day=${day}/'
);

-- ----------------------------------------------------------------------------
-- 3. Analytical View 1: Sentry Snapshot Coverage (Phase 7 Locked Contract)
-- ----------------------------------------------------------------------------
-- Purpose: Authoritative fact-derived coverage abstraction layer.
-- Grain: (snapshot_key)
-- Note: Derived strictly from retained fact rows; uncaptured dates are inferred
--       through sequence and calendar gap analysis, not direct storage probing.
CREATE OR REPLACE VIEW nasa_asteroids.v_sentry_snapshot_coverage AS
SELECT
    snapshot_key,
    TRUE AS is_captured,
    COUNT(*) AS row_count,
    MIN(snapshot_time) AS first_snapshot_time,
    MAX(snapshot_time) AS last_snapshot_time,
    DENSE_RANK() OVER (ORDER BY snapshot_key ASC) AS snapshot_seq
FROM nasa_asteroids.fact_sentry_risk_snapshot
GROUP BY snapshot_key;

-- ----------------------------------------------------------------------------
-- 4. Analytical View 2: Sentry Risk Metric History (Phase 7 Locked Contract)
-- ----------------------------------------------------------------------------
-- Purpose: Snapshot-to-snapshot metric progression, observation arc updates,
--          and deterministic coverage gap detection.
-- Grain: (snapshot_key, sentry_id)
-- Temporal Partition: sentry_id ordered by snapshot_key ASC.
-- Crosswalk: LEFT JOIN against bridge_asteroid_identifier (unresolved preserved).
CREATE OR REPLACE VIEW nasa_asteroids.v_sentry_risk_metric_history AS
WITH bridge_sentry AS (
    SELECT DISTINCT
        identifier_value AS sentry_id,
        asteroid_key
    FROM nasa_asteroids.bridge_asteroid_identifier
    WHERE source_system = 'sentry'
      AND identifier_name = 'sentry_id'
),
sentry_with_coverage AS (
    SELECT
        s.snapshot_key,
        s.run_id,
        s.snapshot_time,
        s.sentry_id,
        s.designation,
        s.fullname,
        s.impact_probability,
        s.palermo_scale_cum,
        s.palermo_scale_max,
        s.torino_scale_max,
        s.potential_impacts_count,
        s.v_infinity_km_s,
        s.last_obs_date,
        s.last_obs_jd,
        s.estimated_diameter_km,
        s.absolute_magnitude,
        s.impact_year_range,
        cov.snapshot_seq AS seq_curr,
        b.asteroid_key
    FROM nasa_asteroids.fact_sentry_risk_snapshot s
    INNER JOIN nasa_asteroids.v_sentry_snapshot_coverage cov
        ON cov.snapshot_key = s.snapshot_key
    LEFT JOIN bridge_sentry b
        ON b.sentry_id = s.sentry_id
),
windowed AS (
    SELECT
        snapshot_key,
        run_id,
        snapshot_time,
        sentry_id,
        designation,
        fullname,
        asteroid_key,
        impact_probability,
        palermo_scale_cum,
        palermo_scale_max,
        torino_scale_max,
        potential_impacts_count,
        v_infinity_km_s,
        last_obs_date,
        last_obs_jd,
        estimated_diameter_km,
        absolute_magnitude,
        impact_year_range,
        seq_curr,
        LAG(seq_curr) OVER (
            PARTITION BY sentry_id
            ORDER BY snapshot_key ASC
        ) AS seq_prev,
        LAG(snapshot_key) OVER (
            PARTITION BY sentry_id
            ORDER BY snapshot_key ASC
        ) AS prev_snapshot_key,
        LAG(impact_probability) OVER (
            PARTITION BY sentry_id
            ORDER BY snapshot_key ASC
        ) AS prev_impact_probability,
        LAG(palermo_scale_cum) OVER (
            PARTITION BY sentry_id
            ORDER BY snapshot_key ASC
        ) AS prev_palermo_scale_cum,
        LAG(palermo_scale_max) OVER (
            PARTITION BY sentry_id
            ORDER BY snapshot_key ASC
        ) AS prev_palermo_scale_max,
        LAG(torino_scale_max) OVER (
            PARTITION BY sentry_id
            ORDER BY snapshot_key ASC
        ) AS prev_torino_scale_max,
        LAG(potential_impacts_count) OVER (
            PARTITION BY sentry_id
            ORDER BY snapshot_key ASC
        ) AS prev_potential_impacts_count,
        LAG(v_infinity_km_s) OVER (
            PARTITION BY sentry_id
            ORDER BY snapshot_key ASC
        ) AS prev_v_infinity_km_s,
        LAG(last_obs_date) OVER (
            PARTITION BY sentry_id
            ORDER BY snapshot_key ASC
        ) AS prev_last_obs_date,
        LAG(estimated_diameter_km) OVER (
            PARTITION BY sentry_id
            ORDER BY snapshot_key ASC
        ) AS prev_estimated_diameter_km,
        LAG(absolute_magnitude) OVER (
            PARTITION BY sentry_id
            ORDER BY snapshot_key ASC
        ) AS prev_absolute_magnitude
    FROM sentry_with_coverage
)
SELECT
    snapshot_key,
    snapshot_time,
    sentry_id,
    designation,
    fullname,
    asteroid_key,
    -- Current mandatory metrics
    impact_probability,
    palermo_scale_cum,
    palermo_scale_max,
    torino_scale_max,
    potential_impacts_count,
    v_infinity_km_s,
    last_obs_date,
    -- Current optional physical metrics (exposed to support downstream lifecycle derivations)
    estimated_diameter_km,
    absolute_magnitude,
    -- Chronological prior observation metrics (LAG)
    prev_snapshot_key,
    prev_impact_probability,
    prev_palermo_scale_cum,
    prev_palermo_scale_max,
    prev_torino_scale_max,
    prev_potential_impacts_count,
    prev_v_infinity_km_s,
    prev_last_obs_date,
    prev_estimated_diameter_km,
    prev_absolute_magnitude,
    -- Arithmetic deltas (strictly linear; zero Palermo percentage calculations)
    (impact_probability - prev_impact_probability) AS delta_impact_probability,
    (palermo_scale_max - prev_palermo_scale_max) AS delta_palermo_scale_max,
    (palermo_scale_cum - prev_palermo_scale_cum) AS delta_palermo_scale_cum,
    (torino_scale_max - prev_torino_scale_max) AS delta_torino_scale_max,
    (potential_impacts_count - prev_potential_impacts_count) AS delta_potential_impacts_count,
    (v_infinity_km_s - prev_v_infinity_km_s) AS delta_v_infinity_km_s,
    CASE
        WHEN prev_last_obs_date IS NULL OR last_obs_date IS NULL THEN NULL
        ELSE DATE_DIFF('day', CAST(prev_last_obs_date AS DATE), CAST(last_obs_date AS DATE))
    END AS delta_last_obs_days,
    -- Analytical and lifecycle flags
    CASE
        WHEN prev_snapshot_key IS NULL THEN TRUE
        ELSE FALSE
    END AS is_first_snapshot,
    CASE
        WHEN prev_last_obs_date IS NULL THEN FALSE
        WHEN last_obs_date > prev_last_obs_date THEN TRUE
        ELSE FALSE
    END AS has_new_observations,
    CASE
        WHEN prev_snapshot_key IS NULL THEN FALSE
        WHEN impact_probability != prev_impact_probability
          OR palermo_scale_max != prev_palermo_scale_max
          OR torino_scale_max != prev_torino_scale_max
          OR potential_impacts_count != prev_potential_impacts_count THEN TRUE
        ELSE FALSE
    END AS is_metric_changed,
    -- Deterministic coverage gap flag
    CASE
        WHEN prev_snapshot_key IS NULL THEN FALSE
        WHEN DATE_DIFF('day', CAST(prev_snapshot_key AS DATE), CAST(snapshot_key AS DATE)) = 1 THEN FALSE
        WHEN (seq_curr - seq_prev) = DATE_DIFF('day', CAST(prev_snapshot_key AS DATE), CAST(snapshot_key AS DATE)) THEN FALSE
        WHEN (seq_curr - seq_prev) < DATE_DIFF('day', CAST(prev_snapshot_key AS DATE), CAST(snapshot_key AS DATE)) THEN TRUE
        ELSE FALSE
    END AS coverage_gap_flag
FROM windowed;
