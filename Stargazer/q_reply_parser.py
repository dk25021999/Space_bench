#This creates question answer pairs from the replies to a stargazer post
import re
import glob

def extract_qa_pairs(text):
    # Normalize line endings
    text = text.replace("\r\n", "\n").strip()

    # Pattern for question headers like "43.   Stability of Lagrangian Points"
    question_pattern = re.compile(
        r"\n*(\d+)\.\s+(.*?)\n",
        re.DOTALL
    )

    # Find all question headers
    matches = list(question_pattern.finditer(text))

    qa_pairs = []

    for i, match in enumerate(matches):
        q_number = match.group(1)
        q_title = match.group(2).strip()

        # Determine text span for this question block
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()

        # Split question and answer using "Reply"
        if "Reply" in block:
            question_text, answer_text = block.split("Reply", 1)
        else:
            # Fallback if "Reply" missing
            question_text = block
            answer_text = ""

        qa_pairs.append({
            "id": int(q_number),
            "title": q_title,
            "question": question_text.replace("\n", " ").strip(),
            "answer": answer_text.replace("\n", " ").strip()
        })

    return qa_pairs



for file_path in glob.glob("spaceflight_answers/*.txt"):
    with open(file_path, "r") as f:
        text = f.read()
        qa_pairs = extract_qa_pairs(text)
        # print(len(text.split("Before you do, though, please read the instructions")))
        with open('Q_A/' + file_path.split('/')[-1], 'w') as out_f:
            out_f.write(str(qa_pairs))
            # for pair in qa_pairs:
            #     out_f.write(f"Q: {pair['question']}\nA: {pair['answer']}\n\n")
        # print(f"File: {file_path}, Extracted Q&A pairs: {len(qa_pairs)}")