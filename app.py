import streamlit as st
import os
import openai
import anthropic
import re

def transcribe_audio(gpt_client, file_path, model_name="whisper-1", prompt_text=None):
    with open(file_path, "rb") as audio_file:
        transcription = gpt_client.audio.transcriptions.create(
            model=model_name,
            file=audio_file,
            prompt=prompt_text
        )
    return transcription.text


def transcript_to_markdown(client, transcript, example_transcripts, example_markdowns, model_id):
    system_prompt = "您是一位專業作家。您的任務是將訪談逐字稿轉換為結構良好、正式且引人入勝的繁體中文部落格文章，並以 Markdown 格式呈現。"
    
    # Construct the prompt with examples
    prompt = (
        "您的任務是將以下訪談逐字稿轉換為一篇潤飾過、結構良好的 Markdown 格式部落格文章。 "
        "請仔細遵循以下說明，以確保輸出符合所需標準：\n\n"
        "1.  **分析範例：** 審查提供的範例逐字稿及其對應的文章，以了解所需的語氣、風格和結構。\n"
        "2.  **保持正式且引人入勝的語氣：** 文章應專業且易於閱讀，避免過於隨意的語言或簡單的逐字轉錄。\n"
        "3.  **文章結構：** 邏輯性地組織內容，使用清晰的標題、段落和其他 Markdown 元素以提高可讀性。\n"
        "4.  **僅輸出文章：** 您的最終輸出應僅為生成的文章，並包含在 <article> 和 </article> 標籤內。請勿在標籤之前或之後包含任何其他文字或解釋。\n\n"
    )
    
    for i in range(len(example_transcripts)):
        prompt += f"<example_transcript_{i+1}>\n{example_transcripts[i]}\n</example_transcript_{i+1}>\n\n"
        prompt += f"<example_article_{i+1}>\n{example_markdowns[i]}\n</example_article_{i+1}>\n\n"

    prompt += (
        f"<transcript>\n{transcript}\n</transcript>\n\n"
        "請根據提供的逐字稿生成文章，並遵循上述所有說明和範例。 "
        "請將您的最終輸出包含在 <article> 和 </article> 標籤內。"
    )

    message = [
        {"role": "user", "content": [{"type": "text", "text": prompt}]}
    ]

    if "claude" in model_id:
        response = client.messages.create(
            model=model_id,
            max_tokens=10000,
            system=system_prompt,
            messages=message,
            temperature=1.0
        )
        article_content = re.search(r'<article>(.*?)</article>', response.content[0].text, re.DOTALL)
    elif "gpt" in model_id:
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "system", "content": system_prompt}] + message,
            max_tokens=10000,
            temperature=1.0
        )
        article_content = re.search(r'<article>(.*?)</article>', response.choices[0].message.content, re.DOTALL)
    else:
        raise ValueError("不支援的模型 ID。")

    
    if article_content:
        return article_content.group(1).strip()
    else:
        # For Claude, response.content[0].text contains the full response
        # For OpenAI, response.choices[0].message.content contains the full response
        full_response_content = response.content[0].text if "claude" in model_id else response.choices[0].message.content
        return ("AI 的回應未遵循指示。以下是完整的回應。 "
                "請尋找 <article> 標籤以找到生成的文章。 "
                "內容為 Markdown 格式，可在以下網址預覽：https://claude.site/artifacts/39f78d93-52a9-48ee-90ac-0732c48f9835\n\n"
                f"{full_response_content}")

def generate_article_from_transcript(client, transcript, model):
    # Load example transcripts and markdowns dynamically
    example_transcript_dir = "./example_transcripts"
    example_markdown_dir = "./example_markdowns"

    example_transcripts = []
    for filename in sorted(os.listdir(example_transcript_dir)):
        if filename.endswith(".txt"):
            with open(os.path.join(example_transcript_dir, filename), "r", encoding="utf-8") as f:
                example_transcripts.append(f.read())

    example_markdowns = []
    for filename in sorted(os.listdir(example_markdown_dir)):
        if filename.endswith(".md"):
            with open(os.path.join(example_markdown_dir, filename), "r", encoding="utf-8") as f:
                example_markdowns.append(f.read())

    with st.spinner('寫手趕稿中...'):
        markdown = transcript_to_markdown(client, transcript, example_transcripts, example_markdowns, model)
    st.divider()
    st.subheader("文章:")
    st.markdown(markdown)
    


