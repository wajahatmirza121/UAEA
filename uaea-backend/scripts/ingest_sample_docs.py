#!/usr/bin/env python3
"""CLI to ingest a folder of sample .txt/.pdf documents into the RAG store.

Usage:
    python scripts/ingest_sample_docs.py ./sample_docs
    python scripts/ingest_sample_docs.py ./sample_docs --doc-id my-doc
"""

import asyncio
import argparse
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import async_session
from app.rag.ingest import ingest_file, ingest_document


SAMPLE_DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sample_docs")

# Inline sample documents (created if sample_docs/ folder doesn't exist)
INLINE_DOCS = {
    "admission-policy.txt": """§1 Admission Policy 2026-27

Admission to all undergraduate programmes requires at least 50% marks in the
qualifying examination (Intermediate or equivalent). Candidates awaiting results
may apply provisionally, subject to submission of the final result card before
the admission deadline.

§2 Eligibility Criteria

For BS programmes: minimum 50% marks in HSSC or equivalent.
For MA/MSc programmes: minimum 2nd division in the qualifying degree.
For M.Phil programmes: minimum CGPA 2.5/4.0 or 60% marks in the qualifying degree.

§3 Application Process

Apply online through the admission portal during the announced window.
Attach scanned copies of all required documents. Generate the fee challan,
pay at any designated bank branch, then upload the stamped receipt.

§4 Merit List

Merit is determined on the basis of marks in the qualifying examination.
Separate merit lists are published for each programme and campus.
Waiting lists are maintained until all seats are filled.
""",
    "fee-circular.txt": """§1 Fee Structure Academic Year 2026-27

All fees are in Pakistani Rupees (PKR) and are subject to annual revision.

§2 Tuition Fees - Undergraduate

BS Computer Science: Rs 28,500 per semester (new enrolment).
BS Computer Science: Rs 2,150 per credit hour (repeat courses).
B.Ed (1.5 Year): Rs 18,600 per semester.
MA Urdu: Rs 16,200 per semester.
MSc Mathematics: Rs 19,800 per semester.

§3 Late Payment Surcharge

A surcharge of Rs 500 per week applies to late fee payments.
Maximum surcharge is capped at Rs 2,000.

§4 Challan Payment Process

Generate the challan from the student portal. Deposit at any designated
bank branch. Portal status updates within two working days of the bank
posting the payment. Keep all three copies of the challan safe.
""",
    "exam-regulations.txt": """§5 Examination Date Sheet

The date sheet is published roughly four weeks before the examination window.
Clashes between two papers in the same slot must be reported to the
Examinations Department within seven days of the date sheet being published.

§6 Examination Conduct

Candidates must bring their CNIC and admit card to every examination.
Mobile phones and electronic devices are strictly prohibited in the
examination hall.

§7 Results and Gazette

Results are published on the results portal once the gazette is notified.
The gazette notification is the official record; the portal display is
provisional and may contain errors.

§8 Rechecking Policy

Rechecking confirms totalling and that no question was left unmarked.
It is NOT a re-evaluation of the paper. Applications for rechecking
close 30 days after the result is declared. Fee is Rs 1,500 per paper.
""",
    "degree-manual.txt": """§3 Degree Issuance

Normal processing time for degree issuance is 6 to 8 weeks after the
gazette is notified. Urgent processing is available at double the normal
fee and takes approximately 3 weeks.

Required documents for degree application:
1. Completed degree application form
2. All semester result cards (photocopies)
3. CNIC (photocopy)
4. Two passport-size photographs
5. Paid degree fee challan (Rs 2,000 for normal, Rs 4,000 for urgent)
6. No-dues clearance certificate from the campus

§4 Transcripts and PRC

Transcript requests are processed in 3 to 4 weeks for normal service
(fee Rs 1,500) and 5 working days for urgent service (fee Rs 3,500).
Collection is in person or by courier at the applicant's cost.

An authority letter is required if someone else collects on your behalf.

§5 Migration Certificate

Migration certificates are issued within 2 weeks. Fee is Rs 1,000.
Required: NOC from the previous institution and a copy of the result card.
""",
    "student-handbook.txt": """§1 Code of Conduct

Students must maintain decorum on campus. Ragging in any form is strictly
prohibited and is a cognizable offence.

§2 Attendance Requirements

Minimum 75% attendance is required to appear in the terminal examination.
Students falling short may be detained by the department.

§3 Assignments

Assignments must be submitted to the allocated tutor by the published date.
Late submissions may incur a penalty as determined by the department.
Plagiarised assignments will receive zero marks.

§4 Scholarships

Need-based scholarships cover up to 50% of tuition fees.
Applications close 25 October each semester.
Results are announced within 6 weeks of the deadline.
Merit scholarships are awarded automatically to position holders.

§5 Grievance Redressal

Students may file grievances through the student portal or in writing
to the campus director. Response time is 10 working days.
""",
}


def create_sample_docs(target_dir: str):
    """Create sample document files in the target directory."""
    os.makedirs(target_dir, exist_ok=True)
    for filename, content in INLINE_DOCS.items():
        path = os.path.join(target_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Created {path}")


async def ingest_folder(folder: str, doc_id: str | None = None):
    """Ingest all .txt and .pdf files in a folder."""
    if not os.path.isdir(folder):
        print(f"Folder not found: {folder}")
        sys.exit(1)

    files = [
        f for f in os.listdir(folder)
        if f.lower().endswith((".txt", ".pdf"))
    ]

    if not files:
        print(f"No .txt or .pdf files found in {folder}")
        sys.exit(1)

    print(f"Found {len(files)} document(s) to ingest.")

    total_chunks = 0
    async with async_session() as db:
        for filename in sorted(files):
            file_path = os.path.join(folder, filename)
            source_id = doc_id or os.path.splitext(filename)[0]
            print(f"  Ingesting {filename} (source_doc_id={source_id})…")
            chunks = await ingest_file(db, file_path, source_id)
            total_chunks += chunks
            print(f"    → {chunks} chunks created")

    print(f"\nDone. Total chunks created: {total_chunks}")


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into the UAEA RAG store.")
    parser.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="Path to folder containing .txt/.pdf files. Defaults to ./sample_docs (created with sample data if missing).",
    )
    parser.add_argument(
        "--doc-id",
        default=None,
        help="Override the source_doc_id for all files (default: filename without extension).",
    )

    args = parser.parse_args()
    folder = args.folder or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_docs")

    if not os.path.isdir(folder) and args.folder is None:
        print(f"Sample docs folder not found. Creating with inline sample documents…")
        create_sample_docs(folder)

    print(f"\nIngesting documents from: {folder}")
    asyncio.run(ingest_folder(folder, args.doc_id))


if __name__ == "__main__":
    main()
