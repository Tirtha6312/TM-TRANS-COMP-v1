
import json
import re
import csv
import hashlib
import base64
from pathlib import Path
from difflib import SequenceMatcher


# ============================================================
# INTERNAL PROVENANCE / AUTHORSHIP
# ============================================================
#
# This attribution is intentionally encoded rather than stored
# as plain text.
#
# Author: Tirtha Mukherjee
# Project: EMP vs OPEN Transcription Comparative Analysis
#
# TM = Tirtha Mukherjee
# ============================================================

_AUTHOR_SIGNATURE = base64.b64decode(
    "VGltdGhhIE11a2hlcmplZQ=="
).decode("utf-8")

_GITHUB_SIGNATURE = base64.b64decode(
    "aHR0cHM6Ly9naXRodWIuY29tL1RpcnRoYTM2MTI="
).decode("utf-8")

_ALGORITHM_ID = "TM-TRANS-COMP-v1"

_COPYRIGHT = base64.b64decode(
    "wqkgVGltdGhhIE11a2hlcmplZQ=="
).decode("utf-8")


def _internal_provenance():
    """
    Internal provenance information.

    Kept separate from the normal user-facing output.
    """

    signature_data = (
        _ALGORITHM_ID
        + "|"
        + _AUTHOR_SIGNATURE
        + "|"
        + _GITHUB_SIGNATURE
    )

    algorithm_signature = hashlib.sha256(
        signature_data.encode("utf-8")
    ).hexdigest()

    return {
        "_algorithm_id": _ALGORITHM_ID,
        "_copyright": _COPYRIGHT,
        "_author": _AUTHOR_SIGNATURE,
        "_source": _GITHUB_SIGNATURE,
        "_signature": algorithm_signature,
    }


# ============================================================
# CONFIGURATION
# ============================================================

OPEN_FOLDER = Path("./open")
EMP_FOLDER = Path("./emp")

OUTPUT_FOLDER = Path("./comparison_results")

REPORT_FILE = OUTPUT_FOLDER / "comparative_report.csv"
DIFF_FILE = OUTPUT_FOLDER / "text_differences.csv"
SUMMARY_FILE = OUTPUT_FOLDER / "overall_summary.csv"


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path):

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception as e:

        print(f"ERROR reading {path}: {e}")

        return None


# ============================================================
# GET TRANSCRIPTION
# ============================================================

def get_transcription(data):

    if not isinstance(data, dict):
        return ""

    text = data.get("transcription")

    if isinstance(text, str):
        return text

    api_response = data.get("api_response")

    if isinstance(api_response, dict):

        text = api_response.get("text")

        if isinstance(text, str):
            return text

    return ""


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    if not text:
        return ""

    # Remove timestamps
    text = re.sub(
        r"\[\d{1,2}:\d{2}\]",
        " ",
        text
    )

    # Remove speaker labels
    text = re.sub(
        r"\bSpeaker\s+\d+\s*:",
        " ",
        text,
        flags=re.IGNORECASE
    )

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize(text):

    text = clean_text(text)

    text = text.lower()

    # Remove punctuation
    text = re.sub(
        r"[^\w\s]",
        " ",
        text
    )

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def tokenize(text):

    return normalize(text).split()


# ============================================================
# WORD ALIGNMENT
# ============================================================

