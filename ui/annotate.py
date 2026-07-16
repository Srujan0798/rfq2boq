"""Annotation UI for active learning review.

Streamlit app for reviewing uncertain entity predictions
and accepting/correcting/rejecting them.

Usage:
    streamlit run ui/annotate.py [--browser.serverPort 8502]

Navigate through review tasks, accept model predictions as-is,
correct wrong entity types, or reject clearly incorrect predictions.
Corrections are saved to data/real_rfqs/annotations/ for retraining.
"""

import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

REVIEW_QUEUE_PATH = Path("data/review_queue/review_queue.json")
ANNOTATIONS_DIR = Path("data/real_rfqs/annotations")
ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)


def load_review_queue():
    if REVIEW_QUEUE_PATH.exists():
        with open(REVIEW_QUEUE_PATH) as f:
            return json.load(f)
    return []


def save_review_queue(tasks):
    with open(REVIEW_QUEUE_PATH, "w") as f:
        json.dump(tasks, f, indent=2)


def load_annotations():
    annotations_file = ANNOTATIONS_DIR / "annotations.json"
    if annotations_file.exists():
        with open(annotations_file) as f:
            return json.load(f)
    return []


def save_annotation(annotation):
    annotations_file = ANNOTATIONS_DIR / "annotations.json"
    annotations = load_annotations()
    annotations.append(annotation)
    with open(annotations_file, "w") as f:
        json.dump(annotations, f, indent=2)


