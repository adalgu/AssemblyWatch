import os
from dotenv import load_dotenv
import sqlite3
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


def get_session_transcripts_from_db(session_id):
    conn = sqlite3.connect('assembly_watch.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT content FROM transcripts WHERE session_id = ? ORDER BY timestamp', (session_id,))
    transcripts = cursor.fetchall()
    conn.close()
    return ' '.join([transcript[0] for transcript in transcripts])


def get_transcript_files():
    transcript_folder = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'transcripts')
    if not os.path.exists(transcript_folder):
        print("transcripts 폴더가 존재하지 않습니다.")
        return []
    return [f for f in os.listdir(transcript_folder) if f.endswith('.txt')]


def get_transcript_from_file(filename):
    transcript_folder = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'transcripts')
    file_path = os.path.join(transcript_folder, filename)
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def create_vector_store(text):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_text(text)
    embeddings = OpenAIEmbeddings()
    return FAISS.from_texts(texts, embeddings)


def generate_summary(vector_store):
    qa_chain = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
        chain_type="stuff",
        retriever=vector_store.as_retriever()
    )
    summary = qa_chain.invoke("회의의 주요 내용을 요약해주세요. 최대한 상세하게 요약해주세요.")
    return summary["result"]


def assess_risk(vector_store):
    risk_template = """
    다음 트랜스크립트를 바탕으로 잠재적인 리스크나 논란의 여지가 있는 이슈를 평가해주세요:
    
    {context}
    
    잠재적 리스크 또는 논란의 여지가 있는 이슈를 상세하게 나열해주세요:
    """
    risk_prompt = PromptTemplate(
        template=risk_template, input_variables=["context"])

    qa_chain = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model="gpt-4o-mini",
                       temperature=0),  # GPT-4 Turbo 사용
        chain_type="stuff",
        retriever=vector_store.as_retriever(),
        chain_type_kwargs={"prompt": risk_prompt}
    )

    risk_assessment = qa_chain.invoke(
        "회의 내용에서 잠재적인 리스크를 식별해주세요. 최대한 상세하게 나열해주세요.")
    return risk_assessment["result"]


def generate_report(session_id=None, filename=None):
    if os.path.exists('assembly_watch.db') and session_id is not None:
        # 데이터베이스에서 세션 정보 가져오기
        conn = sqlite3.connect('assembly_watch.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT title, date, start_time FROM sessions WHERE id = ?', (session_id,))
        session_info = cursor.fetchone()
        conn.close()

        if not session_info:
            return "세션 정보를 찾을 수 없습니다."

        title, date, start_time = session_info
        full_transcript = get_session_transcripts_from_db(session_id)
    elif filename:
        # 파일에서 트랜스크립트 가져오기
        full_transcript = get_transcript_from_file(filename)
        title = filename.split('.')[0]
        date = "날짜 정보 없음"
        start_time = "시작 시간 정보 없음"
    else:
        return "세션 ID 또는 파일 이름을 제공해야 합니다."

    # 벡터 저장소 생성
    vector_store = create_vector_store(full_transcript)

    # 요약 생성
    summary = generate_summary(vector_store)

    # 리스크 평가
    risk_assessment = assess_risk(vector_store)

    # 리포트 생성
    report = f"""
    회의 제목: {title}
    날짜: {date}
    시작 시간: {start_time}

    요약:
    {summary}

    리스크 평가:
    {risk_assessment}
    """

    return report, title


def get_sessions_from_db():
    cursor.execute('SELECT id, title FROM sessions')
    return cursor.fetchall()


if __name__ == "__main__":
    if os.path.exists('assembly_watch.db'):
        conn = sqlite3.connect('assembly_watch.db')
        cursor = conn.cursor()

        sessions = get_sessions_from_db()
        if sessions:
            print("사용 가능한 세션 목록:")
            for session in sessions:
                print(f"ID: {session[0]}, 제목: {session[1]}")

            while True:
                session_id = input("리포트를 생성할 세션 ID를 입력하세요 (또는 'q'를 입력하여 종료): ")
                if session_id.lower() == 'q':
                    print("프로그램을 종료합니다.")
                    exit()
                try:
                    session_id = int(session_id)
                    if session_id in [s[0] for s in sessions]:
                        report, title = generate_report(session_id=session_id)
                        break
                    else:
                        print("유효하지 않은 세션 ID입니다. 다시 시도해주세요.")
                except ValueError:
                    print("숫자를 입력해주세요.")
        else:
            print("사용 가능한 세션이 없습니다.")
            exit()

        conn.close()
    else:
        print("assembly_watch.db 파일이 없습니다. 트랜스크립트 파일을 사용합니다.")
        transcript_files = get_transcript_files()
        if not transcript_files:
            print("사용 가능한 트랜스크립트 파일이 없습니다.")
            exit()
        else:
            print("사용 가능한 트랜스크립트 파일:")
            for i, file in enumerate(transcript_files):
                print(f"{i+1}. {file}")
            while True:
                choice = input("처리할 파일 번호를 선택하세요 (또는 'q'를 입력하여 종료): ")
                if choice.lower() == 'q':
                    print("프로그램을 종료합니다.")
                    exit()
                try:
                    choice = int(choice) - 1
                    if 0 <= choice < len(transcript_files):
                        report, title = generate_report(
                            filename=transcript_files[choice])
                        break
                    else:
                        print("유효하지 않은 선택입니다. 다시 시도해주세요.")
                except ValueError:
                    print("숫자를 입력해주세요.")

    print(report)

    # reports 폴더 생성 (없는 경우)
    reports_folder = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'reports')
    os.makedirs(reports_folder, exist_ok=True)

    # 리포트를 파일로 저장
    report_filename = f"report_{title}.txt"
    report_path = os.path.join(reports_folder, report_filename)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"리포트가 성공적으로 저장되었습니다: {report_path}")