def word_alignment(reference, hypothesis):

    n = len(reference)
    m = len(hypothesis)

    dp = [
        [0] * (m + 1)
        for _ in range(n + 1)
    ]

    for i in range(n + 1):
        dp[i][0] = i

    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):

        for j in range(1, m + 1):

            if reference[i - 1] == hypothesis[j - 1]:

                cost = 0

            else:

                cost = 1

            dp[i][j] = min(

                dp[i - 1][j] + 1,

                dp[i][j - 1] + 1,

                dp[i - 1][j - 1] + cost
            )

    # --------------------------------------------------------
    # Backtracking
    # --------------------------------------------------------

    i = n
    j = m

    matches = 0
    substitutions = 0
    insertions = 0
    deletions = 0

    differences = []

    while i > 0 or j > 0:

        if (
            i > 0
            and j > 0
            and dp[i][j]
            ==
            dp[i - 1][j - 1]
            +
            (
                0
                if reference[i - 1]
                ==
                hypothesis[j - 1]
                else 1
            )
        ):

            if reference[i - 1] == hypothesis[j - 1]:

                matches += 1

            else:

                substitutions += 1

                differences.append({
                    "type": "substitution",
                    "open": reference[i - 1],
                    "emp": hypothesis[j - 1]
                })

            i -= 1
            j -= 1

        elif (
            j > 0
            and dp[i][j]
            ==
            dp[i][j - 1] + 1
        ):

            insertions += 1

            differences.append({
                "type": "insertion",
                "open": "",
                "emp": hypothesis[j - 1]
            })

            j -= 1

        else:

            deletions += 1

            differences.append({
                "type": "deletion",
                "open": reference[i - 1],
                "emp": ""
            })

            i -= 1

    differences.reverse()

    return {
        "matches": matches,
        "substitutions": substitutions,
        "insertions": insertions,
        "deletions": deletions,
        "differences": differences
    }


# ============================================================
# TEXT SIMILARITY
# ============================================================

def calculate_similarity(reference, hypothesis):

    if not reference and not hypothesis:
        return 100.0

    if not reference or not hypothesis:
        return 0.0

    ratio = SequenceMatcher(
        None,
        reference,
        hypothesis
    ).ratio()

    return ratio * 100


# ============================================================
# DUPLICATION DETECTION
# ============================================================

def detect_duplication(reference, hypothesis):

    if not reference:
        return False

    ref_len = len(reference)
    hyp_len = len(hypothesis)

    if hyp_len < ref_len * 1.8:
        return False

    first = hypothesis[:ref_len]

    second = hypothesis[
        ref_len:ref_len * 2
    ]

    first_similarity = SequenceMatcher(
        None,
        reference,
        first
    ).ratio()

    second_similarity = SequenceMatcher(
        None,
        reference,
        second
    ).ratio()

    return (
        first_similarity >= 0.95
        and second_similarity >= 0.95
    )


# ============================================================
# QUALITY
# ============================================================

