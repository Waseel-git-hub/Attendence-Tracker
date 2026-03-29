import streamlit as st
import calendar


from backend import Subject
from datetime import date
from ui_elements import attendance_stat, subject_input, circular_progress, show_lec_on_date, calendar_show,  subject_card, subject_info_card, semi_page_head, day_select, show_timetable, timetable_select, edit_timetable_meta, add_timetable_lec

#---------- session state ----------


st.set_page_config( page_title="The College Hub", layout="wide", initial_sidebar_state="expanded")
if "page" not in st.session_state:
    st.session_state.button_lock = False
    st.session_state.selected_date = date.today().isoformat()
    st.session_state.adding_extra_lec = False
    st.session_state.page = "Homepage"

st.session_state.setdefault("sidebar", True)
st.session_state.setdefault("b_page", None)
st.session_state.setdefault("subject_selected", None)
st.session_state.setdefault("adding_extra", False)


# ---------- sidebar ----------


if st.session_state.sidebar:
    with st.sidebar:
        st.title("The College Hub 🎓")
        
        if st.button("🏠 Homepage", disabled = st.session_state.page == "Homepage"):
            st.session_state.button_lock = False
            st.session_state.adding_extra_lec = False
            st.session_state.selected_date = date.today().isoformat()
            st.session_state.page = "Homepage"
            st.rerun()

        if st.button("📅 Calendar View", disabled = st.session_state.page == "Calendar"):
            st.session_state.selected_date = date.today().isoformat()
            st.session_state.button_lock = False
            st.session_state.calendar_month = date.today().month
            st.session_state.calendar_year = date.today().year
            st.session_state.adding_extra_lec = False
            st.session_state.page = "Calendar"
            st.rerun()

        if st.button("📊 Attendance", disabled = st.session_state.page == "Attendance"):
            st.session_state.page = "Attendance"
            st.rerun()

        if st.button("📜 Subjects", disabled = st.session_state.page == "Subjects"):
            st.session_state.expanded_options_subject = None
            st.session_state.add_new_sub = False
            st.session_state.delete_subject = None
            st.session_state.button_lock = False  
            st.session_state.page = "Subjects"
            st.rerun()

        with st.expander("🗓 Timetable"):
            
            if st.button("View Current Timetable"):
                st.session_state.timetable_edit = False
                st.session_state.day_selected = "Monday"
                st.session_state.page = "Timetable"
            
            if st.button("Edit Timetable"):
                st.session_state.sem_selected = None
                st.session_state.date_range_selected = None
                st.session_state.edit_timetable = False
                st.session_state.add_lec_timetable = False
                st.session_state.day_selected = "Monday"
                st.session_state.page = "Edit_Timetable"

                st.rerun()
            
            if st.button("Add New Timetable"):
                st.session_state.page = "New_Timetable_Template"
                st.rerun()


#-------------- PAGES ---------------


if st.session_state.page == "Attendance":
    
    col1, col2 = st.columns([3,1])
    with col1:
        st.title("📈 Attendance Statistics")
    with col2:
        month_map = { "Overall": "All", **{calendar.month_name[i]: f"{i:02}" for i in range(1, 13)}}
        month_name = st.selectbox("📅 Select Month", list(month_map.keys()))

    st.divider()

    st.subheader(f"📊 Attendance — {month_name}")
    attendance_stat("All", month_name)

    st.divider()

    st.subheader("📚 Subject-wise Attendance")
    subjects = list(Subject.keys())
    col = st.columns(2)
    for i,subject in enumerate(subjects):
        with col[i%2]:
            with st.container(border= True):
                attendance_stat(subject, month_name)
      
#-------------------------------

if st.session_state.page == "Calendar":
   
    st.title(f"Calendar View 📅")
    col1, col2, col3 = st.columns([4,6,1])

    if col1.button("◀", disabled= st.session_state.button_lock) :
        if st.session_state.calendar_month == 1:
            st.session_state.calendar_month = 12
            st.session_state.calendar_year -= 1
        else:
            st.session_state.calendar_month -= 1
        st.rerun()    
    with col2:        
        st.subheader(f"{calendar.month_name[st.session_state.calendar_month]}  {st.session_state.calendar_year}")    
    if col3.button("▶", disabled= st.session_state.button_lock):        
        if st.session_state.calendar_month == 12:
            st.session_state.calendar_month = 1
            st.session_state.calendar_year += 1
        else:
            st.session_state.calendar_month += 1
        st.rerun()
    calendar_show(month=st.session_state.calendar_month, year=st.session_state.calendar_year)
    st.divider()
    show_lec_on_date(st.session_state.selected_date)

