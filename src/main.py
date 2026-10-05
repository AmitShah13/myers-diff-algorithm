"""Myers' O(ND) diff: line diff (Part A) and changed-character ranges (Part B).

The diff core operates on arbitrary hashable sequences. The CLI uses it for
line-level diffs over raw bytes and character-level diffs over strings.
"""

# sys gives us access to command-line arguments and standard input/output streams.
import sys


# This helper reads the input file exactly as bytes so the line diff preserves the original data.
def read_lines(path):
    """Read a file as raw bytes and split it into logical lines."""
# Open in binary mode: this avoids changing newline/encoding details before the diff runs.
    with open(path, "rb") as f:
# split() creates one sequence element per logical line; Myers will compare these elements.
        lines = f.read().split(b"\n")

# A file ending with '\n' has no extra logical line after that newline, so remove the empty item.
    # A trailing newline does not represent an additional logical line.
# Check that the list is non-empty before looking at its last element.
    if lines and not lines[-1]:
        lines.pop()

    return lines


# Myers works on two sequences. This function finds the central matching 'snake' that splits the problem.
def middle_snake(A, B, Ar, Br, n, m):
    """Find the middle snake in the Myers edit graph.

    Returns:
        (sx, sy, ex, ey)

    representing the snake from (sx, sy) to (ex, ey).

    A/B and Ar/Br contain one sentinel element beyond their logical bounds.
    """
# delta is the difference between the two sequence lengths; it determines how the two searches meet.
    delta = n - m
# The parity of delta tells Myers whether the forward/backward searches can overlap on this iteration.
    odd = delta & 1

# We only need to search up to half the total edit-graph depth to find the middle.
    max_d = (n + m + 1) // 2
# offset converts a diagonal number k, which may be negative, into a valid Python list index.
    offset = max_d + 1
# size gives enough space for every diagonal that can be reached by the search.
    size = 2 * max_d + 3

# vf[k] stores the furthest x-position reached by the forward search on diagonal k.
    # Furthest x reached on each diagonal.
# Start every forward diagonal as unreachable; -1 is our sentinel for 'not visited'.
    vf = [-1] * size
# vb does the same job for the backward search.
    vb = [-1] * size

# The first forward point is the origin of the edit graph.
    vf[offset + 1] = 0
# The backward search starts from the opposite side using the same diagonal representation.
    vb[offset + 1] = 0

# These boundaries remember diagonals that have become invalid, reducing unnecessary work.
    # Active diagonal boundaries.
    fs = fe = bs = be = 0

# d is the current number of edits being considered. Myers increases it one layer at a time.
    for d in range(max_d + 1):
        # ---------------------------------------------------------------
        # Forward search
        # ---------------------------------------------------------------
# Only diagonals reachable at edit distance d are considered.
        start = -d + fs
        end = d - fe

# A diagonal changes by 2 each layer, so only every second k is reachable.
        for k in range(start, end + 1, 2):
# Convert diagonal k into the array slot used by vf.
            idx = offset + k

# Choose the predecessor that gives the furthest possible x position.
            if k == -d or (k != d and vf[idx - 1] < vf[idx + 1]):
# Moving down means inserting an element from B.
                # Insertion: move down.
# Reuse the furthest x already reached on the neighboring diagonal.
                x = vf[idx + 1]
            else:
# Moving right means deleting an element from A.
                # Deletion: move right.
# A deletion consumes one element from A, so x advances by one.
                x = vf[idx - 1] + 1

# On diagonal k, y is determined by x-k; this converts graph coordinates back to sequence indices.
            y = x - k
# Save the point before walking through equal elements; this is the start of the snake.
            x0 = x
# Save y for the same reason.
            y0 = y

# A snake is a maximal run of matching elements, so follow equal items for free.
            # Follow the snake.
# Matching elements do not cost an edit, so both sequence positions can advance together.
            while x < n and y < m and A[x] == B[y]:
                x += 1
                y += 1

# Record the furthest x reached after taking the edit and then following its snake.
            vf[idx] = x

