

import json, os
from datetime import date, time, timedelta, datetime
from math import floor

Timetable = {"2026-01-01_to_2026-03-01" : {"Holidays" : {}, "Weekly" : {"Monday" : [], "Tuesday": [], "Wednesday": [], "Thursday": [], "Friday": [], "Saturday": [], "Sunday": []}}}
Subject = {}

def fileload(file, Raw_data):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(Raw_data,f,indent=4)
        return Raw_data
    else:
        with open(file, "r") as f:
            return json.load(f)

Subject = fileload("Attendence.json", Subject)
Timetable = fileload("Timetable.json", Timetable)

Month_name_dict = {"January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06", "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"}

DAY_COLOR = {"All_Attended": "🟢", "All_Absent": "🔴", "Mixed": "🟠", "All_Unmarked": "⚪", "Some_Marked": "🟡", "Canceled": "🟣", None : "⚫"}



# input to data\ sub[str], date[str(yyyy-mm-dd)], time[str(hh:mm)]
def attend_input(subject_selected, lec_date, start_time, end_time, present, lec_uid, room_no = "-", lec_type = "Normal", extra = False):        
    global Subject

    Subject[subject_selected]["Attendence"].setdefault(lec_date, {})   

    if lec_uid is None:
        lec_uid = lec_uid_generate(lec_date, start_time, end_time, subject_selected)

    Subject[subject_selected]["Attendence"][lec_date][lec_uid] = {"Start": start_time, "End": end_time, "Room": room_no, "Present": present, "Type": lec_type, "Extra": extra}
    
    Subject[subject_selected]["Attendence"][lec_date] = dict(sorted(Subject[subject_selected]["Attendence"][lec_date].items(), key=lambda x: time_to_minutes(x[1]["Start"])))

    meta = Subject[subject_selected].get("_meta", {})

    sorted_dates = dict(sorted(((k, v) for k, v in Subject[subject_selected]["Attendence"].items()), key=lambda x: x[0]))

    Subject[subject_selected] = {"_meta": meta, "Attendence" : sorted_dates}

    save_to_file(Subject, "Attendence.json")
    return True

# date[str(yyyy-mm-dd)]
def calendar_indicator(date_selected, subject_selected = None, view_only=False):
    if check_lec_on_date(date_selected, subject_selected):
    
        total = present = absent = unmarked = canceled = 0

        for l in get_lec_for_date(date_selected, view_only= view_only):
            if subject_selected is None or l["Subject"] == subject_selected:
                total += 1
                if l["Status"] == "Present":
                    present += 1
                elif l["Status"] == "Absent":
                    absent += 1
                elif l["Status"] == "Unmarked":
                    unmarked += 1
                elif l["Status"] == "Canceled":
                    canceled += 1


        if canceled > 0 and view_only:
            return "Canceled"

        active = total - canceled
        if active == 0:
            return None

        if present == active:
            return "All_Attended"
        elif absent == active:
            return "All_Absent"
        elif present + absent == active:
            return "Mixed"
        elif not view_only :
            if unmarked == active:
                return "All_Unmarked"
            else:
                return "Some_Marked"
        
    else:
        return None

#::::::::::::::::::::::::::::
# check if there is a overlap time[str,time] on date[str(yyyy-mm-dd)]
def check_lec_overlap(start_time, end_time, date_selected, timetable = True):
    start_time = time_to_minutes(start_time)
    end_time = time_to_minutes(end_time)
    
    if not timetable and check_lec_on_date(date_selected):
        lectures = get_lec_for_date(date_selected)

        for lec in lectures:
            overlap = start_time < time_to_minutes(lec["End"]) and end_time > time_to_minutes(lec["Start"])

            if overlap and lec["Status"] != "Canceled":
                return True
        
    day = date.fromisoformat(date_selected).strftime("%A")
    
    for lec in Timetable.get(day, []):
        if (start_time < time_to_minutes(lec["End"]) and end_time > time_to_minutes(lec["Start"])):
            return True
    
    return False

# check if lec exist on date 
def check_lec_on_date(date_selected, subject_selected = None):
    for subject, subject_data in Subject.items():
        attendence_data = subject_data.get("Attendence", {})

        if (subject_selected and subject != subject_selected) or (date_selected not in attendence_data):
            continue        # filtering subject

        return True
    
    return False

# check if the date is between a range 
def check_date_in_range(date_selected, date_range = None, start_date = None, end_date = None):
    if date_range:
        start_date, end_date = date_range_converter(date_range = date_range)
    if date_selected <= end_date and date_selected >= start_date:
        return True
    return False

# date[str("yyyy-mm-dd")]
def date_range_converter(date_start = None, date_end = None, date_range = None):
    if date_range is None:
        return f"{date_start.isoformat()}_to_{date_end.isoformat()}"
    else:
        return date_range.split("_to_")

# format date range str["yyyy-mm-dd" -> "dd mmm(name) yyyy"]
def date_range_formatter(date_range):
    start, end = date_range_converter(date_range = date_range)
    start = datetime.strptime(start, "%Y-%m-%d")
    end = datetime.strptime(end, "%Y-%m-%d")
    return (f"{start.day} {start.strftime('%b')} {start.year}   →   {end.day} {end.strftime('%b')} {end.year}")