#-------------------------------

if st.session_state.page == "Homepage":

    st.title("Welcome to The College Hub")
    
    st.divider()

    st.header(f"Today's Lectures")
    show_lec_on_date(st.session_state.selected_date)

#-------------------------------  

if st.session_state.page == "Subjects":
    st.title("📜 Manage Subjects")
    
    st.divider()

    col1, col2 = st.columns([3,1])
    
    with col2:
        
        if not st.session_state.add_new_sub:
            if st.button("Add New Subject", key = "add_sub", disabled = st.session_state.button_lock):
                st.session_state.add_new_sub = True
                st.rerun()


    if st.session_state.add_new_sub:
        subject_input(None)
            

    else:
        for subject_selected in Subject.keys():
            subject_card(subject_selected)

#-------------------------------

if st.session_state.page == "Subject_edit":

    semi_page_head(" Edit Subject Details", False)

    subject_input(st.session_state.subject_selected)

#-------------------------------

if st.session_state.page == "Subject_info":
 
    semi_page_head("Subject Information")

    subject_info_card(st.session_state.subject_selected)

    st.info(" More Info will be added soon!")
    

    
    st.divider()

    with st.expander("📅 Attendance Stats"):

        col1, col2, col3 = st.columns([4,6,1])

        if col1.button("◀") :
            if st.session_state.calendar_month == 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
            else:
                st.session_state.calendar_month -= 1
            st.session_state.selected_date = None
            st.rerun()

        with col2:
            st.subheader(f"{calendar.month_name[int(st.session_state.calendar_month)]}  {st.session_state.calendar_year}")

        if col3.button("▶"):
            if st.session_state.calendar_month == 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
            else:
                st.session_state.calendar_month += 1
            st.session_state.selected_date = None
            st.rerun()


        col1, col2 = st.columns([3,1])
        with col1:
            calendar_show(st.session_state.calendar_month, st.session_state.calendar_year, st.session_state.subject_selected, True)        
        with col2:
            circular_progress(st.session_state.subject_selected, calendar.month_name[int(st.session_state.calendar_month)])
    
        if st.session_state.selected_date:
            st.divider()
            show_lec_on_date(st.session_state.selected_date, st.session_state.subject_selected, True)

#-------------------------------

if st.session_state.page == "Timetable":

    col1, col2 = st.columns([2,3])

    with col1:
        if st.button("✏️ Edit"):
            st.session_state.page = "Edit_Timetable"
            st.session_state.b_page = "Timetable"
            st.session_state.add_lec_timetable = False
            st.session_state.edit_timetable = True
            st.session_state.sidebar = False
            st.rerun()

    with col2:
        st.title("▦ Timetable")
    st.divider()

    day_select()
    st.divider()
    
    show_timetable(st.session_state.day_selected) 

#-------------------------------

if st.session_state.page == "New_Timetable_Template":
    semi_page_head("New Timetable Template", False)
    st.info("IT WILL BE CREATED SHORTLY !!")

#-------------------------------

if st.session_state.page == "Edit_Timetable":
    semi_page_head("Edit Timetable", False)

    if not (st.session_state.add_lec_timetable or st.session_state.edit_timetable):
        timetable_select()

    elif st.session_state.edit_timetable:
        if not st.session_state.add_lec_timetable:
            edit_timetable_meta(st.session_state.sem_selected, st.session_state.date_range_selected)
            st.divider()
        day_select()
        show_timetable(st.session_state.day_selected, True, False, st.session_state.date_range_selected, st.session_state.sem_selected)
        
        if st.session_state.add_lec_timetable : 
            add_timetable_lec(st.session_state.day_selected, st.session_state.date_range_selected, st.session_state.sem_selected)
            
        
        col1, col2 = st.columns([4,1])
        if not st.session_state.add_lec_timetable:
            if col2.button("➕ Add Lecture"):
                st.session_state.add_lec_timetable = True
                st.rerun()
            if col1.button("💾 Save"):
                if st.session_state.b_page:
                    st.session_state.page = st.session_state.b_page
                    st.session_state.b_page = None
                st.session_state.sem_selected = None
                st.session_state.date_range_selected = None
                st.session_state.edit_timetable = False
                st.session_state.sidebar = True
                st.rerun()


    









