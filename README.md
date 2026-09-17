# TM-TRANS-COMP-v1™

A Python-based transcription comparative analysis algorithm for evaluating generated speech-to-text transcriptions against reference transcriptions.

The algorithm compares **OPEN** reference transcriptions with **EMP** generated transcriptions and calculates word-level accuracy, WER, text similarity, transcription errors, and duplicate transcription detection.

**Author:** Tirtha Mukherjee
**GitHub:** https://github.com/Tirtha6312

---

## Features

* Compare OPEN and EMP transcription JSON files
* Automatically match corresponding files
* Text normalization
* Timestamp removal
* Speaker-label removal
* Word Error Rate (WER)
* Word-level transcription accuracy
* Text similarity percentage
* Substitution detection
* Deletion detection
* Insertion detection
* Duplicate transcription detection
* Per-file comparative report
* Overall evaluation summary
* Text difference report
* Embedded authorship provenance
* Provenance integrity/tamper detection

---

# Required Folder Structure

The repository contains the comparison algorithm, but **the user must create the input folders themselves**.

Before running the program, create the following structure:

```text
TM-TRANS-COMP-v1/
│
├── compare_transcriptions.py
├── LICENSE
├── README.md
│
├── open/
│   ├── open_audio_001.json
│   ├── open_audio_002.json
│   ├── open_audio_003.json
│   └── ...
│
└── emp/
    ├── emp_audio_001.json
    ├── emp_audio_002.json
    ├── emp_audio_003.json
    └── ...
```

The `open/` and `emp/` folders are **required** for the algorithm to work.

---

# Input Folders

## `open/`

The `open/` folder must contain the **reference transcription JSON files**.

Example:

```text
open/
├── open_audio_001.json
├── open_audio_002.json
├── open_audio_003.json
└── ...
```

## `emp/`

The `emp/` folder must contain the **transcriptions that you want to evaluate**.

Example:

```text
emp/
├── emp_audio_001.json
├── emp_audio_002.json
├── emp_audio_003.json
└── ...
```

---

# File Matching

The algorithm automatically matches files based on their common identifier.

For example:

```text
open_audio_001.json
        ↕
emp_audio_001.json
```

and:

```text
open_audio_002.json
        ↕
emp_audio_002.json
```

The identifier:

```text
audio_001
```

is used to match the two files.

Files without a corresponding pair are not included in the comparison.

---

# JSON Format

Each JSON file should contain a transcription.

Example:

```json
{
    "source_file": "audio_001",
    "transcription": "This is an example transcription."
}
```

The algorithm primarily reads:

```text
transcription
```

If `transcription` is unavailable, the algorithm can also use:

```text
api_response.text
```

For example:

```json
{
    "source_file": "audio_001",
    "api_response": {
        "text": "This is an example transcription."
    }
}
```

---

# Running the Algorithm

Clone the repository:

```bash
git clone git@github.com:Tirtha6312/TM-TRANS-COMP-v1.git
```

Enter the repository:

```bash
cd TM-TRANS-COMP-v1
```

Create the required folders:

```bash
mkdir open emp
```

Place your reference JSON files inside:

```text
open/
```

Place the generated/evaluated JSON files inside:

```text
emp/
```

Then run:

```bash
python3 compare_transcriptions.py
```

---

# Comparison Methodology

## Text Normalization

Before comparison, the algorithm normalizes the transcription text.

It removes elements such as:

```text
[00:16]
[02:53]
Speaker 1:
Speaker 2:
```

It also:

* Converts text to lowercase
* Normalizes whitespace
* Removes punctuation
* Normalizes apostrophes
* Preserves Unicode characters

For example:

```text
[00:16] Speaker 1: Hello, how are you?
```

becomes:

```text
hello how are you
```

---

# Word Error Rate

The primary word-level evaluation metric is **Word Error Rate (WER)**.

```text
WER = (S + D + I) / N
```

Where:

```text
S = Substitutions
D = Deletions
I = Insertions
N = Number of words in the OPEN reference
```

The OPEN transcription is treated as the reference, while the EMP transcription is evaluated against it.

---

# Transcription Accuracy

Accuracy is derived from WER:

```text
Accuracy = (1 - WER) × 100
```

For example:

```text
WER = 0.08

Accuracy = 92%
```

If WER exceeds 100%, the reported accuracy is limited to:

```text
0%
```

---

# Text Similarity

The algorithm also calculates sequence-based text similarity using Python's:

```python
difflib.SequenceMatcher
```

The result is reported as a percentage.

For example:

```text
Text Similarity: 94.52%
```

Text similarity and WER measure different aspects of the comparison and should be considered together.

---

# Error Analysis

The algorithm identifies:

### Substitutions

A word in EMP differs from the corresponding word in OPEN.

```text
OPEN: I need a doctor
EMP:  I need the doctor
```

### Deletions

A word from OPEN is missing in EMP.

```text
OPEN: I need a doctor
EMP:  I need a
```

### Insertions

EMP contains an additional word.

```text
OPEN: I need a doctor
EMP:  I really need a doctor
```

---

# Duplicate Detection

The algorithm checks whether the EMP transcription appears to contain the OPEN transcription more than once.

This can identify cases where a transcription system accidentally repeats the same conversation.

Such files are marked:

```text
DUPLICATED
```

---

# Accuracy Classification

The current classification system is:

|           Accuracy | Classification |
| -----------------: | -------------- |
|              ≥ 95% | EXCELLENT      |
|              ≥ 90% | VERY GOOD      |
|              ≥ 80% | GOOD           |
|              ≥ 70% | FAIR           |
|              ≥ 50% | POOR           |
|              < 50% | VERY POOR      |
| Duplicate detected | DUPLICATED     |

These thresholds can be modified according to the requirements of a particular evaluation project.

---

# Output

After execution, the algorithm creates:

```text
comparison_results/
```

The resulting structure will look like:

```text
TM-TRANS-COMP-v1/
│
├── compare_transcriptions.py
├── LICENSE
├── README.md
│
├── open/
│   ├── open_audio_001.json
│   └── ...
│
├── emp/
│   ├── emp_audio_001.json
│   └── ...
│
└── comparison_results/
    ├── comparative_report.csv
    ├── text_differences.csv
    ├── overall_summary.csv
    └── .analysis_provenance
```

---

# Generated Reports

## `comparative_report.csv`

Contains the comparison results for every matched file.

It includes information such as:

```text
file_id
open_file
emp_file
open_words
emp_words
word_count_difference
word_ratio
wer_percent
accuracy_percent
text_similarity_percent
substitutions
deletions
insertions
duplicated
status
```

---

## `text_differences.csv`

Contains the normalized OPEN and EMP text along with detected textual differences.

This can be used for detailed investigation of individual transcription mismatches.

---

## `overall_summary.csv`

Contains aggregate results across all compared files, including:

```text
files_compared
total_open_words
total_emp_words
word_count_difference
emp_open_word_ratio
overall_wer_percent
overall_accuracy_percent
average_file_accuracy_percent
average_text_similarity_percent
duplicated_files
```

---

# Provenance & Attribution

This algorithm contains embedded authorship/provenance information:

```text
TM-TRANS-COMP™
© Tirtha Mukherjee
https://github.com/Tirtha6312
```

The algorithm identifier is:

```text
TM-TRANS-COMP-v1
```

The attribution information is embedded and encoded within the source code.

A SHA-256 integrity check is performed before the main comparison algorithm executes.

---

# Integrity / Tamper Detection

The program verifies the integrity of the embedded provenance information before running the comparison.

If the protected attribution information is removed or modified, the integrity verification fails and execution terminates.

Example:

```text
ERROR: ALGORITHM INTEGRITY VERIFICATION FAILED

The embedded authorship/provenance information
has been removed or modified.

Execution has been terminated.
```

This mechanism is intended to provide attribution and detect straightforward modifications to the embedded provenance information.

It is **not intended to provide unbreakable DRM or prevent determined reverse engineering**.

---

# Important

### The `open/` and `emp/` folders are not included with this repository.

Anyone using this algorithm must create them manually and provide their own JSON transcription files.

Required:

```text
open/
emp/
```

Without these folders and the corresponding JSON files, the comparison cannot be performed.

---

# Example

Suppose you have:

```text
open/
├── open_audio_001.json
└── open_audio_002.json
```

and:

```text
emp/
├── emp_audio_001.json
└── emp_audio_002.json
```

The algorithm performs:

```text
open_audio_001.json
        ↕
emp_audio_001.json

open_audio_002.json
        ↕
emp_audio_002.json
```

and produces a comparative report containing accuracy, WER, similarity, errors, and duplication status.

---

# Requirements

Python 3.x is required.

The algorithm uses Python standard-library modules including:

```text
os
json
re
csv
sys
base64
hashlib
difflib
```

No external Python packages are required.

---

# License

This project is released under the **MIT License**.

See:

```text
LICENSE
```

for the complete license terms.

---

# Author

**Tirtha Mukherjee**

GitHub:

https://github.com/Tirtha6312

Repository:

https://github.com/Tirtha6312/TM-TRANS-COMP-v1

---

## TM-TRANS-COMP-v1™

**Transcription Comparative Analysis & Evaluation**

© 2026 Tirtha Mukherjee
