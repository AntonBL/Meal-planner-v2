"""Notes Management Page - Track improvements and bugs."""

import streamlit as st
from datetime import datetime

from lib.auth import require_authentication
from lib.notes_manager import (
    add_note,
    delete_note,
    load_notes,
    update_note,
)
from lib.ui import render_header
from lib.mobile_ui import add_mobile_styles

# Require authentication
require_authentication()

# Apply mobile styles
add_mobile_styles()

# Header
render_header(
    title="📝 Notes & Ideas",
    subtitle="Track improvements and bugs for your meal planner"
)

st.markdown("""
Keep track of ideas for improvements and bugs you've noticed.
Use this as your personal issue tracker for the app!
""")

# Initialize session state for form
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'edit_note_id' not in st.session_state:
    st.session_state.edit_note_id = None

# Load all notes
all_notes = load_notes()

# Filter controls
st.subheader("📊 Your Notes")

col1, col2, col3 = st.columns(3)

with col1:
    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "Open", "In Progress", "Done"],
        key="status_filter"
    )

with col2:
    type_filter = st.selectbox(
        "Filter by Type",
        ["All", "Improvement", "Bug"],
        key="type_filter"
    )

with col3:
    sort_by = st.selectbox(
        "Sort by",
        ["Newest First", "Oldest First", "Recently Updated"],
        key="sort_by"
    )

# Apply filters
filtered_notes = all_notes.copy()

if status_filter != "All":
    status_map = {"Open": "open", "In Progress": "in_progress", "Done": "done"}
    filtered_notes = [n for n in filtered_notes if n['status'] == status_map[status_filter]]

if type_filter != "All":
    type_map = {"Improvement": "improvement", "Bug": "bug"}
    filtered_notes = [n for n in filtered_notes if n['type'] == type_map[type_filter]]

# Apply sorting
if sort_by == "Newest First":
    filtered_notes.sort(key=lambda x: x['created_at'], reverse=True)
elif sort_by == "Oldest First":
    filtered_notes.sort(key=lambda x: x['created_at'])
else:  # Recently Updated
    filtered_notes.sort(key=lambda x: x['updated_at'], reverse=True)

# Add new note button
st.divider()
if st.button("➕ Add New Note", type="primary", use_container_width=True):
    st.session_state.show_add_form = not st.session_state.show_add_form
    st.session_state.edit_note_id = None
    st.rerun()

# Add note form
if st.session_state.show_add_form:
    with st.form("add_note_form", clear_on_submit=True):
        st.subheader("➕ New Note")

        note_title = st.text_input(
            "Title",
            placeholder="Brief summary of the idea or issue",
            max_chars=100
        )

        note_description = st.text_area(
            "Description",
            placeholder="Detailed description of what needs to be done or what the problem is...",
            height=150
        )

        note_type = st.radio(
            "Type",
            ["Improvement", "Bug"],
            horizontal=True
        )

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Save Note", type="primary", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit and note_title and note_description:
            note_id = add_note(
                title=note_title,
                description=note_description,
                note_type=note_type.lower()
            )
            if note_id:
                st.success(f"✅ Note added successfully!")
                st.session_state.show_add_form = False
                st.rerun()
            else:
                st.error("❌ Failed to add note")
        elif submit:
            st.error("⚠️ Please fill in both title and description")

        if cancel:
            st.session_state.show_add_form = False
            st.rerun()

    st.divider()

# Display notes
st.subheader(f"📋 Notes ({len(filtered_notes)})")

if not filtered_notes:
    st.info("No notes found. Click 'Add New Note' to create one!")
