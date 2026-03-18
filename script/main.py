import logging
import calendar
from datetime import date
import html
import streamlit as st

from utils.automation import eCards_automation, enrollware_automation
from utils.helper import logger, get_undetected_driver


def run_automation(from_date: str, to_date: str):
    driver = get_undetected_driver(headless=True)
    if not driver:
        raise RuntimeError("Unable to initialize browser driver")
    try:
        ecards_data = eCards_automation(driver, from_date, to_date) or []
        if ecards_data:
            logger.info("Starting Enrollware automation with fetched eCards data...")
            enrollware_automation(driver, ecards_data)
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def run_year_automation(year: int):
    driver = get_undetected_driver(headless=True)
    if not driver:
        raise RuntimeError("Unable to initialize browser driver")
    aggregated_data = []
    try:
        today = date.today()
        max_month = today.month if year == today.year else 12
        for month in range(1, max_month + 1):
            start_date = date(year, month, 1)
            end_day = calendar.monthrange(year, month)[1]
            end_date = date(year, month, end_day)
            start_str = start_date.strftime("%m/%d/%Y")
            end_str = end_date.strftime("%m/%d/%Y")
            logger.info(
                "Fetching data for %s (%s - %s)", start_date.strftime("%b %Y"), start_str, end_str
            )
            month_data = eCards_automation(driver, start_str, end_str) or []
            aggregated_data.extend(month_data)
        if aggregated_data:
            enrollware_automation(driver, aggregated_data)
        else:
            logger.info("No data returned for the selected year.")
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def main():
    st.set_page_config(page_title="Roster Assurance Automation", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(
        """
        <style>
            body { background-color: #0f172a; color: #e5e7eb; }
            .stApp { background-color: #0f172a; }
            .stTextArea textarea { background-color: #111827; color: #e5e7eb; border: 1px solid #1f2937; }
            .stDateInput > div { background-color: #111827; color: #e5e7eb; }
            .stButton>button { background-color: #0f172a; color: white; border: 1px solid #fff; margin-top: 26px; }
            .stButton>button:hover { background-color: rgb(14, 17, 23); color: #fff; border: 1px solid #fff; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Roster Assurance Automation ✨")
    st.write("Select your date range and start the automation. Dates use MM/DD/YYYY.")

    if "log_lines" not in st.session_state:
        st.session_state.log_lines = []

    mode = st.radio("Date Range Mode", ["Month", "Year"], index=0, horizontal=True)

    from_date = None
    to_date = None
    selected_year = None
    col1, col2, col3 = st.columns([1, 1, 1])

    if mode == "Month":
        with col1:
            from_date = st.date_input("From Date", value=date.today(), format="MM/DD/YYYY")
        with col2:
            to_date = st.date_input("To Date", value=date.today(), format="MM/DD/YYYY")
        with col3:
            start_clicked = st.button("Start Automation", type="primary", use_container_width=True)

    else:
        current_year = date.today().year
        year_options = list(range(current_year - 4, current_year + 1))
        with col1:
            selected_year = st.selectbox("Select Year", options=year_options, index=len(year_options) - 1)
        with col2:
            start_clicked = st.button("Start Automation", type="primary", use_container_width=True)

    log_box = st.empty()

    class StreamlitLogHandler(logging.Handler):
        def emit(self, record):
            msg = self.format(record)
            logs = st.session_state.get("log_lines", [])
            logs.append(msg)
            st.session_state.log_lines = logs
            log_content = html.escape("\n".join(logs)).replace("\n", "<br/>")
            log_box.markdown(
                f"""
                <div style='font-size:14px;font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;margin-bottom:8px;'>Logs:</div>
                <div id='log-container' style='background:#111827;color:#e5e7eb;padding:8px;border:1px solid #1f2937;border-radius:4px;height:300px;overflow-y:auto;'>
                    <div style='margin:0;font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;white-space:pre-wrap;'>{log_content}</div>
                </div>
                <script>
                    const logBox = window.document.getElementById('log-container');
                    if (logBox) {{ logBox.scrollTop = logBox.scrollHeight; }}
                </script>
                """,
                unsafe_allow_html=True,
            )

    def validate_range(start, end):
        if start > end:
            st.warning("From Date cannot be after To Date")
            return False
        return True

    if start_clicked:
        if mode == "Month" and (from_date is None or to_date is None or not validate_range(from_date, to_date)):
            return
        st.session_state.log_lines = []
        handler = StreamlitLogHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        try:
            with st.spinner("Running automation..."):
                if mode == "Month":
                    run_automation(from_date.strftime("%m/%d/%Y"), to_date.strftime("%m/%d/%Y"))
                else:
                    run_year_automation(selected_year)
            st.success("Automation completed successfully.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            st.error(f"Error: {e}")
        finally:
            logger.removeHandler(handler)


if __name__ == "__main__":
    main()