# If the search moved beyond A, this diagonal can no longer produce a valid path.
            # Remove diagonals that have left the edit graph.
            if x > n:
                fe += 2
                continue

            if y > m:
                fs += 2
                continue

# When delta is odd, the two searches can meet between layers in a way that must be checked here.
            # For odd delta, the forward and backward searches can overlap.
# Only odd-length differences use this overlap condition in the forward phase.
            if odd:
# Convert the forward diagonal into the corresponding backward diagonal.
                kb = delta - k
# The backward diagonal must be inside the currently explored band.
                if -d < kb < d:
# Look up how far the backward search reached on that diagonal.
                    xb = vb[offset + kb]
# If the two paths touch/cross, the middle snake has been found.
                    if xb != -1 and x + xb >= n:
# Return the snake coordinates in the original forward coordinate system.
                        return x0, y0, x, y

# Now perform the symmetric search from the end of the sequences.
        # ---------------------------------------------------------------
        # Backward search
        # ---------------------------------------------------------------
# Restrict the backward search to diagonals reachable at this edit depth.
        start = -d + bs
        end = d - be

# Again, only every second diagonal is reachable at a given d.
        for k in range(start, end + 1, 2):
            idx = offset + k

# Choose the predecessor that lets the backward search reach furthest toward the start.
            if k == -d or (k != d and vb[idx - 1] < vb[idx + 1]):
# Move along the neighboring diagonal when that gives the better x-position.
                x = vb[idx + 1]
            else:
# Otherwise consume one element from the reverse side, corresponding to a deletion.
                x = vb[idx - 1] + 1

# Recover y from the diagonal number, just like in the forward search.
            y = x - k
# Save the starting x-position of this reverse snake.
            x0 = x
# Save the starting y-position as well.
            y0 = y

# In the reversed sequences, equal items form the same kind of zero-cost snake.
            # Follow the reverse snake.
# Continue while the reverse sequences still contain matching elements.
            while x < n and y < m and Ar[x] == Br[y]:
                x += 1
                y += 1

# Store the furthest reverse x reached on this diagonal.
            vb[idx] = x

            if x > n:
                be += 2
                continue

            if y > m:
                bs += 2
                continue

# For even delta, the forward and backward searches overlap on the same edit layer.
            # For even delta, check overlap with the forward search.
# This overlap test is therefore needed only when delta is even.
            if not odd:
# Translate the backward diagonal into the matching forward diagonal.
                kf = delta - k

# Check whether the corresponding forward diagonal is inside the explored band.
                if -d <= kf <= d:
# Retrieve the furthest x reached by the forward search.
                    xf = vf[offset + kf]
# If forward + backward progress covers the sequence, the searches have met.
                    if xf != -1 and xf + x >= n:
# Convert the reverse coordinates back to the original sequence coordinates.
                        return n - x, m - y, n - x0, m - y0

    raise RuntimeError("middle snake not found")


# Compute the actual minimal set of deletions from a and insertions into b.
def diff_marks(a, b):
    """Compute a minimal Myers diff.

    Returns:
        del_a:
            bytearray marking elements deleted from ``a``.

        ins_b:
            bytearray marking elements inserted into ``b``.

    A value of 1 means the element participates in an edit.
    A value of 0 means it is matched.
    """
# Store the lengths once because they are used several times when creating result arrays.
    na = len(a)
    nb = len(b)

# Map every distinct sequence item to a compact integer so comparisons are cheaper and consistent.
    # Assign a compact integer ID to every distinct item.
# Dictionary: original item -> compact integer ID.
    ids = {}
# ia will contain the integer representation of sequence a.
    ia = []
# ib will contain the integer representation of sequence b.
    ib = []

# Process every item in the first sequence.
    for item in a:
# Reuse an existing ID when this item has already been seen.
        value = ids.get(item)
        if value is None:
# If this is a new item, assign the next unused compact ID.
            value = len(ids)
