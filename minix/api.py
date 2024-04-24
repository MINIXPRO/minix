from __future__ import unicode_literals
import frappe
from datetime import date
from datetime import datetime
from frappe.utils.file_manager import save_url
import requests
import json
from frappe.utils.background_jobs import enqueue
from frappe import _
import sched
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart 
from email.message import EmailMessage

#****************************************************Login API******************************************************************************

@frappe.whitelist( allow_guest=True )
def login(usr, pwd):

    try:

        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()
    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key":0,
            "message":"Authentication Error!"
        }

        return

    api_generate = generate_keys(frappe.session.user)
    user = frappe.get_doc('User', frappe.session.user)
    frappe.response["message"] = {

        "success_key":1,
        "message":"Authentication success",
        "sid":frappe.session.sid,
        "api_key":user.api_key,
        "api_secret":api_generate,
        "username":user.username,
        "email":user.email

    }

def generate_keys(user):

    user_details = frappe.get_doc('User', user)
    api_secret = frappe.generate_hash(length=15)
    if not user_details.api_key:
        api_key = frappe.generate_hash(length=15)
        user_details.api_key = api_key
    user_details.api_secret = api_secret
    user_details.save()

    return api_secret

#***********************************






@frappe.whitelist(allow_guest=True)
def get_attendance():
    url = "http://api.microcrispr.com/Attendance1/api/Values?username=admin&&password=MerilADM"
    response = requests.get(url)
    if response.status_code == 200:
        json_response = response.json()


        if isinstance(json_response, str):
            try:
                json_response = json.loads(json_response)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return
        
        if not isinstance(json_response, list):
            print("JSON response is not a list:", type(json_response))
            return

        
        for item in json_response:
 
            if isinstance(item, dict):
                emp_code = item.get('EmpCode', '').strip()  
                office_punch = item.get('OFFICEPUNCH', '')
                print("***************************************************")
                #print(f"EmpCode: {emp_code}, OFFICEPUNCH: {office_punch}")

                print(emp_code)
                print(office_punch)
                values = frappe.db.sql(""" select employee_code, in_time from `tabAttendance Master` where employee_code=%s """,(emp_code),as_dict=True)
                if values:
                    val = frappe.db.sql(""" UPDATE `tabAttendance Master` SET out_time=%s where employee_code=%s""",(office_punch,emp_code))
                    frappe.db.commit()
                else:
                    doc = frappe.get_doc({
                        'doctype': 'Attendance Master',
                        'employee_code': emp_code,
                        'in_time': office_punch

                    })
                    doc.insert(ignore_permissions=True)
                    frappe.db.commit()


            else:
                print("Item is not a dictionary:", item)
    else:
        print("Failed to fetch data, status code:", response.status_code)



@frappe.whitelist(allow_guest=True)
def test():
    url = "http://api.microcrispr.com/Attendance1/api/Values?username=admin&&password=MerilADM"
    response = requests.get(url)
    if response.status_code == 200:
        json_response = response.json()


        if isinstance(json_response, str):
            try:
                json_response = json.loads(json_response)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return
        
        if not isinstance(json_response, list):
            print("JSON response is not a list:", type(json_response))
            return

        
        for item in json_response:
 
            if isinstance(item, dict):
                emp_code = item.get('EmpCode', '').strip()  
                office_punch = item.get('OFFICEPUNCH', '')
                print("***************************************************")
                print(emp_code)
                print(office_punch)
                office_punch_datetime = datetime.strptime(office_punch, '%Y-%m-%d %H:%M:%S')
                print(office_punch_datetime.date())
                values = frappe.db.sql(""" select employee_code, in_time from `tabAttendance Master` where employee_code=%s and in_time=%s """,(emp_code,office_punch_datetime),as_dict=True)
                if values:
                    print(values)
                #     val = frappe.db.sql(""" UPDATE `tabAttendance Master` SET out_time=%s where employee_code=%s""",(office_punch,emp_code))
                #     frappe.db.commit()
                # else:
                #     doc = frappe.get_doc({
                #         'doctype': 'Attendance Master',
                #         'employee_code': emp_code,
                #         'in_time': office_punch

                #     })
                #     doc.insert(ignore_permissions=True)
                #     frappe.db.commit()


            else:
                print("Item is not a dictionary:", item)
    else:
        print("Failed to fetch data, status code:", response.status_code)

    # values = frappe.db.sql(""" select * from `tabAttendance Master` limit 1 """,as_dict=True)
    # for i in values:
    #     print("******************************")
    #     print(i.in_time.date())
    #     if i.in_time..date() is null:
            







