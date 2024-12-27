import asyncio
from typing import Any, Dict

import streamlit as st
from dotenv import load_dotenv
from gpt_researcher import GPTResearcher
from gpt_researcher.prompts import get_prompt_by_report_type
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# アプリのタイトルを設定
st.title("GPT Researcher with Amazon Nova")


class CustomLogsHandler:
    """
    カスタムログハンドラー

    Attributes:
        logs (list): ログを保存するためのリスト。
    """

    def __init__(self):
        self.logs = []  # ログを保存するリストを初期化

    async def send_json(self, data: Dict[str, Any]) -> None:
        """
        ログデータを処理します。

        Args:
            data (Dict[str, Any]): ログデータ
        """
        self.logs.append(data)  # データをログに追加

        # Streamlitのサイドバーにデータを表示
        expander_label = data["content"] if "content" in data else "Log..."
        with st.sidebar:
            with st.expander(expander_label, expanded=False):
                st.write(data)


# カスタムログハンドラーのインスタンスを作成
custom_logs_handler = CustomLogsHandler()


async def get_report(query: str, report_type: str):
    """
    クエリとレポートタイプに基づいてレポートを生成します。

    Args:
        query (str): ユーザーが入力したクエリ。
        report_type (str): レポートの種類。

    Returns:
        Tuple: レポート、研究コンテキスト、コスト、画像、ソース情報を含むタプル。
    """

    # GPTResearcherを初期化
    researcher = GPTResearcher(
        query,
        report_type,
        websocket=custom_logs_handler,
    )
    researcher.set_verbose(True)  # 詳細なログを有効にする

    # researchを実行
    research_result = await researcher.conduct_research()

    # 追加情報を取得
    research_context = researcher.get_research_context()
    research_costs = researcher.get_costs()
    research_images = researcher.get_research_images()
    research_sources = researcher.get_research_sources()

    return None, research_context, research_costs, research_images, research_sources


async def main():
    """
    メイン処理関数。ユーザー入力を受け取り、結果を表示します。
    """

    # ユーザー入力フォームを作成
    query = st.text_input("Enter your query:")
    start_button = st.button("スタート")

    # クエリが入力され、ボタンが押された場合
    if query and start_button:
        report_type = "research_report"  # レポートタイプを指定

        with st.spinner("処理中です..."):
            # レポート生成処理を実行
            report, context, costs, images, sources = await get_report(
                query, report_type
            )

        # レポート生成のプロンプトを取得
        generate_prompt = get_prompt_by_report_type(report_type)

        # プロンプトを作成
        content = generate_prompt(
            query,
            context,
            sources,
            report_format="APA",
            tone=None,
            total_words=1000,
            language="Japanese",
        )

        # チェーンを設定して出力をストリーム表示
        chain = ChatBedrockConverse(model="amazon.nova-lite-v1:0") | StrOutputParser()

        st.write_stream(chain.stream([HumanMessage(content=content)]))


# 非同期処理を実行
asyncio.run(main())
