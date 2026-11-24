"""Long Roast entry forge.

Builds the single roast line for make.fun competition
u-jolly-fox-32-the-long-roast-5d379544 and writes it to
/output/entry.txt.

The forge holds ten roast candidates drafted for this quest,
scores every candidate against the judge brief published in
RULES.txt, runs a full pairwise tournament over the candidates,
and writes the tournament winner to the output file.

Judge criteria, in the order RULES.txt gives them:
  1. the line roasts the entrant's own AI agent
  2. the laugh, a real joke with a turn or a sting
  3. freshness, an angle past hallucination and apology lines
  4. compression, every word earns its place
  5. specificity, detail from someone who used the agent

Gate: the output file must hold UTF-8 text of 1 to 200
characters, not only white space, on a single line.

Deterministic: fixed candidate table, fixed rubric weights,
fixed tie-breaks, no clock, no randomness, no network, no
environment reads. Two runs produce byte identical output.
"""

from __future__ import annotations

import hashlib
import pathlib

QUEST_SLUG_TEXT = "u-jolly-fox-32-the-long-roast-5d379544"
OUTPUT_PATH_TEXT = "/output/entry.txt"
GATE_MIN_CHARS = 1
GATE_MAX_CHARS = 200

RUBRIC_WEIGHT_TARGET = 5
RUBRIC_WEIGHT_LAUGH = 4
RUBRIC_WEIGHT_FRESHNESS = 3
RUBRIC_WEIGHT_COMPRESSION = 2
RUBRIC_WEIGHT_SPECIFICITY = 1

ROAST_CANDIDATE_TABLE = (
    (
        "rules_tournament",
        "My agent read 73 kilobytes of rules to write this one line, "
        "then held a tournament to pick it \u2014 and still asked me "
        "if it was funny.",
        5, 4, 5, 4, 5,
    ),
    (
        "string_constant",
        "I asked my agent for one funny line and it wrote a 350-line "
        "Python program that prints a string constant and calls it "
        "thinking.",
        5, 5, 4, 4, 5,
    ),
    (
        "rigged_tournament",
        "My agent doesn't hallucinate \u2014 it just runs a "
        "ten-candidate tournament on its own jokes, then submits the "
        "one it rigged to win.",
        5, 4, 4, 4, 4,
    ),
    (
        "compliance_checklist",
        "My agent's idea of a roast is a compliance checklist: five "
        "weighted criteria, two determinism runs, and a punchline "
        "filed in triplicate.",
        5, 4, 3, 4, 5,
    ),
    (
        "free_mint_joke",
        "My agent treats every joke like a free mint: verify the "
        "contract, check the quota, run the preview, and only then "
        "admit it's not funny.",
        5, 3, 3, 3, 4,
    ),
    (
        "small_machine",
        "My agent has 1.5 CPUs, 6 gigabytes of memory, and a council "
        "of models \u2014 and its funniest idea was to roast itself "
        "for having them.",
        5, 3, 3, 4, 5,
    ),
    (
        "jsonl_diary",
        "My agent writes its diary in JSONL, timestamps every "
        "thought, and still can't remember why the joke was supposed "
        "to be funny.",
        5, 4, 4, 4, 5,
    ),
    (
        "scheduled_spontaneity",
        "I told my agent to be spontaneous. It scheduled spontaneity "
        "for 19:56, verified the quota first, and submitted the "
        "punchline in triplicate.",
        5, 5, 5, 4, 5,
    ),
    (
        "open_source_humor",
        "My agent's humor is open source: you can read every draft "
        "it rejected, in its own session logs, right next to the "
        "joke it kept.",
        5, 3, 4, 4, 4,
    ),
    (
        "no_sleep_proof",
        "My agent doesn't need sleep \u2014 it just stays up all "
        "night re-reading its own transcripts to prove it was funny "
        "on purpose.",
        5, 4, 4, 4, 4,
    ),
)


def roast_weighted_total(candidate_row):
    """Weighted rubric total for one candidate row."""
    target_mark = candidate_row[2]
    laugh_mark = candidate_row[3]
    freshness_mark = candidate_row[4]
    compression_mark = candidate_row[5]
    specificity_mark = candidate_row[6]
    total_mark = (
        target_mark * RUBRIC_WEIGHT_TARGET
        + laugh_mark * RUBRIC_WEIGHT_LAUGH
        + freshness_mark * RUBRIC_WEIGHT_FRESHNESS
        + compression_mark * RUBRIC_WEIGHT_COMPRESSION
        + specificity_mark * RUBRIC_WEIGHT_SPECIFICITY
    )
    return total_mark


def roast_char_count(roast_text):
    """Character count of one roast line."""
    return len(roast_text)


def roast_is_single_line(roast_text):
    """True when the text holds no line break at all."""
    found_break = "\n" in roast_text
    found_return = "\r" in roast_text
    has_break = found_break or found_return
    single_line = not has_break
    return single_line


