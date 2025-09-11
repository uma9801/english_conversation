import streamlit as st
import os
import time
from time import sleep
from pathlib import Path
from streamlit.components.v1 import html
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.schema import SystemMessage
from openai import OpenAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import functions as ft
import constants as ct
# 追加
import logging
from initialize import initialize


# 各種設定
load_dotenv()
st.set_page_config(
    page_title=ct.APP_NAME
)
# ログ取得を追加
logger = logging.getLogger(ct.LOGGER_NAME)


############################################################
# 追加：ログ用初期化処理
############################################################
try:
    initialize()
except Exception as e:
    logger.error(f"{ct.INITIALIZE_ERROR_MESSAGE}\n{e}")
    st.error("\n".join([ct.INITIALIZE_ERROR_MESSAGE, ct.COMMON_ERROR_MESSAGE]))
    st.stop()

# アプリ起動時のログ出力
if not "initialized" in st.session_state:
    st.session_state.initialized = True
    logger.info(ct.APP_BOOT_MESSAGE)


# タイトル表示
st.markdown(f"## {ct.APP_NAME}")

# 初期処理
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.start_flg = False
    st.session_state.pre_mode = ""
    st.session_state.shadowing_flg = False
    st.session_state.shadowing_button_flg = False
    st.session_state.shadowing_count = 0
    st.session_state.shadowing_first_flg = True
    st.session_state.shadowing_audio_input_flg = False
    st.session_state.shadowing_evaluation_first_flg = True
    st.session_state.dictation_flg = False
    st.session_state.dictation_button_flg = False
    st.session_state.dictation_count = 0
    st.session_state.dictation_first_flg = True
    st.session_state.dictation_chat_message = ""
    st.session_state.dictation_evaluation_first_flg = True
    st.session_state.chat_open_flg = False
    st.session_state.problem = ""
    
    st.session_state.openai_obj = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    st.session_state.llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=1.0)
    st.session_state.memory = ConversationSummaryBufferMemory(
        llm=st.session_state.llm,
        max_token_limit=1000,
        return_messages=True
    )

    # 英会話レベルの初期化
    st.session_state.pre_englv = ""

    # モード「日常英会話」用のChain作成 → englv反映の為に日常英会話の箇所で作成されるように変更
    # st.session_state.chain_basic_conversation = ft.create_chain(ct.SYSTEM_TEMPLATE_BASIC_CONVERSATION)

# 初期表示
# col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
# 提出課題用
col1, col2, col3, col4 = st.columns([2, 2, 3, 3])
with col1:
    if st.session_state.start_flg:
        st.button("英会話開始", use_container_width=True, type="primary")
    else:
        st.session_state.start_flg = st.button("英会話開始", use_container_width=True, type="primary")
with col2:
    st.session_state.speed = st.selectbox(label="再生速度", options=ct.PLAY_SPEED_OPTION, index=3, label_visibility="collapsed")
with col3:
    st.session_state.mode = st.selectbox(label="モード", options=[ct.MODE_1, ct.MODE_2, ct.MODE_3], label_visibility="collapsed")
    # モードを変更した際の処理。
    if st.session_state.mode != st.session_state.pre_mode:
        # フラグ処理を関数化して実施
        ft.reset_flags_on_mode_or_level_change()
        # 会話履歴（memory）をクリア
        st.session_state.memory = ConversationSummaryBufferMemory(
            llm=st.session_state.llm,
            max_token_limit=1000,
            return_messages=True
        )
        # 画面のチャット履歴をクリア
        st.session_state.messages = []

        st.session_state.pre_mode = st.session_state.mode
        st.rerun()
with col4:
    st.session_state.englv = st.selectbox(label="英語レベル", options=ct.ENGLISH_LEVEL_OPTION, label_visibility="collapsed")
    # 英会話レベルを変更した際の処理。
    if st.session_state.englv != st.session_state.pre_englv:
        # フラグ処理を関数化して実施
        ft.reset_flags_on_mode_or_level_change()

        st.session_state.pre_englv = st.session_state.englv
        st.rerun()


with st.chat_message("assistant", avatar="images/ai_icon.jpg"):
    st.markdown("生成AIが英会話練習をサポートします。繰り返し練習し、英語力をアップさせましょう！")
    st.markdown("**【操作説明】**")
    st.success("""
    - 再生速度・モード・英語レベルをお好みで選択し、「英会話開始」ボタンを押して英会話を始めましょう。
    - 途中でモードや英語レベルを変更した時は、改めて「英会話開始」ボタンを押して再開してください。
    - 発話後に、5秒間沈黙するか「発話終了」ボタンを押すと音声入力が完了します。
    """)
    st.markdown("**【モード説明】**")
    st.info("""
    - 「日常英会話」AIと音声会話ができ、適宜文法添削を行ってくれます。
    - 「シャドーイング」AIがランダムな英文を読み上げた後、それを真似て発話してください。AIが評価を行ってくれます。
    - 「ディクテーション」AIがランダムな英文を読み上げた後、画面下部のチャット欄から英文を真似て入力してください。AIが評価を行ってくれます。
    """)