# Store the new ID so later occurrences get exactly the same value.
            ids[item] = value
# Append the compact representation used by the Myers algorithm.
        ia.append(value)

# Do the same ID conversion for the second sequence.
    for item in b:
        value = ids.get(item)
        if value is None:
            value = len(ids)
            ids[item] = value
        ib.append(value)

# An item that appears in only one sequence cannot be part of an equal matching snake.
    # Items occurring in only one sequence can never be part of a match.
# Set of IDs that occur anywhere in A.
    in_a = set(ia)
# Set of IDs that occur anywhere in B.
    in_b = set(ib)

# Keep only positions from A whose values also exist somewhere in B.
    ma = [i for i, value in enumerate(ia) if value in in_b]
# Keep only positions from B whose values also exist somewhere in A.
    mb = [j for j, value in enumerate(ib) if value in in_a]

# Build the filtered A sequence containing only potentially matching items.
    fa = [ia[i] for i in ma]
# Build the corresponding filtered B sequence.
    fb = [ib[j] for j in mb]

# These marks describe edits in the filtered A sequence; 1 means deleted.
    del_f = bytearray(len(fa))
# These marks describe edits in the filtered B sequence; 1 means inserted.
    ins_f = bytearray(len(fb))

# Each stack entry describes one subproblem: A[a0:a1] must be transformed into B[b0:b1].
    # Each tuple represents:
    #   [a0:a1] -> [b0:b1]
# Initially the entire filtered sequences form one subproblem.
    stack = [(0, len(fa), 0, len(fb))]

# Process subproblems until every region has been resolved.
    while stack:
# Pop one region to solve. Splitting creates smaller regions that are pushed back later.
        a0, a1, b0, b1 = stack.pop()

# First remove the part that is already equal at the beginning.
        # ---------------------------------------------------------------
        # Strip common prefix.
        # ---------------------------------------------------------------
# A common prefix needs no edit, so advance both boundaries together.
        while a0 < a1 and b0 < b1 and fa[a0] == fb[b0]:
            a0 += 1
            b0 += 1

# Then remove the common suffix for the same reason.
        # ---------------------------------------------------------------
        # Strip common suffix.
        # ---------------------------------------------------------------
# Matching suffix elements also need no edits, so shrink both ends.
        while a0 < a1 and b0 < b1 and fa[a1 - 1] == fb[b1 - 1]:
            a1 -= 1
            b1 -= 1

# If A has nothing left, every remaining B element must be inserted.
        # Everything on B is an insertion.
# This condition means the current A subproblem is empty.
        if a0 == a1:
# Only mark B when there is actually something remaining.
            if b0 < b1:
# Mark every remaining B position as an insertion.
                ins_f[b0:b1] = b"\x01" * (b1 - b0)
            continue

# Symmetrically, if B is empty, everything remaining in A is deleted.
        # Everything on A is a deletion.
# This condition means the current B subproblem is empty.
        if b0 == b1:
# Mark every remaining A position as a deletion.
            del_f[a0:a1] = b"\x01" * (a1 - a0)
            continue

# The unresolved middle must now be split using Myers' middle snake.
        # ---------------------------------------------------------------
        # Solve the remaining problem using the middle snake.
        # ---------------------------------------------------------------
# Copy the current A subproblem so the middle-snake routine receives a local sequence.
        A = fa[a0:a1]
# Copy the current B subproblem for the same reason.
        B = fb[b0:b1]

# n is the number of unresolved elements in this A subproblem.
        n = a1 - a0
# m is the number of unresolved elements in this B subproblem.
        m = b1 - b0

# Reverse A because the backward Myers search works from the end.
        Ar = A[::-1]
# Reverse B for the corresponding backward search.
        Br = B[::-1]

# Add sentinel values so boundary comparisons inside middle_snake remain safe.
        # Sentinel values allow the middle-snake implementation to safely
        # perform comparisons at the logical boundary.
# Sentinel for the forward A sequence.
        A.append(-1)
