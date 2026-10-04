import streamlit as st
from datetime import datetime

# Initialize session state if not already initialized
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.tasks = []
    st.session_state.notification_count = 0
    st.session_state.login_error = None

def validate_user(email, password):
    # Dummy validation for demonstration purposes
    return email == "user@example.com" and password == "password"

def add_task(title, description, due_date, priority):
    task_id = len(st.session_state.tasks) + 1
    new_task = {
        "id": task_id,
        "title": title,
        "description": description,
        "due_date": due_date,
        "priority": priority,
        "status": False,
        "created_at": datetime.now()
    }
    st.session_state.tasks.append(new_task)

def get_pending_tasks():
    return [task for task in st.session_state.tasks if not task['status']]

def show_login_page():
    st.subheader("Login")
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        # Validate credentials
        if validate_user(email, password):
            st.session_state.user_id = email
            st.success("Logged in successfully!")
            time.sleep(1)
            st.experimental_rerun()
        else:
            st.error("Invalid credentials!")

    st.subheader("Need an account?")
    if st.button("Sign Up"):
        show_signup_page()

def show_signup_page():
    # Form fields for email, password, confirm password
    # Add validation and store new user in memory
    pass

def show_dashboard():
    st.sidebar.title("Menu")
    if st.sidebar.button("Dashboard"):
        pass
    if st.sidebar.button("My Tasks"):
        show_tasks_page()
    if st.sidebar.button("Notifications"):
        show_notifications()
    if st.sidebar.button("Profile"):
        show_profile()

def show_tasks_page():
    # Display task creation form and task list
    with st.form(key='task_form'):
        title = st.text_input('Title')
        description = st.text_area('Description', max_chars=200)
        due_date = st.date_input('Due Date')
        priority = st.selectbox('Priority', ['High', 'Medium', 'Low'])
        create_task_button = st.form_submit_button(label='Create Task')

    if create_task_button:
        add_task(title, description, due_date, priority)

    st.subheader("Pending Tasks")
    for task in get_pending_tasks():
        with st.container():
            st.write(f"**{task['title']}** - {task['description']}")
            st.write(f"Due Date: {task['due_date']}, Priority: {task['priority']}")
            if st.checkbox('Completed', value=task['status']):
                task['status'] = True
            st.button('Delete', on_click=lambda t=task: delete_task(t))

def show_notifications():
    # Check for overdue tasks
    today = datetime.today().date()
    for task in get_pending_tasks():
        if task["due_date"] <= today:
            st.warning(f"Task '{task['title']}' is overdue!")

def show_profile():
    # Display user details and edit profile form
    pass

def delete_task(task):
    st.session_state.tasks.remove(task)

def main():
    st.title("AI Task Reminder")
    
    # Check if user is logged in
    if "user_id" not in st.session_state:
        show_login_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()