def main():
    st.set_page_config(
        page_title="RFQ Entity Annotation",
        page_icon="📋",
        layout="wide",
    )

    st.title("📋 RFQ Entity Annotation - Active Learning")

    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0

    tasks = load_review_queue()
    pending_tasks = [t for t in tasks if t.get("status") == "pending"]

    st.sidebar.header("📊 Statistics")
    st.sidebar.metric("Total Tasks", len(tasks))
    st.sidebar.metric("Pending", len(pending_tasks))
    st.sidebar.metric("Completed", len([t for t in tasks if t.get("status") != "pending"]))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("High Uncertainty (>0.6)", len([t for t in pending_tasks if t.get("uncertainty", 0) > 0.6]))
    with col2:
        st.metric("Medium (0.3-0.6)", len([t for t in pending_tasks if 0.3 <= t.get("uncertainty", 0) <= 0.6]))
    with col3:
        st.metric("Low (<0.3)", len([t for t in pending_tasks if t.get("uncertainty", 0) < 0.3]))

    st.sidebar.header("🔍 Filter")
    entity_filter = st.sidebar.multiselect(
        "Entity Type",
        options=list(set(t.get("type", "") for t in pending_tasks)),
        default=[],
    )

    filtered_tasks = pending_tasks
    if entity_filter:
        filtered_tasks = [t for t in pending_tasks if t.get("type", "") in entity_filter]

    if not filtered_tasks:
        st.info("No pending review tasks. All done! 🎉")
        return

    if st.session_state.current_idx >= len(filtered_tasks):
        st.session_state.current_idx = 0

    current_task = filtered_tasks[st.session_state.current_idx]

    st.subheader(f"Task #{st.session_state.current_idx + 1} of {len(filtered_tasks)}")
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("### 📝 Sentence Context")
        sentence = current_task.get("sentence", "")
        st.code(sentence, language=None)

        st.markdown("### 🏷️ Entity to Review")
        entity_text = current_task.get("text", "")
        entity_type = current_task.get("type", "")

        cols = st.columns([1, 1, 1])
        with cols[0]:
            st.metric("Entity Text", entity_text)
        with cols[1]:
            st.metric("Predicted Type", entity_type)
        with cols[2]:
            st.metric("Uncertainty", f"{current_task.get('uncertainty', 0):.4f}")

        st.markdown("### ✏️ Correction")
        correction_type = st.selectbox(
            "Correct entity type:",
            options=["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"],
            index=(
                ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"].index(
                    entity_type
                )
                if entity_type
                in ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]
                else 0
            ),
        )

        reviewer_notes = st.text_area(
            "Reviewer notes (optional):", value=current_task.get("reviewer_notes", ""), height=100
        )

    with col_right:
        st.markdown("### 📄 Metadata")
        st.write(f"**Task ID:** {current_task.get('task_id', 'N/A')}")
        st.write(f"**Source:** {current_task.get('source_file', 'N/A')}")
        st.write(f"**Page:** {current_task.get('page', 'N/A')}")
        st.write(f"**Score:** {current_task.get('score', 0):.4f}")
        st.write(f"**Entropy:** {current_task.get('entropy', 0):.4f}")

        st.markdown("### 🎯 Actions")

        col_accept, col_correct, col_reject = st.columns(3)

        action_result = None

        with col_accept:
            if st.button("✅ Accept", use_container_width=True, type="primary"):
                action_result = ("accept", current_task)

        with col_correct:
            if st.button("✏️ Correct", use_container_width=True):
                action_result = ("correct", current_task, correction_type, reviewer_notes)

        with col_reject:
            if st.button("❌ Reject", use_container_width=True):
                action_result = ("reject", current_task)

        if action_result:
            action_type = action_result[0]
            task = action_result[1]

            if action_type == "accept":
                task["status"] = "accepted"
                task["corrected_type"] = task["type"]
                annotation = {
                    "task_id": task["task_id"],
                    "text": task["text"],
                    "type": task["type"],
                    "sentence": task["sentence"],
                    "page": task.get("page"),
                    "action": "accept",
                    "reviewer_notes": reviewer_notes,
                }
            elif action_type == "correct":
                task["status"] = "corrected"
                task["corrected_type"] = action_result[2]
                annotation = {
                    "task_id": task["task_id"],
                    "text": task["text"],
                    "type": action_result[2],
                    "sentence": task["sentence"],
                    "page": task.get("page"),
                    "action": "correct",
                    "original_type": task["type"],
                    "reviewer_notes": reviewer_notes,
                }
            else:
                task["status"] = "rejected"
                task["corrected_type"] = None
                annotation = {
                    "task_id": task["task_id"],
                    "text": task["text"],
                    "type": task["type"],
                    "sentence": task["sentence"],
                    "page": task.get("page"),
                    "action": "reject",
                    "reviewer_notes": reviewer_notes,
                }

            save_annotation(annotation)

            for t in tasks:
                if t["task_id"] == task["task_id"]:
                    t["status"] = task["status"]
                    t["corrected_type"] = task.get("corrected_type")
                    t["reviewer_notes"] = reviewer_notes
                    break

            save_review_queue(tasks)

            st.success(f"Task {action_type}ed! Moving to next...")
            st.session_state.current_idx += 1
            st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Quick Navigation")

    nav_cols = st.columns(4)
    with nav_cols[0]:
        if st.button("⏮ First", use_container_width=True):
            st.session_state.current_idx = 0
            st.rerun()

    with nav_cols[1]:
        if st.button("◀ Previous", use_container_width=True) and st.session_state.current_idx > 0:
            st.session_state.current_idx -= 1
            st.rerun()

    with nav_cols[2]:
        if st.button("Next ▶", use_container_width=True) and st.session_state.current_idx < len(filtered_tasks) - 1:
            st.session_state.current_idx += 1
            st.rerun()

    with nav_cols[3]:
        if st.button("⏭ Last", use_container_width=True):
            st.session_state.current_idx = len(filtered_tasks) - 1
            st.rerun()

    with st.expander("📜 All Pending Tasks"):
        for idx, task in enumerate(filtered_tasks[:20]):
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            with col1:
                st.write(f"**{idx+1}.** {task.get('text', '')}")
            with col2:
                st.write(f"Type: {task.get('type', '')}")
            with col3:
                st.write(f"Unc: {task.get('uncertainty', 0):.3f}")
            with col4:
                if st.button("Go", key=f"goto_{task['task_id']}"):
                    st.session_state.current_idx = idx
                    st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💡 Instructions")
    st.sidebar.markdown("""
    1. **Accept**: Model prediction looks correct
    2. **Correct**: Change the entity type
    3. **Reject**: Clearly wrong prediction
    4. Review notes help track patterns
    """)