# st.divider()

# メッセージリストの一覧表示
for message in st.session_state.messages:
    if message["role"] == "assistant":
        with st.chat_message(message["role"], avatar="images/ai_icon.jpg"):
            st.markdown(message["content"])
    elif message["role"] == "user":
        with st.chat_message(message["role"], avatar="images/user_icon.jpg"):
            st.markdown(message["content"])
    else:
        st.divider()

# LLMレスポンスの下部にモード実行のボタン表示
if st.session_state.shadowing_flg:
    st.session_state.shadowing_button_flg = st.button("シャドーイング開始")
if st.session_state.dictation_flg:
    st.session_state.dictation_button_flg = st.button("ディクテーション開始")

# 「ディクテーション」モードのチャット入力受付時に実行
if st.session_state.chat_open_flg:
    st.info("AIが読み上げた音声を、画面下部のチャット欄からそのまま入力・送信してください。")

st.session_state.dictation_chat_message = st.chat_input("※「ディクテーション」選択時以外は送信不可")

if st.session_state.dictation_chat_message and not st.session_state.chat_open_flg:
    st.stop()

# 「英会話開始」ボタンが押された場合の処理
if st.session_state.start_flg:

    # モード：「ディクテーション」
    # 「ディクテーション」ボタン押下時か、「英会話開始」ボタン押下時か、チャット送信時
    if st.session_state.mode == ct.MODE_3 and (st.session_state.dictation_button_flg or st.session_state.dictation_count == 0 or st.session_state.dictation_chat_message):
        if st.session_state.dictation_first_flg:
            st.session_state.chain_create_problem = ft.create_chain(ct.SYSTEM_TEMPLATE_CREATE_PROBLEM)
            st.session_state.dictation_first_flg = False
        # チャット入力以外
        if not st.session_state.chat_open_flg:
            with st.spinner('問題文生成中...'):
                st.session_state.problem, llm_response_audio = ft.create_problem_and_play_audio()
                logger.info({"生成された問題文(ディクテーション)": st.session_state.problem})

            st.session_state.chat_open_flg = True
            st.session_state.dictation_flg = False
            # st.rerun()で画面や処理は再実行されるが、se.session_stateの値は保持される
            st.rerun()
        # チャット入力時の処理
        else:
            # チャット欄から入力された場合にのみ評価処理が実行されるようにする
            if not st.session_state.dictation_chat_message:
                st.stop()
            
            # AIメッセージとユーザーメッセージの画面表示
            with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
                st.markdown(st.session_state.problem)
            with st.chat_message("user", avatar=ct.USER_ICON_PATH):
                st.markdown(st.session_state.dictation_chat_message)

            # LLMが生成した問題文とチャット入力値をメッセージリストに追加
            st.session_state.messages.append({"role": "assistant", "content": st.session_state.problem})
            st.session_state.messages.append({"role": "user", "content": st.session_state.dictation_chat_message})
            
            with st.spinner('評価結果の生成中...'):
                system_template = ct.SYSTEM_TEMPLATE_EVALUATION.format(
                    llm_text=st.session_state.problem,
                    user_text=st.session_state.dictation_chat_message
                )
                st.session_state.chain_evaluation = ft.create_chain(system_template)
                # 問題文と回答を比較し、評価結果の生成を指示するプロンプトを作成
                llm_response_evaluation = ft.create_evaluation("")
            
            # 評価結果のメッセージリストへの追加と表示
            with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
                st.markdown(llm_response_evaluation)
            st.session_state.messages.append({"role": "assistant", "content": llm_response_evaluation})
            st.session_state.messages.append({"role": "other"})
            
            # 各種フラグの更新
            st.session_state.dictation_flg = True
            st.session_state.dictation_chat_message = ""
            st.session_state.dictation_count += 1
            st.session_state.chat_open_flg = False

            # memoryの内容が評価結果に影響を及ぼすため初期化
            st.session_state.memory = ConversationSummaryBufferMemory(
                llm=st.session_state.llm,
                max_token_limit=1000,
                return_messages=True
            )

            st.rerun()

    
    # モード：「日常英会話」
    if st.session_state.mode == ct.MODE_1:
        st.session_state.chain_basic_conversation = ft.create_chain(ct.SYSTEM_TEMPLATE_BASIC_CONVERSATION)
        # 音声入力を受け取って音声ファイルを作成
        audio_input_file_path = f"{ct.AUDIO_INPUT_DIR}/audio_input_{int(time.time())}.wav"
        ft.record_audio(audio_input_file_path)

        # 音声入力ファイルから文字起こしテキストを取得
        with st.spinner('音声入力をテキストに変換中...'):
            transcript = ft.transcribe_audio(audio_input_file_path)
            audio_input_text = transcript.text

        # 音声入力テキストの画面表示
        with st.chat_message("user", avatar=ct.USER_ICON_PATH):
            st.markdown(audio_input_text)

        with st.spinner("回答の音声読み上げ準備中..."):
            # ユーザー入力値をLLMに渡して回答取得
            llm_response = st.session_state.chain_basic_conversation.predict(input=audio_input_text)
            
            # LLMからの回答を音声データに変換
            llm_response_audio = st.session_state.openai_obj.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=llm_response
            )

            # 一旦mp3形式で音声ファイル作成後、wav形式に変換
            audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
            ft.save_to_wav(llm_response_audio.content, audio_output_file_path)

        # 音声ファイルの読み上げ
        ft.play_wav(audio_output_file_path, speed=st.session_state.speed)

        # AIメッセージの画面表示とリストへの追加
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            st.markdown(llm_response)

        # ユーザー入力値とLLMからの回答をメッセージ一覧に追加
        st.session_state.messages.append({"role": "user", "content": audio_input_text})
        st.session_state.messages.append({"role": "assistant", "content": llm_response})


    # モード：「シャドーイング」
    # 「シャドーイング」ボタン押下時か、「英会話開始」ボタン押下時
    if st.session_state.mode == ct.MODE_2 and (st.session_state.shadowing_button_flg or st.session_state.shadowing_count == 0 or st.session_state.shadowing_audio_input_flg):
        if st.session_state.shadowing_first_flg:
            st.session_state.chain_create_problem = ft.create_chain(ct.SYSTEM_TEMPLATE_CREATE_PROBLEM)
            st.session_state.shadowing_first_flg = False
        
        if not st.session_state.shadowing_audio_input_flg:
            with st.spinner('問題文生成中...'):
                st.session_state.problem, llm_response_audio = ft.create_problem_and_play_audio()
                logger.info({"生成された問題文(シャドーイング)": st.session_state.problem})

        # 音声入力を受け取って音声ファイルを作成
        st.session_state.shadowing_audio_input_flg = True
        audio_input_file_path = f"{ct.AUDIO_INPUT_DIR}/audio_input_{int(time.time())}.wav"
        ft.record_audio(audio_input_file_path)
        st.session_state.shadowing_audio_input_flg = False

        with st.spinner('音声入力をテキストに変換中...'):
            # 音声入力ファイルから文字起こしテキストを取得
            transcript = ft.transcribe_audio(audio_input_file_path)
            audio_input_text = transcript.text
            logger.info(f"音声入力テキスト(シャドーイング)：{audio_input_text}")

        # AIメッセージとユーザーメッセージの画面表示
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            st.markdown(st.session_state.problem)
        with st.chat_message("user", avatar=ct.USER_ICON_PATH):
            st.markdown(audio_input_text)
        
        # LLMが生成した問題文と音声入力値をメッセージリストに追加
        st.session_state.messages.append({"role": "assistant", "content": st.session_state.problem})
        st.session_state.messages.append({"role": "user", "content": audio_input_text})

        with st.spinner('評価結果の生成中...'):
            # 変更：テンプレートは毎回変わる
            # if st.session_state.shadowing_evaluation_first_flg:
            system_template = ct.SYSTEM_TEMPLATE_EVALUATION.format(
                llm_text=st.session_state.problem,
                user_text=audio_input_text
            )
            st.session_state.chain_evaluation = ft.create_chain(system_template)
            st.session_state.shadowing_evaluation_first_flg = False
            # 問題文と回答を比較し、評価結果の生成を指示するプロンプトを作成
            llm_response_evaluation = ft.create_evaluation(audio_input_text)
        logger.info({"生成された評価結果(シャドーイング)": llm_response_evaluation})

        # 評価結果のメッセージリストへの追加と表示
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            st.markdown(llm_response_evaluation)
        st.session_state.messages.append({"role": "assistant", "content": llm_response_evaluation})
        st.session_state.messages.append({"role": "other"})
        
        # 各種フラグの更新
        st.session_state.shadowing_flg = True
        st.session_state.shadowing_count += 1

        # 「シャドーイング」ボタンを表示するために再描画
        st.rerun()