# get the range in which date belongs
def get_date_range(date_selected):
    for sem, ranges in Timetable.items():
        for date_ranges, _ in ranges.items():
            if check_date_in_range(date_selected, date_ranges):
                return True, date_ranges, sem
    return False, None, None

# for ui
def get_semesters_list():
    return list(Timetable.keys())

# for ui
def get_date_ranges_option(sem):
    options = {}

    for key in Timetable.get(sem, {}):
        if key.startswith("_"):
            continue
        label = date_range_formatter(key)
        options[label] = key

    return options

# return timetable for day or whole
def get_timetable_data(sem , date_range, day_selected = None):
    weekly = Timetable[sem][date_range]["Weekly"]
    if day_selected:
        if weekly[day_selected]:
            return True, weekly[day_selected]
        else:
            return False, weekly[day_selected]
    
    return True, weekly

# count bunk/ present[int], total[int], subject[str]
def lec_bunks_count(present, total_marked, subject_selected):

    if total_marked == 0:
        return 0  # No data yet
    
    if subject_selected != "All":
        min_attend = Subject[subject_selected]["_meta"]["Min_Attend"]
    else:
        min_attend = 0.75

    lec_bunk = floor((present - min_attend * total_marked) / min_attend)
    return lec_bunk

# count lec for Subject[str] and Month Name[str]
def lec_count(subject_selected = "All", selected_month_name = "All"):
    attended_lec = absent_lec = unmarked_lec = total_mark_lec = 0

    if subject_selected == "All" :
        subject_selecteds = Subject.keys()

    else:
        if subject_selected not in Subject:
            return 0, 0, 0, 0, 0, 0
        subject_selecteds = [subject_selected]

    for subject in subject_selecteds:                                       

        for lecture_date, lectures in Subject.get(subject, {}).get("Attendence", {}).items():

            if selected_month_name not in ("All", "Overall"):
                month_value = Month_name_dict.get(selected_month_name)
                if not month_value:
                   continue
                try:
                   if lecture_date[5:7] != month_value:
                       continue
                except:
                   continue
            for lec in lectures.values():
                if (lec["Type"] == "Canceled"):
                    continue
                elif (lec["Present"] is None):
                    unmarked_lec += 1
                    continue
                if lec["Present"]:
                    attended_lec += 1
                elif lec["Present"] == False:
                    absent_lec += 1
    total_mark_lec = attended_lec + absent_lec                
    total_lec = total_mark_lec + unmarked_lec
    percent = (attended_lec / total_mark_lec) * 100 if total_mark_lec else 0

    return attended_lec, absent_lec, total_mark_lec, unmarked_lec, total_lec, percent

# delete a specific lecture
def lec_delete(subject_selected, date_selected, lec_uid):
    if subject_selected in Subject:
        if date_selected in Subject[subject_selected]["Attendence"]:
            Subject[subject_selected]["Attendence"][date_selected].pop(lec_uid, None)
    save_to_file(Subject, "Attendence.json")
    return True

# get lectures for date[str(yyyy-mm-dd)] 
def get_lec_for_date(date_selected, subject_selected = None, view_only=False):
    
    lectures_on_date = []
    for subject, subject_data in Subject.items():
        attendence_data = subject_data.get("Attendence", {})
        if (subject_selected and subject != subject_selected) or (date_selected not in attendence_data):
            continue
        for lec_uid, lec_data in attendence_data[date_selected].items():
            extra = lec_data.get("Extra", False)
            if lec_data["Type"] == "Canceled":
                status = "Canceled"
            elif lec_data["Present"] is None:
                if view_only:
                    continue
                status = "Unmarked"
            elif lec_data["Present"]:
                status = "Present"
            else:
                status = "Absent"
            lectures_on_date.append({"Subject": subject,"Start": lec_data["Start"],"End": lec_data["End"],"Room": lec_data.get("Room", "-"),"Lec_UID": lec_uid,"Status": status,"Date": date_selected,"Extra" : extra})

    return sorted(lectures_on_date, key=lambda x: time_to_minutes(x["Start"]))

# gen UID\ date[str(yyyy-mm-dd)], time[str(hh:mm)], subject[str]
def lec_uid_generate(date_selected, start_time, end_time, subject_selected):
    return f"{start_time.replace(":", "")}_{subject_selected[:3].upper()}_{date_selected.replace("-", "")}_{end_time.replace(":", "")}"

# save_to_file data -> file
def save_to_file(data, file):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# conv time(hh:mm)[str, time] to minutes[int] 
def time_to_minutes(t):     
    if isinstance(t, time):
        return t.hour * 60 + t.minute
    if isinstance(t, str):
        h, m = map(int, t.split(":"))
        return h * 60 + m