else:
    for note in filtered_notes:
        # Determine colors and emojis based on note properties
        type_emoji = "🐛" if note['type'] == "bug" else "💡"

        status_colors = {
            "open": "🔴",
            "in_progress": "🟡",
            "done": "🟢"
        }
        status_emoji = status_colors.get(note['status'], "⚪")

        # Format dates
        created = datetime.fromisoformat(note['created_at']).strftime("%b %d, %Y")
        updated = datetime.fromisoformat(note['updated_at']).strftime("%b %d, %Y")

        # Note card
        with st.container():
            # Check if this note is being edited
            is_editing = st.session_state.edit_note_id == note['id']

            if is_editing:
                # Edit mode
                with st.form(f"edit_note_{note['id']}"):
                    st.markdown(f"### {type_emoji} Editing Note")

                    new_title = st.text_input(
                        "Title",
                        value=note['title'],
                        max_chars=100
                    )

                    new_description = st.text_area(
                        "Description",
                        value=note['description'],
                        height=150
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        new_type = st.radio(
                            "Type",
                            ["Improvement", "Bug"],
                            index=0 if note['type'] == "improvement" else 1,
                            horizontal=True,
                            key=f"type_{note['id']}"
                        )

                    with col2:
                        new_status = st.radio(
                            "Status",
                            ["Open", "In Progress", "Done"],
                            index=["open", "in_progress", "done"].index(note['status']),
                            horizontal=True,
                            key=f"status_{note['id']}"
                        )

                    col1, col2 = st.columns(2)
                    with col1:
                        save_edit = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
                    with col2:
                        cancel_edit = st.form_submit_button("❌ Cancel", use_container_width=True)

                    if save_edit:
                        status_map = {"Open": "open", "In Progress": "in_progress", "Done": "done"}
                        if update_note(
                            note['id'],
                            title=new_title,
                            description=new_description,
                            note_type=new_type.lower(),
                            status=status_map[new_status]
                        ):
                            st.success("✅ Note updated successfully!")
                            st.session_state.edit_note_id = None
                            st.rerun()
                        else:
                            st.error("❌ Failed to update note")

                    if cancel_edit:
                        st.session_state.edit_note_id = None
                        st.rerun()
            else:
                # Display mode
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"### {type_emoji} {note['title']}")
                    st.markdown(note['description'])

                    status_label = note['status'].replace('_', ' ').title()
                    type_label = note['type'].title()
                    st.caption(f"{status_emoji} **Status:** {status_label} | **Type:** {type_label}")
                    st.caption(f"📅 Created: {created} | Updated: {updated}")

                with col2:
                    if st.button("✏️ Edit", key=f"edit_{note['id']}", use_container_width=True):
                        st.session_state.edit_note_id = note['id']
                        st.session_state.show_add_form = False
                        st.rerun()

                    if st.button("🗑️ Delete", key=f"delete_{note['id']}", use_container_width=True):
                        if delete_note(note['id']):
                            st.success("✅ Note deleted!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete note")

            st.divider()

# Statistics
with st.expander("📊 Statistics"):
    total_notes = len(all_notes)
    improvements = len([n for n in all_notes if n['type'] == 'improvement'])
    bugs = len([n for n in all_notes if n['type'] == 'bug'])
    open_notes = len([n for n in all_notes if n['status'] == 'open'])
    in_progress = len([n for n in all_notes if n['status'] == 'in_progress'])
    done_notes = len([n for n in all_notes if n['status'] == 'done'])

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Notes", total_notes)
        st.metric("💡 Improvements", improvements)

    with col2:
        st.metric("🔴 Open", open_notes)
        st.metric("🟡 In Progress", in_progress)

    with col3:
        st.metric("🟢 Done", done_notes)
        st.metric("🐛 Bugs", bugs)

# Help section
with st.expander("ℹ️ Help & Tips"):
    st.markdown("""
    ### How to Use This Page

    1. **Add Notes**: Click "Add New Note" to create a new improvement idea or bug report
    2. **Edit Notes**: Click the edit button on any note to modify its details or status
    3. **Delete Notes**: Remove notes that are no longer relevant
    4. **Filter & Sort**: Use the dropdowns to organize your notes

    ### Note Types

    - **💡 Improvement**: Ideas for new features or enhancements
    - **🐛 Bug**: Issues or problems that need to be fixed

    ### Statuses

    - **🔴 Open**: Not yet started
    - **🟡 In Progress**: Currently working on it
    - **🟢 Done**: Completed!

    ### Tips

    - Be specific in your descriptions
    - Update the status as you make progress
    - Mark items as "Done" when completed to track your accomplishments
    - Use this as your personal backlog for app improvements
    """)