def main():
    st.sidebar.title("設定")
    openai_api_key = st.sidebar.text_input("OpenAI API 金鑰", type="password")
    claude_api_key = st.sidebar.text_input("Claude API 金鑰", type="password")
    password = st.sidebar.text_input("佩佩專屬密碼", placeholder="XXX最帥")

    st.sidebar.title("模型選擇")
    model_options = {
        "Claude Sonnet 4 (default)": "claude-sonnet-4-20250514",
        "Claude Opus 4": "claude-opus-4-20250514",
        "GPT-4o mini": "gpt-4o-mini-2024-07-18",
        "GPT-4.1": "gpt-4.1-2025-04-14"
    }
    selected_model_name = st.sidebar.selectbox("選擇一個模型：", list(model_options.keys()))
    model_id = model_options[selected_model_name]

    gpt_client = openai.OpenAI(api_key=openai_api_key)

    if openai_api_key and claude_api_key:
        if "gpt" in model_id:
            client = openai.OpenAI(api_key=openai_api_key)
        elif "claude" in model_id:
            client = anthropic.Anthropic(api_key=claude_api_key)
        else:
            st.error("無效的模型選擇。")
            st.stop()

        st.title("佩佩談話食間專用：Podcast 轉文章小工具")

        # Create tabs
        tab1, tab2, tab3 = st.tabs(["MP3", "逐字稿", "模型"])

        with tab1:
            st.markdown('<span style="color: grey;">音檔必須小於25MB，請將音檔先壓縮後再上傳，https://www.freeconvert.com/mp3-compressor</span>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader("上傳 MP3 檔案", type=["mp3"])
            
            prompt_text = st.text_input("請輸入音檔中可能出現的專有名詞，幫助逐字稿的準確度", "談話食間, 佩佩, (新增關鍵字)")

            if st.button("生成"):
                if password == "周杰倫最帥":
                    if uploaded_file is not None:
                        with st.status("處理中...") as status:
                            status.write("正在上傳音檔...")
                            os.makedirs("podcasts", exist_ok=True)
                            audio_path = os.path.join("podcasts", uploaded_file.name)
                            with open(audio_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            st.success("音檔上傳成功。")

                            status.write("正在轉錄音檔（這可能需要幾分鐘）...")
                            transcript = transcribe_audio(gpt_client, audio_path, prompt_text=prompt_text)
                            st.subheader("逐字稿：")
                            st.text_area("逐字稿", transcript, height=300)

                            status.write(f"正在生成文章... (模型: {model_id})")
                            generate_article_from_transcript(client, transcript, model_id)
                            status.update(label="完成！", state="complete")

                    else:
                        st.error("請上傳 MP3 檔案。")
                else:
                    st.error("誰最帥呀？說了才能用喔！😉")
            

        with tab2:
            transcript_input = st.text_area("在此貼上您的逐字稿：", height=300)
            if st.button("從逐字稿生成"):
                if password == "周杰倫最帥":
                    if transcript_input:
                        with st.status("處理中...") as status:
                            status.write(f"正在生成文章... (模型: {model_id})")
                            generate_article_from_transcript(client, transcript_input, model_id)
                            status.update(label="完成！", state="complete")
                    else:
                        st.error("請提供逐字稿。")
                else:
                    st.error("誰最帥呀？說了才能用喔！😉")

        with tab3:
            st.markdown("""
            ### 模型資訊

            這是一個關於本應用程式中可用的不同大型語言模型的快速指南。

            ---

            #### **Anthropic Claude**

            **Claude Sonnet 4 (default)**
            - **費用**: $3 / 百萬輸入 tokens, $15 / 百萬輸出 tokens
            - **優點**:
              - 理想的平衡了智慧與速度，特別是在處理複雜的任務時。
              - 在需要強大理解能力和快速反應的企業級應用中表現出色。
              - 適用於資料分析、細緻內容創作和程式碼生成。

            **Claude Opus 4**
            - **費用**: $15 / 百萬輸入 tokens, $75 / 百萬輸出 tokens
            - **優點**:
              - 最強大的模型，適用於處理高度複雜的任務。
              - 在需要深度推理、策略規劃和複雜問題解決的場景中表現卓越。
              - 適合研發、進階分析和需要頂級智慧的任務。

            ---

            #### **OpenAI GPT**

            **GPT-4o mini**
            - **費用**: $0.15 / 百萬輸入 tokens, $0.60 / 百萬輸出 tokens
            - **優點**:
              - 為速度和成本進行了優化，是需要快速回應的任務的理想選擇。
              - 適用於聊天機器人、內容摘要和即時翻譯。

            **GPT-4.1**
            - **費用**: $5 / 百萬輸入 tokens, $15 / 百萬輸出 tokens (此為 GPT-4o 價格，僅供參考)
            - **優點**:
              - OpenAI 最新的 GPT-4 模型，具有更高的智慧和改進的效能。
              - 適用於需要高準確度和理解細微差別的複雜任務。
            """)

if __name__ == "__main__":
    main()