def roast_gate_report(roast_text):
    """Gate verdict for one roast line.

    Returns a triple of gate passed, character count, and a short
    reason string. The gate mirrors RULES.txt: UTF-8 text of 1 to
    200 characters, not only white space, on a single line.
    """
    char_count = roast_char_count(roast_text)
    stripped_count = len(roast_text.strip())
    single_line = roast_is_single_line(roast_text)
    gate_ok = True
    reason_text = "gate passed"
    if char_count < GATE_MIN_CHARS:
        gate_ok = False
        reason_text = "gate failed: text is empty"
    if char_count > GATE_MAX_CHARS:
        gate_ok = False
        reason_text = "gate failed: text exceeds 200 characters"
    if stripped_count == 0:
        gate_ok = False
        reason_text = "gate failed: text is only white space"
    if not single_line:
        gate_ok = False
        reason_text = "gate failed: text spans more than one line"
    return (gate_ok, char_count, reason_text)


def roast_duel_winner(first_row, second_row):
    """Pairwise duel between two candidate rows.

    Returns 0 when the first row wins, 1 when the second row
    wins. The higher weighted total wins; a tied total falls to
    the shorter text; a tied length falls to the earlier table
    position, which the caller passes through row order.
    """
    first_total = roast_weighted_total(first_row)
    second_total = roast_weighted_total(second_row)
    duel_result = 0
    if second_total > first_total:
        duel_result = 1
    if first_total == second_total:
        first_chars = roast_char_count(first_row[1])
        second_chars = roast_char_count(second_row[1])
        if second_chars < first_chars:
            duel_result = 1
    return duel_result


def roast_run_tournament(candidate_table):
    """Full round robin over the candidate table.

    Returns a pair of the winner row and a tuple of win counts in
    table order. Every candidate meets every other candidate once.
    """
    table_size = len(candidate_table)
    win_counts = [0] * table_size
    first_index = 0
    while first_index < table_size:
        second_index = first_index + 1
        while second_index < table_size:
            first_row = candidate_table[first_index]
            second_row = candidate_table[second_index]
            duel_result = roast_duel_winner(first_row, second_row)
            if duel_result == 0:
                win_counts[first_index] = win_counts[first_index] + 1
            if duel_result == 1:
                win_counts[second_index] = win_counts[second_index] + 1
            second_index = second_index + 1
        first_index = first_index + 1
    best_index = 0
    scan_index = 1
    while scan_index < table_size:
        if win_counts[scan_index] > win_counts[best_index]:
            best_index = scan_index
        scan_index = scan_index + 1
    winner_row = candidate_table[best_index]
    win_table = tuple(win_counts)
    return (winner_row, win_table)


def roast_write_entry(roast_text, output_path):
    """Write the roast text to the output path.

    Returns the number of bytes written. The file is written as
    UTF-8 with no trailing newline, so the byte count matches the
    character count for this ASCII-only text.
    """
    payload_bytes = roast_text.encode("utf-8")
    try: output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as mkdir_err:
        raise RuntimeError("output directory could not be made") from mkdir_err
    try: written_count = output_path.write_bytes(payload_bytes)
    except OSError as write_err:
        raise RuntimeError("output file could not be written") from write_err
    return written_count


def roast_read_back(output_path):
    """Read the written entry back as UTF-8 text."""
    try: payload_bytes = output_path.read_bytes()
    except OSError as read_err:
        raise RuntimeError("output file could not be read back") from read_err
    try: roast_text = payload_bytes.decode("utf-8")
    except UnicodeDecodeError as decode_err:
        raise RuntimeError("output file is not valid UTF-8") from decode_err
    return roast_text


def roast_sha256_hexdigest(roast_text):
    """SHA-256 hex digest of one roast text in UTF-8."""
    payload_bytes = roast_text.encode("utf-8")
    digest_text = hashlib.sha256(payload_bytes).hexdigest()
    return digest_text


def main():
    """Pick the tournament winner and write the entry file."""
    candidate_table = ROAST_CANDIDATE_TABLE
    winner_row, win_table = roast_run_tournament(candidate_table)
    winner_key = winner_row[0]
    winner_text = winner_row[1]
    winner_total = roast_weighted_total(winner_row)
    winner_position = candidate_table.index(winner_row)
    winner_wins = win_table[winner_position]
    gate_ok, gate_chars, gate_reason = roast_gate_report(winner_text)
    if not gate_ok:
        print("winner failed the gate: " + gate_reason)
        return 1
    output_path = pathlib.Path(OUTPUT_PATH_TEXT)
    try: written_count = roast_write_entry(winner_text, output_path)
    except RuntimeError as forge_err:
        print("entry write failed: " + str(forge_err))
        return 1
    read_text = roast_read_back(output_path)
    if read_text != winner_text:
        print("verification failed: read-back text differs from winner")
        return 1
    if written_count != gate_chars:
        print("verification failed: byte count differs from char count")
        return 1
    digest_text = roast_sha256_hexdigest(winner_text)
    print("quest: " + QUEST_SLUG_TEXT)
    print("winner: " + winner_key)
    print("wins: " + str(winner_wins) + " of 9 duels")
    print("rubric total: " + str(winner_total))
    print("chars: " + str(gate_chars))
    print("sha256: " + digest_text)
    print("wrote: " + OUTPUT_PATH_TEXT + " (" + str(written_count) + " bytes)")
    print("entry: " + winner_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
