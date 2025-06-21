"""Render UI for Agent and Customer. Use the radio button to view the chat."""
import ast
import json
import secrets
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import httpx
import streamlit as st
from loguru import logger
from streamlit_autorefresh import st_autorefresh
from text_to_json import textual_analysis

sys.path.append(str(Path(__file__).parent.resolve().parent))
from unified_logging.config_types import LoggingConfigs
from unified_logging.logging_client import setup_network_logger_client

# App Config
st.set_page_config(page_title="Customer Service Assistant", layout="wide")

CONFIG_FILE_PATH = Path.cwd() / "unified_logging" / "configs.toml"
logging_configs = LoggingConfigs.load_from_path(CONFIG_FILE_PATH)
setup_network_logger_client(logging_configs, logger)

# Dir setup
CACHE_DIR = Path("chat_cache")
TKT_DIR = Path("ticket_log")
CHAT_LOG = Path("chat_log")
CHAT_FILE = CACHE_DIR / "chat.json"
SUMMARY_FILE = CACHE_DIR / "summary.txt"
HIST_SUMMARY = CACHE_DIR / "hist_sum.txt"
KB_ANALYSIS = CACHE_DIR / "kb.txt"
SOLUTION = CACHE_DIR / "solution.txt"
QA_FILE = CACHE_DIR / "qa.txt"
SKILL_ADV = CACHE_DIR / "ms_adv.txt"
RULE_ANALYSIS = CACHE_DIR / "rules.txt"
TKT_DIR.mkdir(exist_ok=True)

def load_chat()-> list:
    """Read chat history from cache file."""
    logger.info("Frontend started.")
    if CHAT_FILE.exists():
        with CHAT_FILE.open() as f:  #open(CHAT_FILE) as f:
            return json.load(f)
    return []

def save_chat(messages: list) -> None:
    """Write chat updates to cache file."""
    with CHAT_FILE.open("w") as f: #open(CHAT_FILE, "w") as f:
        json.dump(messages, f, indent=2)

def dump_ticket(ticket: dict) -> None:
    """Write chat updates to cache file."""
    logger.info("Ticket Saved.")
    file_nm = f"{ticket['ticket_id']}.json"
    tkt_file = TKT_DIR / file_nm
    with tkt_file.open("w") as f:
        json.dump(ticket, f, indent=2, default=str)


def print_bullet_points(d: dict, indent: int = 0) -> None:
    """Iterate through and print dictionary elements."""
    logger.info("Generating rule compliance.")
    for key, value in d.items():
        if isinstance(value, dict):
            prefix = "  " * indent + "- "
            items = ", ".join(f"{k}: {v}" for k, v in value.items())
            st.markdown(f"{prefix} :violet[**{key}**:][{items}]")
        else:
            st.markdown("  " * indent + f"- :violet[**{key}**:] {value}")

st_autorefresh(interval=30000, key="auto-refresh")
# Sidebar: Role selection
role = st.sidebar.radio("Select Role", ["Customer", "Agent"])
st.sidebar.markdown("---")

# Title
st.title("💬 Customer Service Assistant")
chat_placeholder = st.container()


if st.button("Close Chat"):
    # create timestamped log directory
    logger.info("Closing and archiving chat.")
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    archive_dir = CHAT_LOG / f"chat_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # move files from chat_cache to archive directory
    for file in CACHE_DIR.glob("*"):
        shutil.move(str(file), archive_dir / file.name)

    # restore default files
    default_files = {
        "chat.json": [],
        "kb.txt": "",
        "ms_adv.txt": "",
        "qa.txt": "",
        "solution.txt": "",
        "summary.txt": "",
    }

    for filename, content in default_files.items():
        path = CACHE_DIR / filename
        if isinstance(content, list):  # for chat.json
            path.write_text(json.dumps(content, indent=2))
        else:  # for .txt files
            path.write_text(content)

    st.success("Chat history archived and reset.")

# Load current chat
messages = load_chat()

# Show messages
with chat_placeholder:
    for msg in messages:
        if msg["sender"] == "customer":
            st.chat_message("user").write(msg["message"])
        else:
            st.chat_message("assistant").write(msg["message"])

def convert_chat_json_to_string(chat_json: list) -> str:
    """Convert chat type from json to string for backend APIs."""
    sender_map = {
        "customer": "Customer",
        "agent": "Agent",
    }

    result = ""
    for item in chat_json:
        sender = sender_map.get(item["sender"], item["sender"].capitalize())
        message = item["message"]
        result += f"**{sender}:** {message}\n\n"

    return result.strip()

