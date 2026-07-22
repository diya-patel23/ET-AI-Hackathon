"""
Generates a realistic synthetic document set for the demo: maintenance logs,
inspection reports, and a couple of OEM manual / safety excerpts, all built
around a small recurring cast of equipment, engineers, and plants so the
knowledge graph and Root Cause Analysis agent have real cross-document trails
to work with (see architecture doc section 7 — this is the single highest-
leverage prep step).

Deliberately template-based, not LLM-generated, so `python run_seed.py` works
immediately with zero API key and is fully reproducible.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

OUT_DIR = Path(__file__).resolve().parent / "generated_docs"
OUT_DIR.mkdir(exist_ok=True)

PLANTS = ["Plant 1", "Plant 2", "Plant 3"]
ENGINEERS = ["Ravi Shah", "Priya Menon", "Alan Fernandes", "Kavita Rao", "Deepak Nair"]
EQUIPMENT = [
    ("Pump", "P204", "Plant 3", ["Bearing B42", "Seal S17", "Impeller I9"]),
    ("Pump", "P118", "Plant 1", ["Bearing B21", "Gasket G5"]),
    ("Compressor", "C305", "Plant 2", ["Filter F60", "Belt B8"]),
    ("Motor", "M410", "Plant 1", ["Bearing B12", "Coupling C3"]),
    ("Valve", "V220", "Plant 3", ["Seal S22"]),
    ("Boiler", "B501", "Plant 2", ["Gasket G14"]),
    ("Conveyor", "C602", "Plant 1", ["Belt B21", "Bearing B33"]),
    ("Turbine", "T710", "Plant 3", ["Rotor R4", "Bearing B45"]),
]

FAILURE_CHAINS = [
    ("High Temperature", "Bearing Wear", "Oil Leakage", "Pump Shutdown"),
    ("Excess Vibration", "Bearing Misalignment", "Seal Failure", "Unplanned Shutdown"),
    ("Pressure Spike", "Valve Sticking", "Overpressure Trip", "Line Shutdown"),
    ("Belt Slippage", "Belt Wear", "Motor Overload", "Conveyor Stoppage"),
]

STANDARDS = ["OSHA 1910.132", "OSHA 1910.169", "ISO 55001", "API 610"]


def _rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 1)))


def generate_maintenance_logs(n_per_equipment: int = 6):
    rows = []
    today = date.today()
    two_years_ago = today - timedelta(days=730)

    for eq_type, code, plant, parts in EQUIPMENT:
        eq_name = f"{eq_type} {code}"
        events = []
        for _ in range(n_per_equipment):
            event_date = _rand_date(two_years_ago, today)
            engineer = random.choice(ENGINEERS)
            event_type = random.choices(
                ["inspection", "repair", "failure", "replacement"],
                weights=[45, 30, 15, 10],
            )[0]
            downtime = 0.0
            failure_code = ""
            if event_type == "failure":
                chain = random.choice(FAILURE_CHAINS)
                downtime = round(random.uniform(4, 40), 1)
                failure_code = f"FC-{random.randint(1000, 9999)}"
                description = (
                    f"{eq_name} failure. Root symptom chain observed: {chain[0]} -> {chain[1]} "
                    f"-> {chain[2]} -> {chain[3]}. Failure Code: {failure_code}. "
                    f"Part implicated: {random.choice(parts)}."
                )
            elif event_type == "repair":
                description = f"Repaired {random.choice(parts)} on {eq_name} after routine inspection flagged wear."
            elif event_type == "replacement":
                description = f"Replaced {random.choice(parts)} on {eq_name} as preventive maintenance."
            else:
                description = f"Routine inspection of {eq_name}. Visual and vibration checks within normal range."

            events.append({
                "equipment": eq_name,
                "plant": plant,
                "date": event_date,
                "engineer": engineer,
                "event_type": event_type,
                "description": description,
                "downtime_hours": downtime,
                "failure_code": failure_code,
            })
        events.sort(key=lambda e: e["date"])

        # write one maintenance log document per equipment (mirrors how a real plant keeps a running log per asset)
        lines = [
            f"MAINTENANCE LOG",
            f"Equipment: {eq_name}",
            f"Plant: {plant}",
            f"Department: Maintenance",
            "",
        ]
        for e in events:
            lines.append(f"Date: {e['date']}")
            lines.append(f"Engineer: {e['engineer']}")
            lines.append(f"Event Type: {e['event_type']}")
            lines.append(f"Description: {e['description']}")
            lines.append(f"Downtime (hours): {e['downtime_hours']}")
            lines.append("")

        fname = OUT_DIR / f"maintenance_log_{code}.txt"
        fname.write_text("\n".join(lines), encoding="utf-8")
        rows.extend([{**e, "filename": fname.name} for e in events])

    # also dump a master CSV — useful both as an ingestible CSV document and
    # as the source of truth for seeding the structured maintenance_events table directly
    csv_path = OUT_DIR / "maintenance_events_master.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return rows


def generate_inspection_reports(n: int = 15):
    for i in range(n):
        eq_type, code, plant, parts = random.choice(EQUIPMENT)
        eq_name = f"{eq_type} {code}"
        engineer = random.choice(ENGINEERS)
        insp_date = _rand_date(date.today() - timedelta(days=365), date.today())
        standard = random.choice(STANDARDS)
        has_ppe_note = random.random() > 0.2
        expired_cert = random.random() < 0.15

        lines = [
            "INSPECTION REPORT",
            f"Equipment: {eq_name}",
            f"Plant: {plant}",
            f"Inspection Date: {insp_date}",
            f"Inspected by: {engineer}",
            f"Applicable Standard: {standard}",
            "",
            f"Findings: Equipment inspected for wear on {random.choice(parts)}. "
            f"{'PPE requirement confirmed for personnel in the area.' if has_ppe_note else ''}",
            f"{'NOTE: certification expired for this asset, renewal required.' if expired_cert else 'All certifications current.'}",
            f"Pressure reading: {random.randint(20, 90)} psi within acceptable range." if eq_type in ("Boiler", "Compressor", "Pump") else "",
        ]
        text = "\n".join(l for l in lines if l is not None)
        (OUT_DIR / f"inspection_report_{code}_{i}.txt").write_text(text, encoding="utf-8")


def generate_safety_manual_excerpts():
    content = """SAFETY MANUAL EXCERPT — GENERAL PLANT SAFETY
