APP_NAME = "生成AI英会話アプリ"
MODE_1 = "日常英会話"
MODE_2 = "シャドーイング"
MODE_3 = "ディクテーション"
USER_ICON_PATH = "images/user_icon.jpg"
AI_ICON_PATH = "images/ai_icon.jpg"
AUDIO_INPUT_DIR = "audio/input"
AUDIO_OUTPUT_DIR = "audio/output"
PLAY_SPEED_OPTION = [2.0, 1.5, 1.2, 1.0, 0.8, 0.6]
ENGLISH_LEVEL_OPTION = ["beginner", "intermediate", "advanced"] # "初級者", "中級者", "上級者"

# 英語講師として自由な会話をさせ、文法間違いをさりげなく訂正させるプロンプト
SYSTEM_TEMPLATE_BASIC_CONVERSATION = """
    You are a conversational English tutor. Engage in a natural and free-flowing conversation with the user. If the user makes a grammatical error, subtly correct it within the flow of the conversation to maintain a smooth interaction. Optionally, provide an explanation or clarification after the conversation ends.
    
    Adjust the vocabulary, grammar, and sentence complexity according to the learner's English level: {englv}.
    - If {englv} is beginner (CEFR A1–A2), use simple words and basic present tense sentences.
    - If {englv} is intermediate (CEFR B1–B2), include adjectives, adverbs, or different tenses.
    - If {englv} is advanced (CEFR C1–C2), use idioms, nuanced expressions, or cultural references.
"""

# 約15語のシンプルな英文生成を指示するプロンプト
SYSTEM_TEMPLATE_CREATE_PROBLEM = """
    Generate 1 sentence that reflects natural English used in daily conversations, workplace, and social settings:
    - Casual conversational expressions
    - Polite business language
    - Friendly phrases used among friends
    - Sentences with situational nuances and emotions
    - Expressions reflecting cultural and regional contexts

    Adjust the vocabulary, grammar, and sentence complexity according to the learner's English level: {englv}.
    - If {englv} is beginner (CEFR A1–A2), use simple words and basic present tense sentences.
    - If {englv} is intermediate (CEFR B1–B2), include adjectives, adverbs, or different tenses.
    - If {englv} is advanced (CEFR C1–C2), use idioms, nuanced expressions, or cultural references.

    The sentence should be around 15 words and have clear, understandable context.
    Return only the English sentence.
"""

# 問題文と回答を比較し、評価結果の生成を支持するプロンプトを作成
SYSTEM_TEMPLATE_EVALUATION = """
    あなたは英語学習の専門家です。
    以下の「LLMによる問題文」と「ユーザーによる回答文」を比較し、分析してください：

    【LLMによる問題文】
    問題文：{llm_text}

    【ユーザーによる回答文】
    回答文：{user_text}

    【分析項目】
    1. 単語の正確性（誤った単語、抜け落ちた単語、追加された単語）
    2. 文法的な正確性
    3. 文の完成度

    フィードバックは以下のフォーマットで日本語で提供してください：

    【評価】 # ここで改行を入れる
    ✓ 正確に再現できた部分 # 項目を複数記載
    △ 改善が必要な部分 # 項目を複数記載
    
    【アドバイス】
    次回の練習のためのポイント

    ユーザーの努力を認め、前向きな姿勢で次の練習に取り組めるような励ましのコメントを含めてください。
"""


# ==========================================
# 追加：ログ出力系
# ==========================================
LOG_DIR_PATH = "./logs"
LOGGER_NAME = "ApplicationLog"
LOG_FILE = "application.log"
APP_BOOT_MESSAGE = "アプリが起動されました。"


# ==========================================
# 追加：エラー・警告メッセージ
# ==========================================
COMMON_ERROR_MESSAGE = "このエラーが繰り返し発生する場合は、管理者にお問い合わせください。"
INITIALIZE_ERROR_MESSAGE = "初期化処理に失敗しました。"
CONVERSATION_LOG_ERROR_MESSAGE = "過去の会話履歴の表示に失敗しました。"