# A different sentinel keeps the artificial boundary values distinct.
        B.append(-2)
        Ar.append(-1)
        Br.append(-2)

# Find the central matching snake that divides this subproblem into two smaller ones.
        sx, sy, ex, ey = middle_snake(A, B, Ar, Br, n, m)

# Push the right half first so the left half is popped and processed next (LIFO stack behavior).
        # Push right side first so that the left side is processed next.
        stack.append(
            (
                a0 + ex,
                a1,
                b0 + ey,
                b1,
            )
        )
# Push the left half; this is the next subproblem the stack will normally process.
        stack.append(
            (
                a0,
                a0 + sx,
                b0,
                b0 + sy,
            )
        )

# Initially assume every original element is changed; filtered matching positions will overwrite this.
    # Start with everything marked as changed. Only elements that survived
    # the filtered Myers search are then replaced with their actual status.
# 1 means deleted, so start every A position as deleted.
    del_a = bytearray(b"\x01") * na
# 1 means inserted, so start every B position as inserted.
    ins_b = bytearray(b"\x01") * nb

# Map the filtered deletion results back to the original A indices.
    for filtered_index, original_index in enumerate(ma):
# Copy the precise Myers result into the original-position result array.
        del_a[original_index] = del_f[filtered_index]

# Map the filtered insertion results back to the original B indices.
    for filtered_index, original_index in enumerate(mb):
# Copy the precise insertion status into the original-position result array.
        ins_b[original_index] = ins_f[filtered_index]

# Return one deletion mask for A and one insertion mask for B.
    return del_a, ins_b


# Convert consecutive edit marks into compact start-end ranges for human-readable output.
def ranges(marks):
    """Convert a 0/1 bytearray into ``start-end,...`` ranges.

    Returns ``.`` when no elements are marked.
    """
# Number of elements in the mask.
    n = len(marks)
# Store each discovered range before joining them at the end.
    parts = []

# Find the first changed element; find() avoids scanning manually from index 0.
    start = marks.find(1)

# Continue until there are no more marked elements.
    while start != -1:
# The next zero marks the end of the current contiguous changed range.
        end = marks.find(0, start)

# If there is no zero, the changed range continues to the end.
        if end == -1:
# The logical end is the sequence length.
            end = n

# Save the range using the required start-end representation.
        parts.append(f"{start}-{end}")

# Once the end reaches n, there cannot be another range.
        if end >= n:
            break

# Search for the next changed position after the current range.
        start = marks.find(1, end)

    return ",".join(parts) if parts else "."


# Build the final line-based diff, optionally adding character-level highlight markers.
def build_output(a, b, del_a, ins_b, highlight):
    """Build the textual diff output.

    Deletes are emitted before inserts, matching the original behavior.
    """
# Store the lengths because they control the output traversal.
    na = len(a)
    nb = len(b)

# Accumulate output lines here instead of printing each line immediately.
    out = []
# i tracks A and j tracks B while walking through unchanged and changed regions.
    i = j = 0

# Continue until both input sequences have no remaining edits.
    while True:
# Locate the next deletion in A from the current A position.
        next_delete = del_a.find(1, i)
# Locate the next insertion in B from the current B position.
        next_insert = ins_b.find(1, j)

        if next_delete == -1 and next_insert == -1:
            break

# Start by assuming all remaining A elements are unchanged.
        # Number of unchanged lines before the next edit.
# Compute the maximum possible unchanged count before the next A edit.
        count = na - i

# If A has a deletion, it limits how far the unchanged region can extend.
        if next_delete != -1:
            count = min(count, next_delete - i)

# If B has an insertion, it also limits how far the unchanged region can extend.
        if next_insert != -1:
            count = min(count, next_insert - j)

# Only emit an unchanged block when at least one line is available.
        if count:
# Add unchanged lines to the output list.
            out.extend(
                b" " + line
                for line in a[i:i + count]
            )
# Advance both sides by the same number of unchanged lines.
            i += count
            j += count