# Message Input
user_input = st.text_input("Type your message:", key="input")
if st.button("Send") and user_input:
    messages.append({"sender": "customer" if role == "Customer" else "agent", "message": user_input})
    save_chat(messages)
    st.rerun()

def load_file_content(file_type: Literal["summary", "history", "kb", "solution","qa","ms_adv","rules"]) -> str:
    """Extract most recently saved file content."""
    file_map = {
        "summary": SUMMARY_FILE,
        "history": HIST_SUMMARY,
        "kb": KB_ANALYSIS,
        "solution": SOLUTION,
        "qa": QA_FILE,
        "ms_adv": SKILL_ADV,
        "rules": RULE_ANALYSIS,
    }
    file_path: Path = file_map.get(file_type)
    if file_path and file_path.exists():
        return file_path.read_text()
    st.write(":red[Not loaded yet]")
    return ""

# Agent-only tools
if role == "Agent":
    st.subheader("📑 Contextual Insights")
    if st.button("Get insights"):
        logger.info("Fetching insights from backend.")
        # Fetch summary
        with httpx.Client(timeout=1000.0) as client:
            response = client.post("http://127.0.0.1:8002/summarize",
                            json={"text": convert_chat_json_to_string(messages)}).json()
            SUMMARY_FILE.write_text(response.get("result"))
        # Fetch QA report
        with httpx.Client(timeout=1000.0) as client:
            response_1 = client.post("http://127.0.0.1:8004/evaluate",
                            json={"agent_response": convert_chat_json_to_string(messages)}).json()

            QA_FILE.write_text(response_1.get("evaluation"))

        with httpx.Client(timeout=1000.0) as client:
            response_2 = client.post("http://127.0.0.1:8008/ms-advance",
                            json={"conversation": convert_chat_json_to_string(messages)}).json()

            SKILL_ADV.write_text(response_2.get("evaluation"))


        payload = {
            "message": f"{convert_chat_json_to_string(messages)}",
        }
        # Optional query parameter
        params_1 = {"sug_type": 1}
        params_2 = {"sug_type": 0}

        # KB analysis
        with httpx.Client(timeout=1000.0) as client:
            response_3 = client.post("http://127.0.0.1:8006/suggest_solution", json=payload, params=params_1).json()
            KB_ANALYSIS.write_text(f"{response_3.get("suggested_solution")}")

        # Proposed Solution
        with httpx.Client(timeout=1000.0) as client:
            response_4 = client.post("http://127.0.0.1:8006/suggest_solution", json=payload, params=params_2).json()
            SOLUTION.write_text(f"{response_4.get("suggested_solution")}")

        attr_params = textual_analysis(messages)
        RULE_ANALYSIS.write_text(f"{attr_params}")




    col1, col2, col3, col4, col5 = st.tabs([
    "📈 Transcript Analysis",
    "🛠️ Quality Assurance",
    "💡 Suggested Responses",
    "🔍 KB Insights",
    "🚀 Micro-Skill Advancement",
])
    with col1:
        st.markdown("**📈 Transcript Analysis**")
        summary_text = load_file_content("summary")
        try:
            result_dict = ast.literal_eval(summary_text)
            category = str(result_dict.get("category", ""))
        except (ValueError, SyntaxError,IndexError):
            st.write(":orange[*Insufficient chat information to perform analysis.]")
            st.write(":orange[Please  click 'Get Insight' button again after a few chats.] ")
            category = ""
        st.markdown(f"- :violet[**Issue Category:**] {category}")
        try:
            attr_txt = load_file_content("rules")
            attr_json = ast.literal_eval(attr_txt)
            print_bullet_points(attr_json)
        except (ValueError, SyntaxError,IndexError):
            st.write("file not found")

    with col2:
        st.markdown("**🛠️ Quality Assurance**")
        current_qa_op = load_file_content("qa").replace('"', "")
        try:
            if current_qa_op[-1]!="}":
                current_qa_op+="}"
            qa_dict = ast.literal_eval(current_qa_op)
            adherence = str(qa_dict.get("adherence", ""))
            issues = qa_dict.get("issues", "")
            st.markdown(f"- :violet[Adherance:] {adherence}")
            st.markdown(f"- :violet[issues found(if any):] {issues}")
        except (ValueError, SyntaxError,IndexError):
            st.write(":orange[**Insufficient chat information to perform analysis, or improper syntax of prompt object generated due to hallucination.]")
            st.write(":orange[Please  click 'Get Insight' button again after a few chats.] ")

            st.write(f":orange[Raw output received:] {current_qa_op}")
            adherence,issues  = "", ""



    with col3:
        st.markdown("**💡 Top solution given by agents in the past. You can use this as reference.**")
        sol_text = load_file_content("solution")
        try:
            r_dict = ast.literal_eval(sol_text)
            soln = str(r_dict.get("solution", ""))
            st.markdown(f" - {soln}")
        except (ValueError, SyntaxError,IndexError):
            st.write(":orange[**Insufficient chat information to perform analysis, or improper syntax of prompt object generated due to hallucination.]")
            st.write(":orange[Please  click 'Get Insight' button again after a few chats.] ")
            st.write(f":orange[Raw output received:] {sol_text}")

    with col4:
        st.markdown("**🔍 Insights from company's Knowledge Base**")
        kb_text = load_file_content("kb")
        try:
            kb_dict = ast.literal_eval(kb_text)
            kb_soln = str(kb_dict.get("solution", ""))
            st.markdown(f" - {kb_soln}")
        except (ValueError, SyntaxError,IndexError):
            st.write(":orange[**Insufficient chat information to perform analysis, or improper syntax of prompt object generated due to hallucination.]")
            st.write(":orange[Please  click 'Get Insight' button again after a few chats.] ")
            st.write(f":orange[Raw output received:] {kb_text}")




    with col5:
        st.markdown("**🚀 Your current micro-skill scores on a scale of 5**")
        current_ms_op = load_file_content("ms_adv")
        try:
            if current_ms_op[-1]!="}":
                current_ms_op+="}"
            ms_op = ast.literal_eval(current_ms_op)
            for key, value in ms_op.items():
                st.markdown(f"- :violet[{key.capitalize()}:] {value}")
        except (ValueError, SyntaxError,IndexError):
            st.write(":orange[**Insufficient chat information to perform analysis, or improper syntax of prompt object generated due to hallucination.]")
            st.write(":orange[Please  click 'Get Insight' button again after a few chats.] ")
            st.write(f":orange[Raw output received:] {current_ms_op}")

    st.subheader("🔧 Actions")
    col_6, col_7 = st.columns(2)
    with col_6:
        if st.button("Get Current Summary"):
            logger.info("Fetching summary.")
            with httpx.Client(timeout=1000.0) as client:
                response = client.post("http://127.0.0.1:8002/summarize",
                                json={"text": convert_chat_json_to_string(messages)}).json()
            SUMMARY_FILE.write_text(response.get("result"))
        summary_text = load_file_content("summary")
        try:
            result_dict = ast.literal_eval(summary_text)
            summary = str(result_dict.get("summary", ""))
            category = str(result_dict.get("category", ""))
        except (ValueError, SyntaxError,IndexError):
            summary, category = "", ""
        st.markdown(":green[Click the 'Get Current Summary' button to view current chat summary]")
        st.markdown(f":violet[Most Recent Summary:] {summary}")


    with col_7:
        st.markdown(":blue[**Create New Ticket**]")
        ticket_id = secrets.token_hex(4)[:9] #"".join([str(random.randint(0, 9)) for _ in range(9)])
        categ_priority = {"Account Management":"2", "Loan and Credit Services":"2", "Fraud and Security":"1", "Card Services":"2", "Online and Mobile Banking":"3"}
        summary_text = load_file_content("summary")
        try:
            result_dict = ast.literal_eval(summary_text)
            tkt_category = str(result_dict.get("category", ""))
            priority = str(categ_priority[tkt_category])
        except (ValueError, SyntaxError,IndexError):
            priority = 3
        st.markdown(f":green[**System Identified Ticket prioirity:**] {priority}")
        ticket_title = st.text_input("**Additional Ticket Information**")

        if st.button("Submit"):
            summary_text = load_file_content("summary")
            try:
                result_dict = ast.literal_eval(summary_text)
                tkt_summary = str(result_dict.get("summary", ""))
                tkt_category = str(result_dict.get("category", ""))
            except (ValueError, SyntaxError,IndexError):
                tkt_summary, tkt_category = "", ""
            # Save the ticket details as a JSON file in ticket_log folder
            ticket_data = {
                "ticket_id": ticket_id,
                "priority": priority,
                "ticket_title": ticket_title,
                "Summary": tkt_summary,
                "Category": tkt_category,
                "Creation Datetime": datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S"),
            }
            dump_ticket(ticket_data)
            st.success(f"Ticket with id {ticket_id} created successfully!")
