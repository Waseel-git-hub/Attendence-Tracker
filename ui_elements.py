import streamlit as st
import plotly.graph_objects as go
import calendar
from datetime import date, timedelta, datetime
from backend import Subject, DAY_COLOR, initialize_day, get_lec_for_date, attend_input, check_lec_overlap, calendar_indicator, lec_bunks_count, lec_count, subject_add, subject_meta_info, subject_delete, lec_delete, timetable_input, check_date_in_range,check_holiday,check_lec_on_date, get_timetable_data, get_date_range, get_semesters_list, get_date_ranges_option, delete_timetable_lec, holiday_input, initialize_timetable_range


st.session_state.setdefault("adding_extra_lec", False)

# Subject[str], Month Name[str]
def attendance_stat(subject_selected, selected_month_name):

    attended, _, total_marked, _, _, percent = lec_count(subject_selected, selected_month_name)

    if subject_selected != "All":
        col1, col2 = st.columns([4,1])

        with col1:
            st.markdown(f"### {subject_selected}")
        with col2:
            if st.button("ℹ️", key=f"info_{subject_selected}"):
                st.session_state.b_page = "Attendance"
                st.session_state.selected_date = None
                st.session_state.calendar_month = date.today().month
                st.session_state.calendar_year = date.today().year
                st.session_state.sidebar = False
                st.session_state.button_lock = False
                st.session_state.subject_selected = subject_selected
                st.session_state.page = "Subject_info"
                st.rerun()

    if total_marked == 0:
        st.info("No lectures marked")
        return

    bunk = lec_bunks_count(attended, total_marked, subject_selected)
    if bunk == 0 or bunk == -1:
        st.warning("You need to attend next lecture")
    elif bunk > 0:
        st.success(f"You can skip {bunk} lectures")
    elif bunk < 0:
        st.error(f"You need to attend {-bunk} lectures")

    if subject_selected != "Overall":
        col1, col2 = st.columns(2)
        col1.write(f"Attended: {attended}")
        col2.write(f"Total: {total_marked}")
        st.write(f"Attendance: {percent:.2f}%")

    else:
        st.metric(label="",value=f"{percent:.2f}%",delta=f"{attended}/{total_marked} lectures" if total_marked else "No lectures marked")

    st.progress(percent / 100)

# month[mm], year[yyyy], sub[str]
def calendar_show(month, year, subject_selected=None, view_only=False):
    if month is not None:
        st.session_state.calendar_month = month
    if year is not None:
        st.session_state.calendar_year = year

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(st.session_state.calendar_year, st.session_state.calendar_month)

    with st.container(border = True):
        cols = st.columns(7)
        for i, day_name in enumerate(calendar.day_abbr):
            cols[i].write(day_name)

    for week in month_days:

        for i, day in enumerate(week):

            if day.month != st.session_state.calendar_month:

                cols[i].button("-", key= f"{day}")
                continue

            date_str = day.isoformat()
            status= calendar_indicator(date_str, subject_selected, view_only)
            
            if cols[i].button(f"{day.day} {DAY_COLOR[status]}", key=date_str, disabled = (date_str == st.session_state.selected_date) or st.session_state.button_lock):

                st.session_state.selected_date = date_str
                st.rerun()

# sub[str], month[str]
def circular_progress(subject_selected, selected_month_name):
    attended, absent, total_marked, _, _, percent = lec_count(subject_selected, selected_month_name)
    if total_marked == 0:
        st.info("No lectures marked")
        return
    fig = go.Figure(go.Pie(
        values=[attended, absent],
        hole=0.7,
        sort=False,
        textinfo='none')
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        annotations=[dict(
            text=f"{percent:.1f}%",
            x=0.5, y=0.5,
            font_size=24,
            showarrow=False
        )]
    )
    st.plotly_chart(fig, use_container_width=True)