# @frappe.whitelist(allow_guest=True)
# def test():
#     url = "http://api.microcrispr.com/Attendance1/api/Values?username=admin&&password=MerilADM"
#     try:
#         response = requests.get(url)
#     except requests.RequestException as e:
#         print(f"Request failed: {e}")
#         return

#     if response.status_code == 200:
#         try:
#             json_response = response.json()
#         except json.JSONDecodeError as e:
#             print(f"Error decoding JSON: {e}")
#             return

#         if not isinstance(json_response, list):
#             print("JSON response is not a list:", type(json_response))
#             return

#         for item in json_response:
#             if isinstance(item, dict):
#                 emp_code = item.get('EmpCode', '').strip()
#                 office_punch = item.get('OFFICEPUNCH', '')

#                 print("***************************************************")
#                 print(emp_code)
#                 print(office_punch)

#                 # Convert office_punch from string to datetime object
#                 try:
#                     office_punch_datetime = datetime.strptime(office_punch, '%Y-%m-%d %H:%M:%S')
#                     print(office_punch_datetime.date())
#                 except ValueError as e:
#                     print(f"Error parsing office_punch datetime: {e}")
#                     continue

#                 # Example database interaction (commented out)
#                 # values = frappe.db.sql("""SELECT employee_code, in_time FROM `tabAttendance Master` WHERE employee_code=%s""", (emp_code), as_dict=True)
#                 # if values:
#                 #     val = frappe.db.sql("""UPDATE `tabAttendance Master` SET out_time=%s WHERE employee_code=%s""", (office_punch_datetime, emp_code))
#                 #     frappe.db.commit()
#                 # else:
#                 #     doc = frappe.get_doc({
#                 #         'doctype': 'Attendance Master',
#                 #         'employee_code': emp_code,
#                 #         'in_time': office_punch_datetime
#                 #     })
#                 #     doc.insert(ignore_permissions=True)
#                 #     frappe.db.commit()

#             else:
#                 print("Item is not a dictionary:", item)
#     else:
#         print("Failed to fetch data, status code:", response.status_code)

@frappe.whitelist()
def generate():
    doct = frappe.get_doc('Biometric Integration','Microcrispr')
    data = doct.url.format(frappe.utils.get_url())
    s = doct.from_date
    url = data + "&frm=" + str(s)
    headerInfo = {'content-type': 'application/json'}
    r = requests.get(url, headers=headerInfo)
    req = json.loads(r.text)
    reqs = json.loads(req)
    le = len(reqs)
    print(reqs)
    for i in range(0,le):
        id = reqs[i]["EmpCode"]
        datetime = reqs[i]["OFFICEPUNCH"]
        string_date = str(datetime)
        date = string_date.split(' ')[0]
        time = string_date.split(' ')[1]
        if frappe.db.exists({"doctype": "Employee Checkin", "employee": id,"time":date + " " + time}):
            pass
        else:
            doc = frappe.get_doc(dict(
                doctype = "Employee Checkin",
                employee = id,
                time = date + " " + time,
                device_id = "OFFICEPUNCH",
                skip_auto_attendance = '0'
            )).insert(ignore_permissions = False)
        frappe.db.commit()


@frappe.whitelist()
def manual(nam):
    doc = frappe.get_doc('Biometric Integration',nam)
    data = doc.url.format(frappe.utils.get_url())
    s = doc.from_date
    url = data + "&frm=" + str(s)
    print(nam)
    print(url)
    headerInfo = {'content-type': 'application/json'}
    r = requests.get(url, headers=headerInfo)
    req = json.loads(r.text)
    reqs = json.loads(req)
    le = len(reqs)
    print(reqs)
    for i in range(0,le):
        id = reqs[i]["EmpCode"]
        datetime = reqs[i]["OFFICEPUNCH"]
        string_date = str(datetime)
        date = string_date.split(' ')[0]
        time = string_date.split(' ')[1]
        # employee_nam = frappe.db.get_value('Employee',id,'employee_name')
        # or frappe.db.exists({"doctype": "Shift Assignment", "employee": id + ":" + employee_nam}):
        if frappe.db.exists({"doctype": "Employee Checkin", "employee": id,"time":date + " " + time}):
            pass
        else:
            doc = frappe.get_doc(dict(
                doctype = "Employee Checkin",
                employee = id,
                time = date + " " + time,
                device_id = "OFFICEPUNCH",
                skip_auto_attendance = '0'
            )).insert(ignore_permissions = False)
        frappe.db.commit()