def quality(accuracy):

    if accuracy >= 95:
        return "Excellent"

    elif accuracy >= 90:
        return "Very Good"

    elif accuracy >= 80:
        return "Good"

    elif accuracy >= 70:
        return "Fair"

    elif accuracy >= 50:
        return "Poor"

    else:
        return "Very Poor"


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    open_files = {
        p.name: p
        for p in OPEN_FOLDER.glob(
            "open_*.json"
        )
    }

    emp_files = sorted(
        EMP_FOLDER.glob(
            "emp_*.json"
        )
    )

    print("=" * 85)
    print(
        "EMP vs OPEN COMPARATIVE "
        "TRANSCRIPTION STUDY"
    )
    print("=" * 85)

    print(
        f"OPEN files : {len(open_files)}"
    )

    print(
        f"EMP files  : {len(emp_files)}"
    )

    print()

    results = []
    differences_output = []

    total_reference_words = 0
    total_emp_words = 0

    total_matches = 0
    total_substitutions = 0
    total_insertions = 0
    total_deletions = 0

    similarity_values = []
    accuracy_values = []

    # ========================================================
    # COMPARE FILES
    # ========================================================

    for emp_path in emp_files:

        open_filename = (
            "open_"
            + emp_path.name[len("emp_"):]
        )

        open_path = open_files.get(
            open_filename
        )

        if not open_path:

            print(
                f"MISSING: {emp_path.name}"
            )

            continue

        emp_data = load_json(
            emp_path
        )

        open_data = load_json(
            open_path
        )

        if not emp_data or not open_data:
            continue

        # ----------------------------------------------------
        # Extract transcription
        # ----------------------------------------------------

        emp_raw = get_transcription(
            emp_data
        )

        open_raw = get_transcription(
            open_data
        )

        # ----------------------------------------------------
        # Tokenize
        # ----------------------------------------------------

        open_words = tokenize(
            open_raw
        )

        emp_words = tokenize(
            emp_raw
        )

        # ----------------------------------------------------
        # Alignment
        # ----------------------------------------------------

        alignment = word_alignment(
            open_words,
            emp_words
        )

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        reference_count = len(
            open_words
        )

        errors = (
            alignment["substitutions"]
            + alignment["insertions"]
            + alignment["deletions"]
        )

        if reference_count:

            wer = (
                errors
                / reference_count
            )

        else:

            wer = 0

        accuracy = max(
            0,
            (1 - wer) * 100
        )

        similarity = calculate_similarity(
            open_words,
            emp_words
        )

        duplicated = detect_duplication(
            open_words,
            emp_words
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        if duplicated:

            status = "DUPLICATED"

        else:

            status = quality(
                accuracy
            )

        # ----------------------------------------------------
        # Differences
        # ----------------------------------------------------

        for diff in alignment["differences"]:

            differences_output.append({

                "emp_file":
                    emp_path.name,

                "open_file":
                    open_path.name,

                "type":
                    diff["type"],

                "open_word":
                    diff["open"],

                "emp_word":
                    diff["emp"]
            })

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        results.append({

            "file":
                emp_path.name,

            "reference_file":
                open_path.name,

            "open_words":
                reference_count,

            "emp_words":
                len(emp_words),

            "word_difference":
                len(emp_words)
                - reference_count,

            "matches":
                alignment["matches"],

            "substitutions":
                alignment["substitutions"],

            "insertions":
                alignment["insertions"],

            "deletions":
                alignment["deletions"],

            "WER_percent":
                round(
                    wer * 100,
                    2
                ),

            "accuracy_percent":
                round(
                    accuracy,
                    2
                ),

            "text_similarity_percent":
                round(
                    similarity,
                    2
                ),

            "duplicated":
                "YES"
                if duplicated
                else "NO",

            "quality":
                status
        })

        # ----------------------------------------------------
        # Totals
        # ----------------------------------------------------

        total_reference_words += (
            reference_count
        )

        total_emp_words += (
            len(emp_words)
        )

        total_matches += (
            alignment["matches"]
        )

        total_substitutions += (
            alignment["substitutions"]
        )

        total_insertions += (
            alignment["insertions"]
        )

        total_deletions += (
            alignment["deletions"]
        )

        similarity_values.append(
            similarity
        )

        accuracy_values.append(
            accuracy
        )

        # ----------------------------------------------------
        # Console
        # ----------------------------------------------------

        print(
            f"{emp_path.name:<35}"
            f" Accuracy: {accuracy:6.2f}%"
            f"  Similarity: {similarity:6.2f}%"
            f"  {status}"
        )

    # ========================================================
    # OVERALL METRICS
    # ========================================================

    total_errors = (
        total_substitutions
        + total_insertions
        + total_deletions
    )

    if total_reference_words:

        overall_wer = (
            total_errors
            / total_reference_words
        )

        overall_accuracy = (
            1 - overall_wer
        ) * 100

    else:

        overall_wer = 0
        overall_accuracy = 100

    if similarity_values:

        average_similarity = (
            sum(similarity_values)
            / len(similarity_values)
        )

        average_accuracy = (
            sum(accuracy_values)
            / len(accuracy_values)
        )

    else:

        average_similarity = 0
        average_accuracy = 0

    duplicated_count = sum(
        1
        for r in results
        if r["duplicated"] == "YES"
    )

    # ========================================================
    # WRITE COMPARATIVE REPORT
    # ========================================================

    if results:

        with open(
            REPORT_FILE,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=results[0].keys()
            )

            writer.writeheader()

            writer.writerows(
                results
            )

    # ========================================================
    # WRITE DIFFERENCES
    # ========================================================

    if differences_output:

        with open(
            DIFF_FILE,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=
                differences_output[0].keys()
            )

            writer.writeheader()

            writer.writerows(
                differences_output
            )

    # ========================================================
    # HIDDEN PROVENANCE
    # ========================================================
    #
    # This file contains the encoded attribution information.
    #
    # It is intentionally separate from the normal comparison
    # report so the normal CSV remains clean.
    # ========================================================

    provenance = _internal_provenance()

    provenance_file = (
        OUTPUT_FOLDER
        / ".analysis_provenance"
    )

    with open(
        provenance_file,
        "w",
        encoding="utf-8"
    ) as f:

        # Store only encoded/internal metadata.
        encoded_source = base64.b64encode(
            provenance["_source"].encode()
        ).decode()

        encoded_author = base64.b64encode(
            provenance["_author"].encode()
        ).decode()

        f.write(
            f"{provenance['_algorithm_id']}\n"
        )

        f.write(
            f"{encoded_author}\n"
        )

        f.write(
            f"{encoded_source}\n"
        )

        f.write(
            f"{provenance['_signature']}\n"
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    summary = {

        "files_compared":
            len(results),

        "total_open_words":
            total_reference_words,

        "total_emp_words":
            total_emp_words,

        "word_count_difference":
            total_emp_words
            - total_reference_words,

        "correct_word_matches":
            total_matches,

        "substitutions":
            total_substitutions,

        "insertions":
            total_insertions,

        "deletions":
            total_deletions,

        "total_errors":
            total_errors,

        "overall_WER_percent":
            round(
                overall_wer * 100,
                2
            ),

        "overall_accuracy_percent":
            round(
                overall_accuracy,
                2
            ),

        "average_file_accuracy_percent":
            round(
                average_accuracy,
                2
            ),

        "average_text_similarity_percent":
            round(
                average_similarity,
                2
            ),

        "duplicated_transcriptions":
            duplicated_count
    }

    with open(
        SUMMARY_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=summary.keys()
        )

        writer.writeheader()

        writer.writerow(summary)

    # ========================================================
    # FINAL CONSOLE REPORT
    # ========================================================

    print()
    print("=" * 85)
    print("COMPARATIVE STUDY SUMMARY")
    print("=" * 85)

    print(
        f"Files compared              : "
        f"{len(results)}"
    )

    print(
        f"OPEN reference words        : "
        f"{total_reference_words}"
    )

    print(
        f"EMP words                   : "
        f"{total_emp_words}"
    )

    print(
        f"Word count difference       : "
        f"{total_emp_words - total_reference_words}"
    )

    print()

    print(
        f"Correct word matches        : "
        f"{total_matches}"
    )

    print(
        f"Substitutions               : "
        f"{total_substitutions}"
    )

    print(
        f"Insertions                  : "
        f"{total_insertions}"
    )

    print(
        f"Deletions                   : "
        f"{total_deletions}"
    )

    print(
        f"Total errors                : "
        f"{total_errors}"
    )

    print()

    print(
        f"Overall WER                 : "
        f"{overall_wer * 100:.2f}%"
    )

    print(
        f"Overall Accuracy            : "
        f"{overall_accuracy:.2f}%"
    )

    print(
        f"Average File Accuracy       : "
        f"{average_accuracy:.2f}%"
    )

    print(
        f"Average Text Similarity     : "
        f"{average_similarity:.2f}%"
    )

    print()

    print(
        f"Duplicated transcriptions   : "
        f"{duplicated_count}"
    )

    print()

    print("Reports generated:")

    print(
        f"  {REPORT_FILE}"
    )

    print(
        f"  {DIFF_FILE}"
    )

    print(
        f"  {SUMMARY_FILE}"
    )


if __name__ == "__main__":
    main()