# date[yyyy-mm-dd], sub[str]
def show_lec_on_date(date_selected, subject_selected = None, view_only=False):
    initialize_day(date_selected)
    col1, col2, col3 = st.columns([4,2,1])
    with col1:
        st.subheader(f"📅 {date.fromisoformat(date_selected).strftime("%d|%m|%Y")} - {date.fromisoformat(date_selected).strftime("%A")}")
    if not view_only:
        with col2:
            if not st.session_state.adding_extra_lec :
                if st.button("Add Extra Lecture"):
                    st.session_state.button_lock = True
                    st.session_state.adding_extra_lec = True
                    st.rerun()
            else :
                if st.button("Cancel"):
                    st.session_state.adding_extra_lec = False
                    st.session_state.button_lock = False
                    st.rerun()

        with col3:
            if st.button("🔄️"):
                st.rerun() 
        

    if not st.session_state.adding_extra_lec:
        if check_lec_on_date(date_selected):
            lectures = get_lec_for_date(date_selected, subject_selected, view_only)
            if not view_only:
                c1, c2, c3, c4, c5 = st.columns([2,2,4,4,1])
                c1.write("Subject")
                c2.write("Timing")
                c3.write("Room No.")
                c4.write("Action")
                c5.write("Delete")
            else:
                c1, c2, c3, c4 = st.columns([2,2,2,2])
                c1.write("Subject")
                c2.write("Timing")
                c3.write("Room No.")
                c4.write("Status")

            for lec in lectures:
                if lec["Status"] == "Unmarked" and view_only:
                    continue

                with st.container(border=True):
                    c1, c2, c3, c4, c5, c6, c7 = st.columns([2,2,1,2,2,2,1])
                    c1.markdown(f"**{lec['Subject']}**")
                    c2.write(f"{lec['Start']} - {lec['End']}")
                    c3.write(lec["Room"])

                    if lec["Status"] in ("Normal", "Unmarked") and not view_only:

                        if c4.button("✅Present", key=f"p_{lec['Lec_UID']}", disabled= st.session_state.button_lock):

                            attend_input(lec["Subject"],date_selected,lec["Start"],lec["End"],True,lec["Lec_UID"],lec["Room"],extra=lec["Extra"])
                            st.rerun()

                        if c5.button("❌Absent", key=f"a_{lec['Lec_UID']}", disabled= st.session_state.button_lock):

                            attend_input(lec["Subject"],date_selected,lec["Start"],lec["End"],False,lec["Lec_UID"],lec["Room"],extra=lec["Extra"])
                            st.rerun()

                        if c6.button("🚫Cancel", key=f"cancel_{lec['Lec_UID']}", disabled= st.session_state.button_lock):

                            attend_input(lec["Subject"],date_selected,lec["Start"],lec["End"],None,lec["Lec_UID"],lec["Room"],"Canceled", lec["Extra"])
                            st.rerun()

                    else:
                    
                        if lec.get("Status") == "Canceled":

                            if lec.get("Extra"):
                                c4.write("Extra")
                            if not view_only:
                                c5.write("🚫 Canceled")
                            else:   
                                c6.write("🚫 Canceled")

                        elif lec.get("Status") == "Present":

                            if lec.get("Extra"):
                                c4.write("Extra")
                            if not view_only:
                                c5.write("✅ Attended")
                            else:
                                c6.write("✅ Attended")

                        elif lec.get("Status") == "Absent":

                            if lec.get("Extra"):
                                c4.write("Extra")
                            if not view_only:
                                c5.write("❌ Missed")
                            else:
                                c6.write("❌ Missed")

                        elif lec.get("Status") == "Unmarked" and view_only:
                            continue

                    if not view_only:
                        if lec.get("Status") != "Unmarked":

                            if c6.button("Clear", key= f"clear_{lec['Lec_UID']}", disabled= st.session_state.button_lock):

                                attend_input(lec["Subject"], date_selected, lec["Start"],lec["End"],None,lec["Lec_UID"],lec["Room"], extra=lec["Extra"])
                                st.rerun()

                        if c7.button("🗑", key= f"del_{lec['Lec_UID']}", disabled= st.session_state.button_lock):
                            lec_delete(lec['Subject'], date_selected, lec['Lec_UID'])
                            st.rerun()
        else :
            st.info("No lectures scheduled for this date.")

    else:
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            sub = st.selectbox("Subject", list(Subject.keys()))
            start = st.time_input("Start Time")

        with col2:
            room = st.text_input("Room")
            end = st.time_input("End Time", (datetime.combine(date.today(), start) + timedelta(minutes=60)).time())
        
        with col1:
            if st.button("Add Lecture", disabled= start >= end or check_lec_overlap(start, end, date_selected, False)):
                attend_input(sub, date_selected, start.strftime("%H:%M"), end.strftime("%H:%M"), None, None, room, extra = True)
                st.session_state.button_lock = False
                st.session_state.adding_extra_lec = False
                st.rerun()
        with col2:
                if start >= end:
                    st.error("End time must be after start time")
                elif check_lec_overlap(start, end, date_selected, False):
                    st.error("Time conflicts with an Active lecture")