# The next section consumes one contiguous deletion/insertion block.
        # ---------------------------------------------------------------
        # Consume one contiguous edit block.
        # ---------------------------------------------------------------
# Find where the current deletion block ends.
        delete_end = del_a.find(0, i)
        if delete_end == -1:
            delete_end = na

# Find where the current insertion block ends.
        insert_end = ins_b.find(0, j)
        if insert_end == -1:
            insert_end = nb

# Extract the old lines participating in this edit block.
        deleted = a[i:delete_end]
# Extract the new lines participating in this edit block.
        inserted = b[j:insert_end]

# The original behavior emits deletions before insertions.
        out.extend(b"-" + line for line in deleted)

# In normal 'lines' mode, output the inserted lines without character markers.
        if not highlight:
            out.extend(b"+" + line for line in inserted)
        else:
# In highlight mode, pair old/new lines so their changed characters can be analyzed.
            paired = min(len(deleted), len(inserted))

# Emit every inserted line; the following '?' line explains character changes where possible.
            for index, line in enumerate(inserted):
                out.append(b"+" + line)

# Only paired old/new lines can have a character-level comparison.
                if index < paired:
# Decode bytes back to text while preserving undecodable bytes through surrogateescape.
                    old = deleted[index].decode(
                        "utf-8",
                        "surrogateescape",
                    )
# Decode the corresponding new line using the same lossless strategy.
                    new = line.decode(
                        "utf-8",
                        "surrogateescape",
                    )

# Myers is reused at character level to identify deleted/inserted character positions.
                    deleted_marks, inserted_marks = diff_marks(old, new)

# Format those character masks into the assignment's human-readable marker.
                    marker = (
                        f"? {ranges(deleted_marks)} | "
                        f"{ranges(inserted_marks)}"
                    ).encode("utf-8")

# Add the character-range explanation immediately after the new line.
                    out.append(marker)

# Continue scanning after this complete edit block.
        i = delete_end
        j = insert_end

# After all edits, emit any unchanged lines remaining at the end.
    # Remaining unchanged tail.
# Check whether A still has an unchanged tail.
    if i < na:
# Prefix each remaining line with a space to represent 'unchanged'.
        out.extend(b" " + line for line in a[i:])

    return out


# This is the command-line entry point used by the operating system.
def main():
    """CLI entry point."""
# The program expects exactly: command, old-file path, new-file path.
    if len(sys.argv) != 4:
# Print the correct command format to stderr when the user supplied bad arguments.
        print(
            "usage: main.py lines|highlight A_PATH B_PATH",
            file=sys.stderr,
        )
        return 2

# Read whether the user requested normal line diff or character highlighting.
    command = sys.argv[1]

# Only the two supported modes are valid.
    if command not in ("lines", "highlight"):
# Report the valid syntax instead of continuing with an unknown command.
        print(
            "usage: main.py lines|highlight A_PATH B_PATH",
            file=sys.stderr,
        )
        return 2

    try:
# Read the old file as raw lines.
        a = read_lines(sys.argv[2])
# Read the new file as raw lines.
        b = read_lines(sys.argv[3])
# File access can fail because of a missing file, permissions, etc.
    except OSError as exc:
# Report the operating-system error clearly to the user.
        print(
            f"error: cannot read file: {exc}",
            file=sys.stderr,
        )
        return 2

# Compute the minimal Myers edit masks that drive the final output.
    del_a, ins_b = diff_marks(a, b)

    output = build_output(
        a,
        b,
        del_a,
        ins_b,
        command == "highlight",
    )

# Only write to stdout when there is something to print.
    if output:
# Join output records with newlines and add the final newline expected by CLI tools.
        sys.stdout.buffer.write(b"\n".join(output) + b"\n")
# Flush the buffered binary stdout so the complete result is delivered immediately.
        sys.stdout.buffer.flush()

# Return zero to indicate successful execution.
    return 0


# Run main() only when this file is executed directly, not when imported as a module.
if __name__ == "__main__":
# Convert main's return code into the process exit status.
    raise SystemExit(main())