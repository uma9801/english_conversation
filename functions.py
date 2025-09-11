import streamlit as st
import os
import time
from pathlib import Path
import wave
import pyaudio
from pydub import AudioSegment
from audiorecorder import audiorecorder
import numpy as np
from scipy.io.wavfile import write
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.schema import SystemMessage
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
import constants as ct
import logging

def record_audio(audio_input_file_path):
    """
    音声入力を受け取って音声ファイルを作成
    """

    audio = audiorecorder(
        start_prompt="発話開始",
        pause_prompt="やり直す",
        stop_prompt="発話終了",
        start_style={"color":"white", "background-color":"black"},
        pause_style={"color":"gray", "background-color":"white"},
        stop_style={"color":"white", "background-color":"black"}
    )

    if len(audio) > 0:
        audio.export(audio_input_file_path, format="wav")
    else:
        st.stop()

def transcribe_audio(audio_input_file_path):
    """
    音声入力ファイルから文字起こしテキストを取得
    Args:
        audio_input_file_path: 音声入力ファイルのパス
    """

    with open(audio_input_file_path, 'rb') as audio_input_file:
        transcript = st.session_state.openai_obj.audio.transcriptions.create(
            model="whisper-1",
            file=audio_input_file,
            language="en"
        )
    
    # 音声入力ファイルを削除
    os.remove(audio_input_file_path)

    return transcript

def save_to_wav(llm_response_audio, audio_output_file_path):
    """
    一旦mp3形式で音声ファイル作成後、wav形式に変換
    Args:
        llm_response_audio: LLMからの回答の音声データ
        audio_output_file_path: 出力先のファイルパス
    """

    temp_audio_output_filename = f"{ct.AUDIO_OUTPUT_DIR}/temp_audio_output_{int(time.time())}.mp3"
    with open(temp_audio_output_filename, "wb") as temp_audio_output_file:
        temp_audio_output_file.write(llm_response_audio)
    
    audio_mp3 = AudioSegment.from_file(temp_audio_output_filename, format="mp3")
    audio_mp3.export(audio_output_file_path, format="wav")

    # 音声出力用に一時的に作ったmp3ファイルを削除
    os.remove(temp_audio_output_filename)

def play_wav(audio_output_file_path, speed=1.0):
    """
    音声ファイルの読み上げ
    Args:
        audio_output_file_path: 音声ファイルのパス
        speed: 再生速度（1.0が通常速度、0.5で半分の速さ、2.0で倍速など）
    """

    # 音声ファイルの読み込み
    audio = AudioSegment.from_wav(audio_output_file_path)
    
    # 速度を変更
    if speed != 1.0:
        # frame_rateを変更することで速度を調整
        modified_audio = audio._spawn(
            audio.raw_data, 
            overrides={"frame_rate": int(audio.frame_rate * speed)}
        )
        # 元のframe_rateに戻すことで正常再生させる（ピッチを保持したまま速度だけ変更）
        modified_audio = modified_audio.set_frame_rate(audio.frame_rate)

        modified_audio.export(audio_output_file_path, format="wav")

    # PyAudioで再生
    with wave.open(audio_output_file_path, 'rb') as play_target_file:
        p = pyaudio.PyAudio()
        stream = p.open(
            format=p.get_format_from_width(play_target_file.getsampwidth()),
            channels=play_target_file.getnchannels(),
            rate=play_target_file.getframerate(),
            output=True
        )

        data = play_target_file.readframes(1024)
        while data:
            stream.write(data)
            data = play_target_file.readframes(1024)

        stream.stop_stream()
        stream.close()
        p.terminate()
    
    # LLMからの回答の音声ファイルを削除
    os.remove(audio_output_file_path)

def create_chain(system_template):
    """
    LLMによる回答生成用のChain作成
    """
    # 英語レベルをログに出力
    logger = logging.getLogger(ct.LOGGER_NAME)
    logger.info({"モード": st.session_state.mode, "英語レベル": st.session_state.englv})

    # system_templateにst.session_state.englvを埋め込むためのcustom_system_template変数を用意
    custom_system_template = system_template.format(englv=st.session_state.englv)
    # custom_system_templateの内容をログに出力
    logger.info({"create_chain実行時のテンプレート": custom_system_template})

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=custom_system_template),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{input}")
    ])
    # logger.info({"create_chain実行時のprompt": prompt})
    chain = ConversationChain(
        llm=st.session_state.llm,
        memory=st.session_state.memory,
        prompt=prompt
    )
    # logger.info({"memoryの内容": st.session_state.memory})
    return chain

def create_problem_and_play_audio():
    """
    問題生成と音声ファイルの再生
    Args:
        chain: 問題文生成用のChain
        speed: 再生速度（1.0が通常速度、0.5で半分の速さ、2.0で倍速など）
        openai_obj: OpenAIのオブジェクト
    """

    logger = logging.getLogger(ct.LOGGER_NAME)

    # 問題文を生成するChainを実行し、問題文を取得
    problem = st.session_state.chain_create_problem.predict(input="")

    # LLMからの回答を音声データに変換
    llm_response_audio = st.session_state.openai_obj.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=problem
    )

    # 音声ファイルの作成
    audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
    save_to_wav(llm_response_audio.content, audio_output_file_path)

    # 音声ファイルの読み上げ
    play_wav(audio_output_file_path, st.session_state.speed)

    # llm_response_audioはどこでも使っていないから不要なのでは？
    return problem, llm_response_audio

def create_evaluation(audio_input_text):
    """
    ユーザー入力値の評価生成
    """

    llm_response_evaluation = st.session_state.chain_evaluation.predict(input=audio_input_text)

    return llm_response_evaluation

# モードや英会話レベル変更時のフラグ管理関数
def reset_flags_on_mode_or_level_change():
    """
    モードや英会話レベル変更時に各種フラグをリセット
    """
    # 英語レベル変更時のみ各first_flgをTrueにして、テンプレートに英語レベルが反映されるようにする

    # 自動でそのモードの処理が実行されないようにする
    st.session_state.start_flg = False
    # 「日常英会話」選択時の初期化処理
    if st.session_state.mode == ct.MODE_1:
        st.session_state.dictation_flg = False
        st.session_state.shadowing_flg = False
    # 「シャドーイング」選択時の初期化処理
    st.session_state.shadowing_count = 0
    if st.session_state.mode == ct.MODE_2:
        st.session_state.dictation_flg = False       
        if st.session_state.englv != st.session_state.pre_englv:
            # 英語レベルに合わせたchain再作成用のフラグ管理
            st.session_state.shadowing_first_flg = True
    # 「ディクテーション」選択時の初期化処理
    st.session_state.dictation_count = 0
    if st.session_state.mode == ct.MODE_3:
        st.session_state.shadowing_flg = False
        if st.session_state.englv != st.session_state.pre_englv:
            # 英語レベルに合わせたchain再作成用のフラグ管理
            st.session_state.dictation_first_flg = True
    # チャット入力欄を非表示にする
    st.session_state.chat_open_flg = False