# show timetable for selected parametres
def show_timetable(day_selected, edit = False, recent = True, date_range = None, sem = None):
    if recent:
        _, date_range, sem = get_date_range(str(date.today()))
        st.session_state.date_range_selected = date_range
        st.session_state.sem_selected = sem
    found, lectures = get_timetable_data(sem, date_range, day_selected)
    if found and lectures :
        for lec in lectures :
            with st.container(border=True):
                    if edit:
                        col1, col2, col3, col4 = st.columns([2,2,2,1])

                        col1.markdown(f"🕒 {lec['Start']} - {lec['End']}")
                        col2.markdown(f"#### {lec['Subject']}")
                        col3.markdown(f"📍 {lec.get('Room','None')}")
                        if col4.button("🗑️", key = f"delete_{lec['Subject']}_{lec['Start']}"):
                            delete_timetable_lec(sem, date_range, day_selected, lec["Subject"], lec["Start"], lec["End"])
                            st.rerun()
                    else:
                        col1, col2, col3 = st.columns([2,3,1])
                        col1.markdown(f"🕒 {lec['Start']} - {lec['End']}")
                        col2.markdown(f"#### {lec['Subject']}")
                        col3.markdown(f"📍 {lec.get('Room','-')}")
    else:
        st.info("No Lecture is there")
    st.divider()

# title[str]
def semi_page_head(title, back_button = True):
    col1, col2 = st.columns([2,3])

    with col1:
        if back_button:
            if st.button("⬅️ Back"):
                st.session_state.page = st.session_state.b_page
                st.session_state.b_page = None
                st.session_state.sidebar = True
                st.rerun()

    with col2:
        st.title(title)
    
    st.divider()

# sub[str]         
def subject_card(subject_selected):
    _, _, _, _, _, percent = lec_count(subject_selected)
    with st.container(border=True):
        col1, col2, col3 = st.columns([2,3,1])
        with col1:
           st.markdown(f"#### {subject_selected}")
        with col2:
            st.progress(percent / 100, text=f"Overall Attendance: {percent:.2f}%")
        with col3:
            if st.session_state.expanded_options_subject != subject_selected:
                if st.button("🔽", key=f"expand_{subject_selected}", disabled= st.session_state.button_lock):
                    st.session_state.expanded_options_subject = subject_selected
                    st.rerun()
            else:
                if st.button("🔼", key=f"collapse_{subject_selected}", disabled= st.session_state.button_lock):
                    st.session_state.expanded_options_subject = None
                    st.rerun()

        if st.session_state.expanded_options_subject == subject_selected:
            st.divider()
            col1, col2, col3 = st.columns([1,1,1])

            with col1:
                if st.session_state.delete_subject is None:
                    if st.button("ℹ️ Subject Info", key=f"info_{subject_selected}"):
                        st.session_state.b_page = "Subjects"
                        st.session_state.selected_date = None
                        st.session_state.calendar_month = date.today().month
                        st.session_state.calendar_year = date.today().year
                        st.session_state.sidebar = False
                        st.session_state.subject_selected = subject_selected
                        st.session_state.button_lock = False
                        st.session_state.page = "Subject_info"
                        st.rerun()
                elif st.session_state.delete_subject == subject_selected:
                    st.warning("Delete This Subject?")

            with col2:

                if st.session_state.delete_subject == subject_selected:
                    if st.button("✅ Confirm Deletion", key=f"confirm_delete_{subject_selected}"):
                        subject_delete(st.session_state.delete_subject)
                        st.session_state.delete_subject = None
                        st.session_state.button_lock = False
                        st.session_state.expanded_options_subject = None
                        st.rerun()
                
            with col3:

                if st.session_state.delete_subject is None:
                    if st.button("🗑 Delete Subject", key=f"delete_{subject_selected}"):
                        st.session_state.button_lock = True
                        st.session_state.delete_subject = subject_selected
                        st.rerun()
                
                elif st.session_state.delete_subject == subject_selected:
                    if st.button("❌ Cancel Deletion", key=f"cancel_delete_{subject_selected}"):
                        st.session_state.button_lock = False
                        st.session_state.delete_subject = None
                        st.rerun()

