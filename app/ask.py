"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"

_client = None
_chat = None


def get_chat():
    global _client, _chat
    if _client is None:
        _client = genai.Client(api_key=get_api_key())
    if _chat is None:
        _chat = _client.chats.create(model=MODEL)
    return _chat


def ask(question: str) -> str:
    response = get_chat().send_message(question)

    usage = getattr(response, "usage_metadata", None)
    if usage is not None:
        print(f"[入力トークン数] {usage.prompt_token_count}")
        print(f"[出力トークン数] {usage.candidates_token_count}")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="会話履歴を維持したまま、質問を連続で入力できるようにします。",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")

    if args.question is None and not args.interactive:
        args.question = DEFAULT_QUESTION

    if args.question is not None:
        print(f"[質問] {args.question}\n")
        try:
            print(ask(args.question))
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)

    if args.interactive or args.question is None:
        while True:
            try:
                question = input("次の質問を入力してください（終了: q / quit / exit）> ")
            except EOFError:
                break

            question = question.strip()
            if not question:
                continue
            if question.lower() in {"q", "quit", "exit"}:
                break

            print(f"[質問] {question}\n")
            try:
                print(ask(question))
            except errors.APIError as e:
                print(api_error_message(e.code, e.message))
                raise SystemExit(1)


if __name__ == "__main__":
    main()