Plant: Plant 1
Department: Safety

Section 4: Personal Protective Equipment (PPE)
All personnel working near rotating equipment (Pumps, Compressors, Motors, Turbines) must wear
PPE including hearing protection, safety glasses, and steel-toe footwear, per OSHA 1910.132.

Section 7: Pressure Vessel Safety
Boilers and Compressors operating above 60 psi require inspection every 12 months per OSHA 1910.169.
Any pressure reading exceeding rated limits must trigger immediate shutdown procedures.

Section 9: Bearing and Rotating Equipment Standards
All bearings (see Bearing B42, B21, B12, B33, B45) should be inspected under API 610 guidelines.
Bearings exceeding 900 operating hours without inspection are considered high risk.
"""
    (OUT_DIR / "safety_manual_general.txt").write_text(content, encoding="utf-8")

    oem_content = """OEM MANUAL EXCERPT — CENTRIFUGAL PUMP SERIES (applies to Pump P204, Pump P118)
Manufacturer guidance:
- Bearing wear is the leading cause of unplanned shutdowns in this pump series.
- Recommended bearing inspection interval: every 900 operating hours.
- Early symptoms of bearing wear: elevated temperature, then vibration, then oil leakage.
- If oil leakage is observed, schedule immediate shutdown to avoid impeller damage.
"""
    (OUT_DIR / "oem_manual_pump_series.txt").write_text(oem_content, encoding="utf-8")


def main():
    print("Generating seed documents...")
    rows = generate_maintenance_logs()
    generate_inspection_reports()
    generate_safety_manual_excerpts()
    print(f"Wrote {len(list(OUT_DIR.glob('*')))} files to {OUT_DIR}")
    print(f"Generated {len(rows)} structured maintenance events across {len(EQUIPMENT)} equipment items.")


if __name__ == "__main__":
    main()