#sub[str]
def subject_info_card(subject_selected):
    data, min_attend, faculty = subject_meta_info(subject_selected)
    col1, col2 = st.columns([4,1])
    with col1:
        st.markdown(f"# {subject_selected}")
    with col2:
        if st.button("✏️ Edit", key=f"edit_{subject_selected}"):
            st.session_state.subject_selected = subject_selected
            st.session_state.sidebar = False
            st.session_state.page = "Subject_edit"
            st.rerun()

# sub[str]
def subject_input(old_sub = None):
    old_sub_name = old_faculty = ""
    old_min_attend = 75
    data = None
    if old_sub != None:
        old_sub_name = old_sub
        data, old_min_attend, old_faculty = subject_meta_info(old_sub)

    with st.container(border=True):
        new_sub_name = st.text_input("Subject Name", key= "new_sub_input", value = old_sub_name).strip()
        faculty = st.text_input("Faculty Name", value = old_faculty)
        min_attend = st.number_input("Minimum Attendance Criteria", 0, 100, old_min_attend, 5)/100
        col1, col2 = st.columns([4,1])
        with col1:
            if st.button(f"✅ {'Add New' if old_sub == None else 'Edit'} Subject"):
                subject_add(new_sub_name, min_attend, data, faculty)
                if old_sub != None:         #edit
                    subject_delete(old_sub_name)
                    st.session_state.page = "Subject_info"
                else:
                    st.session_state.add_new_sub = False
                st.rerun()
        with col2:
            if st.button("❎ Cancel"):
                if old_sub == None:             
                    st.session_state.add_new_sub = False 
                else:
                    st.session_state.page = "Subject_info"
                        
                st.rerun()


def day_select():
    cols = st.columns(7)
    for  i, day_names in enumerate(calendar.day_name):
        with cols[i]:
            if st.button(day_names , key=i, disabled = st.session_state.day_selected == day_names) : 
                st.session_state.day_selected =  day_names
                st.rerun()
            




# under progress----------------------------------------------


    

def timetable_select_1():
    col1, col2 = st.columns(2)
    sem = col1.selectbox("Select Semester", get_semesters_list())
    date_range = get_date_ranges_option(sem)[col2.selectbox("Select Date Range", get_date_ranges_option(sem))]
    if col1.button("Select"):
        st.session_state.sem_selected = sem
        st.session_state.date_range_selected = date_range
        st.session_state.edit_timetable = True
        st.session_state.sidebar = False

    st.divider()

def timetable_select():
    for sem in get_semesters_list():
        with st.expander(sem):
            for date_range, key in get_date_ranges_option(sem).items():
                with st.container(border = True):
                    col1, col2 = st.columns([4,1])
                    col1.markdown(date_range)
                    if col2.button("Edit", key = f"{key}_edit"):
                        st.session_state.sem_selected = sem
                        st.session_state.date_range_selected = key
                        st.session_state.edit_timetable = True
                        st.session_state.sidebar = False
                        st.rerun()

def edit_timetable_meta(sem, date_range ):
    old_start, old_end = date_range.split("_to_")
    with st.expander("➕ Add Holidays"):
        with st.container(border = True):
            col1, col2 = st.columns(2)
            holiday_reason = col1.text_input("Reason")
            holiday_date = str(col2.date_input("Select Date"))
            if col1.button("Done"):
                holiday_input(holiday_date, holiday_reason)
                st.rerun()
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start Date", old_start)
    end_date = col2.date_input("End Date", old_end)

def add_timetable_lec(day_selected, date_range, sem):
    
    with st.container(border = True):
        col1, col2 = st.columns(2)
        with col1:
            subject_selected = st.selectbox("Subject", list(Subject.keys()), key= f"subject_{day_selected}")
            lec_start = st.time_input("Start Time")
        with col2:
            room = st.text_input("Room", key = "room_input")
            lec_end = st.time_input("End Time", (datetime.combine(date.today(), lec_start) + timedelta(minutes=60)).time())
        if col1.button("➕ Add Lecture",key = f"Add_lec_to_template" , disabled= lec_start >= lec_end):
            timetable_input(st.session_state.sem_selected, st.session_state.date_range_selected, st.session_state.day_selected, subject_selected, lec_start.strftime("%H:%M"), lec_end.strftime("%H:%M"), room)
            st.rerun()
        if col1.button("💾 Save"):
            initialize_timetable_range(st.session_state.date_range_selected)
            st.session_state.add_lec_timetable = False
            st.rerun()

        if lec_start >= lec_end:
            col2.error("End time must be after start time")