# add subject to file/ name[str], attend[0<float<1]
def subject_add(subject_name, min_attend, data=None, faculty = "-"):
    if (not subject_name) or (subject_name in Subject):
        return Subject

    if data is None:
        data = {
            "_meta": {
                "Faculty": faculty,
                "Min_Attend": min_attend
            },
            "Attendence" : {}
        }
    Subject[subject_name] = data
    temp = dict(sorted(Subject.items(), key=lambda x: x[0].lower()))
    save_to_file(temp, "Attendence.json")
    return temp

# delete subject from file
def subject_delete(subject_selected):
    del Subject[subject_selected]
    save_to_file(Subject, "Attendence.json")

# give meta info for sub[str]
def subject_meta_info(subject_selected):
    subject_data = Subject.get(subject_selected, {})
    meta = subject_data.get("_meta", {})
    min_attend = int(meta.get("Min_Attend", 0.75) * 100)
    faculty = meta.get("Faculty", "-")
    return subject_data, min_attend, faculty

# date[str(yyyy-mm-dd)]
def sem_create(date_start, date_end, sem):
    date_range = date_range_converter(date_start, date_end)
    Timetable[sem] = {
        date_range : {
            "Holidays" : {},
            "Weekly" : { "Monday" : [], "Tuesday" : [], "Wednesday" : [], "Thursday" : [], "Friday" : [], "Saturday" : [], "Sunday" : []}
        }
    }

# for template
def timetable_input(sem, date_range, day_selected, subject_selected, lec_start, lec_end, room = ""):
    lectures = Timetable[sem][date_range]["Weekly"][day_selected]
    lec_add = {
        "Subject": subject_selected,
        "Start": lec_start,
        "End": lec_end,
        "Room": room
    }
    for i, lec in enumerate(lectures):
        if time_to_minutes(lec_start) < time_to_minutes(lec["Start"]):
            lectures.insert(i, lec_add)
            save_to_file(Timetable, "Timetable.json")
            return
    lectures.append(lec_add)
    save_to_file(Timetable, "Timetable.json")


def delete_timetable_lec(sem, date_range, day_selected, subject_selected, lec_start, lec_end):
    lectures = Timetable[sem][date_range]["Weekly"][day_selected]

    for i, lec in enumerate(lectures):
        if lec["Start"] == lec_start and lec["End"] == lec_end and lec["Subject"] == subject_selected:
            lectures.pop(i)
            save_to_file(Timetable, "Timetable.json")
            return True
    return False


# holiday input
def holiday_input(date_selected, reason):
    found, date_range, sem = get_date_range(date_selected)
    if not found:
        return False
    else:
        Timetable[sem][date_range].setdefault("Holidays", {})
        Timetable[sem][date_range]["Holidays"][date_selected] = reason
        save_to_file(Timetable, "Timetable.json")
        return True

# check if there is holiday
def check_holiday(date_selected):
    found, date_range, sem = get_date_range(date_selected)
    if not found:
        return False
    holiday_dates = Timetable[sem][date_range].get("Holidays", {})
    return date_selected in holiday_dates






    


#____________________________________________________________________________________














def get_record(subject_selected):
    records = []
    for subject, date_entries in Subject.items():
        if subject_selected != "All Subjects" and subject != subject_selected:
            continue
        else:
            for date, lectures in date_entries.items():
                if date == "_meta":
                    continue
                for lec_uid, lec in lectures.items():
                    if lec["Type"] == "Canceled":
                        status = "Canceled"
                    elif lec["Present"] is None:
                        status = "Unmarked"
                    elif lec["Present"]:
                        status = "Present"
                    else:
                        status = "Absent"
                    records.append({ "Subject": subject, "Date": date, "Start": lec["Start"], "End": lec["End"], "Room": lec.get("Room", ""), "LectureID": lec_uid, "Status": status})

    records.sort(key=lambda x: ( x["Date"],x["Start"], x["Subject"]))
    return records

def chunk_list(list, n):
    for i in range(0, len(list), n):
        yield list[i:i + n]

def initialize_day(date_selected):
    day_name = date.fromisoformat(date_selected).strftime("%A")
    _, date_range, sem = get_date_range(date_selected)
    for lec in Timetable[sem][date_range]["Weekly"][day_name]:
        subject = lec["Subject"]
        start = lec["Start"]
        end = lec["End"]
        room = lec.get("Room", "")
        extra = lec.get("Extra", False)

        lec_uid = lec_uid_generate(date_selected, start, end, subject)
        Subject[subject].setdefault(date_selected, {})

        if lec_uid not in Subject[subject][date_selected]:
            Subject[subject][date_selected][lec_uid] = {
                "Start": start,
                "End": end,
                "Room": room,
                "Present": None,
                "Type": "Normal",
                "Extra": extra
            }

    save_to_file(Subject, "Attendence.json")

def initialize_timetable_range(date_range):
    full = check_date_in_range(str(date.today()), date_range)
    start_date, end_date = date_range_converter(date_range = date_range)
    start_date = date.fromisoformat(start_date)
    end_date = date.fromisoformat(end_date)
    
    if full:
        current_date_iter = start_date
    else:
        current_date_iter = date.today()
    while current_date_iter <= end_date:
        initialize_day(current_date_iter.isoformat())
        current_date_iter += timedelta(days=1)
    
    return True



