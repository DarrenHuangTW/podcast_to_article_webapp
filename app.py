import streamlit as st
import os
import openai
import anthropic
import re

def transcribe_audio(file_path, model_name="whisper-1", prompt_text=None):
    with open(file_path, "rb") as audio_file:
        transcription = openai.audio.transcriptions.create(
            model=model_name,
            file=audio_file,
            prompt=prompt_text
        )
    return transcription.text


def transcript_to_markdown(client, transcript, example_transcripts, example_markdowns):
    system_prompt = "你是一名專業的寫手，根據所提供的訪談逐字稿，生出一篇markdown格式的繁體中文部落格文章。"
    
    # Construct the prompt with examples
    prompt = (
        "你的任務是將訪談逐字稿轉換為 markdown 格式的文章。請仔細閱讀以下指示，以確保你能夠準確完成任務。\n\n"
    )
    
    for i in range(len(example_transcripts)):
        prompt += f"<example_transcript_{i+1}>\n{example_transcripts[i]}\n</example_transcript_{i+1}>\n\n"
        prompt += f"<example_article_{i+1}>\n{example_markdowns[i]}\n</example_article_{i+1}>\n\n"

    prompt += (
        "在撰寫文章時，請模仿範例文章的寫作風格和語氣。注意文章應該是流暢、易讀的，而不是逐字逐句的轉錄。\n\n"
        f"<transcript>\n{transcript}\n</transcript>\n\n"
        "請將你的文章放在 <article> 標籤內。"
    )

    message = [
        {"role": "user", "content": [{"type": "text", "text": prompt}]}
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        system=system_prompt,
        messages=message,
        temperature=1.0
    )

    article_content = re.search(r'<article>(.*?)</article>', response.content[0].text, re.DOTALL)
    
    if article_content:
        return article_content.group(1).strip()
    else:
        return ("拍謝，AI的回答沒有按造指令，下面是其完整的回答。請在裡面尋找<article>標籤，應該就能找到所生成的文章了，"
                "所使用的是markdown格式，可以貼到這個網址預覽: https://claude.site/artifacts/39f78d93-52a9-48ee-90ac-0732c48f9835\n\n"
                f"{response.content[0].text}")
    


def main():
    st.sidebar.title("Configuration")
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    claude_api_key = st.sidebar.text_input("Claude API Key", type="password")
    password = st.sidebar.text_input("佩佩專屬密碼", placeholder="XXX最帥")

    if openai_api_key and claude_api_key:
        openai.api_key = openai_api_key
        client = anthropic.Anthropic(api_key=claude_api_key)

        st.title("佩佩談話食間專用: Podcast to Article小工具")

        # Create tabs
        tab1, tab2 = st.tabs(["MP3", "Transcript"])

        with tab1:
            st.markdown('<span style="color: grey;">音檔必須小於25MB，請將音檔先壓縮後再上傳，https://www.freeconvert.com/mp3-compressor</span>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Upload an MP3 file", type=["mp3"])
            
            prompt_text = st.text_input("請輸入音檔中可能出現的專有名詞，幫助逐字稿的準確度", "談話食間, 佩佩, (add keywords)")

            if st.button("Generate"):
                if password == "周杰倫最帥":
                    if uploaded_file is not None:
                        os.makedirs("podcasts", exist_ok=True)
                        audio_path = os.path.join("podcasts", uploaded_file.name)
                        with open(audio_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        st.success("Audio file uploaded successfully.")

                        with st.spinner('逐字稿製作中...'):
                            transcript = transcribe_audio(audio_path, prompt_text=prompt_text)
                        st.subheader("逐字稿:")
                        st.text_area("Transcript", transcript, height=300)

                        # Load example transcripts and markdowns
                        example_transcripts = [
                            open("./example_transcripts/麥特.txt", "r", encoding="utf-8").read(),
                            open("./example_transcripts/赤鳶.txt", "r", encoding="utf-8").read(),
                            open("./example_transcripts/lazy_patisserie.txt", "r", encoding="utf-8").read(),
                            open("./example_transcripts/cornerstone.txt", "r", encoding="utf-8").read()
                        ]

                        example_markdowns = [
                            open("./example_markdowns/麥特.md", "r", encoding="utf-8").read(),
                            open("./example_markdowns/赤鳶.md", "r", encoding="utf-8").read(),
                            open("./example_markdowns/lazy_patisserie.md", "r", encoding="utf-8").read(),
                            open("./example_markdowns/cornerstone.md", "r", encoding="utf-8").read()
                        ]

                        with st.spinner('寫手趕稿中...'):
                            markdown = transcript_to_markdown(client, transcript, example_transcripts, example_markdowns)
                        st.divider()
                        st.subheader("文章:")
                        st.markdown(markdown)

                    else:
                        st.error("Please upload an MP3 file.")
                else:
                    st.error("誰最帥呀? 說了才能用喔!😉")
            else:
                st.error("Please provide both OpenAI and Claude API keys.")

        with tab2:
            transcript_input = st.text_area("Paste your transcript here:", height=300)
            if st.button("Generate from Transcript"):
                if password == "周杰倫最帥":
                    if transcript_input:
                        # Load example transcripts and markdowns
                        example_transcripts = [
                            open("./example_transcripts/麥特.txt", "r", encoding="utf-8").read(),
                            open("./example_transcripts/赤鳶.txt", "r", encoding="utf-8").read(),
                            open("./example_transcripts/lazy_patisserie.txt", "r", encoding="utf-8").read(),
                            open("./example_transcripts/cornerstone.txt", "r", encoding="utf-8").read()
                        ]

                        example_markdowns = [
                            open("./example_markdowns/麥特.md", "r", encoding="utf-8").read(),
                            open("./example_markdowns/赤鳶.md", "r", encoding="utf-8").read(),
                            open("./example_markdowns/lazy_patisserie.md", "r", encoding="utf-8").read(),
                            open("./example_markdowns/cornerstone.md", "r", encoding="utf-8").read()
                        ]

                        with st.spinner('寫手趕稿中...'):
                            markdown = transcript_to_markdown(client, transcript_input, example_transcripts, example_markdowns)
                        st.divider()
                        st.subheader("文章:")
                        st.markdown(markdown)
                    else:
                        st.error("Please provide a transcript.")
                else:
                    st.error("誰最帥呀? 說了才能用喔!😉")

if __name__ == "__main__":
    main()