from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime


# Sources that carry a correlation_id in the schema
CORRELATED_SOURCES = {"ATMA", "ATMH", "KAFK", "TERM"}

# Time-window fallback (seconds) for sources without correlation_id
DEFAULT_WINDOW_SECONDS = 300  # 5 minutes


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(ts[:26], fmt)
        except ValueError:
            continue
    return None


class Correlator:
    """
    Cross-source incident correlation engine.

    Strategy 1 — correlation_id grouping:
        For ATMA, ATMH, KAFK, and TERM, join detection rows back to their
        source tables and group any detections that share the same
        correlation_id.  A single correlation_id appearing in multiple
        sources becomes one incident.

    Strategy 2 — time-window fallback:
        For sources that carry no correlation_id (WINOS, GCP, PROM) and for
        CORRELATED_SOURCES detections where correlation_id is NULL, group
        detections for the same atm_id whose detection_timestamp falls within
        DEFAULT_WINDOW_SECONDS of each other.

    Limitations:
        - GCP and PROM do not carry atm_id; they are attached to an incident
          by time-window proximity only when a concurrent atm_id incident exists.
        - correlation_id values are set in the synthetic data generator and will
          be NULL for background/normal traffic rows.
    """

    def __init__(self, db_path: str = "data/clean/atm_logs.db",
                 window_seconds: int = DEFAULT_WINDOW_SECONDS):
        self.db_path = db_path
        self.window_seconds = window_seconds

    # ── helpers ──────────────────────────────────────────────────────────────

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _table_exists(self, conn, name: str) -> bool:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        return row is not None

    def _load_detections(self, conn) -> list[dict]:
        if not self._table_exists(conn, "analysis_detections"):
            return []
        rows = conn.execute(
            """
            SELECT id, anomaly_type, anomaly_name, severity, source, atm_id,
                   detection_timestamp, description, event_count
            FROM analysis_detections
            """
        ).fetchall()
        cols = ["id", "anomaly_type", "anomaly_name", "severity", "source",
                "atm_id", "detection_timestamp", "description", "event_count"]
        return [dict(zip(cols, r)) for r in rows]

    def _fetch_correlation_ids(self, conn, source: str, atm_id: str | None) -> list[str]:
        """Return distinct non-null correlation_ids from the source table for an atm_id."""
        if source not in CORRELATED_SOURCES:
            return []
        try:
            if atm_id and atm_id != "N/A":
                rows = conn.execute(
                    f"SELECT DISTINCT correlation_id FROM [{source}] "
                    f"WHERE atm_id = ? AND correlation_id IS NOT NULL",
                    (atm_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    f"SELECT DISTINCT correlation_id FROM [{source}] "
                    f"WHERE correlation_id IS NOT NULL"
                ).fetchall()
        except sqlite3.OperationalError:
            return []
        return [r[0] for r in rows if r[0]]

    # ── strategy 1: correlation_id grouping ──────────────────────────────────

    def group_by_correlation_id(self, detections: list[dict]) -> dict[str, list[dict]]:
        """
        Returns {correlation_id: [detection, ...]} for detections whose source
        table rows share a correlation_id.  Detections with no resolvable
        correlation_id are excluded (handled by time-window fallback).
        """
        groups: dict[str, list[dict]] = defaultdict(list)

        with self._connect() as conn:
            for det in detections:
                if det["source"] not in CORRELATED_SOURCES:
                    continue
                corr_ids = self._fetch_correlation_ids(conn, det["source"], det.get("atm_id"))
                for cid in corr_ids:
                    groups[cid].append(det)

        # Only keep groups that span more than one source
        return {
            cid: dets
            for cid, dets in groups.items()
            if len({d["source"] for d in dets}) > 1
        }

    # ── strategy 2: time-window fallback ─────────────────────────────────────

    def group_by_time_window(self, detections: list[dict]) -> list[list[dict]]:
        """
        Groups detections for the same atm_id whose detection_timestamp falls
        within self.window_seconds of each other.  Returns a list of groups
        (each group is a list of detection dicts).  Single-source, single-
        detection groups are excluded.
        """
        by_atm: dict[str, list[dict]] = defaultdict(list)
        for det in detections:
            atm = det.get("atm_id") or "N/A"
            by_atm[atm].append(det)

        incident_groups: list[list[dict]] = []

        for atm_id, dets in by_atm.items():
            # Sort by timestamp; use detected_at as fallback
            sortable = sorted(
                dets,
                key=lambda d: _parse_ts(d.get("detection_timestamp")) or datetime.min,
            )

            cluster: list[dict] = [sortable[0]]
            for det in sortable[1:]:
                anchor_ts = _parse_ts(cluster[0].get("detection_timestamp"))
                det_ts = _parse_ts(det.get("detection_timestamp"))
                if (
                    anchor_ts is None
                    or det_ts is None
                    or abs((det_ts - anchor_ts).total_seconds()) <= self.window_seconds
                ):
                    cluster.append(det)
                else:
                    if len({d["source"] for d in cluster}) > 1:
                        incident_groups.append(cluster)
                    cluster = [det]

            if len({d["source"] for d in cluster}) > 1:
                incident_groups.append(cluster)

        return incident_groups

    # ── build + store ─────────────────────────────────────────────────────────

    def build_incidents(self) -> list[dict]:
        """
        Combines both correlation strategies and returns a list of incident
        objects:
        {
            incident_id:     str  — "CORR-<cid>" or "WIN-<atm_id>-<idx>"
            correlation_id:  str | None
            atm_ids:         list[str]
            sources:         list[str]
            anomaly_types:   list[str]
            severity:        str  — CRITICAL if any detection is CRITICAL
            event_count:     int
            earliest_ts:     str | None
            latest_ts:       str | None
            description:     str
            strategy:        str  — "correlation_id" | "time_window"
        }
        """
        with self._connect() as conn:
            detections = self._load_detections(conn)

        if not detections:
            return []

        seen_detection_ids: set[int] = set()
        incidents: list[dict] = []

        # Strategy 1 — correlation_id
        corr_groups = self.group_by_correlation_id(detections)
        for cid, dets in corr_groups.items():
            det_ids = {d["id"] for d in dets}
            seen_detection_ids |= det_ids
            incidents.append(self._make_incident(
                f"CORR-{cid}", cid, dets, "correlation_id"
            ))

        # Strategy 2 — time-window (only for detections not already grouped)
        remaining = [d for d in detections if d["id"] not in seen_detection_ids]
        tw_groups = self.group_by_time_window(remaining)
        for idx, dets in enumerate(tw_groups):
            atm_id = dets[0].get("atm_id") or "N/A"
            incidents.append(self._make_incident(
                f"WIN-{atm_id}-{idx}", None, dets, "time_window"
            ))

        return incidents

    def _make_incident(
        self,
        incident_id: str,
        correlation_id: str | None,
        dets: list[dict],
        strategy: str,
    ) -> dict:
        atm_ids = sorted({d.get("atm_id") or "N/A" for d in dets})
        sources = sorted({d["source"] for d in dets})
        anomaly_types = sorted({d["anomaly_type"] for d in dets})
        severity = "CRITICAL" if any(d["severity"] == "CRITICAL" for d in dets) else "WARNING"
        event_count = sum(d.get("event_count") or 1 for d in dets)

        timestamps = [
            _parse_ts(d.get("detection_timestamp")) for d in dets
        ]
        valid_ts = [t for t in timestamps if t is not None]
        earliest = min(valid_ts).isoformat() if valid_ts else None
        latest = max(valid_ts).isoformat() if valid_ts else None

        descriptions = [d["description"] for d in dets if d.get("description")]
        description = "; ".join(descriptions[:3])
        if len(descriptions) > 3:
            description += f" (+{len(descriptions) - 3} more)"

        return {
            "incident_id": incident_id,
            "correlation_id": correlation_id,
            "atm_ids": atm_ids,
            "sources": sources,
            "anomaly_types": anomaly_types,
            "severity": severity,
            "event_count": event_count,
            "earliest_ts": earliest,
            "latest_ts": latest,
            "description": description,
            "strategy": strategy,
        }

    def store_incidents(self) -> int:
        """
        Builds incidents and writes them to the `incidents` table.
        Returns the number of incidents stored.
        """
        incidents = self.build_incidents()

        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT NOT NULL,
                    correlation_id TEXT,
                    atm_ids TEXT,
                    sources TEXT,
                    anomaly_types TEXT,
                    severity TEXT NOT NULL,
                    event_count INTEGER DEFAULT 1,
                    earliest_ts TEXT,
                    latest_ts TEXT,
                    description TEXT,
                    strategy TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("DELETE FROM incidents")
            conn.executemany(
                """
                INSERT INTO incidents
                    (incident_id, correlation_id, atm_ids, sources, anomaly_types,
                     severity, event_count, earliest_ts, latest_ts, description, strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        i["incident_id"],
                        i["correlation_id"],
                        ", ".join(i["atm_ids"]),
                        ", ".join(i["sources"]),
                        ", ".join(i["anomaly_types"]),
                        i["severity"],
                        i["event_count"],
                        i["earliest_ts"],
                        i["latest_ts"],
                        i["description"],
                        i["strategy"],
                    )
                    for i in incidents
                ],
            )
            conn.commit()

        print(f"[INFO] Correlation complete: {len(incidents)} incident group{'' if len(incidents) == 1 else 's'} written to incidents.")
        return len(incidents)
