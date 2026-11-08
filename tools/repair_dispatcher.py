# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.abspath("."))
import tools.extend_morning_campaign_batches as ext

def repair():
    with open("tools/zcode_continuous_dispatcher.py", "r", encoding="utf-8") as f:
        text = f.read()

    # Locate corruption between 0043 and batch_1930
    idx_0043 = text.find('"0043"')
    idx_1930 = text.find('"batch_1930"')
    if idx_0043 == -1 or idx_1930 == -1:
        print("Could not find anchor indices")
        sys.exit(1)

    # find line break after 0043 line
    idx_newline = text.find("\n", idx_0043)
    # find the comment line before batch_1930
    idx_comment_1930 = text.rfind("# ----------------", idx_0043, idx_1930)

    clean_closing = """
        ]
    },
    """
    repaired_prefix = text[:idx_newline] + clean_closing + text[idx_comment_1930:]

    # Now append morning batches to the end of TASK_BATCHES
    pos_log = repaired_prefix.find("def log(msg: str)")
    pos_bracket = repaired_prefix.rfind("]", 0, pos_log)

    batch_blocks = []
    for bid, btime, tinfo in ext.batches:
        batch_blocks.append(ext.build_batch(bid, btime, tinfo))

    new_batches_str = ",\n" + ",\n".join(batch_blocks) + "\n"
    final_text = repaired_prefix[:pos_bracket] + new_batches_str + repaired_prefix[pos_bracket:]

    with open("tools/zcode_continuous_dispatcher.py", "w", encoding="utf-8") as f:
        f.write(final_text)

    print("Successfully repaired and appended morning campaign batches!")

if __name__ == "__main__":
    repair()
